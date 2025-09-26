import json
from unittest.mock import patch

from django.test import RequestFactory, TestCase
from rest_framework import status
from rest_framework.test import APITestCase
from taggit.models import Tag

from gallery.context_processors import company_config
from gallery.models import CompanyConfig, ContactQuery, PortfolioItem
from gallery.views import (
    contact_form_view,
    get_client_ip
)


class BaseViewTest(TestCase):
    """Base test class with common setup"""

    def setUp(self):
        """Set up test data"""
        self.factory = RequestFactory()

        # Create test company config
        self.config = CompanyConfig.get_instance()
        self.config.email = 'test@company.com'
        self.config.save()

        # Create test tags
        self.tag1 = Tag.objects.create(name='test-tag-1', slug='test-tag-1')
        self.tag2 = Tag.objects.create(name='test-tag-2', slug='test-tag-2')

        # Create test portfolio items
        self.published_item = PortfolioItem.objects.create(
            title='Published Item',
            description='Published description',
            is_published=True
        )
        self.published_item.tags.add(self.tag1)

        self.unpublished_item = PortfolioItem.objects.create(
            title='Unpublished Item',
            description='Unpublished description',
            is_published=False
        )
        self.unpublished_item.tags.add(self.tag2)


class IndexViewTest(BaseViewTest):
    """Test cases for index_view"""

    def test_index_view_get(self):
        """Test index view GET request"""
        from django.test import Client
        client = Client()
        response = client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertIn('latest_portfolio_items', response.context)
        self.assertEqual(len(response.context['latest_portfolio_items']), 1)
        self.assertEqual(response.context['latest_portfolio_items'][0], self.published_item)

    def test_index_view_context(self):
        """Test index view context data"""
        from django.test import Client
        client = Client()
        response = client.get('/')

        # Should only include published items
        items = response.context['latest_portfolio_items']
        self.assertEqual(len(items), 1)
        self.assertTrue(all(item.is_published for item in items))

    def test_index_view_template(self):
        """Test that index view uses correct template"""
        from django.test import Client
        client = Client()
        response = client.get('/')

        # Check that render was called with correct template
        self.assertEqual(response.templates[0].name, 'pages/index.html')


class GalleryViewTest(BaseViewTest):
    """Test cases for gallery_view"""

    def test_gallery_view_get(self):
        """Test gallery view GET request"""
        from django.test import Client
        client = Client()
        response = client.get('/gallery/')

        self.assertEqual(response.status_code, 200)
        self.assertIn('portfolio_items', response.context)
        self.assertIn('all_tags', response.context)

    def test_gallery_view_published_items_only(self):
        """Test that gallery view only shows published items"""
        from django.test import Client
        client = Client()
        response = client.get('/gallery/')

        items = response.context['portfolio_items']
        self.assertEqual(len(items), 1)
        self.assertTrue(all(item.is_published for item in items))
        self.assertEqual(items[0], self.published_item)

    def test_gallery_view_tags(self):
        """Test that gallery view includes tags"""
        from django.test import Client
        from django.db.models import QuerySet
        client = Client()
        response = client.get('/gallery/')

        all_tags = response.context['all_tags']

        # Should be a QuerySet since we're using most_common()[:20]
        self.assertIsInstance(all_tags, QuerySet)
        self.assertGreater(len(all_tags), 0)  # Should have at least some tags

    def test_gallery_view_template(self):
        """Test that gallery view uses correct template"""
        from django.test import Client
        client = Client()
        response = client.get('/gallery/')

        self.assertEqual(response.templates[0].name, 'pages/gallery.html')


