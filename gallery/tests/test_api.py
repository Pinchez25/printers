from django.urls import reverse
from rest_framework.test import APIClient

from .base import InMemoryMediaTestCase
from .factories import PortfolioItemFactory


class GalleryApiTests(InMemoryMediaTestCase):
    def setUp(self):
        self.client = APIClient()

    def test_list_paginates_and_filters_published(self):
        for i in range(8):
            PortfolioItemFactory(title=f"item {i}", tags=["alpha"]).create()
        PortfolioItemFactory(is_published=False).create()

        url = reverse("gallery:gallery_api")
        res = self.client.get(url, {"page": 1, "per_page": 6})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])  # type: ignore[index]
        self.assertEqual(len(data["items"]), 6)  # type: ignore[index]
        self.assertEqual(data["pagination"]["total_items"], 8)  # type: ignore[index]

    def test_search_and_tag_filters(self):
        PortfolioItemFactory(title="Crimson Banner", tags=["promo", "print"]).create()
        PortfolioItemFactory(title="Azure Flyer", tags=["print"]).create()
        PortfolioItemFactory(title="Green Mug", tags=["merch"]).create()

        url = reverse("gallery:gallery_api")
        res = self.client.get(url, {"search": "banner"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()["items"]), 1)  # type: ignore[index]

        res = self.client.get(url, {"tags": "print"})
        self.assertEqual(len(res.json()["items"]), 2)  # type: ignore[index]

        res = self.client.get(url, {"tags": "print,promo"})
        self.assertEqual(len(res.json()["items"]), 1)  # type: ignore[index]

        res = self.client.get(url, {"tags[]": ["all"]})
        self.assertGreaterEqual(len(res.json()["items"]), 3)  # type: ignore[index]

    def test_invalid_page_params_defaults(self):
        PortfolioItemFactory().create()
        url = reverse("gallery:gallery_api")
        res = self.client.get(url, {"page": "x", "per_page": "y"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["pagination"]["current_page"], 1)  # type: ignore[index]


class GalleryTagsApiTests(InMemoryMediaTestCase):
    def setUp(self):
        self.client = APIClient()

    def test_returns_popular_tags_payload(self):
        PortfolioItemFactory(tags=["one", "two"]).create()
        PortfolioItemFactory(tags=["two"]).create()
        url = reverse("gallery:gallery_tags_api")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])  # type: ignore[index]
        names = [t["name"] for t in body["tags"]]  # type: ignore[index]
        self.assertIn("two", names)
