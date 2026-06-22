"""
apps.py — aqui eu registro o meu app portal pro Django reconhecer.

Basicamente o Django precisa saber o nome do app, e esse 'name'
tem que bater igualzinho com o nome da pasta, senao da erro.
"""

from django.apps import AppConfig


class PortalConfig(AppConfig):
    """Config do meu app Portal VG 24H."""
    # esse nome tem que ser igual ao da pasta do app ("portal")
    name = 'portal'
