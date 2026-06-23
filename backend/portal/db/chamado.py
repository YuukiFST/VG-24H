"""portal.db.chamado — extraido de db.py (camada SQL pura).
Veja portal/db/__init__.py para a fachada publica."""


# SimpleNamespace pra montar objetos soltos sem ORM
from types import SimpleNamespace

from django.db import connection
from django.utils import timezone

# sql_lateral_ultimo_status me devolve o trecho de JOIN LATERAL que pega o ultimo status do chamado
from portal.db._shared import sql_lateral_ultimo_status

# popular_status preenche status_atual/sigla/cor; cor_semaforo calcula a cor pelos dias
from portal.db.historico import popular_status
from portal.db.stats import cor_semaforo
from portal.models import ConfiguracaoSemaforo

# DTOs/refs leves pra montar o chamado sem ORM
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
            # pego os campos do chamado e junto nome/descricao do servico e nome do bairro
            "SELECT c.id_chamado, c.num_protocolo, c.prioridade, "
            "c.ponto_de_referencia, c.descricao, c.resolucao, "
            "c.nota_avaliacao, c.comentario_avaliacao, "
            "c.dt_abertura, c.dt_conclusao, c.dt_avaliacao, c.atualizado_em, "
            "c.id_servico, c.id_bairro, c.id_cidadao, "
            "s.nome AS servico_nome, s.descricao AS servico_descricao, "
            "b.nome_bairro "
            "FROM chamado c "
            # JOIN no servico (todo chamado tem servico)
            "JOIN servico s ON c.id_servico = s.id_servico "
            # JOIN no bairro (todo chamado tem bairro)
            "JOIN bairro b ON c.id_bairro = b.id_bairro "
            "WHERE c.id_chamado = %s",
            [pk],
        )
        row = cursor.fetchone()
    if not row:
        return None

    # monto o ChamadoDTO mapeando cada coluna; servico e bairro viram refs aninhadas
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
    # essa query nao trouxe status, entao chamo popular_status pra preencher status_atual/sigla/cor
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
    # faco tudo numa transacao atomica: ou apaga tudo ou nao apaga nada
    with transaction.atomic(), connection.cursor() as cursor:
        # ligo a flag portal.excluindo na sessao pra os triggers de protecao deixarem o DELETE no historico passar
        cursor.execute("SELECT set_config('portal.excluindo', 'true', true)")
        # deleto na ordem das FKs: primeiro os filhos, por ultimo o chamado, senao tomo erro de FK
        cursor.execute("DELETE FROM foto_chamado WHERE id_chamado = %s", [chamado_id])
        cursor.execute("DELETE FROM historico_chamado WHERE id_chamado = %s", [chamado_id])
        cursor.execute("DELETE FROM notificacao WHERE id_chamado = %s", [chamado_id])
        cursor.execute("DELETE FROM chamado WHERE id_chamado = %s", [chamado_id])

