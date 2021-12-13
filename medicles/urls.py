from django.urls import path
from django.urls.conf import include
from . import views

app_name = 'medicles'

urlpatterns = [
    # Home page. Shows search bar without login
    path('', views.index, name='index'),

    # Search page. Results are shown in this page
    path('search/', views.search, name='search'),

    # Advanced search page
    # path('advanced_search/', views.advancedSearch, name='advanced_search'),
    path('advanced_search/', views.advanced_search, name='advanced_search'),

    path('article/<int:article_id>/', views.detail, name='detail'),

    # Tag detail page. Tagging operations are done in here
    path('tag/<int:article_id>/', views.add_tag, name='tag'),

    # Autocomplete page. This is not shown directly.
    # When type in Tag page, request are routed to this url.
    path('autocomplete/', views.ajax_load_tag, name='ajax_load_tag'),

    # Auth pages. Log in, Log out, Sign up
    path('accounts/', include('django.contrib.auth.urls')),

    path('signup/', views.signup, name='signup'),

    path('profile/<int:user_id>/', views.profile, name='profile'),

    path('usersearch/', views.user_search, name='user_search'),

    path('usersearchresults/', views.user_search_results, name='user_search_results'),

    # User Follow Action
    path('users/follow/', views.user_follow, name='user_follow'),

    # User Activity
    path('useractivity/', views.user_activity, name='user_activity'),

]
