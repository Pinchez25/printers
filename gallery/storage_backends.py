import inspect
import mimetypes
import posixpath
from datetime import datetime, timezone as python_timezone
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import File
from django.core.files.storage import Storage
from django.utils import timezone
from django.utils.deconstruct import deconstructible
from supabase import Client, create_client


@deconstructible
class SupabaseStorage(Storage):
    """
    A Django Storage backend for Supabase Storage.
    Supports both public and private buckets with optional signed URLs.
    """

    def __init__(self):
        # Validate required settings
        if not getattr(settings, 'SUPABASE_URL', None):
            raise ImproperlyConfigured("SUPABASE_URL is not set in Django settings.")
        if not getattr(settings, 'SUPABASE_KEY', None):
            raise ImproperlyConfigured("SUPABASE_KEY is not set in Django settings.")
        if not getattr(settings, 'SUPABASE_BUCKET_NAME', None):
            raise ImproperlyConfigured("SUPABASE_BUCKET_NAME is not set in Django settings.")

        self.bucket_name = settings.SUPABASE_BUCKET_NAME
        self.base_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/{self.bucket_name}/"
        self.url_expires_in = getattr(settings, 'SUPABASE_SIGNED_URL_EXPIRES_IN', 3600)
        self._client: Optional[Client] = None  # Lazy initialisation for thread safety

    # --- Internal Utilities ---------------------------------------------------

    @property
    def client(self) -> Client:
        """Thread-safe lazy initialisation of the Supabase client."""
        if self._client is None:
            self._client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        return self._client

    @staticmethod
    def _get_content_type(name: str) -> str:
        content_type, _ = mimetypes.guess_type(name)
        return content_type or 'application/octet-stream'

    @staticmethod
    def _normalise_name(name: str) -> str:
        """Normalise path separators and remove leading slashes."""
        return posixpath.normpath(name).lstrip('/')

    def _get_file_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        """Retrieve file metadata from Supabase by listing the parent directory."""
        name = self._normalise_name(name)
        path, filename = (name.rsplit('/', 1) if '/' in name else ('', name))
        try:
            files = self.client.storage.from_(self.bucket_name).list(path=path or '')
            for f in files:
                if f.get('name') == filename:
                    return f
        except Exception:
            pass
        return None

    # --- Core Django Storage API ---------------------------------------------



    def _save(self, name: str, content) -> str:
        name = self._normalise_name(name)
        content.seek(0)
        file_data = content.read()

        upload_kwargs = {
            "path": name,
            "file": file_data,
            "file_options": {"content-type": self._get_content_type(name)},
        }

        # Check if 'upsert' is accepted by upload()
        sig = inspect.signature(self.client.storage.from_(self.bucket_name).upload)
        if "upsert" in sig.parameters:
            upload_kwargs["upsert"] = True

        try:
            self.client.storage.from_(self.bucket_name).upload(**upload_kwargs)
        except Exception as e:
            raise IOError(f"Failed to upload '{name}' to Supabase: {e}")

        return name

    def _open(self, name: str, mode: str = 'rb') -> File:
        name = self._normalise_name(name)
        try:
            response = self.client.storage.from_(self.bucket_name).download(name)

            # Handle multiple possible SDK response structures
            data = getattr(response, 'data', None)
            if isinstance(response, bytes):
                file_bytes = response
            elif isinstance(data, bytes):
                file_bytes = data
            elif hasattr(response, 'content'):
                file_bytes = response.content
            else:
                raise IOError(f"Unexpected download response type: {type(response)}")

            return File(BytesIO(file_bytes), name=name)

        except Exception as e:
            raise FileNotFoundError(f"Failed to download '{name}': {e}")

    def delete(self, name: str) -> None:
        name = self._normalise_name(name)
        try:
            result = self.client.storage.from_(self.bucket_name).remove([name])
            if isinstance(result, list) and result:
                error = result[0]
                raise IOError(f"Supabase error: {error.get('message', 'Unknown error')}")
        except Exception as e:
            raise IOError(f"Failed to delete '{name}': {e}")

    def exists(self, name: str) -> bool:
        return self._get_file_metadata(name) is not None

    def url(self, name: str) -> str:
        name = self._normalise_name(name)
        if getattr(settings, "SUPABASE_PUBLIC_BUCKET", True):
            return urljoin(self.base_url, name)

        try:
            signed = self.client.storage.from_(self.bucket_name).create_signed_url(
                name, self.url_expires_in
            )

            # Defensive handling for SDK variations
            if isinstance(signed, dict):
                if "signedURL" in signed:
                    return signed["signedURL"]
                if "data" in signed and isinstance(signed["data"], dict):
                    return signed["data"].get("signedURL", "")

            raise IOError(f"Unexpected signed URL response: {signed}")
        except Exception as e:
            raise IOError(f"Failed to create signed URL for '{name}': {e}")

    def size(self, name: str) -> int:
        metadata = self._get_file_metadata(name)
        if metadata is None:
            raise FileNotFoundError(f"File '{name}' does not exist.")
        return metadata.get('metadata', {}).get('size') or metadata.get('size', 0)

    def listdir(self, path: str) -> Tuple[List[str], List[str]]:
        path = self._normalise_name(path)
        if path and not path.endswith('/'):
            path += '/'

        try:
            files = self.client.storage.from_(self.bucket_name).list(path=path or '')
        except Exception:
            return [], []

        directories = set()
        filenames = []

        for f in files:
            full_name = f['name']
            normalised = self._normalise_name(full_name)
            rel_name = normalised[len(path):] if normalised.startswith(path) else normalised
            if '/' in rel_name:
                directories.add(rel_name.split('/', 1)[0])
            else:
                filenames.append(rel_name)

        return list(directories), filenames

    # --- Timestamp Accessors -------------------------------------------------

    def get_accessed_time(self, name):
        return self.get_modified_time(name)

    def get_created_time(self, name):
        return self.get_modified_time(name)

    def get_modified_time(self, name):
        metadata = self._get_file_metadata(name)
        if metadata is None:
            raise FileNotFoundError(f"File '{name}' does not exist.")

        updated_at = metadata.get('updated_at')
        if updated_at:
            dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            return timezone.make_aware(dt, python_timezone.utc)

        return timezone.now()
