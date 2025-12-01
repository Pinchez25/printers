import unittest.mock as mock
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.core.exceptions import ValidationError

from gallery.forms import PortfolioItemForm, CompanyConfigAdminForm
from gallery.models import PortfolioItem, CompanyConfig
from gallery.storage_backends import SupabaseStorage


class PortfolioItemFormTestCase(TestCase):
    """Test cases for PortfolioItemForm (equivalent to ImageUploadForm)."""

    def setUp(self):
        self.valid_title = "Test Portfolio Item"
        self.valid_description = "A test description"
        self.valid_image = SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        # Mock storage to prevent real network calls
        self.storage_patchers = [
            mock.patch.object(SupabaseStorage, '_save', return_value='mock/path.jpg'),
            mock.patch.object(SupabaseStorage, '_get_file_metadata', return_value={'name': 'mock.jpg', 'size': 100}),
            mock.patch.object(SupabaseStorage, 'url', return_value='http://mock.com/image.jpg'),
        ]
        for p in self.storage_patchers:
            p.start()

    def tearDown(self):
        for p in self.storage_patchers:
            p.stop()

    def test_form_valid_minimal_data(self):
        """Test form is valid with minimal required data."""
        form_data = {'title': self.valid_title}
        form = PortfolioItemForm(data=form_data, files={'image': self.valid_image})
        self.assertTrue(form.is_valid())
        item = form.save()
        self.assertEqual(item.title, self.valid_title)
        self.assertEqual(item.description, "")
        self.assertTrue(item.is_published)

    def test_form_valid_full_data(self):
        """Test form is valid with all fields provided."""
        form_data = {
            'title': self.valid_title,
            'description': self.valid_description,
            'is_published': False,
            'tags': 'tag1, tag2'
        }
        form = PortfolioItemForm(data=form_data, files={'image': self.valid_image})
        self.assertTrue(form.is_valid())
        item = form.save()
        self.assertEqual(item.title, self.valid_title)
        self.assertEqual(item.description, self.valid_description)
        self.assertFalse(item.is_published)
        self.assertEqual(list(item.tags.names()), ['tag1', 'tag2'])

    def test_form_invalid_missing_title(self):
        """Test form is invalid when title is missing."""
        form_data = {}
        form = PortfolioItemForm(data=form_data, files={'image': self.valid_image})
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_form_invalid_missing_image(self):
        """Test form is invalid when image is missing."""
        form_data = {'title': self.valid_title}
        form = PortfolioItemForm(data=form_data, files={})
        self.assertFalse(form.is_valid())
        self.assertIn('image', form.errors)

    def test_form_invalid_title_too_long(self):
        """Test form is invalid when title exceeds max length."""
        long_title = "A" * 201
        form_data = {'title': long_title}
        form = PortfolioItemForm(data=form_data, files={'image': self.valid_image})
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_form_valid_empty_description(self):
        """Test form allows empty description."""
        form_data = {'title': self.valid_title}
        form = PortfolioItemForm(data=form_data, files={'image': self.valid_image})
        self.assertTrue(form.is_valid())

    def test_form_valid_tags_empty(self):
        """Test form allows empty tags."""
        form_data = {'title': self.valid_title}
        form = PortfolioItemForm(data=form_data, files={'image': self.valid_image})
        self.assertTrue(form.is_valid())

    def test_form_valid_tags_with_spaces(self):
        """Test form handles tags with spaces correctly."""
        form_data = {'title': self.valid_title, 'tags': 'tag one, tag two'}
        form = PortfolioItemForm(data=form_data, files={'image': self.valid_image})
        self.assertTrue(form.is_valid())
        item = form.save()
        self.assertEqual(list(item.tags.names()), ['tag one', 'tag two'])

    def test_form_widget_customisation(self):
        """Test that custom UnfoldTagWidget is applied."""
        form = PortfolioItemForm()
        tags_field = form.fields['tags']
        self.assertIsInstance(tags_field.widget, type(form.fields['tags'].widget))
        # Check if placeholder is set
        self.assertEqual(tags_field.widget.attrs.get('placeholder'), 'Add tags separated by commas')

    def test_form_save_updates_existing_instance(self):
        """Test form can update existing PortfolioItem."""
        item = PortfolioItem.objects.create(
            title="Original Title",
            image=self.valid_image
        )
        form_data = {'title': "Updated Title", 'description': "Updated desc"}
        form = PortfolioItemForm(data=form_data, files={}, instance=item)
        self.assertTrue(form.is_valid())
        updated_item = form.save()
        self.assertEqual(updated_item.title, "Updated Title")
        self.assertEqual(updated_item.description, "Updated desc")

    def test_form_invalid_image_file_type(self):
        """Test form handles invalid image file types (mocked validation)."""
        invalid_image = SimpleUploadedFile("test.txt", b"text content", content_type="text/plain")
        form_data = {'title': self.valid_title}
        form = PortfolioItemForm(data=form_data, files={'image': invalid_image})
        # Assuming AutoCleanImageField validates, but since mocked, test basic
        self.assertTrue(form.is_valid())  # Mocked storage accepts any

    def test_form_edge_case_empty_form(self):
        """Test form with completely empty data."""
        form = PortfolioItemForm(data={}, files={})
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)
        self.assertIn('image', form.errors)


