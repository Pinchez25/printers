from __future__ import annotations

import uuid
from pathlib import Path

from autoslug import AutoSlugField
from django.db import models
from django.urls import reverse
from django.utils import timezone
from taggit.managers import TaggableManager


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
    image: models.ImageField = models.ImageField(upload_to=upload_to)
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
