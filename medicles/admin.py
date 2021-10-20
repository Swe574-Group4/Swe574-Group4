from django.contrib import admin
from django.urls.base import clear_script_prefix

from.models import Article

# Register your models here.

class ArticleAdmin(admin.ModelAdmin):
    list_display = ('article_id', 'pub_date','article_title')

admin.site.register(Article, ArticleAdmin)