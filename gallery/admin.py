from __future__ import annotations

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html, mark_safe
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import action, display
from unfold.enums import ActionVariant

from .forms import PortfolioItemForm
from .models import CompanyConfig, ContactQuery, PortfolioItem


@admin.register(PortfolioItem)
class PortfolioItemAdmin(ModelAdmin):
    form = PortfolioItemForm
    list_display = (
        "title",
        "is_published",
        "created_at",
        "image_preview",
        "tag_list",
    )
    list_filter = (
        "is_published",
        "created_at",
        ("tags", admin.RelatedFieldListFilter),
    )
    search_fields = ("title", "description", "tags__name")
    search_help_text = "Search by title, description, or tag name"
    readonly_fields = ("created_at", "updated_at", "slug", "image_preview")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    list_display_links = ("title",)  # make only title clickable
    actions = ("make_published", "make_unpublished")

    fieldsets = (
        (None, {
            "fields": ("title", "image", "image_preview", "description", "tags", "is_published")
        }),
        ("DateTime", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def image_preview(self, obj: PortfolioItem) -> str:
        """Display image preview in admin (both saved + live upload)."""
        if obj and obj.image:
            return mark_safe(
                f'<img id="image-preview" src="{obj.image.url}" width="150" style="border-radius: 4px;"/>'
            )
        return mark_safe(
            '<img id="image-preview" src="" width="150" style="display:none; border-radius:4px;"/>'
        )

    image_preview.short_description = "Preview"

    def tag_list(self, obj: PortfolioItem) -> str:
        """Comma-separated list of tags for display in the list view."""
        return ", ".join(tag.name for tag in obj.tags.order_by("name"))

    tag_list.short_description = "Tags"

    def get_queryset(self, request: HttpRequest) -> QuerySet[PortfolioItem]:
        qs: QuerySet[PortfolioItem] = super().get_queryset(request)
        return qs.prefetch_related("tags")

    @action(description="Mark selected items as published", variant=ActionVariant.PRIMARY, icon="person")
    def make_published(self, request: HttpRequest, queryset: QuerySet[PortfolioItem]) -> None:
        updated: int = queryset.update(is_published=True)
        self.message_user(request, f"{updated} portfolio item(s) marked as published.")

    @action(description="Mark selected items as unpublished", variant=ActionVariant.DANGER)
    def make_unpublished(self, request: HttpRequest, queryset: QuerySet[PortfolioItem]) -> None:
        updated: int = queryset.update(is_published=False)
        self.message_user(request, f"{updated} portfolio item(s) marked as unpublished.")

    class Media:
        js = ("js/admin/image_preview.js",)




@admin.register(CompanyConfig)
class CompanyConfigAdmin(ModelAdmin):
    compressed_fields = True
    warn_unsaved_form = True

    exclude = ('singleton_enforcer',)

    fieldsets = (
        ("Basic Information", {
            "fields": ("address", "contact_number", "always_save_contactus_queries"),
            "classes": ["tab"],
        }),
        ("Social Media", {
            "fields": ("facebook_username", "twitter_username", "instagram_username", "tiktok"),
            "classes": ["tab"],
        }),
        ("Email Configuration", {
            "fields": (
                "email_host", 
                "email_port", 
                "email_use_tls",
                "email_username", 
                "email_password",
                "email_from_address", 
                "email_to_address"
            ),
            "classes": ["tab"],
            "description": "Configure SMTP settings for sending contact form emails. Leave 'From' address blank to use email username. Leave 'To' address blank to send to email username.",
        })
    )

    list_display = ['__str__', 'contact_number', 'social_links_status']

    @display(description="Social Media")
    def social_links_status(self, obj):
        links = []
        if obj.facebook_username:
            links.append('<span class="px-2 py-1 rounded bg-blue-500 text-white text-xs">Facebook</span>')
        if obj.twitter_username:
            links.append('<span class="px-2 py-1 rounded bg-sky-500 text-white text-xs">Twitter</span>')
        if obj.instagram_username:
            links.append('<span class="px-2 py-1 rounded bg-pink-500 text-white text-xs">Instagram</span>')
        if obj.tiktok:
            links.append('<span class="px-2 py-1 rounded bg-blue-700 text-white text-xs">LinkedIn</span>')

        if links:
            return mark_safe(' '.join(links))
        return mark_safe('<span class="px-2 py-1 rounded bg-gray-500 text-white text-xs">None configured</span>')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = CompanyConfig.get_instance()
        change_url = reverse(
            f'admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change',
            args=[obj.pk]
        )
        return HttpResponseRedirect(change_url)

    def response_change(self, request, obj):
        return HttpResponseRedirect(".")


@admin.register(ContactQuery)
class ContactQueryAdmin(ModelAdmin):
    # List view configuration
    list_display = [
        "name_with_service",
        "email_link",
        "submitted_date",
        "location_info"
    ]

    list_filter = [
        ("submitted_at", admin.DateFieldListFilter),
        "service_required",
        ("email", admin.EmptyFieldListFilter),
    ]

    search_fields = ["name", "email", "service_required", "message"]

    readonly_fields = ["submitted_at", "ip_address", "user_agent", "location_info"]

    # Detail view configuration
    fieldsets = [
        ("Contact Information", {
            "fields": ["name", "email", "service_required"],
            "classes": ["tab"],
        }),
        ("Message", {
            "fields": ["message"],
            "classes": ["tab"],
        }),
        ("Submission Details", {
            "fields": ["submitted_at", "ip_address", "user_agent", "location_info"],
            "classes": ["tab", "collapse"],
        }),
    ]

    # Unfold specific settings
    list_per_page = 25
    show_full_result_count = False

    # Custom display methods
    @display(description="Contact & Service", ordering="name")
    def name_with_service(self, obj):
        return format_html(
            '<div class="flex flex-col">'
            '<span class="font-medium text-gray-900">{}</span>'
            '<span class="text-sm text-gray-500">{}</span>'
            '</div>',
            obj.name,
            obj.service_required
        )

    @display(description="Email", ordering="email")
    def email_link(self, obj):
        if obj.email:
            return format_html(
                '<a href="mailto:{}" class="text-blue-600 hover:text-blue-800">{}</a>',
                obj.email,
                obj.email
            )
        return format_html('<span class="text-gray-400">No email provided</span>')

    @display(description="Submitted", ordering="submitted_at")
    def submitted_date(self, obj):
        return format_html(
            '<div class="flex flex-col">'
            '<span class="font-medium">{}</span>'
            '<span class="text-sm text-gray-500">{}</span>'
            '</div>',
            obj.submitted_at.strftime("%d %b %Y"),
            obj.submitted_at.strftime("%H:%M")
        )

    @display(description="Location")
    def location_info(self, obj):
        if obj.ip_address:
            return format_html(
                '<div class="flex items-center space-x-2">'
                '<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">'
                '{}'
                '</span>'
                '</div>',
                obj.ip_address
            )
        return mark_safe('<span class="text-gray-400">Unknown</span>')

    def has_add_permission(self, request):
        """Disable adding contact queries through admin"""
        return False

    def has_change_permission(self, request, obj=None):
        """Make contact queries read-only"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Allow deletion for cleanup purposes"""
        return request.user.is_superuser

    # Unfold compressed tables for better mobile experience
    compressed_fields = True


# class PartnerInline(admin.TabularInline):
#     """Inline admin for partners in CompanyConfig"""
#     model = Partner
#     extra = 1
#     fields = ('name', 'description', 'url', 'image', 'is_active', 'display_order')
#     readonly_fields = ()
#     show_change_link = True
#
#     def image_preview(self, obj):
#         """Display image preview in inline"""
#         if obj and obj.image:
#             return mark_safe(
#                 f'<img src="{obj.image.url}" width="100" style="border-radius: 4px;"/>'
#             )
#         return mark_safe('<span class="text-gray-400">No image</span>')
#
#     image_preview.short_description = "Preview"
#
#     def get_fields(self, request, obj=None):
#         fields = list(super().get_fields(request, obj))
#         # Add image preview after image field
#         if 'image' in fields:
#             image_index = fields.index('image')
#             fields.insert(image_index + 1, 'image_preview')
#         return fields
#
#     def get_readonly_fields(self, request, obj=None):
#         return ()


