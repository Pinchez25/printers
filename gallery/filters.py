import logging
import django_filters
from django.db.models import Q, Count
from django.contrib.contenttypes.models import ContentType
from taggit.models import Tag

from .models import PortfolioItem

logger = logging.getLogger(__name__)


def get_popular_tags(limit=20):
    """Get most popular tags for published PortfolioItem instances"""
    try:
        portfolioitem_ct = ContentType.objects.get_for_model(PortfolioItem)
        return Tag.objects.filter(
            taggit_taggeditem_items__content_type=portfolioitem_ct,
            taggit_taggeditem_items__object_id__in=PortfolioItem.objects.filter(
                is_published=True
            ).values_list('id', flat=True)
        ).annotate(
            usage_count=Count('taggit_taggeditem_items')
        ).order_by('-usage_count')[:limit]
    
    except Exception as e:
        logger.error(f"Error retrieving popular tags: {e}")
        return Tag.objects.none()


class PortfolioItemFilter(django_filters.FilterSet):
    """Filter for PortfolioItem with search and tag filtering"""

    search = django_filters.CharFilter(
        method='filter_search',
        label='Search',
        help_text='Search in title, description, and tags'
    )

    tags = django_filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.none(),
        field_name='tags__name',
        to_field_name='name',
        label='Tags',
        help_text='Select multiple tags (OR logic)'
    )

    tag_list = django_filters.CharFilter(
        method='filter_tags_by_name',
        label='Tag List',
        help_text='Comma-separated tag names (AND logic)'
    )

    class Meta:
        model = PortfolioItem
        fields = ['search', 'tags', 'tag_list', 'is_published']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters['tags'].queryset = get_popular_tags()

    def filter_search(self, queryset, name, value):
        """Search across title, description, and tags"""
        if not value:
            return queryset

        return queryset.filter(
            Q(title__icontains=value) |
            Q(description__icontains=value) |
            Q(tags__name__icontains=value)
        ).distinct()

    def filter_tags_by_name(self, queryset, name, value):
        """Filter by comma-separated tag names with AND logic
        
        Example: 'django,python' returns items tagged with both Django AND Python
        """
        if not value:
            return queryset

        tag_names = [tag.strip() for tag in value.split(',') if tag.strip()]
        if not tag_names:
            return queryset

        for tag_name in tag_names:
            queryset = queryset.filter(tags__name__iexact=tag_name)

        return queryset.distinct()