from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from taggit.models import Tag

from gallery.models import PortfolioItem
from gallery.filters import get_popular_tags, PortfolioItemFilter


class GetPopularTagsTestCase(TestCase):

    def setUp(self):
        self.valid_image = SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")

    @patch('gallery.filters.ContentType.objects.get_for_model')
    @patch('gallery.filters.Tag.objects.filter')
    def test_get_popular_tags_success(self, mock_filter, mock_get_for_model):
        mock_ct = MagicMock()
        mock_get_for_model.return_value = mock_ct
        mock_queryset = MagicMock()
        mock_filter.return_value = mock_queryset
        mock_queryset.annotate.return_value = mock_queryset
        mock_queryset.order_by.return_value = mock_queryset
        mock_tag = MagicMock()
        mock_queryset.__getitem__.return_value = [mock_tag]
        result = get_popular_tags(limit=10)
        self.assertEqual(result, [mock_tag])
        mock_filter.assert_called_once()
        mock_queryset.annotate.assert_called_once()
        mock_queryset.order_by.assert_called_once_with('-usage_count')
        mock_queryset.__getitem__.assert_called_once_with(slice(None, 10))

    @patch('gallery.filters.ContentType.objects.get_for_model')
    @patch('gallery.filters.Tag.objects.filter')
    def test_get_popular_tags_exception(self, mock_filter, mock_get_for_model):
        mock_get_for_model.side_effect = Exception("CT error")
        result = get_popular_tags()
        self.assertEqual(list(result), [])

    def test_get_popular_tags_with_published_items(self):
        item = PortfolioItem.objects.create(
            title="Test Item",
            image=self.valid_image,
            is_published=True
        )
        tag = Tag.objects.create(name="testtag")
        item.tags.add(tag)
        result = get_popular_tags()
        self.assertIn(tag, result)

    def test_get_popular_tags_excludes_unpublished(self):
        item = PortfolioItem.objects.create(
            title="Test Item",
            image=self.valid_image,
            is_published=False
        )
        tag = Tag.objects.create(name="testtag")
        item.tags.add(tag)
        result = get_popular_tags()
        self.assertEqual(len(result), 0)


