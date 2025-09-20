from __future__ import annotations

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.html import mark_safe
from unfold.admin import ModelAdmin
from unfold.decorators import action
from unfold.enums import ActionVariant

from .forms import PortfolioItemForm
from .models import PortfolioItem


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
            "fields": ("title", "image", "image_preview", "description","tags")
        }),
        ("Publication", {
            "fields": ("is_published", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def image_preview(self, obj: PortfolioItem) -> str:
        """Display a small image preview in the admin list/detail page."""
        if obj.image:
            return mark_safe(
                f'<img src="{obj.image.url}" width="100" style="border-radius: 4px;"/>'
            )
        return "No image"

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
        css = {
            'all': ('admin/css/taggit-unfold.css',)
        }
