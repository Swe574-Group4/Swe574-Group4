import requests
import xml.etree.ElementTree as ET
#from .models import Article
import datetime
    
# url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=covid&retmode=json&retmax=500&usehistory=y"


# payload={}
# headers = {}

# response = requests.request("GET", url, headers=headers, data=payload)
# articles = response.json()
# web_env = articles['esearchresult']['webenv']
# query_key = articles['esearchresult']['querykey']
# print(web_env, query_key)

# count = int(articles['esearchresult']['count'])
# print(count)
# retmax = 100

# for retstart in range(300):
#     url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&"+ \
#     "WebEnv=" + web_env + \
#     "&query_key="+ query_key + \
#     "&rettype=abstract" + \
#     "&retstart=" + str(retstart) + \
#     "&retmax=" + str(retmax)
#     print(url)
#     payload={}
#     headers = {}
#     response = requests.request("POST", url, headers=headers, data=payload)
#     print(response.content)
#     print(len(response.content))
#     retstart += retmax

# url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&"+ \
# "WebEnv=" + web_env + \
# "&query_key="+ query_key + \
# "&rettype=abstract" + \
# "&retstart=0" + \
# "&retmax=100"
# print(url)
# payload={}
# headers = {}
# response = requests.request("POST", url, headers=headers, data=payload)
# print(response.content)
# print(len(response.content))

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
        # print("i: ", i, "articles[", i, ":", i+retmax, "]")
        # print(articles[i:i+retmax])
        articles_id = ','.join(articles[i:i+retmax])
        # print(articles_id)
        i +=retmax


        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id="+articles_id+"&rettype=abstract"
        print(url)
        payload={}
        headers = {}
        response = requests.request("POST", url, headers=headers, data=payload)
        print("Iteration: ", i)

        # Create xml tree using Element Tree.
        try:
            abs_tree = ET.fromstring(response.content)
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
                #print(author_list)
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


            # try:
            #     pubdate = ""
            #     for date in title.findall('MedlineCitation/Article/Journal/JournalIssue/PubDate'):
            #         year = str(date.find('Year').text)
            #         month = str(datetime.datetime.strptime(str(date.find('Month').text), '%b').month)
            #         day = str(date.find("Day").text)
            #         pubdate = year + "/" + month + "/" + day + " 00:00"
            #         pubdate = datetime.datetime.strptime(pubdate, '%Y/%m/%d %H:%M')
            # except Exception as e:
            #     print("PD Exception: ", e)
            #     continue
            
            try:
                pubdate = ""
                for date2 in title.findall(".//*[@PubStatus='pubmed']"):
                    year = str(date2.find('Year').text)
                    month = str(date2.find('Month').text)
                    day = str(date2.find("Day").text)
                    pubdate = year + "/" + month + "/" + day + " 00:00"
                    pubdate = datetime.datetime.strptime(pubdate, '%Y/%m/%d %H:%M')
                    print("PubDate output:", pubdate, " -- year:", year, " month:", month, " day:", day)
            except Exception as e:
                print("Pub Date Exception: ", e)
                continue

            #print(pubdate)
            # For each article, Put id, title and abstract_all and author_list into an array. 
            each_article_row = [id, pubdate, article_title, abstract_all, author_list, keyword_list]
            #print(each_article_row)
            # Append this into "all_articles" list. This will create 2D list.
            # all _articles = [[id1, title1, abstract1, author_list1],
            #                  [id2, title2, abstract2, author_list2]]
            all_articles.append(each_article_row)
    
    return all_articles

#print(get_articles_with_details("psychiatric", 20))
# from medicles import delete
# t = delete
# list = t.get_articles_with_details("covid", 50000)
# len(list)