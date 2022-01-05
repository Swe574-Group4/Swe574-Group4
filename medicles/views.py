from django.http import HttpResponseBadRequest, HttpResponseRedirect
from .models import Contact, Search
import datetime
import json
import psycopg2
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector, TrigramDistance
from django.db import IntegrityError
from django.shortcuts import redirect, render, get_object_or_404, get_list_or_404
from medicles.forms import AnnotationForm
from medicles.models import Article, Tag, Annotation, FavouriteListTable
from medicles.services import Wikidata
from .forms import SingupForm, TagForm
from django.core.paginator import Paginator, EmptyPage
from collections import Counter
from actions.utils import create_action, delete_action
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from actions.models import Action
from django.http import HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

# Create your views here.

def index(request):
    """
    This function returns the home page of the application.
    
    * If user logged in, it will return user activities as well.
    * If user is anonymous, it will just provide search bar.
    """
    activities = []
    if not request.user.is_anonymous:
        action_users = Action.objects.filter(target_id=request.user.id, verb=1)
        print("User Last Login:", request.user.last_login)
        actor_user_last_login = request.user.last_login.replace(tzinfo=None)
        
        for user in action_users:
            user_actions = Action.objects.filter(user_id=user.user_id)
            for action in user_actions:
                # print(action.action_json)
                # print(json.loads(action.action_json)['published'])
                last_action = json.loads(action.action_json)
                published_date = last_action['published']
                activity_published_date = datetime.datetime.strptime(published_date[:-7], '%Y-%m-%dT%H:%M:%S')
                if activity_published_date < actor_user_last_login:
                    action_type = last_action['type']
                    action_actor_name= last_action['actor']['name']
                    action_actor_url = last_action['actor']['url']
                    action_object_name = last_action['object']['name']
                    action_object_url = last_action['object']['url']
                    activities.append([ action_type,
                                        action_actor_name,
                                        action_actor_url,
                                        action_object_name,
                                        action_object_url
                                        ])
                    print("Date is ", True)
    return render(request, 'medicles/index.html', {'activities': activities})

