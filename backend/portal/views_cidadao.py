"""
views_cidadao.py — Views do Cidadao (Portal VG 24H)

[!] PONTOS CRITICOS:
    1. @perfis("CID") — APENAS cidadaos acessam. COL/GES sao bloqueados.
    2. [!] O status NAO esta em chamado — vem do ULTIMO historico_chamado via Subquery.
    3. [!] Ao abrir chamado, a view NAO insere status — o Trigger 1 cria AB automaticamente.
    4. [!] Privacidade: cada cidadao ve APENAS seus proprios chamados (WHERE id_cidadao = %s).

Operacoes:
  - CREATE: Abrir novo chamado (INSERT em chamado + Trigger 1 cria historico AB)
  - READ:   Listar chamados (SELECT com Subquery no ultimo historico)
  - UPDATE: Cancelar (INSERT historico CA), avaliar (UPDATE chamado), adicionar obs
"""

from types import SimpleNamespace

from django.contrib import messages
from django.db import connection
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from portal import db
from portal.decorators import autenticado, perfis
from portal.forms import (
    AvaliacaoForm,
    CancelarChamadoForm,
    ChamadoNovoForm,
    FotoForm,
    ObservacaoForm,
)
from portal.utils import proximo_protocolo, salvar_foto_upload

# ─── Helpers ─────────────────────────────────────────────────

# FUNCAO AUXILIAR DE SEGURANCA:
# [!] Verifica se o chamado pertence ao cidadao logado.
# Impede que um cidadao acesse chamados de outros cidadaos pela URL.
# Retorna 404 (em vez de 403) para nao revelar se o chamado existe.
def _chamado_do_cidadao(request, pk):
    ch = db.buscar_chamado(pk)
    if not ch:
        raise Http404()
    if ch.id_cidadao_id != request.portal_user.pk:
        raise Http404()
    return ch


# LISTAR CHAMADOS DO CIDADÃO — Rota: /cidadao/chamados/
@autenticado
@perfis("CID")
def cidadao_chamados_lista(request):
    uid = request.portal_user.pk

    # SQL puro: SELECT chamados do cidadão com JOIN em serviço e bairro
    sql = (
        "SELECT c.id_chamado, c.num_protocolo, c.prioridade, "
        "c.descricao, c.dt_abertura, c.atualizado_em, "
        "c.id_servico, c.id_bairro, "
        "s.nome AS servico_nome, s.prazo_amarelo_dias, s.prazo_vermelho_dias, "
        "b.nome_bairro, "
        "("
        "  SELECT sc.sigla FROM historico_chamado hc "
        "  JOIN status_chamado sc ON hc.id_status = sc.id_status "
        "  WHERE hc.id_chamado = c.id_chamado "
        "  ORDER BY hc.dt_alteracao DESC LIMIT 1"
        ") AS sigla_status, "
        "("
        "  SELECT sc.descricao FROM historico_chamado hc "
        "  JOIN status_chamado sc ON hc.id_status = sc.id_status "
        "  WHERE hc.id_chamado = c.id_chamado "
        "  ORDER BY hc.dt_alteracao DESC LIMIT 1"
        ") AS status_descricao "
        "FROM chamado c "
        "JOIN servico s ON c.id_servico = s.id_servico "
        "JOIN bairro b ON c.id_bairro = b.id_bairro "
        "WHERE c.id_cidadao = %s "
    )
    params = [uid]

    # Filtros
    st_filter = request.GET.get("status")
    if st_filter:
        sql += (
            "AND ("
            "  SELECT sc2.sigla FROM historico_chamado hc2 "
            "  JOIN status_chamado sc2 ON hc2.id_status = sc2.id_status "
            "  WHERE hc2.id_chamado = c.id_chamado "
            "  ORDER BY hc2.dt_alteracao DESC LIMIT 1"
            ") = %s "
        )
        params.append(st_filter)

    dt_filter = request.GET.get("data")
    if dt_filter:
        sql += "AND c.dt_abertura::date = %s "
        params.append(dt_filter)

    q_filter = request.GET.get("q")
    if q_filter:
        sql += "AND c.num_protocolo ILIKE %s "
        params.append(f"%{q_filter}%")

    sql += "ORDER BY c.dt_abertura DESC"

    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        rows = cursor.fetchall()

    # Monta lista de objetos para o template
    now = timezone.now()
    chamados = []
    for r in rows:
        dias = (now - r[4]).days
        if dias >= r[10]:
            cor = "vermelho"
        elif dias >= r[9]:
            cor = "amarelo"
        else:
            cor = "verde"
        sigla = r[12] or ""
        status_desc = r[13] or sigla
        chamados.append(SimpleNamespace(
            id_chamado=r[0], pk=r[0], num_protocolo=r[1], prioridade=r[2],
            descricao=r[3], dt_abertura=r[4], atualizado_em=r[5],
            id_servico=SimpleNamespace(id_servico=r[6], pk=r[6], nome=r[8]),
            id_bairro=SimpleNamespace(id_bairro=r[7], pk=r[7], nome_bairro=r[11]),
            sigla_status=sigla, cor_semaforo=cor,
            status_atual=SimpleNamespace(sigla=sigla, descricao=status_desc),
        ))

    # Paginacao (via db.paginar)
    page_obj, total_count = db.paginar(
        chamados, request.GET.get("pagina", 1), por_pagina=15,
    )

    # Stats (Semáforo) — via db.calcular_stats_semaforo
    stats = db.calcular_stats_semaforo(cidadao_id=uid)

    return render(
        request,
        "portal/cidadao/dashboard.html",
        {"lista": page_obj, "total_count": total_count, "page_obj": page_obj, "stats": stats},
    )


