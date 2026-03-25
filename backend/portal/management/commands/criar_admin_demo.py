from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.utils import timezone

from portal.models import Usuario


class Command(BaseCommand):
    help = "Cria admin@portal.vg / admin123 (ADM) se não existir."

    def handle(self, *args, **options):
        email = "admin@portal.vg"
        if Usuario.objects.filter(email__iexact=email).exists():
            self.stdout.write(self.style.WARNING("Admin demo já existe."))
            return
        Usuario.objects.create(
            nome_completo="Administrador Demo",
            cpf="000.000.002-72",
            dt_nascimento="1990-01-01",
            telefone="65988887777",
            email=email,
            senha_hash=make_password("admin123"),
            perfil="ADM",
            ativo=True,
            dt_cadastro=timezone.now(),
        )
        self.stdout.write(self.style.SUCCESS("admin@portal.vg / admin123"))
