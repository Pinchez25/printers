import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client, override_settings
from django.http import HttpRequest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APIClient
from taggit.models import Tag

from gallery.models import PortfolioItem, CompanyConfig, ContactQuery
from gallery.views import (
    capitalise_first_letter, get_client_ip, get_request_data,
    _build_email_connection, send_contact_email, contact_form_view,
    index, serialize_portfolio_item, parse_pagination_params,
    gallery_api, gallery_tags_api
)


class UtilityFunctionsTestCase(TestCase):

    def test_capitalise_first_letter_with_alpha(self):
        result = capitalise_first_letter("hello world")
        self.assertEqual(result, "Hello world")

    def test_capitalise_first_letter_without_alpha(self):
        result = capitalise_first_letter("123world")
        self.assertEqual(result, "123World")

    def test_capitalise_first_letter_empty(self):
        result = capitalise_first_letter("")
        self.assertEqual(result, "")

    def test_capitalise_first_letter_none(self):
        result = capitalise_first_letter(None)
        self.assertIsNone(result)

    def test_capitalise_first_letter_all_non_alpha(self):
        result = capitalise_first_letter("!!!")
        self.assertEqual(result, "!!!")

    def test_get_client_ip_with_x_forwarded_for(self):
        request = HttpRequest()
        request.META = {'HTTP_X_FORWARDED_FOR': '192.168.1.1, 10.0.0.1'}
        result = get_client_ip(request)
        self.assertEqual(result, "192.168.1.1")

    def test_get_client_ip_without_x_forwarded_for(self):
        request = HttpRequest()
        request.META = {'REMOTE_ADDR': '192.168.1.1'}
        result = get_client_ip(request)
        self.assertEqual(result, "192.168.1.1")

    def test_get_client_ip_empty_x_forwarded_for(self):
        request = HttpRequest()
        request.META = {'HTTP_X_FORWARDED_FOR': ', ', 'REMOTE_ADDR': '192.168.1.1'}
        result = get_client_ip(request)
        self.assertEqual(result, "192.168.1.1")

    def test_get_request_data_json(self):
        request = HttpRequest()
        request.method = 'POST'
        request.content_type = 'application/json'
        request._body = b'{"key": "value"}'
        request._read_started = False
        result = get_request_data(request)
        self.assertEqual(result, {"key": "value"})

    def test_get_request_data_json_invalid(self):
        request = HttpRequest()
        request.method = 'POST'
        request.content_type = 'application/json'
        request._body = b'invalid json'
        result = get_request_data(request)
        self.assertEqual(result, {})

    def test_get_request_data_post_form(self):
        request = HttpRequest()
        request.method = 'POST'
        request.POST = MagicMock()
        request.POST.dict.return_value = {'key': 'value'}
        result = get_request_data(request)
        self.assertEqual(result, {"key": "value"})

    def test_get_request_data_no_body(self):
        request = HttpRequest()
        request.method = 'POST'
        request.content_type = 'application/json'
        request._body = b''
        request._read_started = False
        result = get_request_data(request)
        self.assertEqual(result, {})

    @patch('gallery.views.get_connection')
    def test_build_email_connection_success(self, mock_get_connection):
        config = CompanyConfig(
            email_host="smtp.example.com",
            email_username="user@example.com",
            email_password="password"
        )
        mock_connection = MagicMock()
        mock_get_connection.return_value = mock_connection
        result = _build_email_connection(config)
        self.assertEqual(result, mock_connection)
        mock_get_connection.assert_called_once_with(
            host="smtp.example.com",
            port=587,
            username="user@example.com",
            password="password",
            use_tls=True,
            fail_silently=False
        )

    def test_build_email_connection_missing_config(self):
        config = CompanyConfig()
        result = _build_email_connection(config)
        self.assertIsNone(result)

    @patch('gallery.views.render_to_string')
    @patch('gallery.views.send_mail')
    @patch('gallery.views._build_email_connection')
    def test_send_contact_email_success(self, mock_build_connection, mock_send_mail, mock_render_to_string):
        config = CompanyConfig(
            email_from_address="from@example.com",
            email_to_address="to@example.com"
        )
        mock_render_to_string.side_effect = ["html content", "text content"]
        mock_connection = MagicMock()
        mock_build_connection.return_value = mock_connection

        send_contact_email("John", "john@example.com", "123", "Message", "service", config)

        self.assertIn("emails/contact_form.html", [call[0][0] for call in mock_render_to_string.call_args_list])
        mock_send_mail.assert_called_once()

    @patch('gallery.views.render_to_string')
    @patch('gallery.views.send_mail')
    @patch('gallery.views._build_email_connection')
    def test_send_contact_email_fallback_addresses(self, mock_build_connection, mock_send_mail, mock_render_to_string):
        config = CompanyConfig(
            email_username="user@example.com"
        )
        mock_render_to_string.side_effect = ["html content", "text content"]
        mock_connection = MagicMock()
        mock_build_connection.return_value = mock_connection

        send_contact_email("John", "john@example.com", "123", "Message", "service", config)

        call_args = mock_send_mail.call_args
        self.assertEqual(call_args[1]['from_email'], "user@example.com")
        self.assertEqual(call_args[1]['recipient_list'], ["user@example.com"])


class ViewFunctionsTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.api_client = APIClient()
        self.valid_image = SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")

    def test_index_view_get(self):
        response = self.client.get(reverse('gallery:index'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('portfolio_items', response.context)
        self.assertIn('all_tags', response.context)

    def test_index_view_with_published_items(self):
        item = PortfolioItem.objects.create(
            title="Test Item",
            image=self.valid_image,
            is_published=True
        )
        response = self.client.get(reverse('gallery:index'))
        self.assertIn(item, response.context['portfolio_items'])

    def test_index_view_excludes_unpublished(self):
        item = PortfolioItem.objects.create(
            title="Test Item",
            image=self.valid_image,
            is_published=False
        )
        response = self.client.get(reverse('gallery:index'))
        self.assertNotIn(item, response.context['portfolio_items'])

    def test_serialize_portfolio_item(self):
        item = PortfolioItem.objects.create(
            title="test item",
            image=self.valid_image,
            description="Test desc"
        )
        result = serialize_portfolio_item(item)
        self.assertEqual(result['title'], "Test item")
        self.assertEqual(result['description'], "Test desc")
        self.assertIn('id', result)
        self.assertIn('slug', result)

    def test_parse_pagination_params_valid(self):
        request = MagicMock()
        request.GET = {'page': '2', 'per_page': '10'}
        page, per_page = parse_pagination_params(request)
        self.assertEqual(page, 2)
        self.assertEqual(per_page, 10)

    def test_parse_pagination_params_invalid(self):
        request = MagicMock()
        request.GET = {'page': 'invalid', 'per_page': 'invalid'}
        page, per_page = parse_pagination_params(request)
        self.assertEqual(page, 1)
        self.assertEqual(per_page, 6)

    def test_parse_pagination_params_missing(self):
        request = MagicMock()
        request.GET = {}
        page, per_page = parse_pagination_params(request)
        self.assertEqual(page, 1)
        self.assertEqual(per_page, 6)


class ContactFormViewTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse('gallery:contact_form')

    @patch('gallery.views.CompanyConfig.get_instance')
    def test_contact_form_view_missing_required_fields(self, mock_get_instance):
        mock_config = MagicMock()
        mock_get_instance.return_value = mock_config
        data = {'name': '', 'email': '', 'message': ''}
        response = self.client.post(self.url, data, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])

    @patch('gallery.views.CompanyConfig.get_instance')
    def test_contact_form_view_email_not_configured(self, mock_get_instance):
        mock_config = MagicMock()
        mock_config.is_email_configured.return_value = False
        mock_get_instance.return_value = mock_config
        data = {'name': 'John', 'email': 'john@example.com', 'message': 'Test'}
        response = self.client.post(self.url, data, content_type='application/json')
        self.assertEqual(response.status_code, 503)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])

    @patch('gallery.views.send_contact_email')
    @patch('gallery.views.get_client_ip')
    @patch('gallery.views.CompanyConfig.get_instance')
    def test_contact_form_view_success_without_save(self, mock_get_instance, mock_get_ip, mock_send_email):
        mock_config = MagicMock()
        mock_config.is_email_configured.return_value = True
        mock_config.always_save_contactus_queries = False
        mock_get_instance.return_value = mock_config
        mock_get_ip.return_value = "192.168.1.1"
        data = {'name': 'John', 'email': 'john@example.com', 'message': 'Test', 'service': 'banners-stickers'}
        response = self.client.post(self.url, data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        mock_send_email.assert_called_once()

    @patch('gallery.views.send_contact_email')
    @patch('gallery.views.get_client_ip')
    @patch('gallery.views.CompanyConfig.get_instance')
    def test_contact_form_view_success_with_save(self, mock_get_instance, mock_get_ip, mock_send_email):
        mock_config = MagicMock()
        mock_config.is_email_configured.return_value = True
        mock_config.always_save_contactus_queries = True
        mock_get_instance.return_value = mock_config
        mock_get_ip.return_value = "192.168.1.1"
        data = {'name': 'John', 'email': 'john@example.com', 'message': 'Test', 'service': 'banners-stickers'}
        response = self.client.post(self.url, data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ContactQuery.objects.filter(name='John').exists())

    @patch('gallery.views.CompanyConfig.get_instance')
    def test_contact_form_view_config_error(self, mock_get_instance):
        mock_get_instance.side_effect = Exception("Config error")
        data = {'name': 'John', 'email': 'john@example.com', 'message': 'Test'}
        response = self.client.post(self.url, data, content_type='application/json')
        self.assertEqual(response.status_code, 500)

    @patch('gallery.views.send_contact_email')
    @patch('gallery.views.CompanyConfig.get_instance')
    def test_contact_form_view_email_error(self, mock_get_instance, mock_send_email):
        mock_config = MagicMock()
        mock_config.is_email_configured.return_value = True
        mock_config.always_save_contactus_queries = False
        mock_get_instance.return_value = mock_config
        mock_send_email.side_effect = Exception("Email error")
        data = {'name': 'John', 'email': 'john@example.com', 'message': 'Test'}
        response = self.client.post(self.url, data, content_type='application/json')
        self.assertEqual(response.status_code, 500)

    def test_contact_form_view_wrong_method(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)


class GalleryAPITestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = reverse('gallery:gallery_api')
        self.valid_image = SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")

    def test_gallery_api_get_empty(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertTrue(data['success'])
        self.assertEqual(data['items'], [])
        self.assertEqual(data['pagination']['total_items'], 0)

    def test_gallery_api_get_with_items(self):
        item = PortfolioItem.objects.create(
            title="Test Item",
            image=self.valid_image,
            is_published=True
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(len(data['items']), 1)
        self.assertEqual(data['items'][0]['title'], "Test Item")

    def test_gallery_api_search(self):
        item = PortfolioItem.objects.create(
            title="Unique Title",
            image=self.valid_image,
            is_published=True
        )
        response = self.client.get(self.url, {'search': 'Unique'})
        self.assertEqual(len(response.data['items']), 1)
        response = self.client.get(self.url, {'search': 'Nonexistent'})
        self.assertEqual(len(response.data['items']), 0)

    def test_gallery_api_tags_filter(self):
        item = PortfolioItem.objects.create(
            title="Test Item",
            image=self.valid_image,
            is_published=True
        )
        tag = Tag.objects.create(name="testtag")
        item.tags.add(tag)
        response = self.client.get(self.url, {'tags': 'testtag'})
        self.assertEqual(len(response.data['items']), 1)
        response = self.client.get(self.url, {'tags': 'othertag'})
        self.assertEqual(len(response.data['items']), 0)

    def test_gallery_api_pagination(self):
        for i in range(10):
            PortfolioItem.objects.create(
                title=f"Item {i}",
                image=SimpleUploadedFile(f"test{i}.jpg", b"content", content_type="image/jpeg"),
                is_published=True
            )
        response = self.client.get(self.url, {'per_page': '5', 'page': '2'})
        data = response.data
        self.assertEqual(len(data['items']), 5)
        self.assertEqual(data['pagination']['current_page'], 2)
        self.assertEqual(data['pagination']['total_pages'], 2)

    def test_gallery_api_exclude_unpublished(self):
        PortfolioItem.objects.create(
            title="Published",
            image=self.valid_image,
            is_published=True
        )
        PortfolioItem.objects.create(
            title="Unpublished",
            image=SimpleUploadedFile("test2.jpg", b"content", content_type="image/jpeg"),
            is_published=False
        )
        response = self.client.get(self.url)
        self.assertEqual(len(response.data['items']), 1)
        self.assertEqual(response.data['items'][0]['title'], "Published")

    @patch('gallery.views.PortfolioItemFilter')
    def test_gallery_api_filter_error(self, mock_filter):
        mock_filter.side_effect = Exception("Filter error")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 500)
        data = response.data
        self.assertFalse(data['success'])


class GalleryTagsAPITestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = reverse('gallery:gallery_tags_api')

    @patch('gallery.views.get_popular_tags')
    def test_gallery_tags_api_success(self, mock_get_popular_tags):
        mock_tag = MagicMock()
        mock_tag.name = "Test Tag"
        mock_tag.slug = "test-tag"
        mock_tag.item_count = 5
        mock_get_popular_tags.return_value = [mock_tag]
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertTrue(data['success'])
        self.assertEqual(len(data['tags']), 1)
        self.assertEqual(data['tags'][0]['name'], "Test Tag")

    @patch('gallery.views.get_popular_tags')
    def test_gallery_tags_api_error(self, mock_get_popular_tags):
        mock_get_popular_tags.side_effect = Exception("Tags error")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 500)
        data = response.data
        self.assertFalse(data['success'])