@csrf_exempt
def advanced_search(request):
    search_term = request.GET.get('term', None)
    author = request.GET.get('author', None)
    start_date = request.GET.get('start_date')
    radio = request.GET.get('radio')
    end_date = request.GET.get('end_date')
    keyword = request.GET.get('keywords')
    if start_date == "":
        start_date = "1960-01-01"
    if end_date == "":
        end_date = datetime.datetime.now()
    if search_term != None:
        if Article.objects.filter(author_list__icontains=author, pub_date__range=(start_date, end_date), keyword_list__icontains=keyword).exists():
            search_vector = SearchVector('keyword_list', weight='A') + SearchVector(
                'article_title', weight='B') + SearchVector('article_abstract', weight='B')
            search_term_updated = SearchQuery(
                search_term, search_type='websearch')
            # articles = Article.objects.annotate(distance=TrigramDistance(
            #     'keyword_list', search_term_updated)).filter(distance__lte=0.3).order_by('distance')
            articles = Article.objects.annotate(search=SearchVector(
                'keyword_list', 'article_title', 'article_abstract'), ).filter(search=SearchQuery(search_term))
            Article_id = Annotation.objects.filter(
                annotation_value__icontains=search_term).values('article_id')
            list = []
            for i in Article_id:
                id = i['article_id']
                list.append(id)
            noAnnotation = Article.objects.annotate(rank=SearchRank(
                search_vector, search_term_updated, cover_density=True)).filter(rank__gte=0.4,
                                                                                article_title__icontains=search_term,
                                                                                author_list__icontains=author,
                                                                                pub_date__range=(
                                                                                    start_date, end_date),
                                                                                keyword_list__icontains=keyword).values()
            articles = noAnnotation | Article.objects.annotate(rank=SearchRank(
                search_vector, search_term_updated, cover_density=True)).filter(rank__gte=0.4, article_id__in=list,
                                                                                author_list__icontains=author,
                                                                                pub_date__range=(
                                                                                    start_date, end_date),
                                                                                keyword_list__icontains=keyword).values()
            page_number = request.GET.get('page', 1)
            try:
                annotate = request.GET["annotation"]
                if annotate and radio == "desc":
                    articles = articles.order_by('-pub_date')
                    paginate = Paginator(articles, 20)
                    paginated_articles = paginate.get_page(page_number)
                    return render(request, 'medicles/advanced_searchresults.html', {'articles': articles, 'paginated_articles': paginated_articles,
                                                                                    'search_term': search_term, 'author': author, 'keywords': keyword, 'end_date': end_date,
                                                                                    'start_date': start_date, 'radio': radio, 'annotate': annotate})
                if annotate and radio == "asc":
                    articles = articles.order_by('pub_date')
                    paginate = Paginator(articles, 20)
                    paginated_articles = paginate.get_page(page_number)
                    return render(request, 'medicles/advanced_searchresults.html', {'articles': articles, 'paginated_articles': paginated_articles,
                                                                                    'search_term': search_term, 'author': author, 'keywords': keyword, 'end_date': end_date,
                                                                                    'start_date': start_date, 'radio': radio, 'annotate': annotate})
                # if request.GET["annotation"] and radio == "rank":
                #     articles = articles.order_by('-rank')
                #     return render(request, 'medicles/advanced_searchresults.html', {'articles': articles})
            except:
                if radio == "desc":
                    articles = noAnnotation.order_by('-pub_date')
                    paginate = Paginator(articles, 20)
                    paginated_articles = paginate.get_page(page_number)
                    return render(request, 'medicles/advanced_searchresults.html', {'articles': articles, 'paginated_articles': paginated_articles,
                                                                                    'search_term': search_term, 'author': author, 'keywords': keyword, 'end_date': end_date,
                                                                                    'start_date': start_date, 'radio': radio, 'paginate': paginate})
                if radio == "asc":
                    articles = noAnnotation.order_by('pub_date')
                    paginate = Paginator(articles, 20)
                    paginated_articles = paginate.get_page(page_number)
                    return render(request, 'medicles/advanced_searchresults.html', {'articles': articles, 'paginated_articles': paginated_articles,
                                                                                    'search_term': search_term, 'author': author, 'keywords': keyword, 'end_date': end_date,
                                                                                    'start_date': start_date, 'radio': radio, 'paginate': paginate})
                # else:
                #     articles = noAnnotation.order_by('-rank')
                #     return render(request, 'medicles/search_results.html', {'articles': articles})

        else:
            failure = "There is no articles between these dates. Please consider changing the Date Field."
            return render(request, 'medicles/advanced_search.html', {'failure': failure})
            # if request.is_ajax():
    #     text = request.GET.get('term')
    #     articles = Article.objects.filter(
    #         article_title__icontains=text).values()
    #     return JsonResponse({'articles': articles})
    else:
        return render(request, 'medicles/advanced_search.html')

def search(request):
    """
    This function provides main search functionality.

    * When you enter a word, it will search based on weights.
    * Weights are given below:
      * A: Keywords
      * B: Article title
      * C: Article Abstract
    """
    search_term = request.GET.get('q', None)
    if not search_term:
        render(request, 'medicles/index.html')
    search_vector = SearchVector('keyword_list', weight='A') + SearchVector(
        'article_title', weight='B') + SearchVector('article_abstract', weight='B')
    search_term_updated = SearchQuery(search_term, search_type='websearch')
    articles = Article.objects.annotate(distance=TrigramDistance(
        'keyword_list', search_term_updated)).filter(distance__lte=0.3).order_by('distance')
    articles = Article.objects.annotate(search=SearchVector(
        'keyword_list', 'article_title', 'article_abstract'), ).filter(search=SearchQuery(search_term))
    articles = Article.objects.annotate(rank=SearchRank(
        search_vector, search_term_updated, cover_density=True)).filter(rank__gte=0.4).order_by('-rank')
    print("mainsearch")

    paginate = Paginator(articles, 20)
    print('x', paginate)

    page_number = request.GET.get('page', 1)
    paginated_articles = paginate.get_page(page_number)

    search_obj = Search(user=request.user.id, term=search_term)
    search_obj.save()

    user_search_activity(request.user, search_term)

    return render(request, 'medicles/search_results.html', {'articles': articles, 'paginated_articles': paginated_articles, 'search_term': search_term})

