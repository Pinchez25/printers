import logging
from functools import lru_cache
from typing import Any, Callable, Dict, Iterable, Optional

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models, transaction
from django.db.models import FileField, ImageField, Model
from django.db.models.signals import post_delete, post_save

logger = logging.getLogger(__name__)


@lru_cache(maxsize=8)
def _get_cipher_for_key(key: str) -> Fernet:
    return Fernet(key.encode())


class EncryptedCharField(models.CharField):
    PREFIX = 'fernet:'

    def __init__(self, *args, encryption_key: Optional[str] = None, **kwargs):
        self.encryption_key = encryption_key
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self.encryption_key is not None:
            kwargs['encryption_key'] = self.encryption_key
        return name, path, args, kwargs

    def contribute_to_class(self, cls, name, **kwargs):
        super().contribute_to_class(cls, name, **kwargs)
        if self.max_length and self.max_length < 255:
            import warnings
            warnings.warn(
                f"EncryptedCharField '{name}' on {cls.__name__} has max_length={self.max_length}, "
                f"which may be too small for encrypted data. Recommend ≥255.",
                UserWarning,
                stacklevel=2
            )

    def get_internal_type(self):
        return "CharField"

    def get_encryption_key(self) -> str:
        if self.encryption_key:
            key = self.encryption_key
        else:
            key = getattr(settings, "ENCRYPTION_KEY", None)
            if not key:
                raise ValueError("ENCRYPTION_KEY not found in settings.")

        try:
            Fernet(key.encode())
        except ValueError as e:
            raise ValueError(f"Invalid ENCRYPTION_KEY: {e}") from e

        return key

    def _get_cipher(self) -> Fernet:
        return _get_cipher_for_key(self.get_encryption_key())

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)

    def to_python(self, value):
        if value is None or value == '':
            return value

        if not self._is_encrypted(value):
            return value

        encrypted_data = value[len(self.PREFIX):]
        try:
            return self._get_cipher().decrypt(encrypted_data.encode()).decode()
        except InvalidToken:
            raise ValidationError("Failed to decrypt value. Key mismatch or corrupted data.")

    def _is_encrypted(self, value: str) -> bool:
        return isinstance(value, str) and value.startswith(self.PREFIX)

    def get_prep_value(self, value):
        if value is None or value == '':
            return value

        if self._is_encrypted(value):
            return value

        try:
            encrypted = self._get_cipher().encrypt(value.encode()).decode()
            return f"{self.PREFIX}{encrypted}"
        except Exception as e:
            raise ValueError(f"Failed to encrypt value: {e}")


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
      - Race condition: Between checking file references and deletion, another transaction
        could save a record using the same file, resulting in an orphaned file reference.
        This window is typically <100ms and acceptable for most applications.
        For high-concurrency scenarios requiring stronger guarantees, consider:
        * Application-level file reference counting
        * Periodic clean-up jobs to reconcile orphaned references
        * Using object storage with lifecycle policies
    """

    def __init__(self, *args, cleanup: bool = True, raise_on_delete_error: bool = False, **kwargs):
        self.cleanup = bool(cleanup)
        self.raise_on_delete_error = bool(raise_on_delete_error)
        super().__init__(*args, **kwargs)

    def contribute_to_class(self, cls: type[Model], name: str, **kwargs: Any) -> None:
        """
        Register signal handlers once per concrete model and store field references.
        """
        super().contribute_to_class(cls, name, **kwargs)

        existing = getattr(cls, "_autoclean_file_fields", None)
        if existing is None:
            cls._autoclean_file_fields = {}
        cls._autoclean_file_fields[name] = self

        if getattr(cls, "_autoclean_signals_registered", False):
            return

        if getattr(cls._meta, "abstract", False):
            return

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


def _make_post_delete_handler(model_cls: type[Model]) -> Callable:
    """Return a post_delete handler that deletes files for all autoclean fields."""

    def handler(sender: type[Model], instance: Model, **kwargs: Any) -> None:
        autoclean_fields = getattr(sender, "_autoclean_file_fields", {})
        if not autoclean_fields:
            return

        for field_name, field in autoclean_fields.items():
            if not field.cleanup:
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
            except (OSError, IOError) as exc:
                logger.exception(
                    "AutoCleanFileField: failed to delete '%s' on delete for %s.%s: %s",
                    file_name, sender.__name__, field_name, exc
                )
                if field.raise_on_delete_error:
                    raise
            except Exception as exc:
                logger.exception(
                    "AutoCleanFileField: unexpected error deleting '%s' on delete for %s.%s: %s",
                    file_name, sender.__name__, field_name, exc
                )
                if field.raise_on_delete_error:
                    raise

    return handler


def _make_post_save_handler(model_cls: type[Model]) -> Callable:
    """
    Return a post_save handler that schedules old file deletion after transaction commit.
    """

    def handler(sender: type[Model], instance: Model, created: bool, 
                update_fields: Optional[Iterable], **kwargs: Any) -> None:
        if created:
            return

        autoclean_fields = getattr(sender, "_autoclean_file_fields", {})
        if not autoclean_fields:
            return

        autoclean_field_names = set(autoclean_fields.keys())
        if update_fields is not None:
            update_field_names = {str(f) for f in update_fields}
            if not autoclean_field_names.intersection(update_field_names):
                return
        else:
            update_field_names = None

        try:
            old_instance = sender.objects.get(pk=instance.pk)
        except ObjectDoesNotExist:
            return

        files_to_delete = []

        for field_name, field in autoclean_fields.items():
            if not field.cleanup:
                continue

            if update_field_names is not None and field_name not in update_field_names:
                continue

            old_file = getattr(old_instance, field_name, None)
            new_file = getattr(instance, field_name, None)

            old_name = getattr(old_file, "name", None) if old_file else None
            new_name = getattr(new_file, "name", None) if new_file else None

            if not old_name or old_name == new_name:
                continue

            try:
                still_referenced = (
                    sender.objects
                    .filter(**{field_name: old_name})
                    .exclude(pk=instance.pk)
                    .exists()
                )
            except (ObjectDoesNotExist, ValueError, TypeError) as exc:
                logger.exception(
                    "AutoCleanFileField: DB check failed while deciding whether to delete '%s': %s",
                    old_name, exc
                )
                if field.raise_on_delete_error:
                    raise
                continue
            except Exception as exc:
                logger.exception(
                    "AutoCleanFileField: unexpected error during DB check for '%s': %s",
                    old_name, exc
                )
                if field.raise_on_delete_error:
                    raise
                continue

            if still_referenced:
                logger.debug(
                    "AutoCleanFileField: skipping deletion of '%s' because it's still referenced elsewhere",
                    old_name
                )
                continue

            files_to_delete.append((old_file, old_name, field_name, field))

        if files_to_delete:
            transaction.on_commit(lambda: _delete_files(sender, files_to_delete))

    return handler


def _delete_files(sender: type[Model], files_to_delete: list) -> None:
    """Delete files after transaction commit."""
    for old_file, old_name, field_name, field in files_to_delete:
        try:
            old_file.delete(save=False)
            logger.debug(
                "AutoCleanFileField: deleted old file '%s' for %s.%s",
                old_name, sender.__name__, field_name
            )
        except (OSError, IOError) as exc:
            logger.exception(
                "AutoCleanFileField: failed to delete old file '%s' for %s.%s: %s",
                old_name, sender.__name__, field_name, exc
            )
            if field.raise_on_delete_error:
                raise
        except Exception as exc:
            logger.exception(
                "AutoCleanFileField: unexpected error deleting old file '%s' for %s.%s: %s",
                old_name, sender.__name__, field_name, exc
            )
            if field.raise_on_delete_error:
                raise


class AutoCleanImageField(AutoCleanFileField, ImageField):
    """
    ImageField version of AutoCleanFileField for convenience.
    """
    pass
