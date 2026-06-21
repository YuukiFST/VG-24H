"""
views_equipe.py — Views da equipe (gestores e colaboradores — Portal VG 24H)

Este modulo atende as rotas acessiveis por gestores (GES) e colaboradores
(COL). A diferenca principal em relacao ao cidadao eh que a equipe:
- Ve TODOS os chamados (nao apenas os proprios)
- Pode alterar status dos chamados (transicoes de maquina de estados)
- Pode adicionar observacoes e fotos a qualquer chamado
- Tem acesso ao dashboard com graficos e metricas

O cidadao so pode cancelar seus proprios chamados e avalia-los quando
concluidos. A equipe controla o fluxo completo de atendimento.

Mudanca de status segue o padrao event sourcing: cada transicao gera
um novo INSERT em historico_chamado, nunca UPDATE. Os triggers do banco
disparam automaticamente apos cada INSERT:
- Trigger 2A: atualiza atualizado_em na tabela chamado
- Trigger 2B: se status = CO ou CA, seta dt_conclusao = NOW() e gera
  notificacao para o cidadao

Colaboradores (COL) nao podem alterar status de chamados ja encerrados
(Concluido ou Cancelado). Apenas gestores (GES) podem fazer isso.
Essa regra eh aplicada no Python e nao no banco de dados.
"""

import json
from datetime import timedelta
from types import SimpleNamespace

from django.contrib import messages
from django.db import connection, transaction
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from portal import db
from portal.decorators import perfil_codigo, perfis
from portal.forms import EquipeStatusForm, FotoForm, ObservacaoForm
from portal.models import ConfiguracaoSemaforo, Servico
from portal.utils import salvar_foto_upload


def _int_none(v):
    """Converte parametro de query string para int ou None.

    Campos de select enviam string vazia quando "Todos" esta selecionado.
    Essa funcao trata string vazia e None como None (para nao entrar
    na clausula WHERE do SQL) e tenta converter o resto para int.
    """
    if v is None or v == "":
        return None
    try:
        return int(v)
    except ValueError:
        return None


# ------------------------------------------------------------------
# Listar todos os chamados (GET /equipe/chamados/)
# ------------------------------------------------------------------

