from django.contrib.auth.models import User
from django.db import models
from django.db.models.fields.related import ManyToManyField
from medicles.managers import ArticleManager

from django.contrib.postgres.search import SearchVector, SearchVectorField


# Create your models here.

# Article will be filled Entrez API information.

class Article(models.Model):
    #article_id = models.BigIntegerField()
    article_id = models.AutoField(primary_key=True)
    pub_date = models.CharField(max_length=100, blank=True, null=True)
    #pub_date = models.DateTimeField()
    # pub_date = models.TextField(blank=True, null=True)
    article_title = models.TextField(blank=True, null=True)
    article_abstract = models.TextField(blank=True, null=True)
    author_list = models.TextField(blank=True, null=True)
    keyword_list = models.TextField(blank=True, null=True)
    search_vector = SearchVectorField(null=True, )
    #tags = models.TextField(blank=True, null=True)
    favourite = models.ManyToManyField(User,related_name='favourite', default=None, blank=True)

    #objects = ArticleManager()

    def __str__(self):
        return str(self.article_id)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        Article.objects.update(search_vector=(
            SearchVector('article_abstract', weight='A')
            + SearchVector('keyword_list', weight='B')
        )
        )


class Tag(models.Model):
    article = ManyToManyField(Article)
    user = ManyToManyField(User)
    tag_key = models.CharField(
        unique=True, blank=True, null=True, max_length=100)
    tag_value = models.CharField(blank=True, null=True, max_length=100)
