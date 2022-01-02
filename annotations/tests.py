from unittest import TestCase

from annotations.models import AnnotationModel
import datetime


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

    def test_single_insert_to_db_successful(self):
        single_annotation = AnnotationModelTests.setUpAnnotationTestClassData()
        annotation = AnnotationModel.objects.create(
            annotation_json=single_annotation
        )
        print(annotation)
        self.assertEqual(annotation.annotation_json["type"], "Annotation")
        self.assertEqual(annotation.annotation_json["id"], "'http://localhost:8000/article/3454'")
        self.assertEqual(annotation.annotation_json["body"]["format"], 'text/plain')

    # def test_multiple_insert_to_db_successful(self):
    #   single_article_list = ArticleTests.setUpArticleTestClassData()
    #  for i in range(len(single_article_list)):
    #     article = Article.objects.create(article_id=single_article_list[i][0],
    #                                     pub_date=single_article_list[i][1],
    #                                    article_title=single_article_list[i][2],
    #                                   article_abstract=single_article_list[i][3],
    #                                  author_list=single_article_list[i][4],
    #                                 keyword_list=single_article_list[i][5]
    #                                )
    # print(article)
    # count = Article.objects.all().count()
    # self.assertEqual(count, len(single_article_list))