@perfis("COL", "GES")
def equipe_chamados_lista(request):
    """Lista todos os chamados do sistema com filtros, paginacao e ordenacao.

    Diferente da view do cidadao, esta nao filtra por id_cidadao.
    A equipe ve todos os chamados. O WHERE comeca com TRUE para permitir
    concatenar filtros opcionais com AND sem logica condicional.

    A ordenacao padrao eh por prioridade DESC (urgentes primeiro),
    com dt_abertura DESC como criterio de desempate. O usuario pode
    alterar a ordenacao pelos botoes de cabecalho (parametros
    ordenar_por e direcao na query string).

    A coluna "Dias em Aberto" eh calculada no Python como
    (hoje - dt_abertura).days, sem os pontos coloridos do semaforo antigo.
    """
    try:
        pagina = max(1, int(request.GET.get("pagina") or 1))
    except (ValueError, TypeError):
        pagina = 1
    por_pagina = 15
    offset = (pagina - 1) * por_pagina

    # Clase base do FROM/WHERE. WHERE TRUE permite concatenar filtros.
    sql_base = (
        "FROM chamado c "
        "JOIN servico s ON c.id_servico = s.id_servico "
        "JOIN bairro b ON c.id_bairro = b.id_bairro "
        "JOIN cidadao ci ON c.id_cidadao = ci.id_cidadao "
        "JOIN LATERAL ("
        "  SELECT sc.sigla, sc.descricao, sc.id_status FROM historico_chamado hc "
        "  JOIN status_chamado sc ON hc.id_status = sc.id_status "
        "  WHERE hc.id_chamado = c.id_chamado "
        "  ORDER BY hc.dt_alteracao DESC LIMIT 1"
        ") ultimo ON TRUE "
        "WHERE TRUE "
    )
    select_cols = (
        "SELECT c.id_chamado, c.num_protocolo, c.prioridade, "
        "c.descricao, c.dt_abertura, c.atualizado_em, "
        "c.id_servico, c.id_bairro, c.id_cidadao, "
        "s.nome AS servico_nome, "
        "b.nome_bairro, "
        "ci.nome_completo AS cidadao_nome, "
        "ultimo.sigla AS sigla_status, "
        "ultimo.descricao AS status_descricao "
    )
    params = []

    # Filtros opcionais da query string.
    bairro = _int_none(request.GET.get("bairro"))
    st = _int_none(request.GET.get("status"))
    servico_filter = _int_none(request.GET.get("servico"))
    d0 = request.GET.get("de")
    d1 = request.GET.get("ate")
    mostrar_encerrados = request.GET.get("mostrar_encerrados") == "1"
    ordenar_por = request.GET.get("ordenar_por", "prioridade")
    direcao = request.GET.get("direcao", "desc")

    if bairro:
        sql_base += "AND c.id_bairro = %s "
        params.append(bairro)
    if st:
        sql_base += "AND ultimo.id_status = %s "
        params.append(st)
    if servico_filter:
        sql_base += "AND c.id_servico = %s "
        params.append(servico_filter)
    if d0:
        sql_base += "AND c.dt_abertura::date >= %s "
        params.append(d0)
    if d1:
        sql_base += "AND c.dt_abertura::date <= %s "
        params.append(d1)

    if not mostrar_encerrados:
        sql_base += "AND ultimo.sigla NOT IN ('CO', 'CA') "

    # Conta total para a paginacao.
    count_sql = "SELECT COUNT(*) " + sql_base
    with connection.cursor() as cursor:
        cursor.execute(count_sql, params)
        total_count = cursor.fetchone()[0]

    # Mapeia o nome da coluna (vindo da UI) para a expressao SQL.
    # dias_aberto usa intervalo PostgreSQL (NOW() - dt_abertura).
    coluna_ordem = {
        "prioridade": "c.prioridade",
        "dt_abertura": "c.dt_abertura",
        "protocolo": "c.num_protocolo",
        "dias_aberto": "NOW() - c.dt_abertura",
    }.get(ordenar_por, "c.prioridade")
    ordem_direcao = "DESC" if direcao == "desc" else "ASC"

    # Encerrados sempre no final da lista.
    order_fixo = "CASE WHEN ultimo.sigla IN ('CO','CA') THEN 1 ELSE 0 END"
    if ordenar_por == "prioridade":
        data_sql = select_cols + sql_base + f"ORDER BY {order_fixo}, {coluna_ordem} {ordem_direcao}, c.dt_abertura DESC LIMIT %s OFFSET %s"
    else:
        data_sql = select_cols + sql_base + f"ORDER BY {order_fixo}, {coluna_ordem} {ordem_direcao} LIMIT %s OFFSET %s"
    data_params = params + [por_pagina, offset]

    with connection.cursor() as cursor:
        cursor.execute(data_sql, data_params)
        rows = cursor.fetchall()

    # Hidratacao: tuplas do banco viram objetos com atributos nomeados.
    config = ConfiguracaoSemaforo.get_singleton()
    linhas = []
    for r in rows:
        cor = db.cor_semaforo(r[4], config.prazo_amarelo_dias, config.prazo_vermelho_dias)
        sigla = r[12] or ""
        status_desc = r[13] or ""
        ch = SimpleNamespace(
            id_chamado=r[0], pk=r[0], num_protocolo=r[1], prioridade=r[2],
            descricao=r[3], dt_abertura=r[4], atualizado_em=r[5],
            id_servico=SimpleNamespace(id_servico=r[6], pk=r[6], nome=r[9]),
            id_bairro=SimpleNamespace(id_bairro=r[7], pk=r[7], nome_bairro=r[10]),
            id_cidadao=SimpleNamespace(id_cidadao=r[8], pk=r[8], nome_completo=r[11]),
            sigla_status=sigla, cor_semaforo=cor,
            status_atual=SimpleNamespace(sigla=sigla, descricao=status_desc),
        )
        # Dias em aberto: string com dias/horas/minutos.
        delta = timezone.now() - ch.dt_abertura
        if delta.total_seconds() < 3600:
            tempo_str = f"{int(delta.total_seconds() // 60)} minuto(s)"
        elif delta.total_seconds() < 86400:
            tempo_str = f"{int(delta.total_seconds() // 3600)} hora(s)"
        else:
            tempo_str = f"{delta.days} dia(s)"
        linhas.append({"ch": ch, "cor": cor, "dias_aberto": tempo_str})

    # Catalogos para os filtros do template.
    bairros_lista = db.listar_bairros_ativos()
    statuses_lista = db.listar_statuses()

    # Estatisticas do semaforo para os cards no topo.
    stats = db.calcular_stats_semaforo()

    # Estatisticas por servico para a tabela de breakdown.
    servicos_stats = db.calcular_stats_semaforo_por_servico()

    # Catalogo de servicos ativos para o filtro e legenda.
    servicos_catalogo = Servico.objects.filter(ativo=True).order_by("nome")

    # Percentuais para as barras de progresso no template.
    pct_no_prazo = round(stats["no_prazo"] / max(total_count, 1) * 100)
    pct_atencao = round(stats["atencao"] / max(total_count, 1) * 100)
    pct_critico = round(stats["critico"] / max(total_count, 1) * 100)

    page_obj, _ = db.paginar(linhas, pagina, por_pagina=por_pagina, total_count=total_count)

    return render(
        request,
        "portal/equipe/dashboard.html",
        {
            "linhas": page_obj,
            "stats": stats,
            "total_count": total_count,
            "page_obj": page_obj,
            "bairros": bairros_lista,
            "statuses": statuses_lista,
            "filtro_bairro": bairro,
            "filtro_status": st,
            "filtro_servico": servico_filter,
            "filtro_de": d0 or "",
            "filtro_ate": d1 or "",
            "ordenar_por": ordenar_por,
            "direcao": direcao,
            "servicos_stats": servicos_stats,
            "servicos": servicos_catalogo,
            "pct_no_prazo": pct_no_prazo,
            "pct_atencao": pct_atencao,
            "pct_critico": pct_critico,
            "mostrar_encerrados": mostrar_encerrados,
            "config_semaforo": config,
        },
    )