class PortfolioItemFilterTestCase(TestCase):

    def setUp(self):
        self.valid_image = SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        self.filter_class = PortfolioItemFilter

    def test_filter_meta_model(self):
        filter_instance = self.filter_class()
        self.assertEqual(filter_instance.Meta.model, PortfolioItem)

    def test_filter_meta_fields(self):
        filter_instance = self.filter_class()
        self.assertIn('search', filter_instance.Meta.fields)
        self.assertIn('tags', filter_instance.Meta.fields)

    def test_filter_initialisation_sets_tags_queryset(self):
        filter_instance = self.filter_class()
        self.assertIsNotNone(filter_instance.filters['tags'].queryset)

    def test_filter_search_method_exact_match(self):
        item = PortfolioItem.objects.create(
            title="Django Project",
            image=self.valid_image,
            is_published=True
        )
        filter_instance = self.filter_class(data={'search': 'Django'})
        qs = filter_instance.qs
        self.assertIn(item, qs)

    def test_filter_search_method_case_insensitive(self):
        item = PortfolioItem.objects.create(
            title="Django Project",
            image=self.valid_image,
            is_published=True
        )
        filter_instance = self.filter_class(data={'search': 'django'})
        qs = filter_instance.qs
        self.assertIn(item, qs)

    def test_filter_search_method_description(self):
        item = PortfolioItem.objects.create(
            title="Test",
            description="Django application",
            image=self.valid_image,
            is_published=True
        )
        filter_instance = self.filter_class(data={'search': 'Django'})
        qs = filter_instance.qs
        self.assertIn(item, qs)

    def test_filter_search_method_tags(self):
        item = PortfolioItem.objects.create(
            title="Test",
            image=self.valid_image,
            is_published=True
        )
        tag = Tag.objects.create(name="django")
        item.tags.add(tag)
        filter_instance = self.filter_class(data={'search': 'django'})
        qs = filter_instance.qs
        self.assertIn(item, qs)

    def test_filter_search_method_normalised_spaces(self):
        item = PortfolioItem.objects.create(
            title="DjangoProject",
            image=self.valid_image,
            is_published=True
        )
        filter_instance = self.filter_class(data={'search': 'django project'})
        qs = filter_instance.qs
        self.assertIn(item, qs)

    def test_filter_search_method_empty_value(self):
        item = PortfolioItem.objects.create(
            title="Test",
            image=self.valid_image,
            is_published=True
        )
        filter_instance = self.filter_class(data={'search': ''})
        qs = filter_instance.qs
        self.assertIn(item, qs)

    def test_filter_search_method_no_matches(self):
        PortfolioItem.objects.create(
            title="Test",
            image=self.valid_image,
            is_published=True
        )
        filter_instance = self.filter_class(data={'search': 'nonexistent'})
        qs = filter_instance.qs
        self.assertEqual(qs.count(), 0)

    def test_filter_tags_by_name_and_logic(self):
        item1 = PortfolioItem.objects.create(
            title="Item1",
            image=self.valid_image,
            is_published=True
        )
        item2 = PortfolioItem.objects.create(
            title="Item2",
            image=SimpleUploadedFile("test2.jpg", b"content", content_type="image/jpeg"),
            is_published=True
        )
        tag1 = Tag.objects.create(name="tag1")
        tag2 = Tag.objects.create(name="tag2")
        item1.tags.add(tag1, tag2)
        item2.tags.add(tag1)
        filter_instance = self.filter_class(data={'tag_list': 'tag1,tag2'})
        qs = filter_instance.qs
        self.assertIn(item1, qs)
        self.assertNotIn(item2, qs)

    def test_filter_tags_by_name_single_tag(self):
        item = PortfolioItem.objects.create(
            title="Test",
            image=self.valid_image,
            is_published=True
        )
        tag = Tag.objects.create(name="testtag")
        item.tags.add(tag)
        filter_instance = self.filter_class(data={'tag_list': 'testtag'})
        qs = filter_instance.qs
        self.assertIn(item, qs)

    def test_filter_tags_by_name_empty_value(self):
        item = PortfolioItem.objects.create(
            title="Test",
            image=self.valid_image,
            is_published=True
        )
        filter_instance = self.filter_class(data={'tag_list': ''})
        qs = filter_instance.qs
        self.assertIn(item, qs)

    def test_filter_tags_by_name_case_insensitive(self):
        item = PortfolioItem.objects.create(
            title="Test",
            image=self.valid_image,
            is_published=True
        )
        tag = Tag.objects.create(name="TestTag")
        item.tags.add(tag)
        filter_instance = self.filter_class(data={'tag_list': 'testtag'})
        qs = filter_instance.qs
        self.assertIn(item, qs)

    def test_filter_tags_by_name_with_spaces(self):
        item = PortfolioItem.objects.create(
            title="Test",
            image=self.valid_image,
            is_published=True
        )
        tag = Tag.objects.create(name="test tag")
        item.tags.add(tag)
        filter_instance = self.filter_class(data={'tag_list': 'test tag'})
        qs = filter_instance.qs
        self.assertIn(item, qs)

    def test_filter_combined_search_and_tags(self):
        item = PortfolioItem.objects.create(
            title="Django App",
            image=self.valid_image,
            is_published=True
        )
        tag = Tag.objects.create(name="python")
        item.tags.add(tag)
        filter_instance = self.filter_class(data={'search': 'Django', 'tag_list': 'python'})
        qs = filter_instance.qs
        self.assertIn(item, qs)

    def test_filter_is_published_default(self):
        item = PortfolioItem.objects.create(
            title="Test",
            image=self.valid_image,
            is_published=True
        )
        filter_instance = self.filter_class(data={})
        qs = filter_instance.qs
        self.assertIn(item, qs)

    def test_filter_excludes_unpublished_by_default(self):
        PortfolioItem.objects.create(
            title="Unpublished",
            image=self.valid_image,
            is_published=False
        )
        filter_instance = self.filter_class(data={'is_published': True})
        qs = filter_instance.qs
        self.assertEqual(qs.count(), 0)

    def test_filter_with_request_context(self):
        request = MagicMock()
        filter_instance = self.filter_class(data={}, request=request)
        self.assertEqual(filter_instance.request, request)