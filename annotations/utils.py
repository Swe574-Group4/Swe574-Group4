import datetime
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from annotations.models import AnnotationModel


def save_annotation_json(w3c_jsonld_annotation, article_id):
    annotation = AnnotationModel(
        annotation_json=w3c_jsonld_annotation
    )
    annotation.article_id = article_id
    annotation.save()
    return True
