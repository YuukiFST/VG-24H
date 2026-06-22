"""
wsgi.py — eh por aqui que o servidor (gunicorn etc) sobe o meu projeto.

Ele expoe a variavel ``application``, que eh o que o servidor WSGI chama.
Esse arquivo o Django ja gerou pra mim, quase nao mexo nele.

Doc oficial se eu precisar:
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# digo pro Django qual arquivo de settings usar (so define se ja nao tiver)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# monto o app WSGI que o servidor vai chamar a cada requisicao
application = get_wsgi_application()