class ContactFormViewTest(BaseViewTest):
    """Test cases for contact_form_view"""

    def setUp(self):
        """Set up additional test data"""
        super().setUp()
        self.valid_contact_data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'service': 'Business Cards',
            'message': 'I would like to order business cards.'
        }

    def test_contact_form_valid_data(self):
        """Test contact form with valid data"""
        request = self.factory.post('/', data=json.dumps(self.valid_contact_data),
                                    content_type='application/json')
        response = contact_form_view(request)

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        self.assertIn('Thank you for your inquiry', response_data['message'])

    def test_contact_form_invalid_json(self):
        """Test contact form with invalid JSON"""
        request = self.factory.post('/', data='invalid json',
                                    content_type='application/json')
        response = contact_form_view(request)

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('Invalid request format', response_data['message'])

    def test_contact_form_missing_fields(self):
        """Test contact form with missing required fields"""
        invalid_data = {'name': 'John Doe'}  # Missing other required fields
        request = self.factory.post('/', data=json.dumps(invalid_data),
                                    content_type='application/json')
        response = contact_form_view(request)

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])

    def test_contact_form_empty_data(self):
        """Test contact form with empty data"""
        request = self.factory.post('/', data=json.dumps({}),
                                    content_type='application/json')
        response = contact_form_view(request)

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])

    def test_contact_form_save_to_database(self):
        """Test that contact form saves to database when configured"""
        # Enable saving contact queries
        self.config.always_save_contactus_queries = True
        self.config.save()

        request = self.factory.post('/', data=json.dumps(self.valid_contact_data),
                                    content_type='application/json')
        response = contact_form_view(request)

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])

        # Check that contact was saved
        contact = ContactQuery.objects.get(name=self.valid_contact_data['name'])
        self.assertEqual(contact.email, self.valid_contact_data['email'])
        self.assertEqual(contact.service_required, self.valid_contact_data['service'])
        self.assertEqual(contact.message, self.valid_contact_data['message'])

    def test_contact_form_dont_save_to_database(self):
        """Test that contact form doesn't save when not configured"""
        # Disable saving contact queries
        self.config.always_save_contactus_queries = False
        self.config.save()

        request = self.factory.post('/', data=json.dumps(self.valid_contact_data),
                                    content_type='application/json')
        response = contact_form_view(request)

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])

        # Check that no contact was saved
        self.assertEqual(ContactQuery.objects.count(), 0)

    @patch('gallery.views.send_mail')
    def test_contact_form_email_sending(self, mock_send_mail):
        """Test that contact form sends email"""
        mock_send_mail.return_value = True

        request = self.factory.post('/', data=json.dumps(self.valid_contact_data),
                                    content_type='application/json')
        response = contact_form_view(request)

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])

        # Check that send_mail was called
        mock_send_mail.assert_called_once()

    @patch('gallery.views.send_mail')
    def test_contact_form_email_failure(self, mock_send_mail):
        """Test contact form behavior when email fails"""
        mock_send_mail.side_effect = Exception('Email failed')

        request = self.factory.post('/', data=json.dumps(self.valid_contact_data),
                                    content_type='application/json')
        response = contact_form_view(request)

        # Should return error status when email fails
        self.assertEqual(response.status_code, 500)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])

    def test_contact_form_config_error(self):
        """Test contact form when config retrieval fails"""
        with patch('gallery.views.CompanyConfig.get_instance') as mock_get_instance:
            mock_get_instance.side_effect = Exception('Config error')

            request = self.factory.post('/', data=json.dumps(self.valid_contact_data),
                                        content_type='application/json')
            response = contact_form_view(request)

            self.assertEqual(response.status_code, 500)
            response_data = json.loads(response.content)
            self.assertFalse(response_data['success'])


class GetClientIPTest(TestCase):
    """Test cases for get_client_ip utility function"""

    def setUp(self):
        """Set up test data"""
        self.factory = RequestFactory()

    def test_get_client_ip_with_x_forwarded_for(self):
        """Test get_client_ip with X-Forwarded-For header"""
        request = self.factory.get('/', HTTP_X_FORWARDED_FOR='192.168.1.1, 10.0.0.1')
        ip = get_client_ip(request)
        self.assertEqual(ip, '192.168.1.1')

    def test_get_client_ip_without_x_forwarded_for(self):
        """Test get_client_ip without X-Forwarded-For header"""
        request = self.factory.get('/', REMOTE_ADDR='192.168.1.2')
        ip = get_client_ip(request)
        self.assertEqual(ip, '192.168.1.2')

    def test_get_client_ip_empty_x_forwarded_for(self):
        """Test get_client_ip with empty X-Forwarded-For header"""
        request = self.factory.get('/', HTTP_X_FORWARDED_FOR='')
        ip = get_client_ip(request)
        self.assertEqual(ip, '127.0.0.1')  # Django test client default

    def test_get_client_ip_multiple_x_forwarded_for(self):
        """Test get_client_ip with multiple IPs in X-Forwarded-For"""
        request = self.factory.get('/', HTTP_X_FORWARDED_FOR='192.168.1.1, 10.0.0.1, 172.16.0.1')
        ip = get_client_ip(request)
        self.assertEqual(ip, '192.168.1.1')  # Should get first IP


