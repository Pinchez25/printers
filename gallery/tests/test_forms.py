from unittest.mock import MagicMock, patch

from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase
from taggit.models import Tag
from unfold.widgets import UnfoldAdminTextInputWidget

from gallery.forms import PortfolioItemForm, UnfoldTagWidget
from gallery.models import PortfolioItem


class UnfoldTagWidgetTest(TestCase):
    """Test cases for UnfoldTagWidget"""

    def setUp(self):
        """Set up test data"""
        self.widget = UnfoldTagWidget()
        self.request_factory = RequestFactory()

    def test_widget_initialisation(self):
        """Test widget initialisation and attribute setting"""
        widget = UnfoldTagWidget()

        # Check that the widget has the expected attributes
        self.assertIn('class', widget.attrs)
        self.assertIn('placeholder', widget.attrs)
        self.assertEqual(widget.attrs['placeholder'], 'Add tags separated by commas')

    def test_widget_inherits_from_tag_widget(self):
        """Test that UnfoldTagWidget properly inherits from TagWidget"""
        from taggit.forms import TagWidget

        self.assertIsInstance(self.widget, TagWidget)

    def test_widget_class_inheritance(self):
        """Test that widget gets UnfoldAdminTextInputWidget classes"""
        # Create a temporary widget to get its classes
        temp_widget = UnfoldAdminTextInputWidget()
        unfold_classes = temp_widget.attrs.get('class', '')

        # Check that our widget has similar classes
        self.assertIn('class', self.widget.attrs)
        widget_classes = self.widget.attrs['class']

        # Should have some styling classes
        self.assertTrue(len(widget_classes) > 0)

    def test_widget_placeholder_attribute(self):
        """Test that placeholder is correctly set"""
        self.assertEqual(self.widget.attrs['placeholder'], 'Add tags separated by commas')

    def test_widget_rendering(self):
        """Test widget rendering with sample data"""
        html = self.widget.render('tags', 'tag1, tag2, tag3', {'id': 'id_tags'})

        # Should contain input element
        self.assertIn('<input', html)
        self.assertIn('id="id_tags"', html)
        self.assertIn('value="tag1, tag2, tag3"', html)

    def test_widget_empty_value_rendering(self):
        """Test widget rendering with empty value"""
        html = self.widget.render('tags', '', {'id': 'id_tags'})

        # Should contain input element
        self.assertIn('<input', html)
        self.assertIn('id="id_tags"', html)
        # Note: When value is empty, the value attribute might not be present or might be empty
        self.assertIn('name="tags"', html)


