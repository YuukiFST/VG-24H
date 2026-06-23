"""portal.db.notificacao — parte do db.py das notificacoes (SQL puro).
A fachada publica fica em portal/db/__init__.py."""


# connection pros DELETE/UPDATE que eu faco direto no cursor.
from django.db import connection

# fetch_all eh meu helper que ja roda o SELECT e devolve objetos prontos.
from portal.db._shared import fetch_all

# lista dos campos na ordem do SELECT, pro fetch_all saber nomear cada coluna.
# deixei numa constante so porque as duas funcoes de listar usam a MESMA ordem.
_NOTIF_FIELDS = ("id_notificacao", "mensagem", "lida", "arquivada", "dt_envio", "id_chamado_id")


def listar_notificacoes_cidadao(uid):
    """Pega as notificacoes (nao arquivadas) de um cidadao."""
    # ideia: o cidadao so pode ver notificacao dos chamados DELE. Por isso o
    # subselect pega os id_chamado onde id_cidadao = ele, e eu filtro por IN.
    # arquivada = FALSE pra esconder as que ele ja arquivou, e ordeno por
    # data desc pra mostrar a mais recente primeiro.
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

def marcar_notificacoes_lidas(nids):
    """Marca um monte de notificacoes como lidas de uma vez."""
    # se a lista veio vazia eu nem rodo SQL, saio fora pra nao gastar a toa.
    if not nids:
        return
    with connection.cursor() as cursor:
        # truque do Postgres: ANY(%s) deixa eu passar a lista inteira de ids
        # num parametro so e atualizar todos numa tacada (em vez de um por um).
        cursor.execute(
            "UPDATE notificacao SET lida = TRUE WHERE id_notificacao = ANY(%s)", [nids]
        )

def excluir_notificacao(nid, uid_cidadao=None, uid_servidor=None):
    """Apaga uma notificacao, mas so se o usuario tiver permissao nela."""
    with connection.cursor() as cursor:
        # detalhe de seguranca: eu nao deleto so pelo id da notificacao, senao
        # qualquer um podia apagar a notificacao dos outros. Eu amarro o DELETE
        # ao dono do chamado tambem (o AND id_chamado IN (...)). Se a notificacao
        # nao for daquele usuario, o WHERE nao casa e nada eh apagado.
        if uid_cidadao:
            # caso cidadao: o chamado precisa ser dele (id_cidadao).
            cursor.execute(
                "DELETE FROM notificacao WHERE id_notificacao = %s "
                "AND id_chamado IN (SELECT c.id_chamado FROM chamado c WHERE c.id_cidadao = %s)",
                [nid, uid_cidadao]
            )
        elif uid_servidor:
            # caso servidor: ele precisa ter atuado no chamado (via historico).
            cursor.execute(
                "DELETE FROM notificacao WHERE id_notificacao = %s "
                "AND id_chamado IN ("
                "  SELECT DISTINCT hc.id_chamado FROM historico_chamado hc WHERE hc.id_servidor = %s"
                ")", [nid, uid_servidor]
            )
