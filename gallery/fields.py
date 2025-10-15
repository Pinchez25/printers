import logging
from typing import Callable, Dict, Iterable, Optional

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import FileField, ImageField, Model
from django.db.models.signals import post_delete, post_save

logger = logging.getLogger(__name__)


class AutoCleanFileField(FileField):
    """
    FileField that automatically cleans up old files:
      - deletes old file when field is replaced (post_save, after transaction commit)
      - deletes file when model instance is deleted (post_delete)

    Options:
      cleanup (bool): whether this field should auto-clean (default True)
      raise_on_delete_error (bool): re-raise exceptions during deletion (default False)

    Note:
      - Cleanup does NOT occur during bulk operations (bulk_create, bulk_update, raw SQL),
        as Django signals are not triggered in those cases.
      - File deletion is deferred until after the database transaction commits,
        ensuring consistency between database state and storage.
    """

    def __init__(self, *args, cleanup: bool = True, raise_on_delete_error: bool = False, **kwargs):
        self.cleanup = bool(cleanup)
        self.raise_on_delete_error = bool(raise_on_delete_error)
        super().__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name, **kwargs):
        """
        Register signal handlers once per concrete model and store field references.
        """
        super().contribute_to_class(cls, name, **kwargs)

        existing = getattr(cls, "_autoclean_file_fields", None)
        if existing is None:
            cls._autoclean_file_fields: Dict[str, "AutoCleanFileField"] = {}
        cls._autoclean_file_fields[name] = self

        if getattr(cls, "_autoclean_signals_registered", False):
            return

        if getattr(cls._meta, "abstract", False):
            return

        # Use dispatch_uid to prevent duplicate signal registration
        post_delete.connect(
            receiver=_make_post_delete_handler(cls),
            sender=cls,
            dispatch_uid=f"{cls._meta.label_lower}_autoclean_post_delete",
        )
        post_save.connect(
            receiver=_make_post_save_handler(cls),
            sender=cls,
            dispatch_uid=f"{cls._meta.label_lower}_autoclean_post_save",
        )

        cls._autoclean_signals_registered = True


def _make_post_delete_handler(model_cls) -> Callable:
    """Return a post_delete handler that deletes files for all autoclean fields."""

    def _handler(sender, instance, **kwargs):
        for field_name, field in getattr(sender, "_autoclean_file_fields", {}).items():
            if not getattr(field, "cleanup", True):
                continue

            file_field = getattr(instance, field_name, None)
            if not file_field:
                continue

            file_name = getattr(file_field, "name", None)
            if not file_name:
                continue

            try:
                file_field.delete(save=False)
                logger.debug(
                    "AutoCleanFileField: deleted file '%s' for %s.%s",
                    file_name, sender.__name__, field_name
                )
            except Exception as exc:
                logger.exception(
                    "AutoCleanFileField: failed to delete '%s' on delete for %s.%s: %s",
                    file_name, sender.__name__, field_name, exc
                )
                if getattr(field, "raise_on_delete_error", False):
                    raise

    return _handler


def _make_post_save_handler(model_cls) -> Callable:
    """
    Return a post_save handler that schedules old file deletion after transaction commit.
    """

    def _handler(sender, instance: Model, created: bool, update_fields: Optional[Iterable], **kwargs):
        if created:
            return

        # Optimise: skip if update_fields is provided and no autoclean fields are included
        autoclean_field_names = set(getattr(sender, "_autoclean_file_fields", {}).keys())
        if update_fields is not None:
            update_field_names = {str(f) for f in update_fields}
            if not autoclean_field_names.intersection(update_field_names):
                return

        try:
            old_instance = sender.objects.get(pk=instance.pk)
        except ObjectDoesNotExist:
            return

        files_to_delete = []

        for field_name, field in getattr(sender, "_autoclean_file_fields", {}).items():
            if not getattr(field, "cleanup", True):
                continue

            # Skip if field wasn't updated (when update_fields is specified)
            if update_fields is not None and field_name not in {str(f) for f in update_fields}:
                continue

            old_file = getattr(old_instance, field_name, None)
            new_file = getattr(instance, field_name, None)

            old_name = getattr(old_file, "name", None) if old_file else None
            new_name = getattr(new_file, "name", None) if new_file else None

            # No old file or same file → nothing to delete
            if not old_name or old_name == new_name:
                continue

            # Check if any other instance still references this file
            try:
                still_referenced = (
                    sender.objects
                    .filter(**{field_name: old_name})
                    .exclude(pk=instance.pk)
                    .exists()
                )
            except Exception as exc:
                logger.exception(
                    "AutoCleanFileField: DB check failed while deciding whether to delete '%s': %s",
                    old_name, exc
                )
                if getattr(field, "raise_on_delete_error", False):
                    raise
                continue

            if still_referenced:
                logger.debug(
                    "AutoCleanFileField: skipping deletion of '%s' because it's still referenced elsewhere",
                    old_name
                )
                continue

            files_to_delete.append((old_file, old_name, field_name))

        if files_to_delete:
            transaction.on_commit(lambda: _delete_files(sender, files_to_delete))

    return _handler


def _delete_files(sender, files_to_delete):
    """Delete files after transaction commit."""
    for old_file, old_name, field_name in files_to_delete:
        field = sender._autoclean_file_fields.get(field_name)
        try:
            old_file.delete(save=False)
            logger.debug(
                "AutoCleanFileField: deleted old file '%s' for %s.%s",
                old_name, sender.__name__, field_name
            )
        except Exception as exc:
            logger.exception(
                "AutoCleanFileField: failed to delete old file '%s' for %s.%s: %s",
                old_name, sender.__name__, field_name, exc
            )
            if field and getattr(field, "raise_on_delete_error", False):
                raise


class AutoCleanImageField(AutoCleanFileField, ImageField):
    """
    ImageField version of AutoCleanFileField for convenience.
    """
    pass