# ------------------------------------------------------------------
# Gerenciar prazos dos servicos (GET/POST /equipe/chamados/prazos/)
# ------------------------------------------------------------------

@require_http_methods(["GET", "POST"])
def gestao_prazos(request):
    """Gerencia os prazos globais do semaforo (amarelo/vermelho).

    Agora global (ConfiguracaoSemaforo singleton), nao mais por servico.
    Acessivel apenas por gestores (GES).
    """
    u = request.portal_user
    if not u:
        return redirect("portal:login")
    if u.perfil != "GES":
        messages.error(
            request,
            "Você não tem permissão para alterar os prazos. "
            "Apenas o Gestor pode realizar esta configuração."
        )
        return redirect("portal:equipe_chamados")

    if request.method == "POST":
        try:
            prazo_amarelo = int(request.POST.get("prazo_amarelo_dias", 15))
            prazo_vermelho = int(request.POST.get("prazo_vermelho_dias", 30))
        except (ValueError, TypeError):
            messages.error(request, "Valores inválidos.")
            return redirect("portal:gestao_prazos")

        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE configuracao_semaforo SET prazo_amarelo_dias = %s, prazo_vermelho_dias = %s WHERE id = 1",
                [prazo_amarelo, prazo_vermelho],
            )
        messages.success(request, "Prazos atualizados.")
        return redirect("portal:gestao_prazos")

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT prazo_amarelo_dias, prazo_vermelho_dias FROM configuracao_semaforo WHERE id = 1"
        )
        row = cursor.fetchone()

    config = SimpleNamespace(
        prazo_amarelo_dias=row[0] if row else 15,
        prazo_vermelho_dias=row[1] if row else 30,
    )

    return render(
        request,
        "portal/equipe/servico_prazos.html",
        {"config": config},
    )


