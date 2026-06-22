"""
asgi.py — versao ASGI do entry point (pra servidor async, tipo uvicorn).

Igual o wsgi, mas pro mundo assincrono. Tambem expoe a ``application``.
Nao to usando async de verdade ainda, mas o Django ja deixa esse arquivo pronto.

Doc oficial:
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

# aponto o settings do projeto (so seta se ainda nao tiver setado)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# crio o app ASGI que o servidor async vai usar
application = get_asgi_application()
