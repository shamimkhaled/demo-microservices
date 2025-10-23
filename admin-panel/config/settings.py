import os
import sys
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

# Add service paths to Python path
SERVICE_DIR = BASE_DIR.parent / 'services'
ORGANIZATION_SERVICE_DIR = SERVICE_DIR / 'organization-service'
AUTH_SERVICE_DIR = SERVICE_DIR / 'auth-service'

sys.path.extend([
    str(AUTH_SERVICE_DIR),
    str(ORGANIZATION_SERVICE_DIR),
    str(ORGANIZATION_SERVICE_DIR / 'apps'),  # Add organization apps directory
    str(AUTH_SERVICE_DIR / 'apps'),  # Add auth apps directory
    str(BASE_DIR.parent / 'shared'),  # Add shared directory
])


# Debug: Print sys.path to verify paths are added
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug(f"sys.path after additions: {sys.path}")



SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me')

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party
    'rest_framework',
    'django_filters',

    # Service apps - Use direct app paths

    'users.apps.UsersConfig',
    'roles.apps.RolesConfig',
    'authentication.apps.AuthenticationConfig',
    'organizations.apps.OrganizationsConfig',  # Changed from apps.organizations

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Use same database as services
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR.parent / 'services' / 'auth-service' / 'db.sqlite3',
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    },
    'auth_db': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': SERVICE_DIR / 'auth-service' / 'db.sqlite3',
    },
    'organization_db': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': SERVICE_DIR / 'organization-service' / 'db.sqlite3',
    }
}

DATABASE_ROUTERS = ['config.db_routers.DatabaseRouter']

# Use same user model
AUTH_USER_MODEL = 'users.User'

# Password validation
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

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Dhaka'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'