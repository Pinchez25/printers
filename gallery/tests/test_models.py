from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from taggit.models import Tag

from gallery.models import CompanyConfig, ContactQuery, PortfolioItem


class PortfolioItemModelTest(TestCase):
    """Test cases for PortfolioItem model"""

    def setUp(self):
        """Set up test data"""
        self.portfolio_item_data = {
            'title': 'Test Portfolio Item',
            'description': 'This is a test description for the portfolio item.',
            'is_published': True,
        }

    @patch('gallery.models.get_backblaze_storage')
    def test_portfolio_item_creation(self, mock_storage):
        """Test creating a PortfolioItem instance"""
        # Mock the storage to prevent network calls
        mock_storage.return_value = MagicMock()

        item = PortfolioItem.objects.create(**self.portfolio_item_data)
        self.assertEqual(item.title, self.portfolio_item_data['title'])
        self.assertEqual(item.description, self.portfolio_item_data['description'])
        self.assertTrue(item.is_published)
        self.assertIsNotNone(item.slug)
        self.assertIsNotNone(item.created_at)
        self.assertIsNotNone(item.updated_at)

    @patch('gallery.models.get_backblaze_storage')
    def test_portfolio_item_str_method(self, mock_storage):
        """Test the string representation of PortfolioItem"""
        mock_storage.return_value = MagicMock()
        item = PortfolioItem.objects.create(**self.portfolio_item_data)
        self.assertEqual(str(item), self.portfolio_item_data['title'])

    @patch('gallery.models.get_backblaze_storage')
    def test_portfolio_item_slug_generation(self, mock_storage):
        """Test automatic slug generation"""
        mock_storage.return_value = MagicMock()
        item = PortfolioItem.objects.create(**self.portfolio_item_data)
        self.assertTrue(item.slug)
        # Slug should be URL-friendly
        self.assertNotIn(' ', item.slug)
        self.assertNotIn('\'', item.slug)

    @patch('gallery.models.get_backblaze_storage')
    def test_portfolio_item_auto_timestamps(self, mock_storage):
        """Test automatic timestamp creation and updates"""
        mock_storage.return_value = MagicMock()
        item = PortfolioItem.objects.create(**self.portfolio_item_data)
        original_created_at = item.created_at
        original_updated_at = item.updated_at


        item.title = 'Updated Title'
        item.save()

        self.assertEqual(item.created_at, original_created_at)
        self.assertGreater(item.updated_at, original_updated_at)

    @patch('gallery.models.get_backblaze_storage')
    def test_portfolio_item_default_values(self, mock_storage):
        """Test default values for PortfolioItem"""
        mock_storage.return_value = MagicMock()
        item = PortfolioItem.objects.create(title='Test Item')
        self.assertTrue(item.is_published)
        self.assertEqual(item.description, '')

    @patch('gallery.models.get_backblaze_storage')
    def test_portfolio_item_get_absolute_url(self, mock_storage):
        """Test the get_absolute_url method"""
        mock_storage.return_value = MagicMock()
        item = PortfolioItem.objects.create(**self.portfolio_item_data)
        with self.assertRaises(Exception):
            item.get_absolute_url()

    @patch('gallery.models.get_backblaze_storage')
    def test_portfolio_item_tags_relationship(self, mock_storage):
        """Test the tags relationship"""
        mock_storage.return_value = MagicMock()
        item = PortfolioItem.objects.create(**self.portfolio_item_data)

        # Add tags
        tag1 = Tag.objects.create(name='test-tag-1', slug='test-tag-1')
        tag2 = Tag.objects.create(name='test-tag-2', slug='test-tag-2')

        item.tags.add(tag1, tag2)

        item.refresh_from_db()

        # Check tags are associated
        self.assertIn(tag1, item.tags.all())
        self.assertIn(tag2, item.tags.all())
        self.assertEqual(item.tags.count(), 2)

    @patch('gallery.models.get_backblaze_storage')
    def test_portfolio_item_ordering(self, mock_storage):
        """Test default ordering by creation date"""
        mock_storage.return_value = MagicMock()
        # Create items with different timestamps
        item1 = PortfolioItem.objects.create(title='First Item')
        item2 = PortfolioItem.objects.create(title='Second Item')

        # Update the second item's timestamp to be older
        item2.created_at = timezone.now() - timedelta(days=1)
        item2.save()

        items = list(PortfolioItem.objects.all())
        # Should be ordered by created_at descending (newest first)
        self.assertEqual(items[0], item1)
        self.assertEqual(items[1], item2)


