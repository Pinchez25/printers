from django.http import HttpRequest
from django.test import RequestFactory

from gallery.context_processors import company_config
from gallery.views import (capitalise_first_letter, get_client_ip, get_request_data, parse_pagination_params,
                           serialize_portfolio_item)
from .base import InMemoryMediaTestCase
from .factories import PortfolioItemFactory, ensure_company_config


class HelperFunctionTests(InMemoryMediaTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_capitalise_first_letter(self):
        self.assertEqual(capitalise_first_letter(" hello"), " Hello")
        self.assertEqual(capitalise_first_letter("123abc"), "123Abc")
        self.assertIsNone(capitalise_first_letter(None))

    def test_get_client_ip_prefers_forwarded(self):
        req = self.factory.get("/", HTTP_X_FORWARDED_FOR="1.2.3.4, 5.6.7.8")
        self.assertEqual(get_client_ip(req), "1.2.3.4")
        req = self.factory.get("/")
        req.META["REMOTE_ADDR"] = "9.9.9.9"
        self.assertEqual(get_client_ip(req), "9.9.9.9")

    def test_get_request_data_handles_json_and_form(self):
        req = self.factory.post("/", data={"a": "1"})
        self.assertEqual(get_request_data(req), {"a": "1"})
        req = self.factory.post("/", data="{\"a\": 2}", content_type="application/json")
        self.assertEqual(get_request_data(req), {"a": 2})
        req = self.factory.post("/", data="not json", content_type="application/json")
        self.assertEqual(get_request_data(req), {})

    def test_serialize_and_pagination_params(self):
        item = PortfolioItemFactory(title="alpha").create()
        data = serialize_portfolio_item(item)
        self.assertEqual(data["title"], "Alpha")
        req = self.factory.get("/", {"page": "x", "per_page": "y"})
        self.assertEqual(parse_pagination_params(req), (1, 6))


class ContextProcessorTests(InMemoryMediaTestCase):
    def test_company_config_in_context(self):
        ensure_company_config(email_configured=True)
        req = HttpRequest()
        ctx = company_config(req)
        self.assertIn("config", ctx)
        self.assertIn("admin_email", ctx)
