from django.db import models
from django.db.models.deletion import CASCADE
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db.models import JSONField


class AnnotationModel(models.Model):
    annotation_json = JSONField(default=dict)
    #article_id = models.CharField(unique=True, blank=True, null=True, max_length=100)