def detail(request, article_id):
    """
    Returns detail of an article on a separate page.
    Provides below options:
    * You can tag the article both as free text or using Wikidata tags
    * You can favourite the article
    """
    article = Article.objects.get(pk=article_id)
    article = get_object_or_404(Article, pk=article_id)

    checkAnnotation = str(request.body).find("annotation_key")
    checkTag = str(request.body).find("tag_key")
    if checkAnnotation != -1:
        alert_flag = add_annotation(request, article_id)

    elif checkTag != -1:
        alert_flag = add_tag(request, article_id)

    else:
        alert_flag = False
    alreadyFavourited = False
    if FavouriteListTable.objects.filter(article=article).exists():
        if FavouriteListTable.objects.filter(user=request.user.id).exists():
            alreadyFavourited = True

    return render(request, 'medicles/detail.html',
                  {'article': article, 'alert_flag': alert_flag, 'alreadyFavourited': alreadyFavourited})

@ login_required
def add_tag(request, article_id):
    """
    This function helps you to tag the article.
    * You can use just free text
    * You can use just Wikidata tags
    * You can use both free and Wikidata tags
      If you use both, you will see your text on the page.
      However, when you click, it will redirect you to the Wikidata page.
    """
    alert_flag = False
    if request.method == 'POST':
        form = TagForm(request.POST)

        tag_request_from_browser = ''
        if form.is_valid():
            article_will_be_updated = Article.objects.get(
                pk=article_id)  # Gets the article that will be associated
            # Gets the user that will be associated
            article_will_be_updated = Article.objects.get(
                pk=article_id)  # Gets the article that will be associated
            # Gets the user that will be associated
            user_will_be_updated = User.objects.get(pk=request.user.id)
            print(request.user.id)
            tag_request_from_browser = form.cleaned_data['tag_key'].split(':')
            print(tag_request_from_browser)
            tag_key = tag_request_from_browser[0]
            user_def_tag_key = form.cleaned_data['user_def_tag_key']

            # If Wikidata tag_key and user defined user_def_tag_key exists. It will create user_def_tag_key.
            if tag_key and user_def_tag_key:
                try:
                    tag_value = 'http://www.wikidata.org/wiki/' + \
                                tag_request_from_browser[2]
                    # tag = Tag(tag_key = form.cleaned_data['tag_key'],
                    #         tag_value = form.cleaned_data['tag_value']
                    #         )
                    tag = Tag(tag_key=user_def_tag_key,
                              tag_value=tag_value
                              )
                    tag.save()
                    tag.article.add(article_will_be_updated)
                    tag.user.add(user_will_be_updated)
                except IntegrityError:
                    alert_flag = True
                    # return HttpResponseRedirect('medicles:index')

            # If user_def_tag_key does not exist. It will create Wikidata tag_key.
            elif not user_def_tag_key:
                try:
                    tag_value = 'http://www.wikidata.org/wiki/' + \
                                tag_request_from_browser[2]
                    # tag = Tag(tag_key = form.cleaned_data['tag_key'],
                    #         tag_value = form.cleaned_data['tag_value']
                    #         )
                    tag = Tag(tag_key=tag_key,
                              tag_value=tag_value
                              )
                    tag.save()
                    tag.article.add(article_will_be_updated)
                    tag.user.add(user_will_be_updated)
                    # return HttpResponseRedirect('medicles:index')
                except IntegrityError:
                    alert_flag = True

            # If Wikidata tag key does not exist. User defined user_def_tag_key will be created.
            elif not tag_key:
                try:
                    tag_value = ''
                    # tag = Tag(tag_key = form.cleaned_data['tag_key'],
                    #         tag_value = form.cleaned_data['tag_value']
                    #         )
                    tag = Tag(tag_key=user_def_tag_key,
                              tag_value=tag_value
                              )
                    tag.save()
                    tag.article.add(article_will_be_updated)
                    tag.user.add(user_will_be_updated)
                    # return HttpResponseRedirect('medicles:index')
                except IntegrityError:
                    alert_flag = True
            else:
                pass
    else:
        form = TagForm()

    return alert_flag

