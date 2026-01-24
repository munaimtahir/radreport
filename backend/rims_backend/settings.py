from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret-key")
DEBUG = os.getenv("DJANGO_DEBUG", "0") == "1"
# Configure via DJANGO_ALLOWED_HOSTS in production (comma-separated). No wildcards by default.
ALLOWED_HOSTS = [h.strip() for h in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "corsheaders",
    "rest_framework",
    "rest_framework.authtoken",
    "django_filters",
    "drf_spectacular",

    "apps.audit",
    "apps.patients",
    "apps.catalog",
    "apps.studies",
    "apps.workflow",
    "apps.consultants",
    "apps.reporting",


]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # Serve static files in production
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "rims_backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "rims_backend.wsgi.application"

# Database configuration - supports both SQLite (dev) and PostgreSQL (production)
if os.getenv("DATABASE_URL") or os.getenv("DB_ENGINE") == "postgresql":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME", "rims"),
            "USER": os.getenv("DB_USER", "rims"),
            "PASSWORD": os.getenv("DB_PASSWORD", "rims"),
            "HOST": os.getenv("DB_HOST", "127.0.0.1"),
            "PORT": os.getenv("DB_PORT", "5434"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Karachi"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# WhiteNoise configuration for production static file serving
# This replaces the need for a separate web server to serve static files
# CompressedManifestStaticFilesStorage adds compression and cache-busting hashes
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOWED_ORIGINS = [o.strip() for o in os.getenv("CORS_ALLOWED_ORIGINS", "https://rims.alshifalab.pk,http://localhost:5173").split(",") if o.strip()]
CORS_ALLOW_CREDENTIALS = True

# CSRF Trusted Origins
CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.getenv("CSRF_TRUSTED_ORIGINS", "https://rims.alshifalab.pk,https://api.rims.alshifalab.pk,http://localhost:5173").split(",") if o.strip()]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "RIMS API",
    "DESCRIPTION": "Radiology Information Management System (merge-friendly scaffold)",
    "VERSION": "0.1.0",
}

OPD_ENABLED = os.getenv("OPD_ENABLED", "false").lower() in ("1", "true", "yes")

# Security settings (configure via env for production; keep dev friendly defaults)
SECURE_PROXY_SSL_HEADER = None
secure_proxy_header = os.getenv("SECURE_PROXY_SSL_HEADER", "")
if secure_proxy_header:
    header_parts = [part.strip() for part in secure_proxy_header.split(",") if part.strip()]
    if len(header_parts) == 2:
        SECURE_PROXY_SSL_HEADER = (header_parts[0], header_parts[1])

SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "0").lower() in ("1", "true", "yes")
CSRF_COOKIE_SECURE = os.getenv("CSRF_COOKIE_SECURE", "0").lower() in ("1", "true", "yes")

SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "0") or "0")
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv("SECURE_HSTS_INCLUDE_SUBDOMAINS", "0").lower() in ("1", "true", "yes")
SECURE_HSTS_PRELOAD = os.getenv("SECURE_HSTS_PRELOAD", "0").lower() in ("1", "true", "yes")

from datetime import timedelta
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
}

LOG_LEVEL = os.getenv("DJANGO_LOG_LEVEL", "INFO")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
}
