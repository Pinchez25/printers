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
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from gallery.filters import PortfolioItemFilter
from gallery.models import CompanyConfig, ContactQuery, PortfolioItem

logger = logging.getLogger(__name__)

HOMEPAGE_ITEMS_LIMIT = 6
DEFAULT_PAGE_SIZE = 6
TAGS_LIMIT = 20


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def send_contact_email(name, email, message, service, config):
    email_context = {
        'name': name,
        'email': email,
        'phone': None,
        'message': message,
        'service': service,
        'config': config,
        'submitted_at': timezone.now(),
    }

    html_message = render_to_string('emails/contact_form.html', email_context)
    plain_message = render_to_string('emails/contact_form.txt', email_context)
    recipient_email = settings.EMAIL_HOST_USER or settings.DEFAULT_FROM_EMAIL

    send_mail(
        subject=f'New Inquiry from {name}',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient_email],
        html_message=html_message,
        fail_silently=False,
    )


@require_http_methods(["POST"])
def contact_form_view(request):
    try:
        if request.content_type and 'application/json' in request.content_type:
            data = json.loads(request.body.decode(
                'utf-8')) if request.body else {}
        else:
            data = request.POST.dict()
    except json.JSONDecodeError:
        data = request.POST.dict()

    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip()
    phone = (data.get('phone') or '').strip()
    service = (data.get('service') or '').strip()
    message = (data.get('message') or '').strip()

    if not all([name, email, message]):
        return JsonResponse({
            'success': False,
            'message': 'Please provide your name, email, and message.'
        }, status=400)

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
                    email=email,
                    service_required=service,
                    message=message,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                )

            # Include phone and service in email context by passing a small wrapper
            # We'll render templates using the same send_contact_email helper but
            # it expects phone in context; pass phone via monkeypatch in kwargs.
            # Simpler: render templates here and send_mail directly so phone is included.
            # Map known service slugs to human-friendly labels
            SERVICE_LABELS = {
                'banners-stickers': 'Banners & Stickers',
                'merchandise': 'Merchandise Branding',
                'hospital-stationery': 'Books & Hospital Stationery',
                'campaign-items': 'Campaign & Promotional Items',
                'packaging': 'Packaging Solutions',
                'brochures-flyers': 'Brochures & Flyers',
                'other': 'Other',
            }

            service_label = SERVICE_LABELS.get(service, service or 'Other')

            email_context = {
                'name': name,
                'email': email,
                'phone': phone,
                'message': message,
                'service': service,
                'service_label': service_label,
                'config': config,
                'submitted_at': timezone.now(),
            }

            html_message = render_to_string(
                'emails/contact_form.html', email_context)
            plain_message = render_to_string(
                'emails/contact_form.txt', email_context)
            recipient_email = settings.EMAIL_HOST_USER or settings.DEFAULT_FROM_EMAIL

            send_mail(
                subject=f'New Inquiry from {name}',
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


def index(request):
    """Single page application view that provides all data for the frontend"""
    # Get all published portfolio items for the portfolio section
    portfolio_items = PortfolioItem.objects.filter(
        is_published=True
    ).prefetch_related('tags').order_by('-created_at')

    # Get all tags for filtering (same as original gallery view)
    all_tags = PortfolioItem.tags.most_common()[:TAGS_LIMIT]

    context = {
        'portfolio_items': portfolio_items,
        'all_tags': all_tags,
    }
    return render(request, 'index.html', context)


def serialize_portfolio_item(item):
    return {
        'id': item.id,
        'title': item.title.title() if item.title else '',
        'slug': item.slug,
        'description': item.description or '',
        'thumbnail': item.get_image_url(),
        'fullImage': item.get_image_url(),
        'tags': list(item.tags.names()),
        'created_at': item.created_at.isoformat() if item.created_at else None,
    }


@api_view(['GET'])
@permission_classes([AllowAny])
def gallery_api(request):
    try:
        search = request.GET.get('search', '').strip()
        raw_tags_csv = request.GET.get('tags', '').strip()
        tags = [t.strip() for t in raw_tags_csv.split(',') if t.strip()
                ] if raw_tags_csv else request.GET.getlist('tags[]')

        try:
            page = int(request.GET.get('page', 1))
            per_page = int(request.GET.get('per_page', DEFAULT_PAGE_SIZE))
        except (ValueError, TypeError):
            page = 1
            per_page = DEFAULT_PAGE_SIZE

        filter_params = {'is_published': True}

        if search:
            filter_params['search'] = search

        if tags and 'all' not in tags:
            filter_params['tag_list'] = ','.join(tags)

        filter_instance = PortfolioItemFilter(
            data=filter_params, request=request)
        queryset = filter_instance.qs.prefetch_related('tags')

        paginator = Paginator(queryset, per_page)
        page_obj = paginator.get_page(page)

        items_data = [serialize_portfolio_item(item) for item in page_obj]

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
            'message': 'An error occurred whilst fetching gallery data.',
            'error': str(e) if settings.DEBUG else 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def gallery_tags_api(request):
    try:
        from .filters import get_popular_tags

        popular_tags = get_popular_tags(limit=TAGS_LIMIT)

        tags_data = [
            {
                'name': tag.name,
                'slug': tag.slug,
                'count': getattr(tag, 'item_count', 0)
            }
            for tag in popular_tags
        ]

        response_data = {
            'success': True,
            'tags': tags_data
        }

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error in gallery tags API: {e}")
        return Response({
            'success': False,
            'message': 'An error occurred whilst fetching tags.',
            'error': str(e) if settings.DEBUG else 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
