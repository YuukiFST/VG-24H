"""portal.db.notificacao — extraido de db.py (camada SQL pura).
Veja portal/db/__init__.py para a fachada publica."""


from django.db import connection

from portal.db._shared import fetch_all

_NOTIF_FIELDS = ("id_notificacao", "mensagem", "lida", "arquivada", "dt_envio", "id_chamado_id")


def listar_notificacoes_cidadao(uid):
    """Lista notificacoes nao arquivadas de um cidadao."""
    return fetch_all(
        "SELECT n.id_notificacao, n.mensagem, n.lida, n.arquivada, "
        "n.dt_envio, n.id_chamado "
        "FROM notificacao n "
        "WHERE n.arquivada = FALSE "
        "AND n.id_chamado IN (SELECT c.id_chamado FROM chamado c WHERE c.id_cidadao = %s) "
        "ORDER BY n.dt_envio DESC",
        [uid],
        fields=_NOTIF_FIELDS,
    )

def listar_notificacoes_servidor(uid):
    """Lista notificacoes nao arquivadas de um servidor."""
    return fetch_all(
        "SELECT n.id_notificacao, n.mensagem, n.lida, n.arquivada, "
        "n.dt_envio, n.id_chamado "
        "FROM notificacao n "
        "WHERE n.arquivada = FALSE "
        "AND n.id_chamado IN ("
        "  SELECT DISTINCT hc.id_chamado FROM historico_chamado hc WHERE hc.id_servidor = %s"
        ") ORDER BY n.dt_envio DESC",
        [uid],
        fields=_NOTIF_FIELDS,
    )

def marcar_notificacoes_lidas(nids):
    """Marca notificacoes como lidas."""
    if not nids:
        return
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE notificacao SET lida = TRUE WHERE id_notificacao = ANY(%s)", [nids]
        )

def excluir_notificacao(nid, uid_cidadao=None, uid_servidor=None):
    """Exclui notificacao com verificacao de permissao."""
    with connection.cursor() as cursor:
        if uid_cidadao:
            cursor.execute(
                "DELETE FROM notificacao WHERE id_notificacao = %s "
                "AND id_chamado IN (SELECT c.id_chamado FROM chamado c WHERE c.id_cidadao = %s)",
                [nid, uid_cidadao]
            )
        elif uid_servidor:
            cursor.execute(
                "DELETE FROM notificacao WHERE id_notificacao = %s "
                "AND id_chamado IN ("
                "  SELECT DISTINCT hc.id_chamado FROM historico_chamado hc WHERE hc.id_servidor = %s"
                ")", [nid, uid_servidor]
            )
