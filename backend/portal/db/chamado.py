"""portal.db.chamado — extraido de db.py (camada SQL pura).
Veja portal/db/__init__.py para a fachada publica."""


from types import SimpleNamespace

from django.db import connection
from django.utils import timezone

from portal.db._shared import sql_lateral_ultimo_status
from portal.db.historico import criar_historico, popular_status
from portal.db.stats import cor_semaforo
from portal.models import ConfiguracaoSemaforo
from portal.types import (
    BairroRef,
    ChamadoDTO,
    ServicoRef,
)


def buscar_chamado(pk):
    """Busca chamado por ID com JOIN em servico e bairro.

    Retorna um SimpleNamespace com todos os campos do chamado,
    incluindo dados do servico (nome, prazos) e bairro. Tambem
    popula status_atual, sigla_status e cor_semaforo via popular_status().

    Usado por views_cidadao e views_equipe para detalhe do chamado.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT c.id_chamado, c.num_protocolo, c.prioridade, "
            "c.ponto_de_referencia, c.descricao, c.resolucao, "
            "c.nota_avaliacao, c.comentario_avaliacao, "
            "c.dt_abertura, c.dt_conclusao, c.dt_avaliacao, c.atualizado_em, "
            "c.id_servico, c.id_bairro, c.id_cidadao, "
            "s.nome AS servico_nome, s.descricao AS servico_descricao, "
            "b.nome_bairro "
            "FROM chamado c "
            "JOIN servico s ON c.id_servico = s.id_servico "
            "JOIN bairro b ON c.id_bairro = b.id_bairro "
            "WHERE c.id_chamado = %s",
            [pk],
        )
        row = cursor.fetchone()
    if not row:
        return None

    ch = ChamadoDTO(
        id_chamado=row[0], pk=row[0], num_protocolo=row[1], prioridade=row[2],
        ponto_de_referencia=row[3], descricao=row[4], resolucao=row[5],
        nota_avaliacao=row[6], comentario_avaliacao=row[7],
        dt_abertura=row[8], dt_conclusao=row[9], dt_avaliacao=row[10],
        atualizado_em=row[11], id_cidadao_id=row[14],
        id_servico=ServicoRef(
            id_servico=row[12], pk=row[12], nome=row[15],
            descricao=row[16],
        ),
        id_bairro=BairroRef(id_bairro=row[13], pk=row[13], nome_bairro=row[17]),
    )
    popular_status(ch)
    return ch

def excluir_chamado_com_cascata(chamado_id):
    """Exclui chamado em cascata com bypass de triggers.

    Ativa a flag portal.excluindo na sessao PostgreSQL para permitir
    que os triggers de protecao (fn_historico_sem_delete) deixem
    os DELETEs passarem. A flag vale para toda a transacao atual.

    Deleta na ordem correta respeitando as FKs:
    foto_chamado → historico_chamado → notificacao → chamado.
    """
    from django.db import transaction
    with transaction.atomic(), connection.cursor() as cursor:
        cursor.execute("SELECT set_config('portal.excluindo', 'true', true)")
        cursor.execute("DELETE FROM foto_chamado WHERE id_chamado = %s", [chamado_id])
        cursor.execute("DELETE FROM historico_chamado WHERE id_chamado = %s", [chamado_id])
        cursor.execute("DELETE FROM notificacao WHERE id_chamado = %s", [chamado_id])
        cursor.execute("DELETE FROM chamado WHERE id_chamado = %s", [chamado_id])

def listar_chamados_cidadao(uid, status=None, data=None, q=None, pagina=1, por_pagina=15):
    """Lista chamados do cidadao com filtros e paginacao.

    Retorna (lista_de_chamados, total_count) — ambos ja paginados.
    Cada chamado inclui cor_semaforo e sigla_status.
    """
    offset = (pagina - 1) * por_pagina
    sql_base = (
        "FROM chamado c "
        "JOIN servico s ON c.id_servico = s.id_servico "
        "JOIN bairro b ON c.id_bairro = b.id_bairro "
        + sql_lateral_ultimo_status()
        + "WHERE c.id_cidadao = %s "
    )
    select_cols = (
        "SELECT c.id_chamado, c.num_protocolo, c.prioridade, "
        "c.descricao, c.dt_abertura, c.atualizado_em, "
        "c.id_servico, c.id_bairro, "
        "s.nome AS servico_nome, b.nome_bairro, "
        "ultimo.sigla AS sigla_status, "
        "ultimo.descricao AS status_descricao "
    )
    params = [uid]

    if status:
        sql_base += "AND ultimo.sigla = %s "
        params.append(status)
    if data:
        sql_base += "AND c.dt_abertura::date = %s "
        params.append(data)
    if q:
        from portal.utils import escape_like
        sql_base += "AND c.num_protocolo ILIKE %s "
        params.append(f"%{escape_like(q)}%")

    count_sql = "SELECT COUNT(*) " + sql_base
    with connection.cursor() as cursor:
        cursor.execute(count_sql, params)
        total_count = cursor.fetchone()[0]
        data_sql = select_cols + sql_base + "ORDER BY c.dt_abertura DESC LIMIT %s OFFSET %s"
        cursor.execute(data_sql, params + [por_pagina, offset])
        rows = cursor.fetchall()

    config = ConfiguracaoSemaforo.get_singleton()
    chamados = []
    for r in rows:
        cor = cor_semaforo(r[4], config.prazo_amarelo_dias, config.prazo_vermelho_dias)
        sigla = (r[10] or "").strip()
        chamados.append(SimpleNamespace(
            id_chamado=r[0], pk=r[0], num_protocolo=r[1], prioridade=r[2],
            descricao=r[3], dt_abertura=r[4], atualizado_em=r[5],
            id_servico=SimpleNamespace(id_servico=r[6], pk=r[6], nome=r[8]),
            id_bairro=SimpleNamespace(id_bairro=r[7], pk=r[7], nome_bairro=r[9]),
            sigla_status=sigla, cor_semaforo=cor,
            status_atual=SimpleNamespace(sigla=sigla, descricao=r[11]),
        ))
    return chamados, total_count

def listar_chamados_equipe(filtros, pagina=1, por_pagina=15):
    """Lista todos os chamados com filtros para a equipe.

    filtros = dict com chaves: bairro, status, servico, de, ate,
              mostrar_encerrados, ordenar_por, direcao
    Retorna (lista_de_chamados, total_count).
    """
    from portal.utils import formatar_dias_em_aberto
    offset = (pagina - 1) * por_pagina

    sql_base = (
        "FROM chamado c "
        "JOIN servico s ON c.id_servico = s.id_servico "
        "JOIN bairro b ON c.id_bairro = b.id_bairro "
        "JOIN cidadao ci ON c.id_cidadao = ci.id_cidadao "
        + sql_lateral_ultimo_status()
        + "WHERE TRUE "
    )
    select_cols = (
        "SELECT c.id_chamado, c.num_protocolo, c.prioridade, "
        "c.descricao, c.dt_abertura, c.atualizado_em, "
        "c.id_servico, c.id_bairro, c.id_cidadao, "
        "s.nome AS servico_nome, b.nome_bairro, "
        "ci.nome_completo AS cidadao_nome, "
        "ultimo.sigla AS sigla_status, "
        "ultimo.descricao AS status_descricao "
    )
    params = []

    bairro = filtros.get("bairro")
    st = filtros.get("status")
    servico_filter = filtros.get("servico")
    d0 = filtros.get("de")
    d1 = filtros.get("ate")
    mostrar_encerrados = filtros.get("mostrar_encerrados", False)
    ordenar_por = filtros.get("ordenar_por", "prioridade")
    direcao = filtros.get("direcao", "desc")

    if bairro:
        sql_base += "AND c.id_bairro = %s "; params.append(bairro)
    if st:
        sql_base += "AND ultimo.id_status = %s "; params.append(st)
    if servico_filter:
        sql_base += "AND c.id_servico = %s "; params.append(servico_filter)
    if d0:
        sql_base += "AND c.dt_abertura::date >= %s "; params.append(d0)
    if d1:
        sql_base += "AND c.dt_abertura::date <= %s "; params.append(d1)
    if not mostrar_encerrados:
        sql_base += "AND ultimo.sigla NOT IN ('CO', 'CA') "

    count_sql = "SELECT COUNT(*) " + sql_base
    coluna_ordem = {
        "prioridade": "c.prioridade", "dt_abertura": "c.dt_abertura",
        "protocolo": "c.num_protocolo", "dias_aberto": "NOW() - c.dt_abertura",
    }.get(ordenar_por, "c.prioridade")
    ordem_direcao = "DESC" if direcao == "desc" else "ASC"
    order_fixo = "CASE WHEN ultimo.sigla IN ('CO','CA') THEN 1 ELSE 0 END"
    order_clause = f"ORDER BY {order_fixo}, {coluna_ordem} {ordem_direcao}"
    if ordenar_por == "prioridade":
        order_clause += ", c.dt_abertura DESC"

    data_sql = select_cols + sql_base + order_clause + " LIMIT %s OFFSET %s"
    with connection.cursor() as cursor:
        cursor.execute(count_sql, params)
        total_count = cursor.fetchone()[0]
        cursor.execute(data_sql, params + [por_pagina, offset])
        rows = cursor.fetchall()

    config = ConfiguracaoSemaforo.get_singleton()
    linhas = []
    for r in rows:
        cor = cor_semaforo(r[4], config.prazo_amarelo_dias, config.prazo_vermelho_dias)
        sigla = (r[12] or "").strip()
        ch = SimpleNamespace(
            id_chamado=r[0], pk=r[0], num_protocolo=r[1], prioridade=r[2],
            descricao=r[3], dt_abertura=r[4], atualizado_em=r[5],
            id_servico=SimpleNamespace(id_servico=r[6], pk=r[6], nome=r[9]),
            id_bairro=SimpleNamespace(id_bairro=r[7], pk=r[7], nome_bairro=r[10]),
            id_cidadao=SimpleNamespace(id_cidadao=r[8], pk=r[8], nome_completo=r[11]),
            sigla_status=sigla, cor_semaforo=cor,
            status_atual=SimpleNamespace(sigla=sigla, descricao=r[13]),
        )
        linhas.append({"ch": ch, "cor": cor, "dias_aberto": formatar_dias_em_aberto(ch.dt_abertura)})
    return linhas, total_count

def buscar_chamado_detalhe_equipe(pk):
    """Busca chamado completo para a view da equipe, com servico/bairro/cidadao/categoria."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT c.id_chamado, c.num_protocolo, c.prioridade, "
            "c.ponto_de_referencia, c.descricao, c.resolucao, "
            "c.nota_avaliacao, c.comentario_avaliacao, "
            "c.dt_abertura, c.dt_conclusao, c.dt_avaliacao, c.atualizado_em, "
            "c.id_servico, c.id_bairro, c.id_cidadao, "
            "s.nome AS servico_nome, s.descricao AS servico_descricao, "
            "b.nome_bairro, "
            "ci.nome_completo AS cidadao_nome, ci.email AS cidadao_email, "
            "ci.telefone AS cidadao_telefone, "
            "cat.nome AS categoria_nome "
            "FROM chamado c "
            "JOIN servico s ON c.id_servico = s.id_servico "
            "JOIN bairro b ON c.id_bairro = b.id_bairro "
            "JOIN cidadao ci ON c.id_cidadao = ci.id_cidadao "
            "JOIN categoria_servico cat ON s.id_categoria = cat.id_categoria "
            "WHERE c.id_chamado = %s", [pk]
        )
        row = cursor.fetchone()
    if not row:
        return None
    ch = SimpleNamespace(
        id_chamado=row[0], pk=row[0], num_protocolo=row[1], prioridade=row[2],
        ponto_de_referencia=row[3], descricao=row[4], resolucao=row[5],
        nota_avaliacao=row[6], comentario_avaliacao=row[7],
        dt_abertura=row[8], dt_conclusao=row[9], dt_avaliacao=row[10],
        atualizado_em=row[11],
        id_servico=SimpleNamespace(id_servico=row[12], pk=row[12], nome=row[15],
                                   descricao=row[16],
                                   id_categoria=SimpleNamespace(nome=row[21])),
        id_bairro=SimpleNamespace(id_bairro=row[13], pk=row[13], nome_bairro=row[17]),
        id_cidadao=SimpleNamespace(id_cidadao=row[14], pk=row[14],
                                   nome_completo=row[18], email=row[19], telefone=row[20]),
    )
    popular_status(ch)
    return ch

