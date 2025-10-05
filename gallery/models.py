import uuid
from pathlib import Path

from autoslug import AutoSlugField
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django_backblaze_b2 import BackblazeB2Storage
from taggit.managers import TaggableManager
from django.templatetags.static import static
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill, ResizeToFit


def get_backblaze_storage():
    return BackblazeB2Storage()


def upload_to(instance: "PortfolioItem", filename: str) -> str:
    ext = Path(filename).suffix
    unique_name = f"{uuid.uuid4().hex}{ext}"
    date = instance.created_at or timezone.now()
    return f"portfolio/{date.year}/{date.month}/{unique_name}"


class PortfolioItem(models.Model):
    title: models.CharField = models.CharField(max_length=200)
    slug: AutoSlugField = AutoSlugField(
        populate_from="title",
        unique=True,
    )
    image = models.ImageField(
        upload_to=upload_to, storage=get_backblaze_storage)

    # Processed images via ImageKit
    thumbnail = ImageSpecField(
        source="image",
        processors=[ResizeToFill(300, 300)],  # square thumbnail, crop like cover
        format="JPEG",
        options={"quality": 85},
    )
    preview = ImageSpecField(
        source="image",
        processors=[ResizeToFit(1600, 1200)],  # resized large for lightbox
        format="JPEG",
        options={"quality": 90},
    )

    description: models.TextField = models.TextField(blank=True)
    is_published: models.BooleanField = models.BooleanField(default=True)
    tags: TaggableManager = TaggableManager(blank=True)
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["slug"]),
        ]

    def get_absolute_url(self) -> str:
        return reverse("gallery:detail", kwargs={"slug": self.slug})

    def get_image_url(self) -> str:
        """Return full image URL, falling back to a default static image.

        This method is resilient to storage/back-end errors (e.g., Backblaze B2
        missing files or permissions) and will always return a safe URL.
        """
        try:
            return self.image.url
        except Exception:
            # Any error (missing file, storage error, etc.) falls back to default
            return static("default.jpg")

    def get_thumbnail_url(self) -> str:
        """Return thumbnail URL, falling back if image missing or inaccessible."""
        try:
            return self.thumbnail.url
        except Exception:
            # Fall back to the original image URL; that method is already safe
            return self.get_image_url()

    def get_preview_url(self) -> str:
        """Return preview/lightbox-sized URL, falling back if missing or inaccessible."""
        try:
            return self.preview.url
        except Exception:
            return self.get_image_url()

    def __str__(self) -> str:
        return self.title


class CompanyConfig(models.Model):
    singleton_enforcer = models.BooleanField(default=True, unique=True, editable=False,
                                             help_text="Ensures only one configuration exists")

    address = models.TextField(blank=True, help_text="Company address")
    contact_number = models.CharField(
        max_length=20, blank=True, help_text="Contact phone number e.g. 254758123456")
    facebook_username = models.CharField(
        max_length=100, blank=True, help_text="Facebook username")
    twitter_username = models.CharField(
        max_length=100, blank=True, help_text="Twitter handle")
    instagram_username = models.CharField(
        max_length=100, blank=True, help_text="Instagram username")
    tiktok = models.CharField(
        max_length=100, blank=True, help_text="TikTok username")
    always_save_contactus_queries = models.BooleanField(default=False,
                                                        help_text="Always save contact form submissions to database")


    class Meta:
        verbose_name = "Company Configuration"
        verbose_name_plural = "Company Configuration"

    def save(self, *args, **kwargs):
        self.singleton_enforcer = True
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        if not self.pk and CompanyConfig.objects.exists():
            raise ValidationError("Only one Company Configuration is allowed.")

    @classmethod
    def get_instance(cls):
        obj, created = cls.objects.get_or_create(singleton_enforcer=True)
        return obj

    def __str__(self):
        return "Company Configuration"


class ContactQuery(models.Model):
    name = models.CharField(
        max_length=200, help_text="Contact person's full name")
    email = models.EmailField(blank=True, help_text="Contact email (optional)")
    service_required = models.CharField(
        max_length=100, help_text="Type of service requested")
    message = models.TextField(help_text="Contact message or inquiry details")
    submitted_at = models.DateTimeField(
        auto_now_add=True, help_text="When the inquiry was submitted")
    ip_address = models.GenericIPAddressField(
        blank=True, null=True, help_text="IP address of the submitter")
    user_agent = models.TextField(
        blank=True, help_text="Browser user agent string")

    class Meta:
        ordering = ["-submitted_at"]
        verbose_name = "Contact Query"
        verbose_name_plural = "Contact Queries"

    def __str__(self):
        return f"{self.name} - {self.service_required} ({self.submitted_at.strftime('%Y-%m-%d')})"
