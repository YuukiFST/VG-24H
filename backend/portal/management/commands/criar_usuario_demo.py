"""
Management command: criar_usuario_demo

Cria o usuario demo@portal.vg / demo123 (perfil CID) se nao existir.
Usado para testes e apresentacoes (login como cidadao).

Execucao: python manage.py criar_usuario_demo
"""

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone


class Command(BaseCommand):
    help = "Cria demo@portal.vg / demo123 (CID) se nao existir."

    def handle(self, *args, **options):
        email = "demo@portal.vg"

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM cidadao WHERE LOWER(email) = %s",
                [email],
            )
            if cursor.fetchone():
                self.stdout.write(self.style.WARNING("Demo ja existe."))
                return

            cursor.execute(
                "INSERT INTO cidadao "
                "(nome_completo, cpf, dt_nascimento, telefone, email, "
                "senha_hash, perfil, ativo, dt_cadastro) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                [
                    "Cidadao Demonstracao",
                    "00000000191",
                    "1995-06-15",
                    "65999990000",
                    email,
                    make_password("demo123"),
                    "CID",
                    True,
                    timezone.now(),
                ],
            )

        self.stdout.write(self.style.SUCCESS("demo@portal.vg / demo123"))
