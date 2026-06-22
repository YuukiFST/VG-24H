"""
Meu command: criar_admin_demo

Cria o usuario gestor@portal.vg / admin123 (perfil GES) se nao existir.
Igual o de cidadao, mas esse eh pra eu logar como gestor nas apresentacoes.

Pra rodar: python manage.py criar_admin_demo
"""

# make_password pra hashear a senha antes de salvar
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db import connection  # SQL puro, conexao na mao
from django.utils import timezone


class Command(BaseCommand):
    help = "Cria gestor@portal.vg / admin123 (GES) se nao existir."

    def handle(self, *args, **options):
        # email fixo do meu gestor de demonstracao
        email = "gestor@portal.vg"

        with connection.cursor() as cursor:
            # confiro se ja tem um servidor com esse email pra nao criar duplicado
            cursor.execute(
                "SELECT 1 FROM servidor WHERE LOWER(email) = %s",
                [email],
            )
            # achou? entao so aviso e saio
            if cursor.fetchone():
                self.stdout.write(self.style.WARNING("Gestor demo ja existe."))
                return

            # gestor precisa estar ligado a uma secretaria, entao pego a primeira que existir
            cursor.execute(
                "SELECT id_secretaria FROM secretaria LIMIT 1"
            )
            sec_row = cursor.fetchone()
            # se nao tem nenhuma secretaria, nao da pra criar o gestor; mando rodar o seed antes
            if not sec_row:
                self.stdout.write(self.style.ERROR(
                    "Nenhuma secretaria cadastrada. Execute o seed primeiro."
                ))
                return

            # tudo certo, insiro o gestor ja vinculado aquela secretaria
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
                    make_password("admin123"),   # hash da senha admin123
                    "GES",                        # perfil gestor
                    True,                         # ja entra ativo
                    timezone.now(),               # data de cadastro = agora
                    sec_row[0],                   # id da secretaria que peguei ali em cima
                ],
            )

        # mostro o login do gestor que criei
        self.stdout.write(self.style.SUCCESS("gestor@portal.vg / admin123"))
