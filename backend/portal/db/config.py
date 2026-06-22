"""portal.db.config — extraido de db.py (camada SQL pura).
Veja portal/db/__init__.py para a fachada publica."""


from types import SimpleNamespace

from django.db import connection


def buscar_configuracao_prazos():
    """Retorna configuracao de prazos do semaforo ou defaults."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT prazo_amarelo_dias, prazo_vermelho_dias "
            "FROM configuracao_semaforo WHERE id = 1"
        )
        row = cursor.fetchone()
    return SimpleNamespace(
        prazo_amarelo_dias=row[0] if row else 15,
        prazo_vermelho_dias=row[1] if row else 30,
    )

def atualizar_configuracao_prazos(prazo_amarelo, prazo_vermelho):
    """Atualiza prazos globais do semaforo."""
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE configuracao_semaforo SET prazo_amarelo_dias = %s, "
            "prazo_vermelho_dias = %s WHERE id = 1",
            [prazo_amarelo, prazo_vermelho],
        )
