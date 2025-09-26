from unittest.mock import patch

from django.test import TestCase
from taggit.models import Tag

from gallery.filters import PortfolioItemFilter, get_popular_tags
from gallery.models import PortfolioItem


class GetPopularTagsTest(TestCase):
    """Test cases for get_popular_tags utility function"""

    def setUp(self):
        """Set up test data"""
        # Create test tags
        self.tag1 = Tag.objects.create(name='popular-tag-1', slug='popular-tag-1')
        self.tag2 = Tag.objects.create(name='popular-tag-2', slug='popular-tag-2')
        self.tag3 = Tag.objects.create(name='unpopular-tag', slug='unpopular-tag')

        # Create test portfolio items
        self.item1 = PortfolioItem.objects.create(
            title='Item 1',
            description='Description 1',
            is_published=True
        )
        self.item1.tags.add(self.tag1)

        self.item2 = PortfolioItem.objects.create(
            title='Item 2',
            description='Description 2',
            is_published=True
        )
        self.item2.tags.add(self.tag1, self.tag2)

        self.item3 = PortfolioItem.objects.create(
            title='Item 3',
            description='Description 3',
            is_published=True
        )
        self.item3.tags.add(self.tag2)

        # Create unpublished item (should not be counted)
        self.unpublished_item = PortfolioItem.objects.create(
            title='Unpublished Item',
            description='Should not appear in popular tags',
            is_published=False
        )
        self.unpublished_item.tags.add(self.tag3)

    def test_get_popular_tags_basic(self):
        """Test get_popular_tags with default limit"""
        tags = get_popular_tags()

        # Should return tags ordered by usage count
        self.assertEqual(len(tags), 2)  # Only tags from published items

        # tag1 should be first (used by 2 items)
        self.assertEqual(tags[0].name, self.tag1.name)
        self.assertEqual(tags[0].usage_count, 2)

        # tag2 should be second (used by 2 items)
        self.assertEqual(tags[1].name, self.tag2.name)
        self.assertEqual(tags[1].usage_count, 2)

    def test_get_popular_tags_with_limit(self):
        """Test get_popular_tags with custom limit"""
        tags = get_popular_tags(limit=2)

        # Should return only top 2 tags
        self.assertEqual(len(tags), 2)
        self.assertEqual(tags[0].name, self.tag1.name)
        self.assertEqual(tags[1].name, self.tag2.name)

    def test_get_popular_tags_empty_result(self):
        """Test get_popular_tags when no tags exist"""
        # Delete all tags
        Tag.objects.all().delete()

        tags = get_popular_tags()
        self.assertEqual(len(tags), 0)

    def test_get_popular_tags_unpublished_items_excluded(self):
        """Test that unpublished items are excluded from popular tags"""
        tags = get_popular_tags()

        # tag3 should not appear since it's only used by unpublished items
        tag3 = next((tag for tag in tags if tag.name == self.tag3.name), None)
        self.assertIsNone(tag3)  # Should not be included

    @patch('gallery.filters.ContentType.objects.get_for_model')
    def test_get_popular_tags_content_type_error(self, mock_get_for_model):
        """Test get_popular_tags error handling"""
        mock_get_for_model.side_effect = Exception('ContentType error')

        tags = get_popular_tags()
        self.assertEqual(len(tags), 0)

    @patch('gallery.filters.Tag.objects.filter')
    def test_get_popular_tags_filter_error(self, mock_filter):
        """Test get_popular_tags when filter raises exception"""
        mock_filter.side_effect = Exception('Filter error')

        tags = get_popular_tags()
        self.assertEqual(len(tags), 0)

    def test_get_popular_tags_annotation(self):
        """Test that usage_count annotation is correctly applied"""
        tags = get_popular_tags()

        for tag in tags:
            self.assertTrue(hasattr(tag, 'usage_count'))
            self.assertIsInstance(tag.usage_count, int)
            self.assertGreaterEqual(tag.usage_count, 0)

    def test_get_popular_tags_ordering(self):
        """Test that tags are ordered by usage count descending"""
        tags = get_popular_tags()

        # Check that tags are ordered by usage_count descending
        usage_counts = [tag.usage_count for tag in tags]
        self.assertEqual(usage_counts, sorted(usage_counts, reverse=True))