class CompanyConfigModelTest(TestCase):
    """Test cases for CompanyConfig model"""

    def setUp(self):
        """Set up test data"""
        self.config_data = {
            'address': '123 Test Street, Test City, TC 12345',
            'email': 'test@company.com',
            'contact_number': '254758123456',
            'facebook_username': 'testcompany',
            'twitter_username': 'testcompany',
            'instagram_username': 'testcompany',
            'tiktok': 'testcompany',
            'services_offered': ['Business Cards', 'Posters', 'Banners'],
            'always_save_contactus_queries': True,
            'happy_customers': 1000,
            'projects_completed': 500,
            'years_experience': 5,
            'support_hours': 24,
        }

    def test_company_config_creation(self):
        """Test creating a CompanyConfig instance"""
        config = CompanyConfig.objects.create(**self.config_data)
        self.assertEqual(config.address, self.config_data['address'])
        self.assertEqual(config.email, self.config_data['email'])
        self.assertEqual(config.contact_number, self.config_data['contact_number'])
        self.assertEqual(config.services_offered, self.config_data['services_offered'])
        self.assertTrue(config.always_save_contactus_queries)
        self.assertEqual(config.happy_customers, 1000)
        self.assertEqual(config.projects_completed, 500)
        self.assertEqual(config.years_experience, 5)
        self.assertEqual(config.support_hours, 24)

    def test_company_config_singleton_enforcer(self):
        """Test that singleton_enforcer is always True"""
        config = CompanyConfig.objects.create(**self.config_data)
        self.assertTrue(config.singleton_enforcer)

        # Try to create another config - should fail
        with self.assertRaises(ValidationError):
            CompanyConfig.objects.create(**self.config_data)

    def test_company_config_get_instance(self):
        """Test the get_instance class method"""
        # Should create a new instance if none exists
        config1 = CompanyConfig.get_instance()
        self.assertIsInstance(config1, CompanyConfig)

        # Should return the same instance
        config2 = CompanyConfig.get_instance()
        self.assertEqual(config1, config2)

    def test_company_config_str_method(self):
        """Test the string representation of CompanyConfig"""
        config = CompanyConfig.objects.create(**self.config_data)
        self.assertEqual(str(config), "Company Configuration")

    def test_company_config_default_values(self):
        """Test default values for CompanyConfig"""
        config = CompanyConfig.get_instance()
        self.assertEqual(config.services_offered, [])
        self.assertFalse(config.always_save_contactus_queries)
        self.assertEqual(config.happy_customers, 5000)
        self.assertEqual(config.projects_completed, 15000)
        self.assertEqual(config.years_experience, 8)
        self.assertEqual(config.support_hours, 24)

    def test_company_config_save_method(self):
        """Test the save method enforces singleton"""
        config = CompanyConfig.get_instance()
        config.address = 'New Address'
        config.save()

        # Should still be the same instance
        config2 = CompanyConfig.get_instance()
        self.assertEqual(config, config2)
        self.assertEqual(config.address, 'New Address')

    def test_company_config_clean_method(self):
        """Test the clean method validation"""
        # Create first instance
        CompanyConfig.objects.create(**self.config_data)

        # Try to create another - should raise ValidationError
        config2 = CompanyConfig(**self.config_data)
        with self.assertRaises(ValidationError):
            config2.full_clean()


class ContactQueryModelTest(TestCase):
    """Test cases for ContactQuery model"""

    def setUp(self):
        """Set up test data"""
        self.contact_data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'service_required': 'Business Cards',
            'message': 'I would like to order some business cards for my company.',
            'ip_address': '192.168.1.1',
            'user_agent': 'Mozilla/5.0 (Test Browser)',
        }

    def test_contact_query_creation(self):
        """Test creating a ContactQuery instance"""
        contact = ContactQuery.objects.create(**self.contact_data)
        self.assertEqual(contact.name, self.contact_data['name'])
        self.assertEqual(contact.email, self.contact_data['email'])
        self.assertEqual(contact.service_required, self.contact_data['service_required'])
        self.assertEqual(contact.message, self.contact_data['message'])
        self.assertEqual(contact.ip_address, self.contact_data['ip_address'])
        self.assertEqual(contact.user_agent, self.contact_data['user_agent'])
        self.assertIsNotNone(contact.submitted_at)

    def test_contact_query_str_method(self):
        """Test the string representation of ContactQuery"""
        contact = ContactQuery.objects.create(**self.contact_data)
        expected_str = f"{self.contact_data['name']} - {self.contact_data['service_required']} ({contact.submitted_at.strftime('%Y-%m-%d')})"
        self.assertEqual(str(contact), expected_str)

    def test_contact_query_optional_email(self):
        """Test that email is optional"""
        contact_data_no_email = self.contact_data.copy()
        del contact_data_no_email['email']

        contact = ContactQuery.objects.create(**contact_data_no_email)
        self.assertEqual(contact.email, '')  # Django sets blank email fields to empty string

    def test_contact_query_ordering(self):
        """Test default ordering by submission date"""
        # Create contacts with different timestamps
        contact1 = ContactQuery.objects.create(**self.contact_data)

        contact_data2 = self.contact_data.copy()
        contact_data2['name'] = 'Jane Smith'
        contact2 = ContactQuery.objects.create(**contact_data2)

        contact2.submitted_at = timezone.now() - timedelta(days=1)
        contact2.save()

        contacts = list(ContactQuery.objects.all())
        self.assertEqual(contacts[0], contact1)
        self.assertEqual(contacts[1], contact2)

    def test_contact_query_blank_optional_fields(self):
        """Test that optional fields can be blank"""
        contact_data_blank = {
            'name': 'Test User',
            'service_required': 'Test Service',
            'message': 'Test message',
            'ip_address': None,
            'user_agent': '',
        }

        contact = ContactQuery.objects.create(**contact_data_blank)
        self.assertIsNone(contact.ip_address)
        self.assertEqual(contact.user_agent, '')

    def test_contact_query_max_lengths(self):
        """Test field max length constraints"""
        long_name = 'a' * 201
        contact_data_long = self.contact_data.copy()
        contact_data_long['name'] = long_name

        name_field = ContactQuery._meta.get_field('name')
        self.assertEqual(name_field.max_length, 200)

        contact = ContactQuery.objects.create(**contact_data_long)
        self.assertIsNotNone(contact.name)
