from django.test import TestCase

from gallery.filters import PortfolioItemFilter, get_popular_tags
from .factories import PortfolioItemFactory


class PortfolioItemFilterTests(TestCase):
    def setUp(self):
        PortfolioItemFactory(title="Red Book", tags=["print"]).create()
        PortfolioItemFactory(title="Blue Book", tags=["promo"]).create()
        PortfolioItemFactory(title="Green Pen", tags=["print", "promo"]).create()

    def test_search_matches_title_and_description_and_normalised(self):
        f = PortfolioItemFilter(data={"search": "greenpen", "is_published": True})
        self.assertEqual(f.qs.count(), 1)

    def test_tags_and_tag_list_filters(self):
        f = PortfolioItemFilter(data={"tag_list": "print", "is_published": True})
        self.assertEqual(f.qs.count(), 2)
        f = PortfolioItemFilter(data={"tag_list": "print,promo", "is_published": True})
        self.assertEqual(f.qs.count(), 1)

    def test_get_popular_tags_returns_at_least_existing(self):
        tags = list(get_popular_tags(limit=10))
        names = {t.name for t in tags}
        self.assertTrue({"print", "promo"}.issubset(names))
