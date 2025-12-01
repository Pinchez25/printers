from unittest.mock import patch

from django.core import mail
from django.test import Client
from django.urls import reverse

from gallery.models import ContactQuery
from .base import InMemoryMediaTestCase
from .factories import PortfolioItemFactory, ensure_company_config


class IndexViewTests(InMemoryMediaTestCase):
    def setUp(self):
        self.client = Client()

    def test_index_shows_only_published_items(self):
        PortfolioItemFactory(is_published=True, tags=["alpha"]).create()
        PortfolioItemFactory(is_published=False, tags=["beta"]).create()
        response = self.client.get(reverse("gallery:index"))
        self.assertEqual(response.status_code, 200)
        items = list(response.context["portfolio_items"])  # type: ignore[index]
        self.assertEqual(len(items), 1)
        self.assertIn("all_tags", response.context)


class ContactFormViewTests(InMemoryMediaTestCase):
    def setUp(self):
        self.client = Client()

    def test_missing_fields_returns_400(self):
        ensure_company_config(email_configured=True)
        url = reverse("gallery:contact_form")
        res = self.client.post(url, data={"name": "", "email": "", "message": ""})
        self.assertEqual(res.status_code, 400)
        self.assertFalse(ContactQuery.objects.exists())

    def test_service_unavailable_when_email_not_configured(self):
        ensure_company_config(email_configured=False)
        url = reverse("gallery:contact_form")
        res = self.client.post(url, data={"name": "A", "email": "a@a.com", "message": "Hi"})
        self.assertEqual(res.status_code, 503)

    def test_success_sends_email_and_optionally_saves_query(self):
        ensure_company_config(email_configured=True, always_save=True)
        url = reverse("gallery:contact_form")
        res = self.client.post(url, data={
            "name": "Alice", "email": "alice@example.com", "message": "Hello", "service": "other",
        })
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["success"])  # type: ignore[index]
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(ContactQuery.objects.count(), 1)

    def test_transaction_rolls_back_on_send_failure(self):
        ensure_company_config(email_configured=True, always_save=True)
        url = reverse("gallery:contact_form")
        with patch("gallery.views.send_mail", side_effect=OSError("fail")):
            res = self.client.post(url, data={
                "name": "Alice", "email": "alice@example.com", "message": "Hello", "service": "other",
            })
        self.assertEqual(res.status_code, 500)
        self.assertEqual(ContactQuery.objects.count(), 0)