class GalleryAPITest(APITestCase):
    """Test cases for gallery API endpoints"""

    def setUp(self):
        """Set up test data"""
        # Create test tags
        self.tag1 = Tag.objects.create(name='api-tag-1', slug='api-tag-1')
        self.tag2 = Tag.objects.create(name='api-tag-2', slug='api-tag-2')

        # Create test portfolio items
        self.item1 = PortfolioItem.objects.create(
            title='API Item 1',
            description='API description 1',
            is_published=True
        )
        self.item1.tags.add(self.tag1)

        self.item2 = PortfolioItem.objects.create(
            title='API Item 2',
            description='API description 2',
            is_published=True
        )
        self.item2.tags.add(self.tag2)

    def test_gallery_api_get_all(self):
        """Test gallery API GET request without parameters"""
        response = self.client.get('/api/gallery/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['items']), 2)
        self.assertEqual(response.data['pagination']['total_items'], 2)

    def test_gallery_api_with_search(self):
        """Test gallery API with search parameter"""
        response = self.client.get('/api/gallery/?search=API Item 1')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['items']), 1)
        self.assertEqual(response.data['items'][0]['title'], 'API Item 1')

    def test_gallery_api_with_tags(self):
        """Test gallery API with tags parameter"""
        response = self.client.get(f'/api/gallery/?tags[]={self.tag1.name}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['items']), 1)
        self.assertEqual(response.data['items'][0]['title'], 'API Item 1')

    def test_gallery_api_pagination(self):
        """Test gallery API pagination"""
        response = self.client.get('/api/gallery/?page=1&per_page=1')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['items']), 1)
        self.assertEqual(response.data['pagination']['current_page'], 1)
        self.assertEqual(response.data['pagination']['total_pages'], 2)

    def test_gallery_api_invalid_page(self):
        """Test gallery API with invalid page number"""
        response = self.client.get('/api/gallery/?page=999')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        # Django's Paginator returns the last page when requesting a page beyond available pages
        self.assertEqual(len(response.data['items']), 2)  # Should return all items (last page)
        self.assertEqual(response.data['pagination']['current_page'], 1)  # Should be page 1 (only page)

    def test_gallery_api_unpublished_items_excluded(self):
        """Test that unpublished items are excluded from API"""
        # Create unpublished item
        unpublished = PortfolioItem.objects.create(
            title='Unpublished API Item',
            description='Should not appear in API',
            is_published=False
        )

        response = self.client.get('/api/gallery/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

        # Should only return published items
        titles = [item['title'] for item in response.data['items']]
        self.assertIn('API Item 1', titles)
        self.assertIn('API Item 2', titles)
        self.assertNotIn('Unpublished API Item', titles)


class GalleryTagsAPITest(APITestCase):
    """Test cases for gallery tags API endpoint"""

    def setUp(self):
        """Set up test data"""
        # Create test tags
        self.tag1 = Tag.objects.create(name='popular-tag-1', slug='popular-tag-1')
        self.tag2 = Tag.objects.create(name='popular-tag-2', slug='popular-tag-2')

        # Create test portfolio items with tags
        self.item1 = PortfolioItem.objects.create(
            title='Tagged Item 1',
            description='Description 1',
            is_published=True
        )
        self.item1.tags.add(self.tag1)

        self.item2 = PortfolioItem.objects.create(
            title='Tagged Item 2',
            description='Description 2',
            is_published=True
        )
        self.item2.tags.add(self.tag1, self.tag2)

    def test_gallery_tags_api_get(self):
        """Test gallery tags API GET request"""
        response = self.client.get('/api/gallery/tags/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['tags']), 2)

    def test_gallery_tags_api_structure(self):
        """Test gallery tags API response structure"""
        response = self.client.get('/api/gallery/tags/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

        tags = response.data['tags']
        for tag in tags:
            self.assertIn('name', tag)
            self.assertIn('slug', tag)
            self.assertIn('count', tag)

    def test_gallery_tags_api_popular_tags(self):
        """Test that tags are ordered by popularity"""
        response = self.client.get('/api/gallery/tags/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

        tags = response.data['tags']
        # tag1 should come first as it's used by both items
        self.assertEqual(tags[0]['name'], self.tag1.name)
        self.assertEqual(tags[1]['name'], self.tag2.name)


class CompanyConfigContextProcessorTest(TestCase):
    """Test cases for company_config context processor"""

    def setUp(self):
        """Set up test data"""
        self.factory = RequestFactory()

    def test_company_config_context_processor(self):
        """Test company_config context processor"""
        request = self.factory.get('/')

        context = company_config(request)

        self.assertIn('config', context)
        self.assertIsNotNone(context['config'])

        # Should be a CompanyConfig instance
        from gallery.models import CompanyConfig
        self.assertIsInstance(context['config'], CompanyConfig)

    def test_company_config_context_processor_singleton(self):
        """Test that context processor returns singleton instance"""
        request1 = self.factory.get('/')
        request2 = self.factory.get('/')

        context1 = company_config(request1)
        context2 = company_config(request2)

        # Should return the same instance
        self.assertEqual(context1['config'], context2['config'])
