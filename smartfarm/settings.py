"""
Django settings for smartfarm project.
"""

import dj_database_url
import os
from pathlib import Path
from decouple import config
from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-y(4t5zx!65%3hs+pnpq5e1zj-$*dn)mu@lfb@u7hnd*wd%#)r%'

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# ── INSTALLED APPS ──
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crops',
    'weather',
    'marketplace',
    'orders',
    'users',
    'widget_tweaks',
    'ai_recommendations',
    'admin_panel',
]

# ── MIDDLEWARE ──
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'smartfarm.urls'

# ── TEMPLATES ── (fixed duplicate DIRS)
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'smartfarm.wsgi.application'

# ── DATABASE ──
DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{os.path.join(BASE_DIR, 'db.sqlite3')}"
    )
}

# ── PASSWORD VALIDATION ──
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ── INTERNATIONALIZATION ──
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ── STATIC FILES ── (fixed duplicates)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# ── MEDIA FILES ──
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ── SESSION SETTINGS ──
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# ── DEFAULT PRIMARY KEY ──
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── EMAIL SETTINGS ──
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'paramjeetsangwan001@gmail.com'
EMAIL_HOST_PASSWORD = 'xemo fgit myjn rkeo'
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# ── PASSWORD RESET ──
PASSWORD_RESET_TIMEOUT = 86400  # 24 hours