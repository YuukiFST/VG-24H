"""portal.db.historico — extraido de db.py (camada SQL pura).
Veja portal/db/__init__.py para a fachada publica."""


from django.db import connection
from django.utils import timezone

from portal.db.stats import cor_semaforo
from portal.models import ConfiguracaoSemaforo
from portal.types import (
    HistoricoDTO,
    ServidorRef,
    StatusRef,
)


def popular_status(ch):
    """Busca o status atual do chamado via ultimo registro de historico.

    O chamado nao tem campo de status direto. O status eh determinado
    pelo registro mais recente na tabela historico_chamado (event sourcing).
    Esta funcao popula tres atributos no objeto ch:
    - status_atual: objeto com id_status, sigla e descricao
    - sigla_status: string da sigla (ex: 'AB', 'CO')
    - cor_semaforo: 'verde', 'amarelo' ou 'vermelho'
    """
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT sc.id_status, sc.sigla, sc.descricao "
            "FROM historico_chamado hc "
            "JOIN status_chamado sc ON hc.id_status = sc.id_status "
            "WHERE hc.id_chamado = %s "
            "ORDER BY hc.dt_alteracao DESC LIMIT 1",
            [ch.pk],
        )
        row = cursor.fetchone()

    if row:
        ch.status_atual = StatusRef(
            id_status=row[0], pk=row[0], sigla=row[1], descricao=row[2],
        )
        ch.sigla_status = (row[1] or "").strip()
    else:
        ch.status_atual = None
        ch.sigla_status = ""


    config = ConfiguracaoSemaforo.get_singleton()
    ch.cor_semaforo = cor_semaforo(
        ch.dt_abertura,
        config.prazo_amarelo_dias,
        config.prazo_vermelho_dias,
    )

def buscar_historicos(chamado_pk):
    """Busca historicos de um chamado com JOIN em servidor e status.

    Retorna lista de SimpleNamespace ordenada por data (mais antigo primeiro).
    LEFT JOIN em servidor permite que registros sem servidor (ex: abertura
    automatica pelo Trigger 1) aparecam normalmente.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT hc.id_historico_chamado, hc.dt_alteracao, hc.observacao, "
            "hc.id_servidor, hc.id_status, "
            "sv.nome_completo AS servidor_nome, "
            "sc.sigla AS status_sigla, sc.descricao AS status_descricao "
            "FROM historico_chamado hc "
            "LEFT JOIN servidor sv ON hc.id_servidor = sv.id_servidor "
            "JOIN status_chamado sc ON hc.id_status = sc.id_status "
            "WHERE hc.id_chamado = %s "
            "ORDER BY hc.dt_alteracao",
            [chamado_pk],
        )
        return [
            HistoricoDTO(
                id_historico_chamado=r[0], pk=r[0], dt_alteracao=r[1],
                observacao=r[2], id_servidor_id=r[3],
                id_servidor=ServidorRef(nome_completo=r[5]) if r[3] else None,
                id_status=StatusRef(id_status=r[4], pk=r[4], sigla=r[6], descricao=r[7]),
            )
            for r in cursor.fetchall()
        ]

def criar_historico(chamado_id, status_id, servidor_id=None, observacao=None, dt_alteracao=None):
    """Insere registro em historico_chamado (event sourcing).

    Cada chamada gera um INSERT na tabela historico_chamado, nunca um UPDATE.
    Os triggers Trigger 2A e 2B disparam automaticamente apos o INSERT
    para atualizar atualizado_em e, se aplicavel, dt_conclusao e notificacao.

    Parametros:
        chamado_id: PK do chamado na tabela chamado.
        status_id: PK do status na tabela status_chamado.
        servidor_id: PK do servidor (None se a acao for do cidadao).
        observacao: texto opcional (obs do cidadao, motivo de cancelamento, etc).
        dt_alteracao: data/hora da alteracao (padrao: timezone.now()).

    Retorna o id_historico_chamado gerado (via RETURNING).
    """
    if dt_alteracao is None:
        dt_alteracao = timezone.now()

    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO historico_chamado "
            "(id_chamado, id_servidor, id_status, observacao, dt_alteracao) "
            "VALUES (%s, %s, %s, %s, %s) "
            "RETURNING id_historico_chamado",
            [chamado_id, servidor_id, status_id, observacao, dt_alteracao],
        )
        return cursor.fetchone()[0]

def buscar_sigla_status_atual(chamado_id):
    """Retorna a sigla do status atual do chamado."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT sc.sigla FROM historico_chamado hc "
            "JOIN status_chamado sc ON hc.id_status = sc.id_status "
            "WHERE hc.id_chamado = %s "
            "ORDER BY hc.dt_alteracao DESC LIMIT 1", [chamado_id]
        )
        row = cursor.fetchone()
    return row[0].strip() if row else ""

def listar_status_com_sigla_map():
    """Retorna dict {id_status: sigla} para uso no JS de status."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT id_status, sigla FROM status_chamado")
        return {r[0]: r[1].strip() for r in cursor.fetchall()}
