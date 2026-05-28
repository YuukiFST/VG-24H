"""
apps.py — Configuracao do app portal (Django).

Define o nome do aplicativo para uso no Django.
O campo 'name' deve coincidir com o nome da pasta do app.
"""

from django.apps import AppConfig


class PortalConfig(AppConfig):
    """Configuracao do app Portal VG 24H."""
    name = 'portal'