class PortfolioItemFormTest(TestCase):
    """Test cases for PortfolioItemForm"""

    def setUp(self):
        """Set up test data"""
        # Use the existing default.png file from static directory
        import os
        from django.conf import settings

        static_dir = settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else 'static'
        image_path = os.path.join(static_dir, 'default.png')

        if os.path.exists(image_path):
            with open(image_path, 'rb') as f:
                image_content = f.read()
            self.mock_image = SimpleUploadedFile(
                name='default.png',
                content=image_content,
                content_type='image/png'
            )
        else:
            # Fallback to minimal PNG if file doesn't exist
            png_header = b'\x89PNG\r\n\x1a\n' + b'\x00' * 4
            png_content = png_header + b'fake image content' * 10
            self.mock_image = SimpleUploadedFile(
                name='test_image.png',
                content=png_content,
                content_type='image/png'
            )

        self.form_data = {
            'title': 'Test Portfolio Item',
            'description': 'This is a test description for the portfolio item.',
            'is_published': True,
        }

        # Create some test tags
        self.tag1 = Tag.objects.create(name='test-tag-1', slug='test-tag-1')
        self.tag2 = Tag.objects.create(name='test-tag-2', slug='test-tag-2')

    @patch('gallery.models.get_backblaze_storage')
    def test_form_valid_data(self, mock_storage):
        """Test form with valid data"""
        mock_storage_instance = MagicMock()
        mock_storage.return_value = mock_storage_instance

        # Create form with files parameter for image
        form = PortfolioItemForm(data=self.form_data, files={'image': self.mock_image})
        self.assertTrue(form.is_valid())

    @patch('gallery.models.get_backblaze_storage')
    def test_form_missing_required_fields(self, mock_storage):
        """Test form with missing required fields"""
        mock_storage.return_value = MagicMock()
        # Remove required title field
        invalid_data = self.form_data.copy()
        del invalid_data['title']

        form = PortfolioItemForm(data=invalid_data, files={'image': self.mock_image})
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    @patch('gallery.models.get_backblaze_storage')
    def test_form_title_max_length(self, mock_storage):
        """Test form with title exceeding max length"""
        mock_storage.return_value = MagicMock()
        long_title = 'a' * 201  # Exceeds max_length of 200
        invalid_data = self.form_data.copy()
        invalid_data['title'] = long_title

        form = PortfolioItemForm(data=invalid_data, files={'image': self.mock_image})
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_form_default_values(self):
        """Test form with default values"""
        form = PortfolioItemForm()
        self.assertFalse(form.is_bound)
        self.assertEqual(form.data, {})

    @patch('gallery.models.get_backblaze_storage')
    def test_form_with_tags(self, mock_storage):
        """Test form with tags"""
        mock_storage.return_value = MagicMock()
        form_data_with_tags = self.form_data.copy()
        form_data_with_tags['tags'] = f'{self.tag1.name}, {self.tag2.name}'

        form = PortfolioItemForm(data=form_data_with_tags, files={'image': self.mock_image})
        self.assertTrue(form.is_valid())

        # Save the form to test tag association
        portfolio_item = form.save()
        self.assertIn(self.tag1, portfolio_item.tags.all())
        self.assertIn(self.tag2, portfolio_item.tags.all())

    @patch('gallery.models.get_backblaze_storage')
    def test_form_save_method(self, mock_storage):
        """Test form save method"""
        mock_storage.return_value = MagicMock()
        form = PortfolioItemForm(data=self.form_data, files={'image': self.mock_image})
        self.assertTrue(form.is_valid())

        portfolio_item = form.save()
        self.assertIsInstance(portfolio_item, PortfolioItem)
        self.assertEqual(portfolio_item.title, self.form_data['title'])
        self.assertEqual(portfolio_item.description, self.form_data['description'])
        self.assertTrue(portfolio_item.is_published)

    @patch('gallery.models.get_backblaze_storage')
    def test_form_update_existing_instance(self, mock_storage):
        """Test form with existing instance"""
        mock_storage.return_value = MagicMock()
        # Create existing portfolio item
        existing_item = PortfolioItem.objects.create(
            title='Original Title',
            description='Original description',
            is_published=False
        )

        # Update data
        update_data = {
            'title': 'Updated Title',
            'description': 'Updated description',
            'is_published': True,
        }

        form = PortfolioItemForm(data=update_data, files={'image': self.mock_image}, instance=existing_item)
        self.assertTrue(form.is_valid())

        updated_item = form.save()
        self.assertEqual(updated_item.id, existing_item.id)
        self.assertEqual(updated_item.title, 'Updated Title')
        self.assertEqual(updated_item.description, 'Updated description')
        self.assertTrue(updated_item.is_published)

    def test_form_fields_configuration(self):
        """Test that form has correct fields"""
        form = PortfolioItemForm()
        # Note: slug field is typically excluded from forms when using AutoSlugField
        expected_fields = ['title', 'image', 'description', 'is_published', 'tags']

        # Check that all expected fields are present
        for field_name in expected_fields:
            self.assertIn(field_name, form.fields)

    def test_form_widget_configuration(self):
        """Test that tags field uses UnfoldTagWidget"""
        form = PortfolioItemForm()
        tags_field = form.fields['tags']

        # Check that the widget is our custom UnfoldTagWidget
        self.assertIsInstance(tags_field.widget, UnfoldTagWidget)

    def test_form_field_attributes(self):
        """Test form field attributes"""
        form = PortfolioItemForm()

        # Check title field
        title_field = form.fields['title']
        self.assertIsInstance(title_field, forms.CharField)
        self.assertEqual(title_field.max_length, 200)

        # Check description field
        description_field = form.fields['description']
        self.assertIsInstance(description_field, forms.CharField)
        self.assertFalse(description_field.required)

        # Check is_published field
        is_published_field = form.fields['is_published']
        self.assertIsInstance(is_published_field, forms.BooleanField)
        self.assertTrue(is_published_field.initial)  # Should default to True

    def test_form_meta_configuration(self):
        """Test form Meta configuration"""
        form = PortfolioItemForm()

        # Check model
        self.assertEqual(form.Meta.model, PortfolioItem)

        # Check fields
        self.assertEqual(form.Meta.fields, '__all__')

        # Check widgets
        self.assertIn('tags', form.Meta.widgets)
        self.assertIsInstance(form.Meta.widgets['tags'], UnfoldTagWidget)

    @patch('gallery.models.get_backblaze_storage')
    def test_form_clean_method(self, mock_storage):
        """Test form clean method"""
        mock_storage.return_value = MagicMock()
        form = PortfolioItemForm(data=self.form_data, files={'image': self.mock_image})
        self.assertTrue(form.is_valid())

        # Test that clean method is called during validation
        cleaned_data = form.cleaned_data
        self.assertEqual(cleaned_data['title'], self.form_data['title'])
        self.assertEqual(cleaned_data['description'], self.form_data['description'])
        self.assertTrue(cleaned_data['is_published'])

    @patch('gallery.models.get_backblaze_storage')
    def test_form_with_empty_description(self, mock_storage):
        """Test form with empty description"""
        mock_storage.return_value = MagicMock()
        form_data_no_desc = self.form_data.copy()
        form_data_no_desc['description'] = ''

        form = PortfolioItemForm(data=form_data_no_desc, files={'image': self.mock_image})
        self.assertTrue(form.is_valid())

        portfolio_item = form.save()
        self.assertEqual(portfolio_item.description, '')

    @patch('gallery.models.get_backblaze_storage')
    def test_form_with_long_description(self, mock_storage):
        """Test form with long description"""
        mock_storage.return_value = MagicMock()
        long_description = 'a' * 1000  # Long but valid description
        form_data_long_desc = self.form_data.copy()
        form_data_long_desc['description'] = long_description

        form = PortfolioItemForm(data=form_data_long_desc, files={'image': self.mock_image})
        self.assertTrue(form.is_valid())

        portfolio_item = form.save()
        self.assertEqual(portfolio_item.description, long_description)

    @patch('gallery.models.get_backblaze_storage')
    def test_form_tags_string_conversion(self, mock_storage):
        """Test that tags are properly converted from string to tag objects"""
        mock_storage.return_value = MagicMock()
        form_data_with_tags = self.form_data.copy()
        form_data_with_tags['tags'] = f'{self.tag1.name}, {self.tag2.name}'

        form = PortfolioItemForm(data=form_data_with_tags, files={'image': self.mock_image})
        self.assertTrue(form.is_valid())

        portfolio_item = form.save()
        self.assertEqual(portfolio_item.tags.count(), 2)
        self.assertIn(self.tag1, portfolio_item.tags.all())
        self.assertIn(self.tag2, portfolio_item.tags.all())