def listar_chamados_cidadao(uid, status=None, data=None, q=None, pagina=1, por_pagina=15):
    """Lista chamados do cidadao com filtros e paginacao.

    Retorna (lista_de_chamados, total_count) — ambos ja paginados.
    Cada chamado inclui cor_semaforo e sigla_status.
    """
    # offset da paginacao: quantas linhas pular pra chegar na pagina pedida
    offset = (pagina - 1) * por_pagina
    # monto a parte FROM/JOIN separada do SELECT pra eu reusar tanto no COUNT quanto no SELECT de dados
    sql_base = (
        "FROM chamado c "
        "JOIN servico s ON c.id_servico = s.id_servico "
        "JOIN bairro b ON c.id_bairro = b.id_bairro "
        # aqui entra o JOIN LATERAL que traz a ultima linha de historico = status atual (apelidado de "ultimo")
        + sql_lateral_ultimo_status()
        # so os chamados deste cidadao
        + "WHERE c.id_cidadao = %s "
    )
    select_cols = (
        "SELECT c.id_chamado, c.num_protocolo, c.prioridade, "
        "c.descricao, c.dt_abertura, c.atualizado_em, "
        "c.id_servico, c.id_bairro, "
        "s.nome AS servico_nome, b.nome_bairro, "
        # sigla e descricao do status vem do "ultimo" (resultado do LATERAL)
        "ultimo.sigla AS sigla_status, "
        "ultimo.descricao AS status_descricao "
    )
    # params comeca com o uid; os filtros opcionais vao adicionando na ordem que aparecem na query
    params = [uid]

    # filtro por status: comparo a sigla do ultimo status
    if status:
        sql_base += "AND ultimo.sigla = %s "
        params.append(status)
    # filtro por data de abertura (so a parte da data com ::date)
    if data:
        sql_base += "AND c.dt_abertura::date = %s "
        params.append(data)
    # filtro de busca por protocolo: ILIKE pra ser case-insensitive, escape_like pra escapar % e _
    if q:
        from portal.utils import escape_like
        sql_base += "AND c.num_protocolo ILIKE %s "
        params.append(f"%{escape_like(q)}%")

    # primeiro rodo o COUNT (mesmo sql_base) pra saber o total antes de paginar
    count_sql = "SELECT COUNT(*) " + sql_base
    with connection.cursor() as cursor:
        cursor.execute(count_sql, params)
        total_count = cursor.fetchone()[0]
        # depois rodo o SELECT real ordenado por abertura, com LIMIT/OFFSET da paginacao
        data_sql = select_cols + sql_base + "ORDER BY c.dt_abertura DESC LIMIT %s OFFSET %s"
        cursor.execute(data_sql, params + [por_pagina, offset])
        rows = cursor.fetchall()

    # pego os prazos pra calcular a cor de cada chamado
    config = ConfiguracaoSemaforo.get_singleton()
    chamados = []
    for r in rows:
        # calculo a cor do semaforo pela data de abertura (r[4])
        cor = cor_semaforo(r[4], config.prazo_amarelo_dias, config.prazo_vermelho_dias)
        # sigla limpa (sem espacos), tratando None
        sigla = (r[10] or "").strip()
        # monto cada chamado como objeto, com servico/bairro/status aninhados
        chamados.append(SimpleNamespace(
            id_chamado=r[0], pk=r[0], num_protocolo=r[1], prioridade=r[2],
            descricao=r[3], dt_abertura=r[4], atualizado_em=r[5],
            id_servico=SimpleNamespace(id_servico=r[6], pk=r[6], nome=r[8]),
            id_bairro=SimpleNamespace(id_bairro=r[7], pk=r[7], nome_bairro=r[9]),
            sigla_status=sigla, cor_semaforo=cor,
            status_atual=SimpleNamespace(sigla=sigla, descricao=r[11]),
        ))
    # devolvo a lista paginada e o total geral (pro front montar a paginacao)
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
        # aqui tambem junto o cidadao pra mostrar o nome de quem abriu (view da equipe)
        "JOIN cidadao ci ON c.id_cidadao = ci.id_cidadao "
        # JOIN LATERAL do ultimo status de novo
        + sql_lateral_ultimo_status()
        # WHERE TRUE pra eu poder ir concatenando os AND dos filtros sem quebrar
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

    # leio cada filtro do dict (uso .get pra nao quebrar se nao vier a chave)
    bairro = filtros.get("bairro")
    st = filtros.get("status")
    servico_filter = filtros.get("servico")
    d0 = filtros.get("de")
    d1 = filtros.get("ate")
    mostrar_encerrados = filtros.get("mostrar_encerrados", False)
    ordenar_por = filtros.get("ordenar_por", "prioridade")
    direcao = filtros.get("direcao", "desc")

    # vou concatenando os ANDs conforme o filtro veio preenchido, sempre com %s + append no params
    if bairro:
        sql_base += "AND c.id_bairro = %s "
        params.append(bairro)
    if st:
        # filtro de status aqui usa o id_status do ultimo (nao a sigla)
        sql_base += "AND ultimo.id_status = %s "
        params.append(st)
    if servico_filter:
        sql_base += "AND c.id_servico = %s "
        params.append(servico_filter)
    if d0:
        # data inicial: abertura >= de
        sql_base += "AND c.dt_abertura::date >= %s "
        params.append(d0)
    if d1:
        # data final: abertura <= ate
        sql_base += "AND c.dt_abertura::date <= %s "
        params.append(d1)
    # por padrao escondo os encerrados (CO/CA) a nao ser que peçam pra mostrar
    if not mostrar_encerrados:
        sql_base += "AND ultimo.sigla NOT IN ('CO', 'CA') "

    count_sql = "SELECT COUNT(*) " + sql_base
    # mapa de ordenacao: traduzo o nome amigavel vindo do filtro pra coluna SQL real (com fallback em prioridade)
    coluna_ordem = {
        "prioridade": "c.prioridade", "dt_abertura": "c.dt_abertura",
        "protocolo": "c.num_protocolo", "dias_aberto": "NOW() - c.dt_abertura",
    }.get(ordenar_por, "c.prioridade")
    # direcao asc/desc (default desc)
    ordem_direcao = "DESC" if direcao == "desc" else "ASC"
    # esse CASE forca os encerrados (CO/CA) sempre pro fim da lista, independente da outra ordenacao
    order_fixo = "CASE WHEN ultimo.sigla IN ('CO','CA') THEN 1 ELSE 0 END"
    order_clause = f"ORDER BY {order_fixo}, {coluna_ordem} {ordem_direcao}"
    # se ordenei por prioridade, desempato pelos mais recentes
    if ordenar_por == "prioridade":
        order_clause += ", c.dt_abertura DESC"

    # junto select + base + ordenacao + paginacao pra formar o SQL final dos dados
    data_sql = select_cols + sql_base + order_clause + " LIMIT %s OFFSET %s"
    with connection.cursor() as cursor:
        # COUNT primeiro com os mesmos params dos filtros
        cursor.execute(count_sql, params)
        total_count = cursor.fetchone()[0]
        # depois os dados com os params + limit/offset no fim
        cursor.execute(data_sql, params + [por_pagina, offset])
        rows = cursor.fetchall()

    config = ConfiguracaoSemaforo.get_singleton()
    linhas = []
    for r in rows:
        cor = cor_semaforo(r[4], config.prazo_amarelo_dias, config.prazo_vermelho_dias)
        sigla = (r[12] or "").strip()
        # monto o chamado com servico/bairro/cidadao/status aninhados
        ch = SimpleNamespace(
            id_chamado=r[0], pk=r[0], num_protocolo=r[1], prioridade=r[2],
            descricao=r[3], dt_abertura=r[4], atualizado_em=r[5],
            id_servico=SimpleNamespace(id_servico=r[6], pk=r[6], nome=r[9]),
            id_bairro=SimpleNamespace(id_bairro=r[7], pk=r[7], nome_bairro=r[10]),
            id_cidadao=SimpleNamespace(id_cidadao=r[8], pk=r[8], nome_completo=r[11]),
            sigla_status=sigla, cor_semaforo=cor,
            status_atual=SimpleNamespace(sigla=sigla, descricao=r[13]),
        )
        # alem do chamado, ja devolvo a cor e os dias em aberto formatados pro template
        linhas.append({"ch": ch, "cor": cor, "dias_aberto": formatar_dias_em_aberto(ch.dt_abertura)})
    return linhas, total_count

