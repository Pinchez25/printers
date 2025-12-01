import uuid
from datetime import timezone as dt_timezone
from unittest.mock import patch, MagicMock
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from taggit.models import Tag

from gallery.models import PortfolioItem, CompanyConfig, ContactQuery, upload_to
from gallery.storage_backends import SupabaseStorage


class PortfolioItemModelTestCase(TestCase):

    def setUp(self):
        self.valid_title = "Test Portfolio Item"
        self.valid_description = "A test description"
        self.valid_image = SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        # Mock storage to prevent real network calls
        self.storage_patchers = [
            patch.object(SupabaseStorage, '_save', return_value='mock/path.jpg'),
            patch.object(SupabaseStorage, '_get_file_metadata', return_value={'name': 'mock.jpg', 'size': 100}),
            patch.object(SupabaseStorage, 'url', return_value='http://mock.com/image.jpg'),
        ]
        for p in self.storage_patchers:
            p.start()

    def tearDown(self):
        for p in self.storage_patchers:
            p.stop()

    def test_portfolio_item_creation_minimal(self):
        item = PortfolioItem.objects.create(
            title=self.valid_title,
            image=self.valid_image
        )
        self.assertEqual(item.title, self.valid_title)
        self.assertEqual(item.description, "")
        self.assertTrue(item.is_published)
        self.assertIsNotNone(item.created_at)
        self.assertIsNotNone(item.updated_at)
        self.assertEqual(str(item), self.valid_title)

    def test_portfolio_item_creation_full(self):
        item = PortfolioItem.objects.create(
            title=self.valid_title,
            description=self.valid_description,
            image=self.valid_image,
            is_published=False
        )
        self.assertEqual(item.title, self.valid_title)
        self.assertEqual(item.description, self.valid_description)
        self.assertFalse(item.is_published)

    def test_slug_auto_generation(self):
        item = PortfolioItem.objects.create(
            title=self.valid_title,
            image=self.valid_image
        )
        self.assertEqual(item.slug, "test-portfolio-item")

    def test_slug_uniqueness(self):
        item1 = PortfolioItem.objects.create(
            title=self.valid_title,
            image=self.valid_image
        )
        item2 = PortfolioItem.objects.create(
            title=self.valid_title,
            image=SimpleUploadedFile("test2.jpg", b"file_content", content_type="image/jpeg")
        )
        self.assertNotEqual(item1.slug, item2.slug)
        self.assertTrue(item2.slug.startswith("test-portfolio-item"))

    @patch('gallery.models.reverse')
    def test_get_absolute_url(self, mock_reverse):
        mock_reverse.return_value = f"/gallery/test-slug/"
        item = PortfolioItem.objects.create(
            title=self.valid_title,
            image=self.valid_image
        )
        result = item.get_absolute_url()
        mock_reverse.assert_called_once_with("gallery:detail", kwargs={"slug": item.slug})
        self.assertEqual(result, "/gallery/test-slug/")

    @patch('gallery.models.static')
    def test_get_image_url_success(self, mock_static):
        mock_static.return_value = "/static/default.jpg"
        item = PortfolioItem.objects.create(
            title=self.valid_title,
            image=self.valid_image
        )
        mock_image = MagicMock()
        mock_image.url = 'http://example.com/test.jpg'
        item.image = mock_image
        self.assertEqual(item.get_image_url(), 'http://example.com/test.jpg')

    @patch('gallery.models.static')
    def test_get_image_url_fallback(self, mock_static):
        mock_static.return_value = "/static/default.jpg"
        item = PortfolioItem.objects.create(
            title=self.valid_title,
            image=self.valid_image
        )
        with patch.object(item.image.storage, 'url', side_effect=Exception("Storage error")):
            result = item.get_image_url()
            self.assertEqual(result, "/static/default.jpg")

    def test_title_max_length(self):
        max_length = PortfolioItem._meta.get_field('title').max_length
        self.assertEqual(max_length, 200)

    def test_description_blank(self):
        item = PortfolioItem.objects.create(
            title=self.valid_title,
            image=self.valid_image
        )
        self.assertEqual(item.description, "")

    def test_is_published_default_true(self):
        item = PortfolioItem.objects.create(
            title=self.valid_title,
            image=self.valid_image
        )
        self.assertTrue(item.is_published)

    def test_created_at_auto_now_add(self):
        before = timezone.now()
        item = PortfolioItem.objects.create(
            title=self.valid_title,
            image=self.valid_image
        )
        after = timezone.now()
        self.assertGreaterEqual(item.created_at, before)
        self.assertLessEqual(item.created_at, after)

    def test_updated_at_auto_now(self):
        item = PortfolioItem.objects.create(
            title=self.valid_title,
            image=self.valid_image
        )
        original_updated = item.updated_at
        item.title = "Updated Title"
        item.save()
        self.assertGreater(item.updated_at, original_updated)

    def test_ordering_by_created_at_desc(self):
        item1 = PortfolioItem.objects.create(
            title="First",
            image=self.valid_image
        )
        item2 = PortfolioItem.objects.create(
            title="Second",
            image=SimpleUploadedFile("test2.jpg", b"file_content", content_type="image/jpeg")
        )
        items = list(PortfolioItem.objects.all())
        self.assertEqual(items[0], item2)
        self.assertEqual(items[1], item1)

    def test_tags_blank_by_default(self):
        item = PortfolioItem.objects.create(
            title=self.valid_title,
            image=self.valid_image
        )
        self.assertEqual(list(item.tags.all()), [])

    def test_tags_add_and_retrieve(self):
        item = PortfolioItem.objects.create(
            title=self.valid_title,
            image=self.valid_image
        )
        tag1 = Tag.objects.create(name="tag1")
        tag2 = Tag.objects.create(name="tag2")
        item.tags.add(tag1, tag2)
        self.assertIn(tag1, item.tags.all())
        self.assertIn(tag2, item.tags.all())

    def test_upload_to_function(self):
        mock_instance = MagicMock()
        mock_instance.created_at = timezone.now()
        filename = "test.jpg"
        path = upload_to(mock_instance, filename)
        self.assertIn(str(mock_instance.created_at.year), path)
        self.assertIn(str(mock_instance.created_at.month), path)
        self.assertTrue(path.endswith('.jpg'))
        parts = path.split('/')
        self.assertEqual(parts[0], 'portfolio')
        filename_part = parts[-1]
        name_without_ext = filename_part.split('.')[0]
        self.assertTrue(uuid.UUID(name_without_ext))

    def test_upload_to_without_created_at(self):
        mock_instance = MagicMock()
        mock_instance.created_at = None
        filename = "test.jpg"
        path = upload_to(mock_instance, filename)
        now = timezone.now()
        self.assertIn(str(now.year), path)
        self.assertIn(str(now.month), path)