@autenticado
@perfis("CID")
@require_http_methods(["GET", "POST"])
def cidadao_chamado_novo(request):
    # SQL puro: busca categorias com seus serviços
    categorias_list = []
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_categoria, nome, descricao "
            "FROM categoria_servico WHERE ativo = TRUE "
            "ORDER BY nome"
        )
        cats = cursor.fetchall()
        for cat_row in cats:
            cat = SimpleNamespace(id_categoria=cat_row[0], pk=cat_row[0], nome=cat_row[1], descricao=cat_row[2])
            cursor.execute(
                "SELECT id_servico, nome "
                "FROM servico "
                "WHERE id_categoria = %s AND ativo = TRUE ORDER BY nome",
                [cat.pk],
            )
            cat.servicos = SimpleNamespace(all=lambda rows=[
                SimpleNamespace(id_servico=r[0], pk=r[0], nome=r[1]) for r in cursor.fetchall()
            ]: rows)
            categorias_list.append(cat)

    # SQL puro: busca bairros ativos
    bairros = []
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_bairro, nome_bairro FROM bairro "
            "WHERE ativo = TRUE ORDER BY nome_bairro"
        )
        bairros = [
            SimpleNamespace(id_bairro=r[0], pk=r[0], nome_bairro=r[1])
            for r in cursor.fetchall()
        ]

    if request.method == "POST":
        form = ChamadoNovoForm(request.POST, request.FILES)
        if form.is_valid():
            d = form.cleaned_data
            try:
                url = salvar_foto_upload(request.FILES.get("foto"), request=request)
            except ValueError as e:
                messages.error(request, str(e))
                return render(
                    request,
                    "portal/cidadao/novo_chamado.html",
                    {"form": form, "categorias": categorias_list, "bairros": bairros},
                )
            now = timezone.now()
            protocolo = proximo_protocolo()
            # SQL puro: INSERT na tabela chamado + foto_chamado (transação)
            with connection.cursor() as cursor:
                # [!] INSERT apenas em chamado. NAO insere status!
                #     O Trigger 1 (AFTER INSERT) cria automaticamente o
                #     registro em historico_chamado com status 'AB'.
                cursor.execute(
                    "INSERT INTO chamado "
                    "(num_protocolo, prioridade, ponto_de_referencia, descricao, "
                    "dt_abertura, atualizado_em, id_cidadao, id_servico, id_bairro) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) "
                    "RETURNING id_chamado",            # [!] RETURNING necessario para obter o ID
                    [
                        protocolo, 0,
                        d.get("ponto_de_referencia") or None,
                        d["descricao"], now, now,
                        request.portal_user.pk,
                        d["id_servico"].pk,
                        d["id_bairro"].pk,
                    ],
                )
                chamado_id = cursor.fetchone()[0]       # ID gerado pelo SERIAL
                # INSERT foto do chamado
                cursor.execute(
                    "INSERT INTO foto_chamado (id_chamado, url_foto, dt_upload) "
                    "VALUES (%s, %s, %s)",
                    [chamado_id, url, now],
                )
            messages.success(
                request,
                f"Chamado aberto. Protocolo: {protocolo}",
            )
            return redirect("portal:cidadao_chamado", pk=chamado_id)
    else:
        form = ChamadoNovoForm()
    return render(
        request,
        "portal/cidadao/novo_chamado.html",
        {"form": form, "categorias": categorias_list, "bairros": bairros},
    )


