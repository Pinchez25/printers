import uuid
from pathlib import Path

from autoslug import AutoSlugField
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django_backblaze_b2 import BackblazeB2Storage
from taggit.managers import TaggableManager


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
    image = models.ImageField(upload_to=upload_to, storage=get_backblaze_storage)
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

    def __str__(self) -> str:
        return self.title


class CompanyConfig(models.Model):
    singleton_enforcer = models.BooleanField(default=True, unique=True, editable=False,
                                             help_text="Ensures only one configuration exists")

    address = models.TextField(blank=True, help_text="Company address")
    email = models.EmailField(blank=True, help_text="Contact email")
    contact_number = models.CharField(max_length=20, blank=True, help_text="Contact phone number e.g. 254758123456")
    facebook_username = models.CharField(max_length=100, blank=True, help_text="Facebook username")
    twitter_username = models.CharField(max_length=100, blank=True, help_text="Twitter handle")
    instagram_username = models.CharField(max_length=100, blank=True, help_text="Instagram username")
    tiktok = models.CharField(max_length=100, blank=True, help_text="TikTok username")
    services_offered = models.JSONField(blank=True, default=list, help_text="List of services offered as a JSON array")
    always_save_contactus_queries = models.BooleanField(default=False,
                                                        help_text="Always save contact form submissions to database")

    # Statistics for display
    happy_customers = models.PositiveIntegerField(default=5000, help_text="Number of happy customers")
    projects_completed = models.PositiveIntegerField(default=15000, help_text="Number of projects completed")
    years_experience = models.PositiveIntegerField(default=8, help_text="Years of experience")
    support_hours = models.PositiveIntegerField(default=24, help_text="Hours of support provided")

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
    name = models.CharField(max_length=200, help_text="Contact person's full name")
    email = models.EmailField(blank=True, help_text="Contact email (optional)")
    service_required = models.CharField(max_length=100, help_text="Type of service requested")
    message = models.TextField(help_text="Contact message or inquiry details")
    submitted_at = models.DateTimeField(auto_now_add=True, help_text="When the inquiry was submitted")
    ip_address = models.GenericIPAddressField(blank=True, null=True, help_text="IP address of the submitter")
    user_agent = models.TextField(blank=True, help_text="Browser user agent string")

    class Meta:
        ordering = ["-submitted_at"]
        verbose_name = "Contact Query"
        verbose_name_plural = "Contact Queries"

    def __str__(self):
        return f"{self.name} - {self.service_required} ({self.submitted_at.strftime('%Y-%m-%d')})"