class CompanyConfigModelTestCase(TestCase):

    def setUp(self):
        self.valid_address = "123 Test Street"
        self.valid_contact_number = "254712345678"
        self.valid_facebook_username = "testfb"
        self.valid_twitter_username = "testtw"
        self.valid_instagram_username = "testig"
        self.valid_tiktok = "testtt"
        self.valid_email_host = "smtp.gmail.com"
        self.valid_email_port = 587
        self.valid_email_username = "test@example.com"
        self.valid_email_password = "testpass"
        self.valid_email_from_address = "from@example.com"
        self.valid_email_to_address = "to@example.com"

    def test_company_config_creation_first(self):
        config = CompanyConfig.objects.create()
        self.assertTrue(config.singleton_enforcer)
        self.assertEqual(str(config), "Company Configuration")

    def test_singleton_enforcer_unique(self):
        CompanyConfig.objects.create()
        with self.assertRaises(Exception):
            CompanyConfig.objects.create()

    def test_get_instance_creates_if_none(self):
        config = CompanyConfig.get_instance()
        self.assertIsInstance(config, CompanyConfig)
        self.assertTrue(config.singleton_enforcer)

    def test_get_instance_returns_existing(self):
        config1 = CompanyConfig.get_instance()
        config2 = CompanyConfig.get_instance()
        self.assertEqual(config1, config2)

    def test_save_sets_singleton_enforcer(self):
        config = CompanyConfig()
        config.save()
        self.assertTrue(config.singleton_enforcer)

    def test_clean_allows_first_instance(self):
        config = CompanyConfig()
        config.full_clean()

    def test_clean_raises_validation_error_on_second_instance(self):
        CompanyConfig.objects.create()
        config = CompanyConfig()
        with self.assertRaises(ValidationError):
            config.full_clean()

    def test_is_email_configured_true(self):
        config = CompanyConfig.objects.create(
            email_host=self.valid_email_host,
            email_username=self.valid_email_username,
            email_password=self.valid_email_password
        )
        self.assertTrue(config.is_email_configured())

    def test_is_email_configured_false_missing_username(self):
        config = CompanyConfig.objects.create(
            email_password=self.valid_email_password
        )
        self.assertFalse(config.is_email_configured())

    def test_is_email_configured_false_missing_username(self):
        config = CompanyConfig.objects.create(
            email_host=self.valid_email_host,
            email_password=self.valid_email_password
        )
        self.assertFalse(config.is_email_configured())

    def test_is_email_configured_false_missing_password(self):
        config = CompanyConfig.objects.create(
            email_host=self.valid_email_host,
            email_username=self.valid_email_username
        )
        self.assertFalse(config.is_email_configured())

    def test_email_fields_defaults(self):
        config = CompanyConfig.objects.create()
        self.assertEqual(config.email_host, "smtp.gmail.com")
        self.assertEqual(config.email_port, 587)
        self.assertTrue(config.email_use_tls)

    def test_address_blank(self):
        config = CompanyConfig.objects.create()
        self.assertEqual(config.address, "")

    def test_contact_number_max_length(self):
        max_length = CompanyConfig._meta.get_field('contact_number').max_length
        self.assertEqual(max_length, 20)

    def test_username_fields_max_length(self):
        max_length = CompanyConfig._meta.get_field('facebook_username').max_length
        self.assertEqual(max_length, 100)

    def test_email_fields_max_length(self):
        max_length = CompanyConfig._meta.get_field('email_host').max_length
        self.assertEqual(max_length, 255)

    def test_always_save_contactus_queries_default_false(self):
        config = CompanyConfig.objects.create()
        self.assertFalse(config.always_save_contactus_queries)

    def test_email_use_tls_default_true(self):
        config = CompanyConfig.objects.create()
        self.assertTrue(config.email_use_tls)

    def test_email_from_address_blank_uses_username(self):
        config = CompanyConfig.objects.create(
            email_username=self.valid_email_username
        )
        self.assertEqual(config.email_from_address, "")

    def test_email_to_address_blank_uses_username(self):
        config = CompanyConfig.objects.create(
            email_username=self.valid_email_username
        )
        self.assertEqual(config.email_to_address, "")

    def test_verbose_name(self):
        meta = CompanyConfig._meta
        self.assertEqual(meta.verbose_name, "Company Configuration")
        self.assertEqual(meta.verbose_name_plural, "Company Configuration")


