"""
settings.py — todas as configuracoes do Django do meu Portal VG 24H.

[!] Os pontos que eu preciso lembrar na hora de apresentar:
    1. Banco eh PostgreSQL no Neon (nuvem) — ENGINE = django.db.backends.postgresql
    2. Registrei o PortalUserMiddleware — eh ele que faz o set_config() pras triggers do banco
    3. TIME_ZONE = America/Cuiaba (que eh o fuso de Varzea Grande/MT)
    4. Registrei o context_processors.navegacao — joga nav_user, nav_perfil e notif_count em todo template
"""

# os pra ler variavel de ambiente, Path pra montar caminho da pasta
import os
from pathlib import Path

# load_dotenv le o arquivo .env e joga as variaveis pro ambiente
from dotenv import load_dotenv

# BASE_DIR aponta pra raiz do projeto (subo duas pastas a partir desse arquivo)
BASE_DIR = Path(__file__).resolve().parent.parent
# carrego o .env que fica na raiz, ai consigo ler senha do banco etc
load_dotenv(BASE_DIR / ".env")

# 1. seguranca: a SECRET_KEY tem que vir do .env, nao deixei nenhum valor padrao inseguro
SECRET_KEY = os.environ.get("SECRET_KEY")
# se nao tiver chave eu derrubo o sistema de proposito, pra nao rodar inseguro
if not SECRET_KEY:
    raise ValueError("SECRET_KEY nao configurada. Sistema interrompido por seguranca.")

# 2. DEBUG vem do .env e por padrao fica False; so deixo True quando to no meu pc, em producao TEM que ser False
DEBUG = os.environ.get("DEBUG", "False") == "True"

# hosts que podem acessar o site; leio do .env separado por virgula e tiro os espacos
ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if h.strip()
]

# apps que o Django carrega; so o basico de sessao/mensagem/static mais o meu portal
INSTALLED_APPS = [
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "portal",                           # meu app, o coracao do sistema
]

# middlewares rodam em ordem em toda requisicao; a ordem aqui importa
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",   # serve os arquivos estaticos quando ta em producao
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    # [!] o meu: poe request.portal_user e chama set_config() no Postgres
    "portal.middleware.PortalUserMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# arquivo onde o Django comeca a procurar as rotas
ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],   # minha pasta de templates fica na raiz
        "APP_DIRS": True,                   # deixo o Django achar template dentro do app tambem
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
                # [!] o meu: manda nav_user, nav_perfil e notif_count pra todo template
                "portal.context_processors.navegacao",
            ],
        },
    },
]

# ponto de entrada WSGI que o servidor usa pra subir o app
WSGI_APPLICATION = "config.wsgi.application"

# ============================================================================
# BANCO DE DADOS — PostgreSQL (Neon na nuvem ou local no meu pc)
# ============================================================================
# [!] eu nao deixo nada fixo aqui, leio tudo do .env:
#     POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT
#     e POSTGRES_SSL=require quando eh o Neon (a nuvem exige TLS)
# ============================================================================
# monto o dict de conexao puxando cada pedaco do ambiente (com fallback pro local)
_default_db = {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": os.environ.get("POSTGRES_DB", "portal_vg"),
    "USER": os.environ.get("POSTGRES_USER", "postgres"),
    "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
    "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
    "PORT": os.environ.get("POSTGRES_PORT", "5432"),
}
# se eu marcar POSTGRES_SSL no .env, ligo o sslmode=require (Neon nao conecta sem isso)
if os.environ.get("POSTGRES_SSL", "").lower() in ("1", "true", "yes", "require"):
    _default_db["OPTIONS"] = {"sslmode": "require"}

# o Django espera o dict "default", ai jogo a minha config dentro
DATABASES = {"default": _default_db}

# ============================================================================
# LOCALIZACAO — Varzea Grande/MT
# ============================================================================
LANGUAGE_CODE = "pt-br"                           # site todo em portugues do Brasil
TIME_ZONE = "America/Cuiaba"                      # fuso de Mato Grosso, onde fica VG
USE_I18N = True                                   # liga traducao/internacionalizacao
USE_TZ = True                                     # guardo data/hora com timezone (importante pros prazos)

# ============================================================================
# ARQUIVOS ESTATICOS (CSS, JS, imagens)
# ============================================================================
STATIC_URL = "static/"                            # prefixo da URL dos estaticos
# so adiciono a pasta static se ela existir, senao o Django reclama
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []
STATIC_ROOT = BASE_DIR / "staticfiles"            # pasta pra onde o collectstatic junta tudo
# em producao uso o whitenoise comprimido com manifest (cache-busting nos nomes)
if not DEBUG:
    STORAGES = {
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }

# tipo de id automatico padrao dos models (BigAutoField = id grande)
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ============================================================================
# EMAIL
# ============================================================================
# de quem sai o email; se nao definir no .env uso um remetente fake
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@portal.vg.local")
# por padrao o email so aparece no console (bom pra testar sem mandar de verdade)
EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)

# ============================================================================
# LIMITES DE UPLOAD (8 MB)
# ============================================================================
# limito o tamanho de arquivo/formulario em 8MB pra ninguem entupir o servidor
FILE_UPLOAD_MAX_MEMORY_SIZE = 8 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 8 * 1024 * 1024

# ============================================================================
# SEGURANCA — so liga em producao (quando DEBUG = False)
# ============================================================================
# essas travas de seguranca so fazem sentido com HTTPS, por isso so ligo fora do dev
if not DEBUG:
    SESSION_COOKIE_SECURE = True                  # cookie de sessao so viaja por HTTPS
    CSRF_COOKIE_SECURE = True                     # idem pro cookie de CSRF
    SESSION_COOKIE_SAMESITE = "Lax"               # ajuda a evitar cookie indo pra outro site
    CSRF_COOKIE_SAMESITE = "Lax"
    SECURE_SSL_REDIRECT = True                    # forco http virar https
    SECURE_HSTS_SECONDS = 31536000                # navegador lembra de usar https por 1 ano
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True            # navegador nao tenta adivinhar o tipo do arquivo
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")  # como sei que ta atras de proxy https

# ============================================================================
# SESSAO — expira em 1h ou quando fecha o navegador
# ============================================================================
SESSION_COOKIE_AGE = 3600                              # 1 hora em segundos
SESSION_EXPIRE_AT_BROWSER_CLOSE = True                # fechou o navegador, caiu a sessao
SESSION_SAVE_EVERY_REQUEST = True                     # cada requisicao renova o contador da 1h
