from django.contrib.auth.models import User
from django.contrib.postgres.search import SearchVector, SearchVectorField
from django.db import models
from django.db.models.fields.related import ManyToManyField

from django.db.models.deletion import CASCADE

from django.db.models import JSONField
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in


# Create your models here.

# Article will be filled Entrez API information.
class Article(models.Model):
    # article_id = models.BigIntegerField()
    article_id = models.AutoField(primary_key=True)
    pub_date = models.CharField(max_length=100, blank=True, null=True)
    # pub_date = models.DateTimeField()
    article_title = models.TextField(blank=True, null=True)
    article_abstract = models.TextField(blank=True, null=True)
    author_list = models.TextField(blank=True, null=True)
    keyword_list = models.TextField(blank=True, null=True)
    search_vector = SearchVectorField(null=True, )

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


# This model is used for Tagging functionality
class Tag(models.Model):
    article = ManyToManyField(Article)
    user = ManyToManyField(User)
    tag_key = models.CharField(
        blank=True, null=True, max_length=100)
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


# Add following field to User dynamically
# user_model = get_user_model()
# user_model.add_to_class('following',
#                         models.ManyToManyField('self',
#                         through=Contact,
#                         related_name='followers',
#                         symmetrical=False))

# This model is used as part of Searching activity
class Search(models.Model):
    user = models.IntegerField(blank=True, null=True)
    term = models.TextField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)


# This model is used for Annotation
class Annotation(models.Model):
    article = ManyToManyField(Article)
    article_id = models.CharField(max_length=100, blank=True, null=True)
    user = ManyToManyField(User)
    annotation_key = models.CharField(
        unique=True, blank=True, null=True, max_length=100)
    annotation_value = models.CharField(blank=True, null=True, max_length=100)
    annotation_json = JSONField(default=dict)


# This model is used for Favourited Articles
class FavouriteListTable(models.Model):
    article = models.ForeignKey(Article,
                                db_index=True,
                                blank=True,
                                null=True,
                                on_delete=CASCADE)
    user = models.ForeignKey('auth.User',
                             db_index=True,
                             blank=True,
                             null=True,
                             on_delete=CASCADE)


class CustomUser(models.Model):
    user = models.ForeignKey('auth.User',
                             db_index=True,
                             blank=True,
                             null=True,
                             on_delete=CASCADE)
    last_login = models.DateTimeField(blank=True, null=True, )


def save_last_login(sender, user, **kwargs):
    user = User.objects.get(pk=user.id)
    CustomUser(user=user, last_login=user.last_login).save()


user_logged_in.connect(save_last_login, dispatch_uid="save_last_login")
