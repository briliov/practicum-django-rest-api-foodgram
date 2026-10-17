"""Settings for backend foodgram project."""

from pathlib import Path

from decouple import Csv, config

from utils.constants import PAGE_SIZE

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config(
    "SECRET_KEY",
    default="django-insecure-test-key-placeholder-12345",
)

DEBUG = config("DEBUG_STATUS", default=False, cast=bool)

ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="localhost,127.0.0.1",
    cast=Csv(),
)


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_filters",
    "rest_framework",
    "rest_framework.authtoken",
    "djoser",
    "drf_spectacular",
    "api.apps.ApiConfig",
    "entities.users.apps.UsersConfig",
    "entities.recipes.apps.RecipesConfig",
]

AUTH_USER_MODEL = "users.User"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "core.wsgi.application"

DB_HOST = config("DB_HOST", default=None)

if DB_HOST:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": config("POSTGRES_DB", default="django"),
            "USER": config("POSTGRES_USER", default="django"),
            "PASSWORD": config("POSTGRES_PASSWORD", default=""),
            "HOST": DB_HOST,
            "PORT": config("DB_PORT", default="5432"),
        },
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        },
    }


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation.MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation.CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation.NumericPasswordValidator"
        ),
    },
]

LANGUAGE_CODE = "ru-RU"

TIME_ZONE = "Europe/Moscow"

USE_I18N = True

USE_TZ = True

STATIC_SOURCE = "backend/static/"
STATIC_URL = STATIC_SOURCE
STATIC_ROOT = BASE_DIR / STATIC_SOURCE

MEDIA_SOURCE = "backend/media/"
MEDIA_URL = MEDIA_SOURCE
MEDIA_ROOT = BASE_DIR / MEDIA_SOURCE

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PAGINATION_CLASS": "api.pagination.LimitPageNumberPagination",
    "PAGE_SIZE_QUERY_PARAM": "limit",
    "PAGE_SIZE": PAGE_SIZE,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
    ],
}

DJOSER = {
    "LOGIN_FIELD": "email",
    "SERIALIZERS": {
        "user": "api.serializers.UserSubscribeSerializer",
        "current_user": "api.serializers.UserSubscribeSerializer",
    },
    "PERMISSIONS": {
        "user_list": ["rest_framework.permissions.AllowAny"],
        "user": ("rest_framework.permissions.IsAuthenticatedOrReadOnly",),
    },
}


AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

SPECTACULAR_SETTINGS = {
    "TITLE": "Foodgram API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

GLOBAL_FIXTURES_DIR = BASE_DIR / "fixtures"

FIXTURE_DIRS = [
    GLOBAL_FIXTURES_DIR,
]

CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    default="http://localhost,http://127.0.0.1",
    cast=Csv(),
)

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
