"""portal.db.historico — extraido de db.py (camada SQL pura).
Veja portal/db/__init__.py para a fachada publica."""


from django.db import connection
from django.utils import timezone

# cor_semaforo calcula verde/amarelo/vermelho pelos dias; ConfiguracaoSemaforo guarda os prazos
from portal.db.stats import cor_semaforo
from portal.models import ConfiguracaoSemaforo

# esses sao uns DTO/refs leves que uso pra montar o objeto sem ORM
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
        # como nao tem coluna status, eu descubro o status atual pegando o ultimo historico
        cursor.execute(
            "SELECT sc.id_status, sc.sigla, sc.descricao "
            # parto do historico do chamado
            "FROM historico_chamado hc "
            # junto com a tabela de status pra trazer sigla e descricao
            "JOIN status_chamado sc ON hc.id_status = sc.id_status "
            # so deste chamado
            "WHERE hc.id_chamado = %s "
            # ordeno pela data de alteracao decrescente e pego 1: ou seja, o registro mais novo = status atual
            "ORDER BY hc.dt_alteracao DESC LIMIT 1",
            [ch.pk],
        )
        row = cursor.fetchone()

    # se tem historico, preencho o status_atual e a sigla limpinha (sem espacos)
    if row:
        ch.status_atual = StatusRef(
            id_status=row[0], pk=row[0], sigla=row[1], descricao=row[2],
        )
        ch.sigla_status = (row[1] or "").strip()
    else:
        # chamado sem nenhum historico ainda -> sem status
        ch.status_atual = None
        ch.sigla_status = ""


    # pego os prazos globais do singleton de config pra calcular a cor do semaforo
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
            # LEFT JOIN no servidor pq tem historico sem servidor (ex: abertura
            # automatica por trigger), e mesmo assim quero trazer a linha

            "LEFT JOIN servidor sv ON hc.id_servidor = sv.id_servidor "
            # JOIN normal no status pq todo historico tem status
            "JOIN status_chamado sc ON hc.id_status = sc.id_status "
            "WHERE hc.id_chamado = %s "
            # ordeno crescente pra ficar do mais antigo pro mais novo (linha do tempo)
            "ORDER BY hc.dt_alteracao",
            [chamado_pk],
        )
        # pra cada row monto um HistoricoDTO mapeando as colunas
        return [
            HistoricoDTO(
                id_historico_chamado=r[0], pk=r[0], dt_alteracao=r[1],
                observacao=r[2], id_servidor_id=r[3],
                # so crio o ServidorRef se tinha servidor (r[3]); senao deixo None (foi acao automatica/cidadao)
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
    # se nao passaram a data eu uso agora como padrao
    if dt_alteracao is None:
        dt_alteracao = timezone.now()

    with connection.cursor() as cursor:
        cursor.execute(
            # aqui eh event sourcing: mudar status = inserir nova linha, nunca dar UPDATE
            "INSERT INTO historico_chamado "
            "(id_chamado, id_servidor, id_status, observacao, dt_alteracao) "
            "VALUES (%s, %s, %s, %s, %s) "
            # RETURNING pra eu pegar o id do historico recem criado
            "RETURNING id_historico_chamado",
            [chamado_id, servidor_id, status_id, observacao, dt_alteracao],
        )
        # depois do INSERT os triggers 2A/2B disparam sozinhos no banco; aqui so devolvo o id gerado
        return cursor.fetchone()[0]

def buscar_sigla_status_atual(chamado_id):
    """Retorna a sigla do status atual do chamado."""
    with connection.cursor() as cursor:
        # mesmo truque de antes: ultimo historico = status atual, mas aqui so quero a sigla
        cursor.execute(
            "SELECT sc.sigla FROM historico_chamado hc "
            "JOIN status_chamado sc ON hc.id_status = sc.id_status "
            "WHERE hc.id_chamado = %s "
            "ORDER BY hc.dt_alteracao DESC LIMIT 1", [chamado_id]
        )
        row = cursor.fetchone()
    # devolvo a sigla sem espacos, ou string vazia se nao tem historico
    return row[0].strip() if row else ""

def listar_status_com_sigla_map():
    """Retorna dict {id_status: sigla} para uso no JS de status."""
    with connection.cursor() as cursor:
        # pego todos os status e monto um dict id->sigla pro JS usar
        cursor.execute("SELECT id_status, sigla FROM status_chamado")
        return {r[0]: r[1].strip() for r in cursor.fetchall()}
