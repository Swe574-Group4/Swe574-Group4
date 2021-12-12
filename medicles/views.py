from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector, TrigramDistance
from medicles.forms import TagForm
from django.core import paginator
from django.http.response import Http404
from django.shortcuts import redirect, render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from medicles.models import Article, Tag, FavouriteListTable
from medicles.services import Wikidata
from .forms import SingupForm, TagForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError
from django.contrib.postgres.aggregates import StringAgg


# Create your views here.


def index(request):
    # context = "Welcome to medicles!"
    return render(request, 'medicles/index.html')


# def search(request):
#     search_term = request.GET.get('q', None)
#     #search_term = 'covid'
#     if not search_term:
#         render(request, 'medicles/index.html')
#         #raise Http404('Please enter a word at least!')

#     articles = Article.objects.search(search_term)
#     context = {'articles': articles}
#     #print(context)


#     return render(request, 'medicles/search_results.html', {'articles': articles}) # add context variable if you want to go back


def advanced_search(request):
    if request.GET.get("term") != None:
        search_term = request.GET.get('term', None)
        author = request.GET.get('author', None)
        # print(request.GET.get('author'))
        start_date = request.GET.get('start-date')
        print(request.GET.get)
        print(start_date)
        # print(request.GET.get('start_date'))
        end_date = request.GET.get('end-date')
        keyword = request.GET.get('keywords')
        if start_date == "":
            start_date = "1960-01-01"
        if end_date == "":
            end_date = "2021-11-30"
        print(end_date)
        if Article.objects.filter(pub_date__range=(start_date, end_date)).exists():
            articles = Article.objects.filter(
                article_title__icontains=search_term, author_list__icontains=author,
                pub_date__range=(start_date, end_date), keyword_list__icontains=keyword).values()
            return render(request, 'medicles/search_results.html', {'articles': articles})
        else:
            failure = "There is no articles between these dates. Please consider changing the Date Field."
            return render(request, 'medicles/advanced_search.html', {'failure': failure})

        # if articles != 0:
        # return render(request, 'medicles/search_results.html', {'articles': articles})
    else:
        return render(request, 'medicles/advanced_search.html')


def search(request):
    search_term = request.GET.get('q', None)
    if not search_term:
        render(request, 'medicles/index.html')
    # search_vector = SearchVector('keyword_list', weight='A') + SearchVector(
    #     'article_title', weight='B') + SearchVector('article_abstract', weight='B')
    search_vector = SearchVector('keyword_list', weight='A') + SearchVector(
        'article_title', weight='B')
    search_term_updated = SearchQuery(search_term, search_type='websearch')
    articles = Article.objects.annotate(distance=TrigramDistance(
        'keyword_list', search_term_updated)).filter(distance__lte=0.3).order_by('distance')
    # articles = Article.objects.annotate(search=SearchVector(
    #     'keyword_list', 'article_title', 'article_abstract'),).filter(search=SearchQuery(search_term))
    articles = Article.objects.annotate(search=SearchVector(
        'keyword_list', 'article_title'), ).filter(search=SearchQuery(search_term))
    articles = Article.objects.annotate(rank=SearchRank(
        search_vector, search_term_updated, cover_density=True)).filter(rank__gte=0.4).order_by('-rank')
    print("mainsearch")
    return render(request, 'medicles/search_results.html', {'articles': articles})


''' Working tag form. Simple, just adds one field to Article model.
def add_tag(request, article_id):
    if request.method =='POST':
        form = TagForm(request.POST)
        if form.is_valid():
            article_will_be_updated = Article.objects.get(pk=article_id)
            article_will_be_updated.tags = form.cleaned_data['tag_key'] + ":" + form.cleaned_data['tag_value']
            article_will_be_updated.save()
            print(form.cleaned_data['tag_key'], form.cleaned_data['tag_value'])
            return HttpResponseRedirect('/thanks')

    else:
        form = TagForm()

    return render(request, 'medicles/tag_create.html', {'form': form, 'article_id': article_id})
'''


