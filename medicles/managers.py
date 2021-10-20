from django.db import models

from django.contrib.postgres.search import SearchVector, SearchVectorField, SearchQuery, SearchRank, TrigramSimilarity
from django.contrib.postgres.aggregates import StringAgg


class ArticleManager(models.Manager):
    def search(self, search_text):
        search_vectors = (
            SearchVector('article_abstract', weight = 'A', config = 'english')
            + SearchVector(
                StringAgg('keyword_list', delimiter = ';'),
                weight = 'B',
                config = 'english',
            )   
        )

        search_query = SearchQuery(search_text, config='english')
        
        search_rank = SearchRank(search_vectors, search_query)

        trigram_similarity = TrigramSimilarity('article_abstract', search_text)

        qs = (
            self.get_queryset()
            .filter(search_vector=search_query)
            .annotate(rank = search_rank + trigram_similarity)
            .order_by('-rank')
        )
        return qs