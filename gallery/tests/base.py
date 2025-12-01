import shutil
import tempfile
from contextlib import contextmanager
from unittest.mock import patch

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.test import TestCase, override_settings


class DummyStorage(FileSystemStorage):
    def __init__(self, location=None, base_url=None):
        super().__init__(location=settings.MEDIA_ROOT, base_url=base_url)


@contextmanager
def patched_supabase_storage():
    with patch("gallery.models.SupabaseStorage", DummyStorage):
        yield


class InMemoryMediaTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._media_root = tempfile.mkdtemp(prefix="test_media_")
        cls._override = override_settings(
            MEDIA_ROOT=cls._media_root,
            DEFAULT_FILE_STORAGE="django.core.files.storage.FileSystemStorage",
            EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        )
        cls._override.enable()
        try:
            from gallery.models import PortfolioItem
            field = PortfolioItem._meta.get_field("image")
            field.storage = DummyStorage()
        except Exception:
            pass

    @classmethod
    def tearDownClass(cls):
        try:
            cls._override.disable()
        finally:
            shutil.rmtree(cls._media_root, ignore_errors=True)
        super().tearDownClass()
