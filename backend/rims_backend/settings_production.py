"""
Production Settings for RIMS

This file contains production-specific settings.
Import from this file in production deployments.

Usage:
    export DJANGO_SETTINGS_MODULE=rims_backend.settings_production
    python manage.py runserver
"""

import os
import warnings
from pathlib import Path

# Import settings from base settings module
from rims_backend.settings import (
    BASE_DIR,
    INSTALLED_APPS,
    MIDDLEWARE,
    ROOT_URLCONF,
    TEMPLATES,
    WSGI_APPLICATION,
    AUTH_PASSWORD_VALIDATORS,
    LANGUAGE_CODE,
    TIME_ZONE,
    USE_I18N,
    USE_TZ,
    DEFAULT_AUTO_FIELD,
    CORS_ALLOW_CREDENTIALS,
    REST_FRAMEWORK,
    SPECTACULAR_SETTINGS,
    SIMPLE_JWT,
)

# SECURITY WARNING: Don't run with debug turned on in production!
DEBUG = False

# SECURITY WARNING: Update this with your production domain
ALLOWED_HOSTS = [h.strip() for h in os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",") if h.strip()]
if not ALLOWED_HOSTS:
    raise ValueError(
        "DJANGO_ALLOWED_HOSTS must be set in production. "
        "Example: DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com"
    )

# Ensure SECRET_KEY is set and strong
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
if not SECRET_KEY or len(SECRET_KEY) < 50:
    raise ValueError(
        "DJANGO_SECRET_KEY must be set in environment and be at least 50 characters long. "
        "Generate one with: python -c \"from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())\""
    )

# Warn if SECRET_KEY appears to be weak (simple patterns)
if SECRET_KEY and (len(set(SECRET_KEY)) < 20 or SECRET_KEY == SECRET_KEY[0] * len(SECRET_KEY)):
    warnings.warn(
        "SECRET_KEY appears to use simple patterns. Ensure it's randomly generated.",
        UserWarning
    )

# Enable password validators for production (override base settings)
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 8,
        }
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Database - must use strong password in production
required_db_settings = ["DB_NAME", "DB_USER", "DB_PASSWORD", "DB_HOST"]
missing_db_settings = [key for key in required_db_settings if not os.getenv(key)]
if missing_db_settings:
    raise ValueError(
        f"Missing required database environment variables: {', '.join(missing_db_settings)}. "
        "All of DB_NAME, DB_USER, DB_PASSWORD, and DB_HOST must be set."
    )

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT", "5432"),
        "CONN_MAX_AGE": 600,  # Connection pooling
    }
}

# Static files (CSS, JavaScript, Images)
STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_URL = "/static/"

# Media files
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"

# Security Settings
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "1") == "1"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Ensure logs directory exists
logs_dir = BASE_DIR / "logs"
logs_dir.mkdir(exist_ok=True)

# Logging Configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": logs_dir / "rims.log",
            "formatter": "verbose",
        },
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# CORS - update with production domain
CORS_ALLOWED_ORIGINS = [o.strip() for o in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if o.strip()]
if not CORS_ALLOWED_ORIGINS:
    raise ValueError(
        "CORS_ALLOWED_ORIGINS must be set in production. "
        "Example: CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com"
    )

# Email Configuration (optional)
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
if EMAIL_BACKEND == "django.core.mail.backends.smtp.EmailBackend":
    EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
    EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "1") == "1"
    EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
    EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")

# Cache Configuration (optional - requires Redis)
if os.getenv("REDIS_URL"):
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": os.getenv("REDIS_URL"),
        }
    }
