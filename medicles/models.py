from django.contrib.auth.models import User
from django.contrib.postgres.search import SearchVector, SearchVectorField
from django.db import models
from django.db.models.fields.related import ManyToManyField
from django.db.models import JSONField


# Create your models here.

# Article will be filled Entrez API information.

class Article(models.Model):
    # article_id = models.BigIntegerField()
    article_id = models.AutoField(primary_key=True)
    pub_date = models.CharField(max_length=100, blank=True, null=True)
    # pub_date = models.DateTimeField()
    # pub_date = models.TextField(blank=True, null=True)
    article_title = models.TextField(blank=True, null=True)
    article_abstract = models.TextField(blank=True, null=True)
    author_list = models.TextField(blank=True, null=True)
    keyword_list = models.TextField(blank=True, null=True)
    search_vector = SearchVectorField(null=True, )

    # tags = models.TextField(blank=True, null=True)

    # objects = ArticleManager()

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


class Contact(models.Model):
    user_from = models.ForeignKey('auth.User',
                                  related_name='rel_from_set',
                                  on_delete=models.CASCADE)
    user_to = models.ForeignKey('auth.User',
                                related_name='rel_to_set',
                                on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True,
                                   db_index=True)

    class Meta:
        ordering = ('-created',)

    def __str__(self) -> str:
        return f'{self.user_from} follow {self.user_to}'


class Search(models.Model):
    user = models.IntegerField(blank=True, null=True)
    term = models.TextField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)


class Annotation(models.Model):
    article = ManyToManyField(Article)
    user = ManyToManyField(User)
    annotation_key = models.CharField(unique=True, blank=True, null=True, max_length=100)
    annotation_value = models.CharField(blank=True, null=True, max_length=100)
    annotation_json = JSONField(default=dict)