# ------------------------------------------------------------------
# Detalhe do chamado + acoes (GET/POST /equipe/chamados/<pk>/)
# ------------------------------------------------------------------

@perfis("COL", "GES")
@require_http_methods(["GET", "POST"])
def equipe_chamado_detalhe(request, pk):
    """Exibe detalhes do chamado e processa acoes da equipe.

    Esta view eh hibrida: GET mostra o detalhe completo (com historico,
    fotos e dados do cidadao), POST executa uma acao determinada pelo
    campo oculto "acao" no formulario HTML.

    Acoes disponiveis:
    - status: altera o status do chamado (INSERT historico_chamado).
      Pode atualizar prioridade e resolucao junto. Colaboradores nao
      podem alterar status de chamados encerrados (CO ou CA).
    - obs: adiciona observacao mantendo o mesmo status.
    - foto: faz upload de nova foto para o chamado.

    A flag bloqueia_status_col controla se o formulario de status
    aparece no template. Quando True (COL com chamado encerrado),
    o formulario nao eh renderizado.
    """
    # Busca o chamado com todos os JOINs em uma unica query.
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
            "WHERE c.id_chamado = %s",
            [pk],
        )
        row = cursor.fetchone()
    if not row:
        raise Http404()

    # Monta o objeto chamado com dados aninhados (servico, bairro, cidadao).
    ch = SimpleNamespace(
        id_chamado=row[0], pk=row[0], num_protocolo=row[1], prioridade=row[2],
        ponto_de_referencia=row[3], descricao=row[4], resolucao=row[5],
        nota_avaliacao=row[6], comentario_avaliacao=row[7],
        dt_abertura=row[8], dt_conclusao=row[9], dt_avaliacao=row[10],
        atualizado_em=row[11],
        id_servico=SimpleNamespace(
            id_servico=row[12], pk=row[12], nome=row[15],
            descricao=row[16],
            id_categoria=SimpleNamespace(nome=row[21]),
        ),
        id_bairro=SimpleNamespace(id_bairro=row[13], pk=row[13], nome_bairro=row[17]),
        id_cidadao=SimpleNamespace(
            id_cidadao=row[14], pk=row[14], nome_completo=row[18],
            email=row[19], telefone=row[20],
        ),
    )

    # Popula status atual e cor do semaforo via db.py.
    db.popular_status(ch)

    # Dias em aberto para exibicao no template (string com unidade).
    delta = timezone.now() - ch.dt_abertura
    if delta.total_seconds() < 3600:
        dias_aberto = f"{int(delta.total_seconds() // 60)} minuto(s)"
    elif delta.total_seconds() < 86400:
        dias_aberto = f"{int(delta.total_seconds() // 3600)} hora(s)"
    else:
        dias_aberto = f"{delta.days} dia(s)"

    # Verifica o perfil do usuario e aplica a regra de bloqueio para COL.
    p = perfil_codigo(request.portal_user)
    ts = ch.sigla_status
    bloqueia_status_col = p == "COL" and ts in ("CO", "CA")
    pode_status = not bloqueia_status_col

    # Processa POST (acoes).
    form_status_erro = None
    if request.method == "POST":
        acao = request.POST.get("acao")

        # Acao: alterar status.
        # INSERT historico com o novo status. O status atual eh sempre
        # o ultimo registro de historico (event sourcing).
        if acao == "status" and pode_status:
            form_s = EquipeStatusForm(request.POST)
            if form_s.is_valid():
                novo = form_s.cleaned_data["id_status"]

                with transaction.atomic(), connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO historico_chamado "
                        "(id_chamado, id_servidor, id_status, dt_alteracao) "
                        "VALUES (%s, %s, %s, %s)",
                        [pk, request.portal_user.pk, novo.pk, timezone.now()],
                    )

                    nova_sigla = novo.sigla.strip().upper()
                    pri = request.POST.get("prioridade")
                    prioridade_val = ch.prioridade
                    if pri is not None:
                        try:
                            prioridade_val = max(0, min(5, int(pri)))
                        except (ValueError, TypeError):
                            pass

                    if nova_sigla in ("CO", "CA"):
                        # Status final: salva resolucao e prioridade.
                        resolucao = form_s.cleaned_data.get("resolucao") or None
                        cursor.execute(
                            "UPDATE chamado SET resolucao = %s, prioridade = %s "
                            "WHERE id_chamado = %s",
                            [resolucao, prioridade_val, pk],
                        )
                    else:
                        # Status intermediario: so atualiza prioridade.
                        cursor.execute(
                            "UPDATE chamado SET prioridade = %s "
                            "WHERE id_chamado = %s",
                            [prioridade_val, pk],
                        )

                # Trigger 2B dispara automaticamente apos o INSERT:
                # - Se CO ou CA: seta dt_conclusao = NOW()
                # - Se AB/EA/EE: seta dt_conclusao = NULL
                # - Sempre: gera notificacao para o cidadao

                messages.success(request, "Status atualizado.")
                return redirect("portal:equipe_chamado", pk=pk)
            form_status_erro = form_s
            for e in form_s.non_field_errors():
                messages.error(request, e)

        # Acao: adicionar observacao.
        # INSERT historico mantendo o mesmo status, so com texto.
        if acao == "obs":
            form_o = ObservacaoForm(request.POST)
            if form_o.is_valid():
                status_id = ch.status_atual.pk if ch.status_atual else None
                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO historico_chamado "
                        "(id_chamado, id_servidor, id_status, observacao, dt_alteracao) "
                        "VALUES (%s, %s, %s, %s, %s)",
                        [pk, request.portal_user.pk, status_id,
                         form_o.cleaned_data["texto"], timezone.now()],
                    )
                messages.success(request, "Observação registrada.")
            return redirect("portal:equipe_chamado", pk=pk)

        # Acao: upload de foto.
        if acao == "foto":
            if request.FILES.get("foto"):
                form_f = FotoForm(request.POST, request.FILES)
                if form_f.is_valid():
                    try:
                        url = salvar_foto_upload(request.FILES["foto"], request=request)
                    except ValueError as e:
                        messages.error(request, str(e))
                    else:
                        with connection.cursor() as cursor:
                            cursor.execute(
                                "INSERT INTO foto_chamado "
                                "(id_chamado, url_foto, dt_upload) "
                                "VALUES (%s, %s, %s)",
                                [pk, url, timezone.now()],
                            )
                        messages.success(request, "Foto registrada.")
                else:
                    for field, errors in form_f.errors.items():
                        for error in errors:
                            messages.error(request, error)
            else:
                messages.error(request, "Selecione uma imagem.")
            return redirect("portal:equipe_chamado", pk=pk)

    # GET: busca dados auxiliares para o template.
    historicos = db.buscar_historicos(pk)
    fotos = db.buscar_fotos(pk)
    observacoes = [h for h in historicos if h.observacao]

    if form_status_erro:
        form_status = form_status_erro
    else:
        # Pre-preenche o form com status e resolucao atuais.
        form_status = EquipeStatusForm(
            initial={
                "id_status": ch.status_atual,
                "resolucao": ch.resolucao or "",
            }
        )

    # Prioridades para o select no template.
    PRIORIDADES = [
        (0, "0 — Sem classificacao"),
        (1, "1 — Muito baixa"),
        (2, "2 — Baixa"),
        (3, "3 — Media"),
        (4, "4 — Alta"),
        (5, "5 — Urgente"),
    ]

    # Mapa PK → sigla para o JavaScript saber quais status sao finais.
    # Usado no frontend para mostrar/ocultar o campo de resolucao.
    with connection.cursor() as cursor:
        cursor.execute("SELECT id_status, sigla FROM status_chamado")
        status_sigla_map = {r[0]: r[1].strip() for r in cursor.fetchall()}

    return render(
        request,
        "portal/equipe/chamado_detalhe.html",
        {
            "ch": ch,
            "dias_aberto": dias_aberto,
            "sigla_status": ts,
            "pode_status": pode_status,
            "bloqueia_status_col": bloqueia_status_col,
            "historicos": historicos,
            "fotos": fotos,
            "observacoes": observacoes,
            "form_status": form_status,
            "form_obs": ObservacaoForm(),
            "form_foto": FotoForm(),
            "prioridades": PRIORIDADES,
            "status_sigla_map_json": json.dumps(status_sigla_map),
        },
    )