def detail(request, article_id):
    # article = Article.objects.get(pk=article_id)
    article = get_object_or_404(Article, pk=article_id)

    # alert_flag = add_tag(request, article_id)
    alert_flag = False

    #print(FavouriteListTable.objects.filter(article=article).values_list('pk', flat=True)[0])


    alreadyFavourited = False
    if FavouriteListTable.objects.filter(article=article).exists():
        if FavouriteListTable.objects.filter(user=request.user.id).exists():
            print("adsasdsad")
            alreadyFavourited = True

    if FavouriteListTable.objects.filter(article=article).exists():
        if FavouriteListTable.objects.filter(user=request.user.id).exists():
            print("idk man")
    # user_updated = User.objects.get(pk=request.user.id)
    # favourite = FavouriteListTable()
    # favourite.save()
    # favourite.article.add(article)
    # favourite.user.add(user_updated)

    print("fav:", alreadyFavourited)
    return render(request, 'medicles/detail.html',
                  {'article': article, 'alert_flag': alert_flag, 'alreadyFavourited': alreadyFavourited})


@login_required
def add_tag(request, article_id):
    alert_flag = False
    if request.method == 'POST':
        form = TagForm(request.POST)

        tag_request_from_browser = ''
        if form.is_valid():
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
    # return render(request, 'medicles/tag_create.html', {'form': form, 'article_id': article_id})


def ajax_load_tag(request):
    if request.is_ajax():
        tag_query = request.GET.get('tag_query', '')
        tags = Wikidata.get_tag_data(Wikidata, tag_query)

        data = {
            'tags': tags,
        }
        return JsonResponse(data)


def signup(request):
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
    user = get_object_or_404(User, pk=user_id)

    return render(request, 'medicles/profile.html', {'user': user})


def user_search(request):
    return render(request, 'medicles/user_search.html')


def user_search_results(request):
    search_term = request.GET.get('name', None)
    if not search_term:
        render(request, 'medicles/user_search.html')
    search_vector = SearchVector('username', weight='A') + SearchVector('first_name', weight='B') + SearchVector(
        'last_name', weight='B')
    search_term_updated = SearchQuery(search_term, search_type='websearch')
    users = User.objects.annotate(rank=SearchRank(search_vector, search_term_updated, cover_density=True)).filter(
        rank__gte=0.4).order_by('-rank')
    return render(request, 'medicles/user_search_results.html', {'users': users})


# @login_required
# def follow_article(request, article_id):
#     article = get_object_or_404(Article, pk=article_id)
#
#     # Gets the article that will be associated
#     article_will_be_updated = Article.objects.get(pk=article_id)
#     # Gets the user that will be associated
#     user_will_be_updated = User.objects.get(pk=request.user.id)
#
#     print("user:",request.user.id)
#     print("pmıd:",article_id)
#     if article.favourite.filter(id=request.user.id).exists():
#         article.favourite.remove(request.user)
#
#     else:
#         article.favourite.add(request.user)
#
#     return HttpResponseRedirect(request.META['HTTP_REFERER'])
# return HttpResponseRedirect(request.path_info)
# return "stringX"
def follow_article(request, article_id):
    article = Article.objects.get(pk=article_id)

    user_updated = User.objects.get(pk=request.user.id)

    if request.method == 'POST':
        # form = TagForm(request.POST)

        # Article.objects.filter(favouritelisttable__user=user_will_be_updated).exists():
        if FavouriteListTable.objects.filter(article=article).exists():
            if FavouriteListTable.objects.filter(user=request.user.id).exists():


                # FavouriteListTable.article.remove(article)
                # FavouriteListTable.user.remove(user_updated)

                # favourite = FavouriteListTable()
                # favourite.article.remove(article)
                # favourite.user.remove(user_updated)
                #pk_value = FavouriteListTable.objects.filter(user=request.user.id).values_list('pk', flat=True)[0]
                pk_value = FavouriteListTable.objects.filter(article=article).values_list('pk', flat=True)[0]
                favourite = FavouriteListTable(pk=pk_value)
                favourite.article.remove(article)
                favourite.user.remove(user_updated)

        else:
            favourite = FavouriteListTable()
            favourite.save()
            favourite.article.add(article)
            favourite.user.add(user_updated)

    return HttpResponseRedirect(request.META['HTTP_REFERER'])
    # return


@login_required
def favourite_articles_list(request):
    favourite_articles = Article.objects.filter(favourite=request.user)
    return render(request, 'medicles/favourites.html', {'favourite_articles': favourite_articles})