@ login_required
def add_annotation(request, article_id):
    alert_flag = False
    if request.method == 'POST':
        form = AnnotationForm(request.POST)

        annotation_request_from_browser = ''
        if form.is_valid():

            # Retrieve values for w3c_json_annotation from form data.
            article_will_be_updated = Article.objects.get(
                pk=article_id)  # Gets the article that will be associated
            # Gets the user that will be associated
            user_will_be_updated = User.objects.get(pk=request.user.id)
            print(request.user.id)
            annotation_request_from_browser = form.cleaned_data['annotation_key'].split(
                ':')
            print(annotation_request_from_browser)

            annotation_input = annotation_request_from_browser[0]
            user_def_annotation_key = form.cleaned_data['user_def_annotation_key']
            startIndex = form.data["annotation_start_index"]
            endIndex = form.data["annotation_end_index"]
            # If Wikidata tag_key and user defined user_def_tag_key exists. It will create user_def_tag_key.
            if annotation_input and user_def_annotation_key:
                try:
                    # Web Annotation Data Model - Text Position Selector JSON-LD Implementation
                    w3c_jsonld_annotation = {
                        "@context": "http://www.w3.org/ns/anno.jsonld",
                        "id": f'http://localhost:8000/article/{article_id}',
                        "type": "Annotation",
                        "body": {
                            "type": "TextualBody",
                            "purpose": "Tagging",
                            "value": annotation_input
                        },
                        "target": {
                            "source": user_def_annotation_key,
                            "selector": {
                                "type": "TextPositionSelector",
                                "start": startIndex,
                                "end": endIndex
                            }
                        },
                        "created": str(datetime.datetime.now().date())
                    }

                    print(w3c_jsonld_annotation)
                    annotation = Annotation(annotation_key=user_def_annotation_key,
                                            annotation_value=annotation_input,
                                            annotation_json=w3c_jsonld_annotation,
                                            article_id=article_id
                                            )
                    annotation.save()
                    annotation.article.add(article_will_be_updated)
                    annotation.user.add(user_will_be_updated)
                except IntegrityError:
                    alert_flag = True
                    # return HttpResponseRedirect('medicles:index')

            else:
                pass

    else:
        form = AnnotationForm()

    return alert_flag

def ajax_load_tag(request):
    """
    This function provides autocompletion for Wikidata tags.
    When use starts typing on article detail page,
    function will return the suggested Wikidata tags.
    """
    if request.is_ajax():
        tag_query = request.GET.get('tag_query', '')
        tags = Wikidata.get_tag_data(Wikidata, tag_query)

        data = {
            'tags': tags,
        }
        return JsonResponse(data)

def signup(request):
    """
    Provides basic signup functionality for users.
    """
    if request.method == 'POST':
        form = SingupForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            # print(username, password)
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect('medicles:index')
    else:
        print("not working")
        form = SingupForm()
    return render(request, 'medicles/signup.html', {'form': form})

def profile(request, user_id):
    user = User.objects.get(pk=user_id)
    followerCount = 0
    followingCount = 0

    tags = get_list_or_404(Tag, user=user_id)
    tagKeys = []
    for tag in tags:
        tagKeys.append(tag.tag_key)

    c = Counter(tagKeys)
    mostPopularTags = c.most_common(3)

    return render(request, 'medicles/profile.html', {'user': user, 'tags': tags, 'mostPopularTags': mostPopularTags, 'followerCount': followerCount, 'followingCount': followingCount})

def user_search(request):
    return render(request, 'medicles/user_search.html')

def user_search_results(request):
    search_term = request.GET.get('name', None)
    search_term_tag = request.GET.get('tags', None)
    if not search_term and search_term_tag:
        render(request, 'medicles/user_search.html')
    search_vector = SearchVector('username', weight='A') + SearchVector('first_name', weight='B') + SearchVector(
        'last_name', weight='B')
    search_vector_tag = SearchVector('tag_key', weight='A')
    search_term_updated = SearchQuery(search_term, search_type='websearch')
    search_term_updated_tag = SearchQuery(
        search_term_tag, search_type='websearch')
    users = User.objects.annotate(rank=SearchRank(search_vector, search_term_updated, cover_density=True)).filter(
        rank__gte=0.4).order_by('-rank')
    tags = Tag.objects.annotate(rank=SearchRank(search_vector_tag, search_term_updated_tag, cover_density=True)).filter(
        rank__gte=0.4).order_by('-rank')
    #taggedUsers = getUsersFromTagId(tags)
    taggedUsers = []
    return render(request, 'medicles/user_search_results.html', {'users': users, 'taggedUsers': taggedUsers})