@autenticado
@perfis("CID")
@require_http_methods(["GET", "POST"])
def cidadao_chamado_detalhe(request, pk):
    """
    [!] ACOES DISPONIVEIS (campo 'acao' no POST):
        1. 'obs'      — INSERT em historico_chamado (observacao)
        2. 'foto'     — INSERT em foto_chamado
        3. 'cancelar' — INSERT historico com status CA + UPDATE resolucao
        4. 'avaliar'  — UPDATE chamado (nota_avaliacao + comentario)

    [!] REGRAS DE NEGOCIO:
        - Obs/foto: bloqueadas se chamado estiver CO ou CA
        - Cancelar: so se AB ou EA
        - Avaliar: so se CO e nunca avaliado
        - Triggers no BD (R1/R2) tambem bloqueiam obs/foto em CO/CA
    """
    ch = _chamado_do_cidadao(request, pk)
    ts = ch.sigla_status
    pode_obs_foto = ts not in ("CO", "CA")
    pode_cancelar = ts in ("AB", "EA")
    pode_avaliar = ts == "CO" and ch.nota_avaliacao is None

    if request.method == "POST":
        acao = request.POST.get("acao")
        if acao == "obs" and pode_obs_foto:
            form_o = ObservacaoForm(request.POST)
            if form_o.is_valid():
                # SQL puro: INSERT observação no historico_chamado
                status_id = ch.status_atual.pk if ch.status_atual else None
                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO historico_chamado "
                        "(id_chamado, id_servidor, id_status, observacao, dt_alteracao) "
                        "VALUES (%s, %s, %s, %s, %s)",
                        [pk, None, status_id, form_o.cleaned_data["texto"], timezone.now()],
                    )
                messages.success(request, "Observação registrada.")
            return redirect("portal:cidadao_chamado", pk=pk)
        if acao == "foto" and pode_obs_foto:
            form_f = FotoForm(request.POST, request.FILES)
            if form_f.is_valid() and request.FILES.get("foto"):
                try:
                    url = salvar_foto_upload(request.FILES["foto"], request=request)
                except ValueError as e:
                    messages.error(request, str(e))
                else:
                    # SQL puro: INSERT foto no foto_chamado
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "INSERT INTO foto_chamado (id_chamado, url_foto, dt_upload) "
                            "VALUES (%s, %s, %s)",
                            [pk, url, timezone.now()],
                        )
                    messages.success(request, "Foto adicionada.")
            return redirect("portal:cidadao_chamado", pk=pk)
        if acao == "cancelar" and pode_cancelar:
            form_c = CancelarChamadoForm(request.POST)
            if form_c.is_valid():
                # SQL puro: busca o id do status 'CA' (Cancelado)
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT id_status FROM status_chamado WHERE sigla = 'CA'"
                    )
                    ca_id = cursor.fetchone()[0]
                    # [!] INSERT historico com status CA
                    #     Trigger 2B: atualiza dt_conclusao + gera notificacao
                    cursor.execute(
                        "INSERT INTO historico_chamado "
                        "(id_chamado, id_servidor, id_status, observacao, dt_alteracao) "
                        "VALUES (%s, %s, %s, %s, %s)",
                        [pk, None, ca_id, form_c.cleaned_data["motivo"], timezone.now()],
                    )
                    # UPDATE resolucao do chamado
                    cursor.execute(
                        "UPDATE chamado SET resolucao = %s WHERE id_chamado = %s",
                        [form_c.cleaned_data["motivo"], pk],
                    )
                messages.success(request, "Chamado cancelado.")
            return redirect("portal:cidadao_chamado", pk=pk)
        if acao == "avaliar" and pode_avaliar:
            form_a = AvaliacaoForm(request.POST)
            if form_a.is_valid():
                # SQL puro: UPDATE avaliação do chamado
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE chamado SET nota_avaliacao = %s, "
                        "comentario_avaliacao = %s, dt_avaliacao = %s "
                        "WHERE id_chamado = %s",
                        [
                            form_a.cleaned_data["nota"],
                            form_a.cleaned_data.get("comentario") or None,
                            timezone.now(),
                            pk,
                        ],
                    )
                messages.success(request, "Avaliação registrada.")
            return redirect("portal:cidadao_chamado", pk=pk)

    # SQL puro: busca historicos e fotos (via db.py)
    historicos = db.buscar_historicos(pk)
    fotos = db.buscar_fotos(pk)

    # Observações = registros com observacao preenchida
    observacoes = [h for h in historicos if h.observacao]

    return render(
        request,
        "portal/cidadao/chamado_detalhe.html",
        {
            "ch": ch,
            "historicos": historicos,
            "fotos": fotos,
            "observacoes": observacoes,
            "sigla_status": ts,
            "pode_obs_foto": pode_obs_foto,
            "pode_cancelar": pode_cancelar,
            "pode_avaliar": pode_avaliar,
            "form_obs": ObservacaoForm(),
            "form_foto": FotoForm(),
            "form_cancelar": CancelarChamadoForm(),
            "form_avaliar": AvaliacaoForm(),
        },
    )