def buscar_chamado_detalhe_equipe(pk):
    """Busca chamado completo para a view da equipe, com servico/bairro/cidadao/categoria."""
    with connection.cursor() as cursor:
        # versao completa pra equipe: trago tambem dados do cidadao (email/telefone) e o nome da categoria
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
            # JOIN extra na categoria passando pela tabela servico (servico -> categoria)
            "JOIN categoria_servico cat ON s.id_categoria = cat.id_categoria "
            "WHERE c.id_chamado = %s", [pk]
        )
        row = cursor.fetchone()
    if not row:
        return None
    # monto o objeto com servico (que ainda aninha a categoria dentro), bairro e cidadao
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
    # de novo, essa query nao traz status, entao populo via funcao
    popular_status(ch)
    return ch

def chamado_existe(pk):
    """Retorna True se o chamado existe."""
    with connection.cursor() as cursor:
        # SELECT 1 so pra checar existencia, nem preciso dos dados
        cursor.execute("SELECT 1 FROM chamado WHERE id_chamado = %s", [pk])
        return cursor.fetchone() is not None

def avaliar_chamado(chamado_id, nota, comentario):
    """Registra avaliacao de chamado."""
    with connection.cursor() as cursor:
        # gravo nota, comentario e a data da avaliacao (agora) no proprio chamado
        cursor.execute(
            "UPDATE chamado SET nota_avaliacao = %s, "
            "comentario_avaliacao = %s, dt_avaliacao = %s "
            "WHERE id_chamado = %s",
            [nota, comentario, timezone.now(), chamado_id],
        )

def buscar_status_ca():
    """Retorna o ID do status Cancelado (CA)."""
    with connection.cursor() as cursor:
        # pego o id do status cuja sigla eh 'CA' (Cancelado), usado quando vou cancelar um chamado
        cursor.execute("SELECT id_status FROM status_chamado WHERE sigla = 'CA'")
        row = cursor.fetchone()
    # devolvo o id ou None se por algum motivo nao existir
    return row[0] if row else None

