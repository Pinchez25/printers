import json
import logging
from smtplib import SMTPException

from django.conf import settings
from django.core.mail import get_connection, send_mail
from django.core.paginator import Paginator
from django.db import transaction
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from gallery.filters import PortfolioItemFilter, get_popular_tags
from gallery.models import CompanyConfig, ContactQuery, PortfolioItem

logger = logging.getLogger(__name__)

DEFAULT_PAGE_SIZE = 6
TAGS_LIMIT = 20

SERVICE_LABELS: dict[str, str] = {
    "banners-stickers": "Banners & Stickers",
    "merchandise": "Merchandise Branding",
    "hospital-stationery": "Books & Hospital Stationery",
    "campaign-items": "Campaign & Promotional Items",
    "packaging": "Packaging Solutions",
    "brochures-flyers": "Brochures & Flyers",
    "other": "Other",
}


def capitalise_first_letter(text: str | None) -> str | None:
    """Capitalise the first alphabetical character in the string."""
    if not text:
        return text
    for index_, char in enumerate(text):
        if char.isalpha():
            return text[:index_] + char.upper() + text[index_ + 1:]
    return text


def get_client_ip(request: HttpRequest) -> str:
    """Return the first IP address from X-Forwarded-For or fallback to REMOTE_ADDR."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
        if ip:
            return ip
    return request.META.get("REMOTE_ADDR", "")


def get_request_data(request: HttpRequest) -> dict:
    """Extract JSON body or POST form data."""
    content_type = request.content_type or ""
    if "application/json" in content_type:
        try:
            return json.loads(request.body.decode("utf-8")) if request.body else {}
        except json.JSONDecodeError:
            return {}
    return request.POST.dict()


def _build_email_connection(config: CompanyConfig):
    """Return a fully constructed email connection or None if not configured."""
    if not (config.email_host and config.email_username and config.email_password):
        return None

    return get_connection(
        host=config.email_host,
        port=config.email_port,
        username=config.email_username,
        password=config.email_password,
        use_tls=bool(config.email_use_tls),
        fail_silently=False,
    )


def send_contact_email(
        name: str,
        email: str,
        phone: str,
        message: str,
        service: str,
        config: CompanyConfig,
) -> None:
    """Render and send the contact form email."""
    service_label = SERVICE_LABELS.get(service, service or "Other")

    context = {
        "name": name,
        "email": email,
        "phone": phone,
        "message": message,
        "service": service,
        "service_label": service_label,
        "config": config,
        "submitted_at": timezone.now(),
    }

    html_message = render_to_string("emails/contact_form.html", context)
    text_message = render_to_string("emails/contact_form.txt", context)

    from_email = (
            config.email_from_address
            or config.email_username
            or settings.DEFAULT_FROM_EMAIL
    )
    to_email = (
            config.email_to_address
            or config.email_username
            or settings.DEFAULT_FROM_EMAIL
    )

    connection = _build_email_connection(config)

    send_mail(
        subject=f"New Inquiry from {name}",
        message=text_message,
        from_email=from_email,
        recipient_list=[to_email],
        html_message=html_message,
        fail_silently=False,
        connection=connection,
    )


@require_http_methods(["POST"])
def contact_form_view(request: HttpRequest) -> JsonResponse:
    data = get_request_data(request)

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    phone = (data.get("phone") or "").strip()
    service = (data.get("service") or "").strip()
    message = (data.get("message") or "").strip()

    if not all([name, email, message]):
        return JsonResponse(
            {"success": False, "message": "Please provide your name, email, and message."},
            status=400,
        )

    try:
        config = CompanyConfig.get_instance()
    except Exception as exc:
        logger.error("Failed to load company config: %s", exc)
        return JsonResponse(
            {
                "success": False,
                "message": "Server configuration error. Please try again later.",
            },
            status=500,
        )

    if not config.is_email_configured():
        return JsonResponse(
            {
                "success": False,
                "message": "Email service is currently unavailable. Please try again later or contact us directly.",
            },
            status=503,
        )

    try:
        with transaction.atomic():
            if config.always_save_contactus_queries:
                ContactQuery.objects.create(
                    name=name,
                    email=email,
                    service_required=service,
                    message=message,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get("HTTP_USER_AGENT", ""),
                )

            send_contact_email(name, email, phone, message, service, config)

        return JsonResponse(
            {
                "success": True,
                "message": "Thank you for your inquiry! We will get back to you soon.",
            }
        )

    except (SMTPException, OSError, ConnectionError, TimeoutError) as exc:
        logger.error("Email sending failed: %s", exc)
        return JsonResponse(
            {
                "success": False,
                "message": "There was an issue processing your request. Please try again later.",
            },
            status=500,
        )

    except Exception as exc:
        logger.error("Unexpected error in contact form: %s", exc)
        return JsonResponse(
            {
                "success": False,
                "message": "An unexpected error occurred. Please try again later.",
            },
            status=500,
        )


def index(request: HttpRequest) -> HttpResponse:
    portfolio_items = (
        PortfolioItem.objects.filter(is_published=True)
        .prefetch_related("tags")
        .order_by("-created_at")
    )

    all_tags = PortfolioItem.tags.most_common()[:TAGS_LIMIT]

    return render(
        request,
        "index.html",
        {"portfolio_items": portfolio_items, "all_tags": all_tags},
    )


def serialize_portfolio_item(item: PortfolioItem) -> dict[str, object]:
    return {
        "id": item.id,
        "title": capitalise_first_letter(item.title),
        "slug": item.slug,
        "description": item.description or "",
        "thumbnail": item.get_image_url(),
        "fullImage": item.get_image_url(),
        "tags": list(item.tags.names()),
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


def parse_pagination_params(request: Request) -> tuple[int, int]:
    try:
        page = int(request.GET.get("page", 1))
        per_page = int(request.GET.get("per_page", DEFAULT_PAGE_SIZE))
    except (TypeError, ValueError):
        return 1, DEFAULT_PAGE_SIZE
    return page, per_page


@api_view(["GET"])
@permission_classes([AllowAny])
def gallery_api(request: Request):
    try:
        search = request.GET.get("search", "").strip()

        raw_tags = request.GET.get("tags", "").strip()
        tags = (
            [t.strip() for t in raw_tags.split(",") if t.strip()]
            if raw_tags
            else request.GET.getlist("tags[]")
        )

        page, per_page = parse_pagination_params(request)

        filter_params = {"is_published": True}
        if search:
            filter_params["search"] = search
        if tags and "all" not in tags:
            filter_params["tag_list"] = ",".join(tags)

        filter_instance = PortfolioItemFilter(data=filter_params, request=request)
        queryset = filter_instance.qs.prefetch_related("tags")

        paginator = Paginator(queryset, per_page)
        page_obj = paginator.get_page(page)

        items_data = [serialize_portfolio_item(item) for item in page_obj]

        return Response(
            {
                "success": True,
                "items": items_data,
                "pagination": {
                    "current_page": page_obj.number,
                    "total_pages": paginator.num_pages,
                    "total_items": paginator.count,
                    "has_next": page_obj.has_next(),
                    "has_previous": page_obj.has_previous(),
                },
                "filters": {"search": search, "tags": tags},
            },
            status=status.HTTP_200_OK,
        )

    except Exception as exc:
        logger.error("Error in gallery API: %s", exc)
        return Response(
            {
                "success": False,
                "message": "An error occurred whilst fetching gallery data.",
                "error": str(exc) if settings.DEBUG else "Internal server error",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def gallery_tags_api(request: Request):
    try:
        popular_tags = get_popular_tags(limit=TAGS_LIMIT)

        tags_data = [
            {
                "name": tag.name,
                "slug": tag.slug,
                "count": getattr(tag, "item_count", 0),
            }
            for tag in popular_tags
        ]

        return Response(
            {"success": True, "tags": tags_data}, status=status.HTTP_200_OK
        )

    except Exception as exc:
        logger.error("Error in gallery tags API: %s", exc)
        return Response(
            {
                "success": False,
                "message": "An error occurred whilst fetching tags.",
                "error": str(exc) if settings.DEBUG else "Internal server error",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

