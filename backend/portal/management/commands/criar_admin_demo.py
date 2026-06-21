"""
Management command: criar_admin_demo

Cria o usuario gestor@portal.vg / admin123 (perfil GES) se nao existir.
Usado para testes e apresentacoes (login como gestor).

Execucao: python manage.py criar_admin_demo
"""

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone


class Command(BaseCommand):
    help = "Cria gestor@portal.vg / admin123 (GES) se nao existir."

    def handle(self, *args, **options):
        email = "gestor@portal.vg"

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM servidor WHERE LOWER(email) = %s",
                [email],
            )
            if cursor.fetchone():
                self.stdout.write(self.style.WARNING("Gestor demo ja existe."))
                return

            cursor.execute(
                "SELECT id_secretaria FROM secretaria LIMIT 1"
            )
            sec_row = cursor.fetchone()
            if not sec_row:
                self.stdout.write(self.style.ERROR(
                    "Nenhuma secretaria cadastrada. Execute o seed primeiro."
                ))
                return

            cursor.execute(
                "INSERT INTO servidor "
                "(nome_completo, cpf, dt_nascimento, telefone, email, "
                "senha_hash, perfil, ativo, dt_cadastro, id_secretaria) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                [
                    "Gestor Demo",
                    "00000000272",
                    "1990-01-01",
                    "65988887777",
                    email,
                    make_password("admin123"),
                    "GES",
                    True,
                    timezone.now(),
                    sec_row[0],
                ],
            )

        self.stdout.write(self.style.SUCCESS("gestor@portal.vg / admin123"))