@autenticado
@perfis("CID")
@require_http_methods(["GET", "POST"])
def cidadao_notificacoes(request):
    uid = request.portal_user.pk
    # SQL puro: busca notificações dos chamados do cidadão
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT n.id_notificacao, n.mensagem, n.lida, n.arquivada, "
            "n.dt_envio, n.id_chamado "
            "FROM notificacao n "
            "WHERE n.arquivada = FALSE "
            "AND n.id_chamado IN ("
            "    SELECT c.id_chamado FROM chamado c WHERE c.id_cidadao = %s"
            ") "
            "ORDER BY n.dt_envio DESC",
            [uid],
        )
        lista = [
            SimpleNamespace(
                id_notificacao=r[0], pk=r[0], mensagem=r[1],
                lida=r[2], arquivada=r[3], dt_envio=r[4], id_chamado_id=r[5],
            )
            for r in cursor.fetchall()
        ]

    if request.method == "POST":
        nid = request.POST.get("excluir")
        if nid:
            # SQL puro: DELETE notificação (apenas se pertence a um chamado do cidadão)
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM notificacao "
                    "WHERE id_notificacao = %s "
                    "AND id_chamado IN ("
                    "    SELECT c.id_chamado FROM chamado c WHERE c.id_cidadao = %s"
                    ")",
                    [nid, uid],
                )
            messages.info(request, "Notificação removida.")
        return redirect("portal:cidadao_notificacoes")
    return render(
        request,
        "portal/cidadao/notificacoes.html",
        {"lista": lista},
    )