# User Activity View
def user_activity(request):
    user_from = request.user.id
    all_actions = Action.objects.filter(user_id=user_from)
    detailed_actions = []
    for action in all_actions:
        if action.verb == 'is following':
            subject_user = User.objects.filter(id=user_from)

            print(subject_user.all)
            target_user = User.objects.filter(id=action.target_id)
            detailed_actions.append(
                [subject_user[0], subject_user[0].first_name + ' ' + subject_user[0].last_name, action.verb,
                 target_user[0].first_name + ' ' + target_user[0].last_name])
        if action.verb == 'searched':
            subject_user = User.objects.filter(id=user_from)

            print(subject_user.all)
            target_term = Search.objects.filter(id=action.target_id)
            detailed_actions.append(
                [subject_user[0], subject_user[0].first_name + ' ' + subject_user[0].last_name, action.verb,
                 target_term[0].term])

    return render(request, 'medicles/user_activity.html', {'detailed_actions': detailed_actions})


# Custom AJAX required decorator
def ajax_required(f):
    """
    AJAX request required decorator
    use it in your views:

    @ajax_required
    def my_view(request):
        ....
    """

    def wrap(request, *args, **kwargs):
        if not request.is_ajax():
            return HttpResponseBadRequest()
        return f(request, *args, **kwargs)

    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap


# Used in W3C_JSON variable in activity functions
home_url = "http://localhost:8000"

@ csrf_exempt
@ ajax_required
@ require_POST
@ login_required
def user_follow(request):
    """
    Provides User Following functionality.
    User the mode USER from native django.contrib.auth.models
    Writes actions to separate ACTIONS app as W3C standards suggests
    """
    user_id = request.POST.get('id')
    action = request.POST.get('action')

    # Target user object gets using below query
    user = User.objects.get(id=user_id)

    published_date = get_published_date()
    actor_profile_url = get_user_profile_url(request.user.id)
    actor_fullname = get_user_fullname(request.user)

    target_profile_url = get_user_profile_url(user.id)
    target_fullname = get_user_fullname(user)

    if user_id and action:
        try:
            # Moved below variable to outside of if-else condition
            # user = User.objects.get(id=user_id)

            # Activity Streams 2.0 JSON-LD Implementation
            w3c_json = json.dumps({
                "@context": "https://www.w3.org/ns/activitystreams",
                "summary": "{} is following {}".format(actor_fullname, target_fullname),
                "type": "Follow",
                "published": published_date,
                "actor": {
                    "type": "Person",
                    "id": actor_profile_url,
                    "name": actor_fullname,
                    "url": actor_profile_url
                },
                "object": {
                    "id": target_profile_url,
                    "type": "Person",
                    "url": target_profile_url,
                    "name": target_fullname,
                }
            })
            print(w3c_json)

            if action == 'follow':
                Contact.objects.get_or_create(user_from=request.user,
                                              user_to=user)
                create_action(request.user, verb=1,
                              activity_json=w3c_json, target=user)
            else:
                print("I am here!!!")
                Contact.objects.filter(user_from=request.user,
                                       user_to=user).delete()
                delete_action(request.user, verb=1, target=user)
            return JsonResponse({'status': 'ok'})
        except User.DoesNotExist:
            return JsonResponse({'status': 'error'})
    return JsonResponse({'status': 'error'})

def get_published_date():
    return str(datetime.datetime.now().isoformat())

# Gets user id as input and returns user profile
def get_user_profile_url(user_id):
    return home_url + "/user/" + str(user_id)

# Gets user object as input and returns User's Full Name
def get_user_fullname(user):
    return str(user.first_name + " " + user.last_name)