def chamado_existe(pk):
    """Retorna True se o chamado existe."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1 FROM chamado WHERE id_chamado = %s", [pk])
        return cursor.fetchone() is not None

def listar_chamados_painel(cidadao_pk):
    """Lista chamados do cidadao para o painel (versao resumida)."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT c.id_chamado, c.num_protocolo, c.descricao, "
            "c.prioridade, c.dt_abertura, "
            "s.nome AS servico_nome, b.nome_bairro, "
            "ultimo.sigla AS sigla_status "
            "FROM chamado c "
            "LEFT JOIN servico s ON c.id_servico = s.id_servico "
            "LEFT JOIN bairro b ON c.id_bairro = b.id_bairro "
            + sql_lateral_ultimo_status(colunas="sc.sigla")
            + "WHERE c.id_cidadao = %s "
            "ORDER BY c.dt_abertura DESC", [cidadao_pk]
        )
        config = ConfiguracaoSemaforo.get_singleton()
        chamados = []
        for row in cursor.fetchall():
            cor = cor_semaforo(row[4], config.prazo_amarelo_dias, config.prazo_vermelho_dias)
            chamados.append(SimpleNamespace(
                id_chamado=row[0], num_protocolo=row[1], descricao=row[2],
                prioridade=row[3], dt_abertura=row[4],
                servico_nome=row[5], nome_bairro=row[6],
                sigla_status=row[7], cor_semaforo=cor,
                dias_em_aberto=(timezone.now().date() - row[4].date()).days,
            ))
        return chamados

def avaliar_chamado(chamado_id, nota, comentario):
    """Registra avaliacao de chamado."""
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE chamado SET nota_avaliacao = %s, "
            "comentario_avaliacao = %s, dt_avaliacao = %s "
            "WHERE id_chamado = %s",
            [nota, comentario, timezone.now(), chamado_id],
        )

def buscar_status_ca():
    """Retorna o ID do status Cancelado (CA)."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT id_status FROM status_chamado WHERE sigla = 'CA'")
        row = cursor.fetchone()
    return row[0] if row else None

def cancelar_chamado(chamado_id, motivo):
    """Cancela chamado: insere historico CA + atualiza resolucao."""
    from django.db import transaction
    ca_id = buscar_status_ca()
    if not ca_id:
        raise ValueError("Status CA nao encontrado")
    with transaction.atomic(), connection.cursor() as cursor:
        criar_historico(chamado_id, ca_id, observacao=motivo)
        cursor.execute(
            "UPDATE chamado SET resolucao = %s WHERE id_chamado = %s",
            [motivo, chamado_id],
        )
