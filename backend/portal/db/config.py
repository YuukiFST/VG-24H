"""portal.db.config — parte do db.py que cuida da config do semaforo (SQL puro).
A fachada publica fica em portal/db/__init__.py."""


# SimpleNamespace pra devolver os prazos como objeto (.prazo_amarelo_dias etc).
from types import SimpleNamespace

# connection do Django pra rodar o SQL na mao.
from django.db import connection


def buscar_configuracao_prazos():
    """Pega os prazos do semaforo (quando fica amarelo/vermelho) ou usa default."""
    with connection.cursor() as cursor:
        # so existe uma linha de config, por isso o WHERE id = 1 fixo.
        cursor.execute(
            "SELECT prazo_amarelo_dias, prazo_vermelho_dias "
            "FROM configuracao_semaforo WHERE id = 1"
        )
        row = cursor.fetchone()
    # se nao tiver config no banco (row None), eu caio nos defaults: 15 e 30 dias.
    # esse "if row else" me protege de dar erro quando o banco ta vazio.
    return SimpleNamespace(
        prazo_amarelo_dias=row[0] if row else 15,
        prazo_vermelho_dias=row[1] if row else 30,
    )

def atualizar_configuracao_prazos(prazo_amarelo, prazo_vermelho):
    """Salva os prazos novos do semaforo (a unica linha de config, id = 1)."""
    with connection.cursor() as cursor:
        # passo os valores como %s (parametrizado) pra evitar injection.
        cursor.execute(
            "UPDATE configuracao_semaforo SET prazo_amarelo_dias = %s, "
            "prazo_vermelho_dias = %s WHERE id = 1",
            [prazo_amarelo, prazo_vermelho],
        )
