import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


def user_profile_photo_path(instance, filename):
    return f"profile_photos/user_{instance.id}/{filename}"


class CustomUser(AbstractUser):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    profile_photo = models.ImageField(
        upload_to=user_profile_photo_path,
        blank=True,
        null=True,
        verbose_name=_("Profile photo")
    )
    role = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name=_("Role / Position"),
        help_text=_("Used for 'Our Team' display.")
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Description"),
        help_text=_("Short biography or details for 'Our Team'.")
    )

    def __str__(self):
        return self.get_full_name() or self.username
