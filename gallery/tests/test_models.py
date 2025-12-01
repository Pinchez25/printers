from django.core.exceptions import ValidationError

from gallery.models import CompanyConfig, ContactQuery
from .base import InMemoryMediaTestCase
from .factories import PortfolioItemFactory, ensure_company_config


class PortfolioItemModelTests(InMemoryMediaTestCase):
    def test_creation_and_string_and_slug_uniqueness(self):
        item1 = PortfolioItemFactory(title="blue poster").create()
        item2 = PortfolioItemFactory(title="blue poster").create()
        self.assertEqual(str(item1), "blue poster")
        self.assertNotEqual(item1.slug, item2.slug)

    def test_get_image_url_returns_non_empty_string(self):
        item = PortfolioItemFactory().create()
        url = item.get_image_url()
        self.assertTrue(isinstance(url, str) and url)


class CompanyConfigModelTests(InMemoryMediaTestCase):
    def test_singleton_enforced(self):
        first = CompanyConfig.get_instance()
        with self.assertRaises(ValidationError):
            CompanyConfig().full_clean()
        self.assertTrue(first.pk)

    def test_is_email_configured_flag(self):
        cfg = ensure_company_config(email_configured=True)
        self.assertTrue(cfg.is_email_configured())
        cfg = ensure_company_config(email_configured=False)
        self.assertFalse(cfg.is_email_configured())


class ContactQueryModelTests(InMemoryMediaTestCase):
    def test_string_and_ordering(self):
        q1 = ContactQuery.objects.create(name="Alice", email="a@a.com", service_required="print", message="m1")
        q2 = ContactQuery.objects.create(name="Bob", email="b@b.com", service_required="design", message="m2")
        self.assertIn("Alice", str(q1))
        self.assertEqual(list(ContactQuery.objects.all()), [q2, q1])
