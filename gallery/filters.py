import logging
import django_filters
from django.db.models import Q, Count
from django.db.models.functions import Lower, Replace
from django.contrib.contenttypes.models import ContentType
from django.db import models
from taggit.models import Tag


from .models import PortfolioItem

logger = logging.getLogger(__name__)


def get_popular_tags(limit=20):
    """Get the most popular tags for published PortfolioItem instances"""
    try:
        portfolioitem_ct = ContentType.objects.get_for_model(PortfolioItem)
        published_ids = PortfolioItem.objects.filter(
            is_published=True
        ).values_list('id', flat=True)

        return Tag.objects.filter(
            taggit_taggeditem_items__content_type=portfolioitem_ct,
            taggit_taggeditem_items__object_id__in=published_ids
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

    @staticmethod
    def filter_search(queryset, name, value):
        """Search across title, description, and tags with space-normalised matching"""
        if not value:
            return queryset

        normalised_value = value.replace(' ', '').lower()

        search_query = (
            Q(title__icontains=value) |
            Q(description__icontains=value) |
            Q(tags__name__icontains=value)
        )

        queryset_with_normalised = queryset.annotate(
            normalised_title=Lower(
                Replace('title', models.Value(' '), models.Value(
                    ''), output_field=models.CharField())
            ),
            normalised_description=Lower(
                Replace('description', models.Value(' '), models.Value(
                    ''), output_field=models.TextField())
            )
        )

        normalised_query = (
            Q(normalised_title__icontains=normalised_value) |
            Q(normalised_description__icontains=normalised_value)
        )

        return queryset_with_normalised.filter(search_query | normalised_query).distinct()

    @staticmethod
    def filter_tags_by_name(queryset, name, value):
        """Filter by comma-separated tag names with AND logic

        Example: 'django, python' returns items tagged with both Django AND Python
        """
        if not value:
            return queryset

        tag_names = [tag.strip() for tag in value.split(',') if tag.strip()]

        for tag_name in tag_names:
            queryset = queryset.filter(tags__name__iexact=tag_name)

        return queryset.distinct()
