"""
Management command: criar_admin_demo

Cria o usuario gestor@portal.vg / admin123 (perfil GES) se nao existir.
Usado para testes e apresentacoes (login como gestor).

Execucao: python manage.py criar_admin_demo
"""

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.utils import timezone

from portal.models import Secretaria, Servidor


class Command(BaseCommand):
    help = "Cria gestor@portal.vg / admin123 (GES) se nao existir."

    def handle(self, *args, **options):
        email = "gestor@portal.vg"

        # Verifica se o gestor demo ja existe (evita duplicidade).
        if Servidor.objects.filter(email__iexact=email).exists():
            self.stdout.write(self.style.WARNING("Gestor demo ja existe."))
            return

        # Precisa de uma secretaria para associar o servidor.
        sec = Secretaria.objects.first()
        if not sec:
            self.stdout.write(self.style.ERROR(
                "Nenhuma secretaria cadastrada. Execute o seed primeiro."
            ))
            return

        # Cria o servidor gestor com senha hasheada.
        Servidor.objects.create(
            nome_completo="Gestor Demo",
            cpf="00000000272",
            dt_nascimento="1990-01-01",
            telefone="65988887777",
            email=email,
            senha_hash=make_password("admin123"),
            perfil="GES",
            ativo=True,
            dt_cadastro=timezone.now(),
            id_secretaria=sec,
        )
        self.stdout.write(self.style.SUCCESS("gestor@portal.vg / admin123"))
