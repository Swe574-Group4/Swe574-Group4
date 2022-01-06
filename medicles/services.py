
import requests
import xml.etree.ElementTree as ET
from .models import Article, Tag
import datetime
import json
from django.db import IntegrityError

def get_article_ids(term, retmax):
    term = term.replace(" ", "+")
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed" + \
        "&term=" + term + \
        "&retmode=json" + \
        "&retmax=" + str(retmax)

    payload={}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload)
    articles = response.json()
    #print(len(articles['esearchresult']['idlist']))
    article_list = []
    for i in range(len(articles['esearchresult']['idlist'])):
        article_list.append(articles['esearchresult']['idlist'][i])
    return article_list

def get_articles_with_details(term, retmax, retmax_iter):
    ## New empty list. We will append all information into this list.
    ## articles list will not be used. 
    all_articles = []

    # Get articles from method get_article_ids()
    articles = get_article_ids(term, retmax)
    #print(articles)
    retmax = retmax_iter
    i = 0

    while i < (len(articles)):
        articles_id = ','.join(articles[i:i+retmax])
        i +=retmax

        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id="+articles_id+"&rettype=abstract"
        #print(url)
        payload={}
        headers = {}
        response = requests.request("POST", url, headers=headers, data=payload)
        print("Iteration: ", i)
        # Create xml tree using Element Tree.
        try:
            abs_tree = ET.fromstring(response.content)
        #root=abs_tree.tag
        except Exception as e:
            print("ET Exception: ", e)
            continue

        # 'PubmedArticle/MedlineCitation' will find each article.
        # Using each article we will find PMID, Title, Abstract and Authors 
        for title in abs_tree.findall('PubmedArticle'):
            # Find ID of article.
            id = title.find('MedlineCitation/PMID').text

            # Find title of article.
            article_title = title.find('MedlineCitation/Article/ArticleTitle').text

            # Abstract field can have multiple AbstractText fields. We should get all of them.
            # Create an empty "abstract_all" variable. Iteratively search for AbstractText field and append it.
            abstract_all = ""
            for abstract in title.findall('MedlineCitation/Article/Abstract/AbstractText'):
                abstract_all += str(abstract.text)

            # AuthorList field can have multiple Author fields. Create an empty "author_list" variable.
            # Iteratively search for Author fields and append it to "author_list".
            # LastName and Forename are different fields. Merge them and put ";" between authors.
            # Remove ";" at the end of "author_list" using strip(';') function.
            try:
                author_list = ""
                for author in title.findall('MedlineCitation/Article/AuthorList/Author'):
                    author_name = author.find('LastName').text + " " + author.find('ForeName').text + ";"
                    author_list += author_name
                author_list = author_list.strip(';')
            except Exception as e:
                print("AL Exception: ", e)
                continue

            try:
                keyword_list = ""
                for keyword in title.findall('MedlineCitation/KeywordList/Keyword'):
                    keyword_list += str(keyword.text) + ";"
                keyword_list = keyword_list.strip(";")
                #print(keyword_list)
            except Exception as e:
                print("KL Exception: ", e)
                continue
            
            try:
                pubdate = ""
                for date2 in title.findall(".//*[@PubStatus='pubmed']"):
                    year = str(date2.find('Year').text)
                    month = str(date2.find('Month').text)
                    day = str(date2.find("Day").text)
                    if day.count('') <=2 and month.count('') <=2 :
                            pubdate = year + "/0" + month + "/0" + day
                    elif day.count('') <=2 and month.count('') >2 :
                        pubdate = year + "/" + month + "/0" + day
                    elif day.count('') >2 and month.count('') <=2 :
                        pubdate = year + "/0" + month + "/" + day
                    else:
                        pubdate = year + "/" + month + "/" + day # + " 00:00"
                    #pubdate = datetime.datetime.strptime(pubdate, '%Y/%m/%d %H:%M')
                    #print("PubDate output:", pubdate, " -- year:", year, " month:", month, " day:", day)
            except Exception as e:
                print("Pub Date Exception: ", e)
                continue

            # For each article, Put id, title and abstract_all and author_list into an array. 
            each_article_row = [id, pubdate, article_title, abstract_all, author_list, keyword_list]
            # Append this into "all_articles" list. This will create 2D list.
            # all _articles = [[id1, title1, abstract1, author_list1],
            #                  [id2, title2, abstract2, author_list2]]
            all_articles.append(each_article_row)
    
    return all_articles

def create_db(term, retmax, retmax_iter):
    articles = get_articles_with_details(term, retmax, retmax_iter)

    cleaned_articles = []
    for art in articles:
        if art[2]:
            cleaned_articles.append(art)
    
    start_index = 0
    end_index = 5000
    increment = end_index
    iter = len(cleaned_articles) / end_index
    i = 0
    div_articles = []
    while(i < iter):
        print('Iteration: ', i)
        if end_index > len(cleaned_articles):
            end_index = len(cleaned_articles)
        try:
            print('div_articles['+str(start_index)+':'+str(end_index)+']')
        except:
            pass
        div_articles = cleaned_articles[start_index:end_index]
        start_index += increment
        end_index += increment
        if end_index > len(cleaned_articles):
            end_index = len(cleaned_articles)
        i +=1

        Article.objects.bulk_create([Article(**{'article_id': a[0],
                                                'pub_date': a[1],
                                                'article_title': a[2],
                                                'article_abstract': a[3],
                                                'author_list': a[4],
                                                'keyword_list': a[5]})
                                            for a in div_articles],  ignore_conflicts=True)
        print(Article.objects.all().count(), ' articles are written into database.')
    query_result = Article.objects.all()

    return query_result


def update_db(term, retmax):
    latest_article_id = Article.objects.latest('article_id').article_id
    new_articles = get_articles_with_details(term, retmax)
    for i in range(len(new_articles)):
        if int(new_articles[i][0]) > latest_article_id:
            Article.objects.create(article_id = new_articles[i][0],
            pub_date = new_articles[i][1],
            article_title = new_articles[i][2],
            article_abstract = new_articles[i][3],
            author_list = new_articles[i][4],
            keyword_list = new_articles[i][5],
            )
    
    query_result = Article.objects.all()
    return query_result


class Wikidata():
    def get_wikidata_url_by_name(term):
        url = "https://www.wikidata.org/w/api.php?action=wbsearchentities&format=json&search=" + term + "&language=en"
        payload = {}
        headers = {}
        response = requests.get(url, headers=headers, data=payload)
        return json.loads(response.text)

    def get_tag_data(self, term):
        tag_list = self.get_wikidata_url_by_name(term)
        results = []
        for tag in tag_list['search']:
            #if len(tag['label'].split()) < 4:
                results.append(tag['label'] + " : " + tag['description']  +" : " + tag['id'])
            #print(tag)
        return results
        
'''
    def create_tag_data(self, term):
        tag_list = self.get_wikidata_url_by_name(term)
        for tag in tag_list['search']:
            if len(tag['label'].split()) < 4:
                Tag.objects.create(tag_key = tag['label'],
                                tag_value = tag['concepturi']
                )
                print('label:', tag['label'], 'url:', tag['concepturi'])
'''