def user_search_activity(user, search_term):
    """
    This function saves user activity of each user.
    It is being used in search() function above.
    """
    now = timezone.now()
    last_minute = now - datetime.timedelta(seconds=60)
    target_search = Search.objects.filter(
        user=user.id, term=search_term, created__gte=last_minute).last()

    # Variables used for actor
    published_date = get_published_date()
    actor_profile_url = get_user_profile_url(user.id)
    actor_fullname = get_user_fullname(user)

    # Variables used for target
    target_object_url = get_target_search_url(target_search.id)
    target_object_name = get_target_search_name(target_search.id)

    # Activity Streams 2.0 JSON-LD Implementation
    w3c_json = json.dumps({
        "@context": "https://www.w3.org/ns/activitystreams",
        "summary": "{} searched {}".format(actor_fullname, target_object_name),
        "type": "Search",
        "published": published_date,
        "actor": {
            "type": "Person",
            "id": actor_profile_url,
            "name": actor_fullname,
            "url": actor_profile_url
        },
        "object": {
            "id": target_object_url,
            "type": "Article",
            "url": target_object_url,
            "name": target_object_name,
        }
    })
    print(w3c_json)

    # Create action for search term for a specific user
    create_action(user=user, verb=3, activity_json=w3c_json,
                  target=target_search)
    return True

# Gets target search url used in activity json
def get_target_search_url(id):
    return home_url + "/search/" + str(id)

# Gets target search name used in activity json
def get_target_search_name(id):
    search_obj = Search.objects.filter(id=id)
    print('Search object: ', search_obj)
    return search_obj[0].term

# Gets target article url used in activity json
def get_target_article_url(id):
    return home_url + "/article/" + str(id)

@ csrf_exempt
# @ajax_required
@ require_POST
@ login_required
def favourite_article(request, article_id):
    article = Article.objects.get(pk=article_id)
    user_updated = User.objects.get(pk=request.user.id)

    # Variables used for actor
    published_date = get_published_date()
    actor_profile_url = get_user_profile_url(user_updated)
    actor_fullname = get_user_fullname(user_updated)

    # Variables used for target
    target_object_url = get_target_article_url(article.article_id)
    target_object_name = article.article_title

    # Activity Streams 2.0 JSON-LD Implementation
    w3c_json = json.dumps({
        "@context": "https://www.w3.org/ns/activitystreams",
        "summary": "{} favorited {}".format(actor_fullname, target_object_name),
        "type": "Favourite",
        "published": published_date,
        "actor": {
            "type": "Person",
            "id": actor_profile_url,
            "name": actor_fullname,
            "url": actor_profile_url
        },
        "object": {
            "id": target_object_url,
            "type": "Article",
            "url": target_object_url,
            "name": target_object_name,
        }
    })
    print(w3c_json)

    # remove user and article id info from favouriteListTable in database
    if FavouriteListTable.objects.filter(article=article).exists() and FavouriteListTable.objects.filter(
            user=request.user.id).exists():

        favourite = FavouriteListTable.objects.filter(
            article=article, user=user_updated)
        favourite.delete()

        # Delete action for favorite article by specific user
        delete_action(user=user_updated, verb=4, target=article)

    # save and link user and article id in database
    else:
        favourite = FavouriteListTable(article=article, user=user_updated)
        favourite.save()

        # Create action for favorite article by specific user
        create_action(user=user_updated, verb=4, activity_json=w3c_json, target=article)

    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def favourite_article_List(request):
    # get current user and user's favorited articles
    current_user = User.objects.get(pk=request.user.id)
    users_favourite_list = FavouriteListTable.objects.filter(user=current_user)

    # retrieve article_id and the article objects from Article table
    article_id_list = []
    for object in users_favourite_list:
        article_id_list.append(object.article_id)
    articles = Article.objects.filter(article_id__in=article_id_list)

    return render(request, 'medicles/favourites.html', {'articles': articles})


def getUsersFromTagId(tags) -> list[User]:
    userTags = getUsersWithQuery(tags)

    userList = [User]
    for userTag in userTags:
        user = get_object_or_404(User, id=userTag)
        userList.append(user)

    return userList


def getUsersWithQuery(tags) -> list[int]:
    userTags = []
    conn = psycopg2.connect(
        host="localhost",
        database="medicles",
        user="postgres",
        password="postgres"
    )
    cur = conn.cursor()
    sql = 'select user_id from medicles_tag_user where id = %s;'
    for tag1 in tags:
        cur.execute(sql, (tag1.id,))
        result = cur.fetchone()
        userTags.append(result[0])

    return userTags
