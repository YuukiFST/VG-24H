"""
Management command: arquivar_notificacoes

Arquiva automaticamente notificacoes com mais de 30 dias.
Execucao manual: python manage.py arquivar_notificacoes
Para producao, agendar via cron ou Render Cron Job.

O parametro --dias permite configurar o periodo de corte
(padrao: 30 dias).
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone


class Command(BaseCommand):
    help = "Arquiva notificacoes com mais de 30 dias."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dias",
            type=int,
            default=30,
            help="Numero de dias apos os quais arquivar (padrao: 30).",
        )

    def handle(self, *args, **options):
        dias = options["dias"]
        limite = timezone.now() - timedelta(days=dias)

        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE notificacao SET arquivada = TRUE "
                "WHERE arquivada = FALSE AND dt_envio < %s",
                [limite],
            )
            total = cursor.rowcount

        self.stdout.write(
            self.style.SUCCESS(f"{total} notificacao(oes) arquivada(s).")
        )
