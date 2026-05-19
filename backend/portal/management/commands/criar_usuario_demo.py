"""
Management command: criar_usuario_demo
Cria o usuario demo@portal.vg / demo123 (perfil CID) se nao existir.
Usado para testes e apresentacao (login como Cidadao).
"""
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.utils import timezone

from portal.models import Cidadao


class Command(BaseCommand):
    help = "Cria demo@portal.vg / demo123 (CID) se nao existir."

    def handle(self, *args, **options):
        email = "demo@portal.vg"
        if Cidadao.objects.filter(email__iexact=email).exists():
            self.stdout.write(self.style.WARNING("Demo ja existe."))
            return
        Cidadao.objects.create(
            nome_completo="cidadao Demonstracao",
            cpf="00000000191",
            dt_nascimento="1995-06-15",
            telefone="65999990000",
            email=email,
            senha_hash=make_password("demo123"),
            perfil="CID",
            ativo=True,
            dt_cadastro=timezone.now(),
        )
        self.stdout.write(self.style.SUCCESS("demo@portal.vg / demo123"))
