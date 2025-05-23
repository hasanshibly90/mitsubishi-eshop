"""
Django settings for eshop_project project.
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-*lj^j+jtg%l(2o_4x+6&4=h%zp%5*s5w626(2l*^mt8v&$7kjm'
DEBUG = True
ALLOWED_HOSTS = []

###############################################
# INSTALLED_APPS
###############################################
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',           # If you use Django REST Framework
    'eshop',                    # Your custom app
    'widget_tweaks',
    'mptt',
]

###############################################
# JAZZMIN SETTINGS (sample)
###############################################
JAZZMIN_SETTINGS = {
    "site_title": "My eShop Admin",
    "site_header": "My eShop Admin",
    "site_brand": "My eShop",
    "login_logo": None,  # or "images/logo.png" if you have a static logo
    "show_sidebar": True,
    "navigation_expanded": True,
    # Add more Jazzmin config if you like:
    # https://django-jazzmin.readthedocs.io/en/latest/configuration/
}

###############################################
# MIDDLEWARE
###############################################
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'eshop_project.urls'

###############################################
# TEMPLATES
###############################################
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        # Merged lines for template dirs—Django will look in both places below,
        # plus the built-in app directories (because APP_DIRS=True).
        'DIRS': [
            BASE_DIR / 'eshop' / 'templates',
            BASE_DIR / 'templates',
        ],

        'APP_DIRS': True,  # crucial for automatically loading "eshop/templates/eshop/"
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

WSGI_APPLICATION = 'eshop_project.wsgi.application'

###############################################
# DATABASE
###############################################
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

###############################################
# AUTH PASSWORD VALIDATORS
###############################################
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

###############################################
# INTERNATIONALIZATION
###############################################
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

###############################################
# STATIC & MEDIA
###############################################
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'eshop' / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

###############################################
# EMAIL CONFIG
###############################################
# Production (Google Workspace)
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_PORT = 587
# EMAIL_HOST_USER = 'info@sisl-bd.com'
# EMAIL_HOST_PASSWORD = 'YOUR_GOOGLE_WORKSPACE_APP_PASSWORD'
# EMAIL_USE_TLS = True
# DEFAULT_FROM_EMAIL = 'info@sisl-bd.com'

# Development (Console Backend)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
