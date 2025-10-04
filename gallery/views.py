import json
import logging
from smtplib import SMTPException

from django.conf import settings
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from gallery.filters import PortfolioItemFilter
from gallery.models import CompanyConfig, ContactQuery, PortfolioItem

logger = logging.getLogger(__name__)


@require_http_methods(["POST"])
def contact_form_view(request):
    """Handle contact form submission via AJAX"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid request format.'
        }, status=400)

    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    service = data.get('service', '').strip()
    message = data.get('message', '').strip()

    try:
        config = CompanyConfig.get_instance()
    except Exception as e:
        logger.error(f"Failed to get company config: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Server configuration error. Please try again later.'
        }, status=500)

    try:
        with transaction.atomic():
            if config.always_save_contactus_queries:
                ContactQuery.objects.create(
                    name=name,
                    email=email or None,
                    service_required=service,
                    message=message,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )

            # Send email notification
            email_context = {
                'name': name,
                'email': email,
                'service': service,
                'message': message,
                'config': config,
            }

            html_message = render_to_string('emails/contact_form.html', email_context)

            plain_message = render_to_string('emails/contact_form.txt', email_context)

            recipient_email = config.email if config.email else settings.DEFAULT_FROM_EMAIL

            send_mail(
                subject=f'New Inquiry - {service}',
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient_email],
                html_message=html_message,
                fail_silently=False,
            )

        return JsonResponse({
            'success': True,
            'message': 'Thank you for your inquiry! We will get back to you soon.'
        })

    except (SMTPException, OSError, ConnectionError, TimeoutError) as e:
        logger.error(f"Email sending failed: {e}")
        return JsonResponse({
            'success': False,
            'message': 'There was an issue processing your request. Please try again later.'
        }, status=500)
    except Exception as e:
        logger.error(f"Unexpected error in contact form: {e}")
        return JsonResponse({
            'success': False,
            'message': 'An unexpected error occurred. Please try again later.'
        }, status=500)


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def index_view(request):
    """Main index view"""
    config = CompanyConfig.get_instance()

    # Get latest 6 published portfolio items for homepage gallery
    latest_portfolio_items = PortfolioItem.objects.filter(
        is_published=True
    ).select_related().prefetch_related('tags').order_by('-created_at')[:6]

    context = {
        'latest_portfolio_items': latest_portfolio_items,
    }
    return render(request, 'index.html', context)


def gallery_view(request):
    """Gallery view with optimised queries"""
    config = CompanyConfig.get_instance()

    # Get all published portfolio items with optimized query
    portfolio_items = PortfolioItem.objects.filter(is_published=True).select_related().prefetch_related('tags')

    # Get unique tags for filtering
    all_tags = PortfolioItem.tags.most_common()[:20]  # Limit to top 20 tags for performance

    context = {
        'portfolio_items': portfolio_items,
        'all_tags': all_tags,
    }
    return render(request, 'gallery.html', context)


@api_view(['GET'])
@permission_classes([AllowAny])
def gallery_api(request):
    """API endpoint for gallery data with search and filtering using Django-filter"""
    try:
        # Get query parameters
        search = request.GET.get('search', '').strip()
        # Support both CSV ?tags=a,b and array ?tags[]=a&tags[]=b
        raw_tags_csv = request.GET.get('tags', '').strip()
        tags = []
        if raw_tags_csv:
            tags = [t.strip() for t in raw_tags_csv.split(',') if t.strip()]
        else:
            tags = request.GET.getlist('tags[]')
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 6))

        # Build filter parameters
        filter_params = {'is_published': True}

        # Add search parameter if provided
        if search:
            filter_params['search'] = search

        # Add tag parameters if provided
        if tags and 'all' not in tags:
            filter_params['tag_list'] = ','.join(tags)

        # Create filter instance
        filter_instance = PortfolioItemFilter(data=filter_params, request=request)
        queryset = filter_instance.qs

        # Optimise with select_related and prefetch_related
        queryset = queryset.select_related().prefetch_related('tags')

        # Paginate results using Django's Paginator
        paginator = Paginator(queryset, per_page)
        page_obj = paginator.get_page(page)

        # Prepare data for JSON response
        items_data = []
        for item in page_obj:
            items_data.append({
                'id': item.id,
                'title': item.title,
                'slug': item.slug,
                'description': item.description or '',
                'thumbnail': item.get_thumbnail_url(),
                'fullImage': item.get_preview_url(),
                'tags': list(item.tags.names()),
                'created_at': item.created_at.isoformat() if item.created_at else None,
            })

        response_data = {
            'success': True,
            'items': items_data,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_items': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            },
            'filters': {
                'search': search,
                'tags': tags,
            }
        }

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error in gallery API: {e}")
        return Response({
            'success': False,
            'message': 'An error occurred while fetching gallery data.',
            'error': str(e) if settings.DEBUG else 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def gallery_tags_api(request):
    """API endpoint for available filter tags"""
    try:
        from .filters import get_popular_tags

        # Get popular tags for PortfolioItem
        popular_tags = get_popular_tags(limit=20)

        tags_data = []
        for tag in popular_tags:
            tags_data.append({
                'name': tag.name,
                'slug': tag.slug,
                'count': tag.item_count if hasattr(tag, 'item_count') else 0
            })

        response_data = {
            'success': True,
            'tags': tags_data
        }

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error in gallery tags API: {e}")
        return Response({
            'success': False,
            'message': 'An error occurred while fetching tags.',
            'error': str(e) if settings.DEBUG else 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