class ContactQueryModelTestCase(TestCase):

    def setUp(self):
        self.valid_name = "John Doe"
        self.valid_email = "john@example.com"
        self.valid_service_required = "banners-stickers"
        self.valid_message = "Test message"
        self.valid_ip_address = "192.168.1.1"
        self.valid_user_agent = "Test Agent"

    def test_contact_query_creation_minimal(self):
        query = ContactQuery.objects.create(
            name=self.valid_name,
            service_required=self.valid_service_required,
            message=self.valid_message
        )
        self.assertEqual(query.name, self.valid_name)
        self.assertEqual(query.email, "")
        self.assertEqual(query.service_required, self.valid_service_required)
        self.assertEqual(query.message, self.valid_message)
        self.assertIsNotNone(query.submitted_at)
        self.assertIsNone(query.ip_address)
        self.assertEqual(query.user_agent, "")
        expected_str = f"{self.valid_name} - {self.valid_service_required} ({query.submitted_at.strftime('%Y-%m-%d')})"
        self.assertEqual(str(query), expected_str)

    def test_contact_query_creation_full(self):
        query = ContactQuery.objects.create(
            name=self.valid_name,
            email=self.valid_email,
            service_required=self.valid_service_required,
            message=self.valid_message,
            ip_address=self.valid_ip_address,
            user_agent=self.valid_user_agent
        )
        self.assertEqual(query.email, self.valid_email)
        self.assertEqual(query.ip_address, self.valid_ip_address)
        self.assertEqual(query.user_agent, self.valid_user_agent)

    def test_name_max_length(self):
        max_length = ContactQuery._meta.get_field('name').max_length
        self.assertEqual(max_length, 200)

    def test_service_required_max_length(self):
        max_length = ContactQuery._meta.get_field('service_required').max_length
        self.assertEqual(max_length, 100)

    def test_email_blank(self):
        query = ContactQuery.objects.create(
            name=self.valid_name,
            service_required=self.valid_service_required,
            message=self.valid_message
        )
        self.assertEqual(query.email, "")

    def test_ip_address_blank_null(self):
        query = ContactQuery.objects.create(
            name=self.valid_name,
            service_required=self.valid_service_required,
            message=self.valid_message
        )
        self.assertIsNone(query.ip_address)

    def test_user_agent_blank(self):
        query = ContactQuery.objects.create(
            name=self.valid_name,
            service_required=self.valid_service_required,
            message=self.valid_message
        )
        self.assertEqual(query.user_agent, "")

    def test_submitted_at_auto_now_add(self):
        before = timezone.now()
        query = ContactQuery.objects.create(
            name=self.valid_name,
            service_required=self.valid_service_required,
            message=self.valid_message
        )
        after = timezone.now()
        self.assertGreaterEqual(query.submitted_at, before)
        self.assertLessEqual(query.submitted_at, after)

    def test_ordering_by_submitted_at_desc(self):
        query1 = ContactQuery.objects.create(
            name="First",
            service_required=self.valid_service_required,
            message=self.valid_message
        )
        query2 = ContactQuery.objects.create(
            name="Second",
            service_required=self.valid_service_required,
            message=self.valid_message
        )
        queries = list(ContactQuery.objects.all())
        self.assertEqual(queries[0], query2)
        self.assertEqual(queries[1], query1)

    def test_str_method_formatting(self):
        query = ContactQuery.objects.create(
            name=self.valid_name,
            service_required=self.valid_service_required,
            message=self.valid_message
        )
        expected = f"{self.valid_name} - {self.valid_service_required} ({query.submitted_at.strftime('%Y-%m-%d')})"
        self.assertEqual(str(query), expected)

    def test_verbose_name(self):
        meta = ContactQuery._meta
        self.assertEqual(meta.verbose_name, "Contact Query")
        self.assertEqual(meta.verbose_name_plural, "Contact Queries")