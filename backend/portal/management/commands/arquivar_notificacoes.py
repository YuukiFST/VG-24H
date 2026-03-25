"""
Management command: arquivar_notificacoes

Automatically archives notifications older than 30 days.
Run via: python manage.py arquivar_notificacoes
Schedule via cron or Render Cron Job for production.
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from portal.models import Notificacao


class Command(BaseCommand):
    help = "Arquiva notificações com mais de 30 dias."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dias",
            type=int,
            default=30,
            help="Número de dias após os quais arquivar (padrão: 30).",
        )

    def handle(self, *args, **options):
        dias = options["dias"]
        limite = timezone.now() - timedelta(days=dias)
        qs = Notificacao.objects.filter(arquivada=False, dt_envio__lt=limite)
        total = qs.update(arquivada=True)
        self.stdout.write(
            self.style.SUCCESS(f"{total} notificação(ões) arquivada(s).")
        )
