from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.utils import timezone

from portal.models import Secretaria, Servidor


class Command(BaseCommand):
    help = "Cria gestor@portal.vg / admin123 (GES) se não existir."

    def handle(self, *args, **options):
        email = "gestor@portal.vg"
        if Servidor.objects.filter(email__iexact=email).exists():
            self.stdout.write(self.style.WARNING("Gestor demo já existe."))
            return
        sec = Secretaria.objects.first()
        if not sec:
            self.stdout.write(
                self.style.ERROR("Nenhuma secretaria cadastrada. Execute o seed primeiro.")
            )
            return
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