# ------------------------------------------------------------------
# Excluir chamado (POST /equipe/chamados/<pk>/excluir/)
# ------------------------------------------------------------------

@perfis("GES")
@require_http_methods(["POST"])
def gestao_chamado_excluir(request, pk):
    """Exclui permanentemente um chamado (apenas gestores).

    A exclusao requer justificativa obrigatoria e segue estes passos:
    1. Verifica se o chamado existe.
    2. Ativa a flag portal.excluindo na sessao PostgreSQL para permitir
       que os triggers de protecao (fn_historico_sem_delete) deixem
       o DELETE passar. Sem essa flag, os triggers bloqueiam.
    3. Registra log de auditoria no historico com a justificativa.
    4. Deleta em cascata manual: fotos, historicos, notificacoes e
       o chamado. A ordem importa por causa das foreign keys.

    Tudo acontece dentro de transaction.atomic() — se qualquer passo
    falhar, tudo eh desfeito.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_chamado, num_protocolo FROM chamado "
            "WHERE id_chamado = %s",
            [pk],
        )
        row = cursor.fetchone()
    if not row:
        raise Http404()

    protocolo = row[1]
    justificativa = (request.POST.get("justificativa") or "").strip()

    if not justificativa:
        messages.error(request, "É obrigatório informar uma justificativa para excluir o chamado.")
        return redirect("portal:equipe_chamado", pk=pk)

    with transaction.atomic():
        with connection.cursor() as cursor:
            # Ativa bypass dos triggers de protecao DELETE.
            # O terceiro parametro (true) indica que a config vale
            # para toda a transacao atual (nao so esta query).
            cursor.execute("SELECT set_config('portal.excluindo', 'true', true)")

            # Busca o status atual para incluir no log de auditoria.
            cursor.execute(
                "SELECT hc.id_status FROM historico_chamado hc "
                "WHERE hc.id_chamado = %s "
                "ORDER BY hc.dt_alteracao DESC LIMIT 1",
                [pk],
            )
            st_row = cursor.fetchone()
            status_id = st_row[0] if st_row else None

            # Registra a exclusao no historico antes de deletar.
            # O prefixo [EXCL] facilita buscas de auditoria futuras.
            cursor.execute(
                "INSERT INTO historico_chamado "
                "(id_chamado, id_servidor, id_status, observacao, dt_alteracao) "
                "VALUES (%s, %s, %s, %s, %s)",
                [pk, request.portal_user.pk, status_id,
                 f"[EXCL] Chamado excluído. Justificativa: {justificativa}",
                 timezone.now()],
            )

            # Delete em cascata manual (ordem respeita as FKs).
            cursor.execute("DELETE FROM foto_chamado WHERE id_chamado = %s", [pk])
            cursor.execute("DELETE FROM historico_chamado WHERE id_chamado = %s", [pk])
            cursor.execute("DELETE FROM notificacao WHERE id_chamado = %s", [pk])
            cursor.execute("DELETE FROM chamado WHERE id_chamado = %s", [pk])

    messages.success(request, f"Chamado {protocolo} excluído com sucesso.")
    return redirect("portal:equipe_chamados")


# ------------------------------------------------------------------
# Dashboard com graficos (GET /equipe/)
# ------------------------------------------------------------------

@perfis("COL", "GES")
@require_http_methods(["GET"])
def equipe_dashboard(request):
    """Dashboard com metricas e dados para graficos (Chart.js).

    Gera quatro metricas:
    - atendidas_hoje: chamados concluidos hoje (dt_conclusao = hoje)
    - atendidas_semana: chamados concluidos nos ultimos 7 dias
    - status_labels/data: distribuicao por status (para grafico de pizza)
    - bairros_labels/data: top 10 bairros com mais chamados (para barras)

    O campo dt_conclusao eh preenchido automaticamente pelo Trigger 2B
    quando um INSERT em historico_chamado tem status CO ou CA. Nao eh
    setado manualmente pelo codigo Python.
    """
    agora = timezone.now()
    hoje = agora.date()
    inicio_semana = hoje - timedelta(days=7)

    with connection.cursor() as cursor:
        # Chamados concluidos hoje.
        # Subquery verifica se o ultimo historico tem sigla "CO".
        cursor.execute('''
            SELECT COUNT(*) FROM chamado c
            WHERE (
                SELECT sc.sigla FROM historico_chamado hc
                JOIN status_chamado sc ON hc.id_status = sc.id_status
                WHERE hc.id_chamado = c.id_chamado
                ORDER BY hc.dt_alteracao DESC LIMIT 1
            ) = 'CO'
            AND c.dt_conclusao::date = %s
        ''', [hoje])
        atendidas_hoje = cursor.fetchone()[0] or 0

        # Chamados concluidos nos ultimos 7 dias.
        cursor.execute('''
            SELECT COUNT(*) FROM chamado c
            WHERE (
                SELECT sc.sigla FROM historico_chamado hc
                JOIN status_chamado sc ON hc.id_status = sc.id_status
                WHERE hc.id_chamado = c.id_chamado
                ORDER BY hc.dt_alteracao DESC LIMIT 1
            ) = 'CO'
            AND c.dt_conclusao::date >= %s
        ''', [inicio_semana])
        atendidas_semana = cursor.fetchone()[0] or 0

        # Distribuicao por status (para grafico de pizza/barras).
        cursor.execute('''
            SELECT sc.descricao, COUNT(c.id_chamado)
            FROM chamado c
            JOIN historico_chamado hc ON hc.id_chamado = c.id_chamado
            JOIN status_chamado sc ON sc.id_status = hc.id_status
            WHERE hc.id_historico_chamado = (
                SELECT id_historico_chamado FROM historico_chamado
                WHERE id_chamado = c.id_chamado
                ORDER BY dt_alteracao DESC LIMIT 1
            )
            GROUP BY sc.descricao
        ''')
        status_geral_rows = cursor.fetchall()
        status_labels = [row[0] for row in status_geral_rows]
        status_data = [row[1] for row in status_geral_rows]

        # Top 10 bairros com mais chamados.
        cursor.execute('''
            SELECT b.nome_bairro, COUNT(c.id_chamado) as qtd
            FROM chamado c
            JOIN bairro b ON c.id_bairro = b.id_bairro
            GROUP BY b.nome_bairro
            ORDER BY qtd DESC
            LIMIT 10
        ''')
        bairros_rows = cursor.fetchall()
        bairros_labels = [row[0] for row in bairros_rows]
        bairros_data = [row[1] for row in bairros_rows]

    # Converte listas para JSON (consumido pelo Chart.js no template).
    context = {
        'atendidas_hoje': atendidas_hoje,
        'atendidas_semana': atendidas_semana,
        'status_labels_json': json.dumps(status_labels),
        'status_data_json': json.dumps(status_data),
        'bairros_labels_json': json.dumps(bairros_labels),
        'bairros_data_json': json.dumps(bairros_data),
    }

    return render(request, "portal/equipe/estatisticas_graficos.html", context)
