from unittest import TestCase

from django.test import Client

from annotations.models import AnnotationModel
import datetime

from medicles import services


class AnnotationModelTests(TestCase):
    @classmethod
    def setUpAnnotationTestClassData(cls):
        w3c_jsonld_annotation = {
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "id": f'http://localhost:8000/article/3454',
            "type": "Annotation",
            "body": {
                "type": "TextualBody",
                "purpose": "tagging",
                "value": "annotation_input",
                "format": "text/plain"
            },
            "target": {
                "source": f'http://localhost:8000/article/{"article_id"}',
                "selector": {
                    "type": "TextPositionSelector",
                    "start": "startIndex",
                    "end": "endIndex"
                },
                "text": "user_def_annotation_key"
            },
            "creator": {
                "id": "request.user.id",
                "type": "Person",
                "name": str("request.user"),
                "nickname": "pseudo",
                "email_sha1": "request.user.email"
            },
            "created": str(datetime.datetime.now().date())
        }

        return w3c_jsonld_annotation

    def setUpAnnotationTestClassDataMultiple(self):
        w3c_jsonld_annotation1 = {
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "id": f'http://localhost:8000/article/3454',
            "type": "Annotation",
            "body": {
                "type": "TextualBody",
                "purpose": "tagging",
                "value": "annotation_input",
                "format": "text/plain"
            },
            "target": {
                "source": f'http://localhost:8000/article/{"article_id"}',
                "selector": {
                    "type": "TextPositionSelector",
                    "start": "startIndex",
                    "end": "endIndex"
                },
                "text": "user_def_annotation_key"
            },
            "creator": {
                "id": "request.user.id",
                "type": "Person",
                "name": str("request.user"),
                "nickname": "pseudo",
                "email_sha1": "request.user.email"
            },
            "created": str(datetime.datetime.now().date())
        }

        w3c_jsonld_annotation2 = {
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "id": f'http://localhost:8000/article/3454',
            "type": "Annotation",
            "body": {
                "type": "TextualBody",
                "purpose": "tagging",
                "value": "annotation_input",
                "format": "text/plain"
            },
            "target": {
                "source": f'http://localhost:8000/article/{"article_id"}',
                "selector": {
                    "type": "TextPositionSelector",
                    "start": "startIndex",
                    "end": "endIndex"
                },
                "text": "user_def_annotation_key"
            },
            "creator": {
                "id": "request.user.id",
                "type": "Person",
                "name": str("request.user"),
                "nickname": "pseudo",
                "email_sha1": "request.user.email"
            },
            "created": str(datetime.datetime.now().date())
        }

        return [w3c_jsonld_annotation1, w3c_jsonld_annotation2]

    def test_single_insert_to_db_successful(self):
        single_annotation = AnnotationModelTests.setUpAnnotationTestClassData()
        annotation = AnnotationModel.objects.create(
            annotation_json=single_annotation
        )
        print(annotation)
        self.assertEqual(annotation.annotation_json["type"], "Annotation")
        self.assertEqual(annotation.annotation_json["id"], 'http://localhost:8000/article/3454')
        self.assertEqual(annotation.annotation_json["body"]["format"], 'text/plain')

    def test_multiple_insert_to_db_successful(self):
        multiple_annotation_list = AnnotationModelTests.setUpAnnotationTestClassDataMultiple(self)
        initial_count = AnnotationModel.objects.all().count()
        for i in range(len(multiple_annotation_list)):
            annotation_json = multiple_annotation_list[i]
            AnnotationModel.objects.create(annotation_json=annotation_json)
        count = AnnotationModel.objects.all().count()
        self.assertEqual(count, initial_count + len(multiple_annotation_list))

    def test_index_page_accessed_successfully(self):
        c = Client()
        response = c.get('/')
        self.assertEqual(response.status_code, 200)

    def test_search_page_accessed_successfully(self):
        c = Client()
        response = c.get('/search')
        self.assertEqual(response.status_code, 301)