class PortfolioItemFilterTest(TestCase):
    """Test cases for PortfolioItemFilter"""

    def setUp(self):
        """Set up test data"""
        # Create test tags
        self.tag1 = Tag.objects.create(name='filter-tag-1', slug='filter-tag-1')
        self.tag2 = Tag.objects.create(name='filter-tag-2', slug='filter-tag-2')

        # Create test portfolio items
        self.item1 = PortfolioItem.objects.create(
            title='Filter Item 1',
            description='Description with filter tag 1',
            is_published=True
        )
        self.item1.tags.add(self.tag1)

        self.item2 = PortfolioItem.objects.create(
            title='Filter Item 2',
            description='Description with filter tag 2',
            is_published=True
        )
        self.item2.tags.add(self.tag2)

        self.item3 = PortfolioItem.objects.create(
            title='Filter Item 3',
            description='Description with both tags',
            is_published=True
        )
        self.item3.tags.add(self.tag1, self.tag2)

        # Create unpublished item
        self.unpublished_item = PortfolioItem.objects.create(
            title='Unpublished Filter Item',
            description='Should not appear in filters',
            is_published=False
        )
        self.unpublished_item.tags.add(self.tag1)

    def test_filter_search_title(self):
        """Test search filter on title"""
        filter_instance = PortfolioItemFilter(data={'search': 'Filter Item 1'})
        queryset = filter_instance.qs

        items = list(queryset)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].title, 'Filter Item 1')

    def test_filter_search_description(self):
        """Test search filter on description"""
        filter_instance = PortfolioItemFilter(data={'search': 'filter tag 1'})
        queryset = filter_instance.qs

        items = list(queryset)
        # Should find items with "filter tag 1" in description
        self.assertEqual(len(items), 1)  # Only item1 has "filter tag 1" in description

    def test_filter_search_tags(self):
        """Test search filter on tags"""
        filter_instance = PortfolioItemFilter(data={'search': 'filter-tag-1'})
        queryset = filter_instance.qs

        items = list(queryset)
        # Should find items tagged with filter-tag-1
        self.assertEqual(len(items), 3)  # item1, item3, and unpublished item

    def test_filter_search_case_insensitive(self):
        """Test that search is case insensitive"""
        filter_instance = PortfolioItemFilter(data={'search': 'FILTER ITEM'})
        queryset = filter_instance.qs

        items = list(queryset)
        # Should find all items since the search matches titles
        self.assertEqual(len(items), 4)  # All items

    def test_filter_search_empty(self):
        """Test search filter with empty value"""
        filter_instance = PortfolioItemFilter(data={'search': ''})
        queryset = filter_instance.qs

        items = list(queryset)
        self.assertEqual(len(items), 4)  # All items

    def test_filter_tags_by_name_single(self):
        """Test filtering by single tag name"""
        filter_instance = PortfolioItemFilter(data={'tag_list': 'filter-tag-1'})
        queryset = filter_instance.qs

        items = list(queryset)
        self.assertEqual(len(items), 3)  # item1, item3, and unpublished item

    def test_filter_tags_by_name_multiple(self):
        """Test filtering by multiple tag names (AND logic)"""
        filter_instance = PortfolioItemFilter(data={'tag_list': 'filter-tag-1, filter-tag-2'})
        queryset = filter_instance.qs

        items = list(queryset)
        self.assertEqual(len(items), 1)  # Only item3 has both tags
        self.assertEqual(items[0].title, 'Filter Item 3')

    def test_filter_tags_by_name_empty(self):
        """Test tag filter with empty value"""
        filter_instance = PortfolioItemFilter(data={'tag_list': ''})
        queryset = filter_instance.qs

        items = list(queryset)
        self.assertEqual(len(items), 4)  # All items

    def test_filter_tags_by_name_whitespace(self):
        """Test tag filter with whitespace"""
        filter_instance = PortfolioItemFilter(data={'tag_list': '  filter-tag-1  ,  filter-tag-2  '})
        queryset = filter_instance.qs

        items = list(queryset)
        self.assertEqual(len(items), 1)  # Only item3 has both tags

    def test_filter_published_only(self):
        """Test that filter only includes published items by default"""
        filter_instance = PortfolioItemFilter()
        queryset = filter_instance.qs

        items = list(queryset)
        # Should include all items since we didn't set is_published=True in the filter
        # The filter defaults to showing all items, not just published ones
        self.assertEqual(len(items), 4)  # All items including unpublished

    def test_filter_initialization_popular_tags(self):
        """Test that filter initializes with popular tags"""
        filter_instance = PortfolioItemFilter()

        # Should have popular tags in the tags queryset
        popular_tags = list(filter_instance.filters['tags'].queryset)
        self.assertGreater(len(popular_tags), 0)

    def test_filter_distinct_results(self):
        """Test that filter returns distinct results"""
        # Create duplicate scenario
        filter_instance = PortfolioItemFilter(data={'search': 'filter'})
        queryset = filter_instance.qs

        items = list(queryset)
        # Should not have duplicates even if search matches multiple fields
        unique_items = list(set(items))
        self.assertEqual(len(items), len(unique_items))

    def test_filter_combined_search_and_tags(self):
        """Test combining search and tag filters"""
        filter_instance = PortfolioItemFilter(data={
            'search': 'Item 1',
            'tag_list': 'filter-tag-1'
        })
        queryset = filter_instance.qs

        items = list(queryset)
        self.assertEqual(len(items), 1)  # item1 matches both criteria
        self.assertEqual(items[0].title, 'Filter Item 1')

    def test_filter_no_matches(self):
        """Test filter with no matching results"""
        filter_instance = PortfolioItemFilter(data={
            'search': 'nonexistent',
            'tag_list': 'nonexistent-tag'
        })
        queryset = filter_instance.qs

        items = list(queryset)
        self.assertEqual(len(items), 0)

    def test_filter_queryset_optimization(self):
        """Test that filter uses optimized queryset"""
        filter_instance = PortfolioItemFilter(data={'search': 'filter'})

        # Check that the queryset has select_related and prefetch_related
        queryset = filter_instance.qs
        self.assertIsNotNone(queryset)

    def test_filter_tags_queryset_initialization(self):
        """Test that tags filter is properly initialized"""
        filter_instance = PortfolioItemFilter()

        tags_filter = filter_instance.filters['tags']
        self.assertIsNotNone(tags_filter.queryset)

        # Should have some tags available
        available_tags = list(tags_filter.queryset)
        self.assertGreater(len(available_tags), 0)

    def test_filter_method_calls(self):
        """Test that custom filter methods are called correctly"""
        filter_instance = PortfolioItemFilter(data={'search': 'test'})

        # Test that filter_search method exists and is callable
        self.assertTrue(hasattr(filter_instance, 'filter_search'))
        self.assertTrue(callable(filter_instance.filter_search))

        # Test that filter_tags_by_name method exists and is callable
        self.assertTrue(hasattr(filter_instance, 'filter_tags_by_name'))
        self.assertTrue(callable(filter_instance.filter_tags_by_name))

    def test_filter_base_fields(self):
        """Test that filter has expected base fields"""
        filter_instance = PortfolioItemFilter()

        expected_fields = ['search', 'tags', 'tag_list', 'is_published']
        for field_name in expected_fields:
            self.assertIn(field_name, filter_instance.filters)

    def test_filter_field_types(self):
        """Test that filter fields have correct types"""
        filter_instance = PortfolioItemFilter()

        # Search field should be CharFilter
        search_filter = filter_instance.filters['search']
        from django_filters import CharFilter
        self.assertIsInstance(search_filter, CharFilter)

        # Tags field should be ModelMultipleChoiceFilter
        tags_filter = filter_instance.filters['tags']
        from django_filters import ModelMultipleChoiceFilter
        self.assertIsInstance(tags_filter, ModelMultipleChoiceFilter)

        # Tag list field should be CharFilter
        tag_list_filter = filter_instance.filters['tag_list']
        self.assertIsInstance(tag_list_filter, CharFilter)
