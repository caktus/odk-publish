"""
Django settings for config project.

Generated by 'django-admin startproject' using Django 4.2.2.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

import logging
import os

from pathlib import Path

import dj_database_url
import structlog
from import_export.formats import base_formats
from ..import_export_formats import XLSX

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-t1586xqgp3f7k%0@k-gfxpewx)9!cl$*z!a!sckvu0gcoy3afj"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DJANGO_DEBUG", "False") == "True"
ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")

ALLOWED_HOSTS = []

# Application definition

AUTH_USER_MODEL = "users.User"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/accounts/login/"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "django.contrib.sites",  # new
    # 3rd party
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "django_celery_beat",
    "django_filters",
    "django_htmx",
    "django_structlog",
    "django_tables2",
    "import_export",
    "template_partials",
    # Local
    "apps.odk_publish",
    "apps.mdm",
    "apps.patterns",
    "apps.tailscale",
    "apps.users",
]

if not os.getenv("USE_GUNICORN"):
    INSTALLED_APPS.insert(0, "daphne")

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "django_structlog.middlewares.RequestMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "apps.odk_publish.middleware.ODKProjectMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            "templates",
            BASE_DIR / "config" / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

ASGI_APPLICATION = "config.asgi.application"
WSGI_APPLICATION = "config.wsgi.application"

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# https://docs.djangoproject.com/en/4.1/ref/settings/#conn-max-age
CONN_MAX_AGE = os.getenv("DATABASE_CONN_MAX_AGE")
if CONN_MAX_AGE is not None:
    CONN_MAX_AGE = int(CONN_MAX_AGE)
# https://docs.djangoproject.com/en/4.1/ref/settings/#conn-health-checks
CONN_HEALTH_CHECKS = os.getenv("DATABASE_CONN_HEALTH_CHECKS", "True") == "True"
DATABASES = {
    "default": dj_database_url.config(
        default="postgresql://postgres@localhost:9061/odk_publish",
        conn_max_age=CONN_MAX_AGE,
        ssl_require=os.getenv("DATABASE_SSL_REQUIRE", "False") == "True",
    ),
}

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]
# django-allauth
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
SITE_ID = 1
ACCOUNT_EMAIL_VERIFICATION = "none"
LOGIN_REDIRECT_URL = "home"
ACCOUNT_LOGOUT_ON_GET = True
# https://docs.allauth.org/en/latest/socialaccount/configuration.html
SOCIALACCOUNT_STORE_TOKENS = True
SOCIALACCOUNT_ONLY = True
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APP": {
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        },
        "SCOPE": [
            "profile",
            "email",
            "https://www.googleapis.com/auth/drive.readonly",
            "https://www.googleapis.com/auth/drive.metadata.readonly",
        ],
        "AUTH_PARAMS": {
            "access_type": "offline",
        },
    }
}

# Google Auth
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "America/New_York"

USE_I18N = True

USE_TZ = True

# https://docs.djangoproject.com/en/4.1/topics/i18n/formatting/#creating-custom-format-files
FORMAT_MODULE_PATH = ["config.formats"]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"
STATICFILES_DIRS = [
    BASE_DIR / "config" / "static",
]
STATIC_ROOT = BASE_DIR / "public" / "static"

# Uploaded media files
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "/media/"

STORAGES = {
    "default": {
        "BACKEND": os.getenv("DEFAULT_FILE_STORAGE", "django.core.files.storage.FileSystemStorage")
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Optionally configure settings for S3/MinIO
AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")
AWS_S3_CUSTOM_DOMAIN = os.getenv("AWS_S3_CUSTOM_DOMAIN", "")
AWS_LOCATION = os.getenv("AWS_LOCATION", f"{ENVIRONMENT}/")
AWS_S3_ENDPOINT_URL = os.getenv("AWS_S3_ENDPOINT_URL")
AWS_S3_USE_SSL = int(os.getenv("AWS_S3_USE_SSL", "1")) == 1
# AWS_S3_VERIFY is a funny setting whose allowed values are
# None, False, or a string (path to a AA bundle). Support all
# those values here.
AWS_S3_VERIFY = os.getenv("AWS_S3_VERIFY")
if AWS_S3_VERIFY and AWS_S3_VERIFY.lower() in ("false", "0"):
    AWS_S3_VERIFY = False
AWS_DEFAULT_ACL = os.getenv("AWS_DEFAULT_ACL")
AWS_S3_ADDRESSING_STYLE = os.getenv("AWS_S3_ADDRESSING_STYLE", None)
AWS_S3_SIGNATURE_VERSION = os.getenv("AWS_S3_SIGNATURE_VERSION", "s3v4")
AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME", "us-east-1")
# See https://github.com/wagtail/wagtail/pull/4495#issuecomment-387434521
AWS_S3_FILE_OVERWRITE = False
AWS_QUERYSTRING_AUTH = os.getenv("AWS_QUERYSTRING_AUTH", "True") == "True"
# If not set, boto3 internally looks up IAM credentials
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGGING_CAPTURE_WARNINGS = os.getenv("LOGGING_CAPTURE_WARNINGS", "True") == "True"
if LOGGING_CAPTURE_WARNINGS:
    logging.captureWarnings(True)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json_formatter": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.processors.JSONRenderer(),
        },
        "plain_console": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.dev.ConsoleRenderer(),
        },
        "key_value": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.processors.KeyValueRenderer(
                key_order=["timestamp", "level", "event", "logger"]
            ),
        },
    },
    "handlers": {
        # Important notes regarding handlers.
        #
        # 1. Make sure you use handlers adapted for your project.
        # These handlers configurations are only examples for this library.
        # See python's logging.handlers: https://docs.python.org/3/library/logging.handlers.html
        #
        # 2. You might also want to use different logging configurations depending of the environment.
        # Different files (local.py, tests.py, production.py, ci.py, etc.) or only conditions.
        # See https://docs.djangoproject.com/en/dev/topics/settings/#designating-the-settings
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "plain_console",
        },
    },
    "loggers": {
        "django_structlog": {
            "handlers": ["console"],
            "level": "INFO",
        },
        # Make sure to replace the following logger's name for yours
        "apps": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
    },
}

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

# EMAIL
# ------------------------------------------------------------------------------
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_SUBJECT_PREFIX = "[odk-publish %s] " % ENVIRONMENT.title()
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "no-reply@caktusgroup.com")
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST = os.getenv("EMAIL_HOST", "localhost")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", False)
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", False)
# use TLS or SSL, not both:
assert not (EMAIL_USE_TLS and EMAIL_USE_SSL)
if EMAIL_USE_TLS:
    default_smtp_port = 587
elif EMAIL_USE_SSL:
    default_smtp_port = 465
else:
    default_smtp_port = 25
EMAIL_PORT = os.getenv("EMAIL_PORT", default_smtp_port)
# django_ses.SESBackend
USE_SES_V2 = os.getenv("USE_SES_V2", "True") == "True"
AWS_SES_REGION_NAME = os.getenv("AWS_SES_REGION_NAME", "us-east-2")
AWS_SES_REGION_ENDPOINT = os.getenv("AWS_SES_REGION_ENDPOINT", "email.us-east-2.amazonaws.com")
# django-email-bandit
BANDIT_ALLOW_EMAILS = os.getenv("BANDIT_ALLOW_EMAILS", "").split(":")
if any(BANDIT_ALLOW_EMAILS):
    INSTALLED_APPS += ("bandit",)  # noqa: F405
    EMAIL_BACKEND = "config.email_backends.HijackSESBackend"
    BANDIT_EMAIL = ["admin@caktusgroup.com"]
    BANDIT_WHITELIST = BANDIT_ALLOW_EMAILS
    LOGGING["loggers"]["bandit"] = {  # noqa
        "handlers": ["console"],
        "level": "DEBUG",
        "propagate": False,
    }

# Celery
# https://docs.celeryq.dev/en/v5.3.1/userguide/configuration.html#new-lowercase-settings
# broker_url
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
# broker_connection_retry_on_startup
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = (
    os.getenv("CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP", "False") == "True"
)
if CELERY_BROKER_URL.startswith("rediss"):
    import ssl

    # broker_use_ssl
    CELERY_BROKER_USE_SSL = {
        "ssl_cert_reqs": ssl.CERT_REQUIRED,
    }
    # redis_backend_use_ssl
    CELERY_REDIS_BACKEND_USE_SSL = {
        "ssl_cert_reqs": ssl.CERT_REQUIRED,
    }
CELERY_BEAT_SCHEDULER = os.getenv(
    "CELERY_BEAT_SCHEDULER", "django_celery_beat.schedulers:DatabaseScheduler"
)

# Google Auth
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# pyODK
ODK_CENTRAL_USERNAME = os.getenv("ODK_CENTRAL_USERNAME")
ODK_CENTRAL_PASSWORD = os.getenv("ODK_CENTRAL_PASSWORD")

# django-import-export
IMPORT_EXPORT_FORMATS = [base_formats.CSV, XLSX]
