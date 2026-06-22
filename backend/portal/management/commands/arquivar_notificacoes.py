"""
Meu command: arquivar_notificacoes

Esse comando arquiva sozinho as notificacoes que ja tem mais de 30 dias,
pra lista do usuario nao ficar gigante.
Pra rodar na mao: python manage.py arquivar_notificacoes
Em producao a ideia eh agendar via cron ou Cron Job do Render.

Se eu quiser mudar o corte de 30 dias, passo --dias N (padrao eh 30).
"""

# timedelta pra eu subtrair os dias da data de hoje
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import connection  # uso SQL puro, por isso pego a conexao direto
from django.utils import timezone


class Command(BaseCommand):
    # esse texto aparece quando rodo python manage.py help
    help = "Arquiva notificacoes com mais de 30 dias."

    def add_arguments(self, parser):
        # registro o argumento opcional --dias pra escolher o periodo de corte
        parser.add_argument(
            "--dias",
            type=int,
            default=30,
            help="Numero de dias apos os quais arquivar (padrao: 30).",
        )

    def handle(self, *args, **options):
        # pego o valor de --dias que o usuario passou (ou 30 por padrao)
        dias = options["dias"]
        # calculo a data limite: tudo enviado antes disso vai ser arquivado
        limite = timezone.now() - timedelta(days=dias)

        with connection.cursor() as cursor:
            # marco como arquivada toda notificacao antiga que ainda nao tava arquivada
            cursor.execute(
                "UPDATE notificacao SET arquivada = TRUE "
                "WHERE arquivada = FALSE AND dt_envio < %s",
                [limite],
            )
            # rowcount me diz quantas linhas o UPDATE mexeu
            total = cursor.rowcount

        # mostro no terminal quantas eu arquivei, em verde de sucesso
        self.stdout.write(
            self.style.SUCCESS(f"{total} notificacao(oes) arquivada(s).")
        )