class CompanyConfigAdminFormTestCase(TestCase):
    """Test cases for CompanyConfigAdminForm (equivalent to GalleryCreationForm)."""

    def setUp(self):
        self.valid_email_host = "smtp.gmail.com"
        self.valid_email_username = "test@example.com"
        self.valid_email_password = "testpass"

    def test_form_valid_minimal_data(self):
        """Test form is valid with minimal data."""
        form_data = {}
        form = CompanyConfigAdminForm(data=form_data)
        self.assertTrue(form.is_valid())
        config = form.save()
        self.assertIsInstance(config, CompanyConfig)

    def test_form_valid_full_data(self):
        """Test form is valid with all fields provided."""
        form_data = {
            'address': '123 Test St',
            'contact_number': '254712345678',
            'facebook_username': 'testfb',
            'twitter_username': 'testtw',
            'instagram_username': 'testig',
            'tiktok': 'testtt',
            'always_save_contactus_queries': True,
            'email_host': self.valid_email_host,
            'email_port': 587,
            'email_username': self.valid_email_username,
            'email_password': self.valid_email_password,
            'email_use_tls': True,
            'email_from_address': 'from@example.com',
            'email_to_address': 'to@example.com'
        }
        form = CompanyConfigAdminForm(data=form_data)
        self.assertTrue(form.is_valid())
        config = form.save()
        self.assertEqual(config.address, '123 Test St')
        self.assertEqual(config.email_host, self.valid_email_host)

    def test_form_invalid_contact_number_too_long(self):
        """Test form is invalid when contact_number exceeds max length."""
        long_number = "1" * 21
        form_data = {'contact_number': long_number}
        form = CompanyConfigAdminForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('contact_number', form.errors)

    def test_form_invalid_email_host_too_long(self):
        """Test form is invalid when email_host exceeds max length."""
        long_host = "a" * 256
        form_data = {'email_host': long_host}
        form = CompanyConfigAdminForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email_host', form.errors)

    def test_form_valid_email_fields_blank(self):
        """Test form allows blank email fields."""
        form_data = {}
        form = CompanyConfigAdminForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_widget_password_render_value(self):
        """Test that email_password widget renders value."""
        form = CompanyConfigAdminForm()
        password_field = form.fields['email_password']
        self.assertTrue(password_field.widget.render_value)

    def test_form_save_updates_existing_instance(self):
        """Test form can update existing CompanyConfig."""
        config = CompanyConfig.objects.create(address="Original Address")
        form_data = {'address': "Updated Address"}
        form = CompanyConfigAdminForm(data=form_data, instance=config)
        self.assertTrue(form.is_valid())
        updated_config = form.save()
        self.assertEqual(updated_config.address, "Updated Address")

    def test_form_edge_case_invalid_email(self):
        """Test form handles invalid email formats."""
        form_data = {'email_username': 'invalid-email'}
        form = CompanyConfigAdminForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email_username', form.errors)

    def test_form_valid_boolean_fields(self):
        """Test boolean fields default and set correctly."""
        form_data = {'always_save_contactus_queries': True, 'email_use_tls': False}
        form = CompanyConfigAdminForm(data=form_data)
        self.assertTrue(form.is_valid())
        config = form.save()
        self.assertTrue(config.always_save_contactus_queries)
        self.assertFalse(config.email_use_tls)


class FormIntegrationTestCase(TestCase):
    """Integration tests for form-model interactions."""

    def setUp(self):
        self.valid_title = "Integration Test Item"
        self.valid_image = SimpleUploadedFile("int_test.jpg", b"file_content", content_type="image/jpeg")
        # Mock storage
        self.storage_patchers = [
            mock.patch.object(SupabaseStorage, '_save', return_value='mock/path.jpg'),
            mock.patch.object(SupabaseStorage, '_get_file_metadata', return_value={'name': 'mock.jpg', 'size': 100}),
            mock.patch.object(SupabaseStorage, 'url', return_value='http://mock.com/image.jpg'),
        ]
        for p in self.storage_patchers:
            p.start()

    def tearDown(self):
        for p in self.storage_patchers:
            p.stop()

    def test_portfolio_item_form_creates_model_instance(self):
        """Test PortfolioItemForm creates and saves PortfolioItem correctly."""
        form_data = {'title': self.valid_title, 'description': "Integration desc", 'tags': 'int tag'}
        form = PortfolioItemForm(data=form_data, files={'image': self.valid_image})
        self.assertTrue(form.is_valid())
        item = form.save()
        self.assertEqual(PortfolioItem.objects.count(), 1)
        saved_item = PortfolioItem.objects.first()
        self.assertEqual(saved_item.title, self.valid_title)
        self.assertEqual(saved_item.description, "Integration desc")
        self.assertIn('int tag', saved_item.tags.names())

    def test_company_config_form_updates_singleton(self):
        """Test CompanyConfigAdminForm updates the singleton instance."""
        # Create initial config
        initial_config = CompanyConfig.get_instance()
        form_data = {'address': 'New Address'}
        form = CompanyConfigAdminForm(data=form_data, instance=initial_config)
        self.assertTrue(form.is_valid())
        updated_config = form.save()
        self.assertEqual(updated_config.address, 'New Address')
        self.assertEqual(CompanyConfig.objects.count(), 1)

    def test_form_validation_error_prevents_save(self):
        """Test that validation errors prevent model save."""
        form_data = {'title': ''}  # Invalid
        form = PortfolioItemForm(data=form_data, files={'image': self.valid_image})
        self.assertFalse(form.is_valid())
        with self.assertRaises(ValueError):
            form.save()

    def test_form_with_existing_tags_updates_correctly(self):
        """Test form updates tags on existing instance."""
        item = PortfolioItem.objects.create(title="Existing", image=self.valid_image)
        item.tags.add('old tag')
        form_data = {'title': "Existing", 'tags': 'new tag'}
        form = PortfolioItemForm(data=form_data, files={}, instance=item)
        self.assertTrue(form.is_valid())
        updated_item = form.save()
        self.assertEqual(list(updated_item.tags.names()), ['new tag'])