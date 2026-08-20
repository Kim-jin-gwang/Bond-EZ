"""
Django settings for config project.

로컬 개발: backend-pjt/.env 를 자동 로드 (docker-compose는 env_file로 주입)
프로덕션(Render): 환경변수로 주입 — DEBUG=False가 기본값이므로 로컬에서는 DEBUG=True 필요
"""

from pathlib import Path
from urllib.parse import urlparse, parse_qs

import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# .env 자동 로드 (python-dotenv가 없으면 조용히 건너뜀 — 프로덕션은 env로 주입)
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / '.env')
except ImportError:
    pass

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-dev-only-do-not-use-in-production')

# 프로덕션 안전 기본값: 명시적으로 DEBUG=True를 줘야 개발 모드
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = [
    h.strip() for h in os.environ.get('ALLOWED_HOSTS', '*').split(',') if h.strip()
]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'apps.accounts',
    'apps.bonds',
    'apps.chat',
    'apps.glossary',
    'apps.indicators',
    'apps.news',
    'apps.portfolios',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
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
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# DATABASE_URL(예: Neon의 postgresql://...) 한 줄이 있으면 그것을 우선 사용,
# 없으면 개별 POSTGRES_* / DB_* 환경변수를 사용한다.

_database_url = os.environ.get('DATABASE_URL', '')
if _database_url:
    _parsed = urlparse(_database_url)
    _qs = parse_qs(_parsed.query)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': _parsed.path.lstrip('/'),
            'USER': _parsed.username or '',
            'PASSWORD': _parsed.password or '',
            'HOST': _parsed.hostname or '',
            'PORT': str(_parsed.port or 5432),
            'OPTIONS': {'sslmode': _qs.get('sslmode', ['require'])[0]},
            'DISABLE_SERVER_SIDE_CURSORS': True,
            'CONN_HEALTH_CHECKS': True,
            'CONN_MAX_AGE': int(os.environ.get('DB_CONN_MAX_AGE', '60')),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('POSTGRES_DB', 'postgres'),
            'USER': os.environ.get('POSTGRES_USER', 'postgres'),
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'postgres'),
            'HOST': os.environ.get('DB_HOST', 'db'),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
    }

    DB_SSLMODE = os.environ.get('DB_SSLMODE', '')
    if DB_SSLMODE:
        DATABASES['default']['OPTIONS'] = {'sslmode': DB_SSLMODE}
        DATABASES['default']['DISABLE_SERVER_SIDE_CURSORS'] = True
        DATABASES['default']['CONN_HEALTH_CHECKS'] = True
        DATABASES['default']['CONN_MAX_AGE'] = int(os.environ.get('DB_CONN_MAX_AGE', '60'))

    DB_CHANNEL_BINDING = os.environ.get('DB_CHANNEL_BINDING', '')
    if DB_CHANNEL_BINDING:
        DATABASES['default'].setdefault('OPTIONS', {})['channel_binding'] = DB_CHANNEL_BINDING


# CORS / CSRF — 프론트(Cloudflare Pages)와 백엔드(Render)가 서로 다른 도메인이므로
# 교차 출처 쿠키 인증 설정이 필수
CORS_ALLOWED_ORIGINS = [
    o.strip() for o in os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',') if o.strip()
]
CORS_ALLOW_CREDENTIALS = True
if DEBUG and not CORS_ALLOWED_ORIGINS:
    CORS_ALLOW_ALL_ORIGINS = True

CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',') if o.strip()
]

if not DEBUG:
    # 교차 사이트에서 세션 쿠키가 전송되려면 SameSite=None + Secure 필요
    SESSION_COOKIE_SAMESITE = 'None'
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SAMESITE = 'None'
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization
LANGUAGE_CODE = 'ko-kr'
TIME_ZONE = 'Asia/Seoul'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage'},
}

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Elasticsearch — 데모 배포에서는 미사용(빈 값). 모든 호출부가 ORM 폴백을 갖고 있다.
ELASTICSEARCH_HOSTS = [
    host.strip()
    for host in os.environ.get('ELASTICSEARCH_HOSTS', '').split(',')
    if host.strip()
]
ELASTICSEARCH_BONDS_INDEX = os.environ.get('ELASTICSEARCH_BONDS_INDEX', 'bonds_search')
ELASTICSEARCH_GLOSSARY_INDEX = os.environ.get('ELASTICSEARCH_GLOSSARY_INDEX', 'glossary_search')
ELASTICSEARCH_REQUEST_TIMEOUT = float(os.environ.get('ELASTICSEARCH_REQUEST_TIMEOUT', '2'))

NEWS_SUMMARY_LM_MODEL = os.environ.get('NEWS_SUMMARY_LM_MODEL', 'gemini-3.6-flash')
NEWS_SUMMARY_LM_API_KEY = os.environ.get('NEWS_SUMMARY_LM_API_KEY', '')
NEWS_SUMMARY_LM_TEMPERATURE = float(os.environ.get('NEWS_SUMMARY_LM_TEMPERATURE', '0.2'))
NEWS_SUMMARY_LM_MAX_TOKENS = int(os.environ.get('NEWS_SUMMARY_LM_MAX_TOKENS', '2048'))
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
