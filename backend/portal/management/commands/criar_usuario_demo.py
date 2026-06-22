"""
Meu command: criar_usuario_demo

Cria o usuario demo@portal.vg / demo123 (perfil CID) se ele ainda nao existir.
Eu uso isso pra ter um login de cidadao pronto na hora de testar e apresentar.

Pra rodar: python manage.py criar_usuario_demo
"""

# make_password gera o hash da senha, pra eu nunca salvar a senha crua no banco
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db import connection  # SQL puro de novo, pego a conexao direto
from django.utils import timezone


class Command(BaseCommand):
    help = "Cria demo@portal.vg / demo123 (CID) se nao existir."

    def handle(self, *args, **options):
        # email fixo do meu usuario de demonstracao
        email = "demo@portal.vg"

        with connection.cursor() as cursor:
            # primeiro vejo se ja existe um cidadao com esse email (sem ligar pra maiuscula)
            cursor.execute(
                "SELECT 1 FROM cidadao WHERE LOWER(email) = %s",
                [email],
            )
            # se ja achou, aviso e saio sem criar de novo (pra nao duplicar)
            if cursor.fetchone():
                self.stdout.write(self.style.WARNING("Demo ja existe."))
                return

            # nao existe ainda, entao insiro o cidadao demo com a senha ja hasheada
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
                    make_password("demo123"),   # hash da senha demo123
                    "CID",                       # perfil cidadao
                    True,                        # ja entra ativo
                    timezone.now(),              # data de cadastro = agora
                ],
            )

        # mostro o login que acabei de criar pra eu lembrar na hora de testar
        self.stdout.write(self.style.SUCCESS("demo@portal.vg / demo123"))
