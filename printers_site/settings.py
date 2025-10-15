import os
import sys
from pathlib import Path

from django.templatetags.static import static
from dotenv import load_dotenv

import gallery.storage_backends

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR/".env")



SECRET_KEY = os.getenv("SECRET_KEY")

DEBUG = os.getenv("DEBUG", "False") == "True"

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")

# Use SQLite for tests
if 'test' in sys.argv:
    SECRET_KEY = 'test-secret-key'
    DEBUG = True
    ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Application definition

INSTALLED_APPS = [
    "unfold",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'django_filters',
    'accounts.apps.AccountsConfig',
    'gallery.apps.GalleryConfig',
    "taggit",
    "imagekit",
    "django_backblaze_b2",
    'django_cleanup.apps.CleanupConfig',
]

AUTH_USER_MODEL = "accounts.CustomUser"

# Message storage configuration
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'printers_site.urls'

TAGGIT_CASE_INSENSITIVE = True

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'gallery.context_processors.company_config',
            ],
        },
    },
]

WSGI_APPLICATION = 'printers_site.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv("DB_NAME"),
        'USER': os.getenv("DB_USER"),
        'PASSWORD': os.getenv("DB_PASSWORD"),
        'HOST': os.getenv("DB_HOST", "127.0.0.1"),
        'PORT': os.getenv("DB_PORT", "3306"),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# Override database for tests
if 'test' in sys.argv:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASS")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True") == "True"
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-KE'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static'
]
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

UNFOLD = {
    "SITE_TITLE": "PeaShan Enterprises",
    "SITE_HEADER": "PeaShan Enterprises",
    "SITE_SUBHEADER": "Your go to partner for all your printing needs.",
    "SITE_ICON": {
        "light": lambda request: static("icon.ico"),
        "dark": lambda request: static("icon.ico"),
    },
    "SITE_LOGO": {
        "light": lambda request: static("icon.ico"),
        "dark": lambda request: static("icon.ico"),
    },

}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    },
    "django-backblaze-b2": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "django_backblaze_b2_cache_table",
    },
}


BACKBLAZE_CONFIG = {
    "application_key_id": os.getenv("BACKBLAZE_KEY_ID"),
    "application_key": os.getenv("BACKBLAZE_KEY"),
    "bucket": os.getenv("BACKBLAZE_BUCKET"),
    "authorize_on_init": False,
    "validate_on_init": False,
    "account_info": {"type": "memory"},
}

DEFAULT_FILE_STORAGE = "gallery.storage_backends.SupabaseStorage"

SUPABASE_URL = "https://mpsqpcmybupipvjwrqnr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1wc3FwY215YnVwaXB2andycW5yIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1OTkyNzc2NiwiZXhwIjoyMDc1NTAzNzY2fQ.Xeu6IfApqLu8Xo13TxSR9VSzxO0bVVYbffrAOAPUVfs"
SUPABASE_BUCKET_NAME = "printers"

# Optional
SUPABASE_PUBLIC_BUCKET = False  # If True, uses direct URLs
SUPABASE_SIGNED_URL_EXPIRES_IN = 3600  # 1 hour expiry for signed URLs

SUPABASE_S3_ACCESS_KEY_ID = os.getenv("SUPABASE_S3_ACCESS_KEY_ID")
SUPABASE_S3_SECRET_ACCESS_KEY = os.getenv("SUPABASE_S3_SECRET_ACCESS_KEY")
SUPABASE_S3_REGION = os.getenv("SUPABASE_S3_REGION","eu-north-1")

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
