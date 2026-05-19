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


# ═══════════════════════════════════════════════════════════════
# READ — Listar chamados do cidadao — Rota: /cidadao/chamados/
# ═══════════════════════════════════════════════════════════════
# [!] Fluxo: URL → @perfis('CID') → monta SQL dinamico → cursor.execute
#     → tuplas → SimpleNamespace (hidratacao) → semaforo → paginacao → template
@autenticado
@perfis("CID")
def cidadao_chamados_lista(request):
    uid = request.portal_user.pk

    # SQL puro: SELECT com JOINs (chamado + servico + bairro)
    # [!] 2 subqueries correlatas buscam o status ATUAL de cada chamado
    #     via historico_chamado (ORDER BY DESC LIMIT 1 = registro mais recente)
    #     Subquery 1: sigla do status (ex: 'AB', 'CO')
    #     Subquery 2: descricao do status (ex: 'Aberto', 'Concluido')
    # [!] WHERE c.id_cidadao = %s garante privacidade (so ve os proprios chamados)
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

    # Filtros dinamicos: concatenam AND ao SQL base se o usuario selecionou
    # [!] Cada filtro e opcional — se nao informado, o IF e ignorado
    st_filter = request.GET.get("status")       # Filtro por sigla de status (ex: 'AB')
    if st_filter:
        # Subquery para filtrar pelo status ATUAL (ultimo historico)
        sql += (
            "AND ("
            "  SELECT sc2.sigla FROM historico_chamado hc2 "
            "  JOIN status_chamado sc2 ON hc2.id_status = sc2.id_status "
            "  WHERE hc2.id_chamado = c.id_chamado "
            "  ORDER BY hc2.dt_alteracao DESC LIMIT 1"
            ") = %s "
        )
        params.append(st_filter)

    dt_filter = request.GET.get("data")          # Filtro por data de abertura
    if dt_filter:
        sql += "AND c.dt_abertura::date = %s "   # ::date = cast para comparar so o dia
        params.append(dt_filter)

    q_filter = request.GET.get("q")              # Busca por protocolo (parcial)
    if q_filter:
        sql += "AND c.num_protocolo ILIKE %s "   # ILIKE = case-insensitive LIKE
        params.append(f"%{q_filter}%")

    sql += "ORDER BY c.dt_abertura DESC"

    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        rows = cursor.fetchall()

    # HIDRATACAO: converte tuplas do banco em objetos SimpleNamespace
    # [!] r[0], r[1]... sao posicionais — a ordem depende do SELECT acima
    #     SimpleNamespace permite {{ ch.num_protocolo }} nos templates
    now = timezone.now()
    chamados = []
    for r in rows:
        # SEMAFORO: classifica urgencia com base nos prazos do servico
        # r[4]=dt_abertura, r[9]=prazo_amarelo, r[10]=prazo_vermelho
        dias = (now - r[4]).days
        if dias >= r[10]:
            cor = "vermelho"    # Critico: ultrapassou prazo_vermelho_dias
        elif dias >= r[9]:
            cor = "amarelo"     # Atencao: ultrapassou prazo_amarelo_dias
        else:
            cor = "verde"       # No prazo
        sigla = r[12] or ""     # r[12] = resultado da subquery sigla_status
        status_desc = r[13] or sigla  # r[13] = resultado da subquery status_descricao
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


# ═══════════════════════════════════════════════════════════════
# CREATE — Abrir novo chamado — Rota: /cidadao/chamados/novo/
# ═══════════════════════════════════════════════════════════════
# [!] Fluxo CREATE:
#     1. GET → mostra formulario (categorias + servicos + bairros do banco)
#     2. POST → valida form → INSERT chamado → Trigger 1 cria status AB
#                           → INSERT foto_chamado → redirect detalhe
@autenticado
@perfis("CID")
@require_http_methods(["GET", "POST"])
def cidadao_chamado_novo(request):
    # SQL puro: busca categorias com seus servicos (para popular o formulario)
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
            protocolo = proximo_protocolo()  # Gera num sequencial: "2026000001"
            # SQL puro: INSERT chamado + INSERT foto (dentro da mesma transacao Django)
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


# ═══════════════════════════════════════════════════════════════
# UPDATE — Detalhe do chamado + acoes — Rota: /cidadao/chamados/<pk>/
# ═══════════════════════════════════════════════════════════════
# [!] GET: exibe detalhe (via db.buscar_chamado → SELECT com JOINs)
# [!] POST: executa acao conforme campo 'acao' do formulario:
#     'obs'      → INSERT historico_chamado (observacao do cidadao)
#     'foto'     → INSERT foto_chamado (upload de imagem)
#     'cancelar' → INSERT historico CA + UPDATE resolucao (muda status para Cancelado)
#     'avaliar'  → UPDATE chamado (nota 1-5 + comentario, so se status=CO)
@autenticado
@perfis("CID")
@require_http_methods(["GET", "POST"])
def cidadao_chamado_detalhe(request, pk):
    ch = _chamado_do_cidadao(request, pk)  # Busca + verifica se pertence ao cidadao
    ts = ch.sigla_status                   # Status atual (ex: 'AB', 'CO', 'CA')
    # Regras de negocio: o que o cidadao pode fazer depende do status atual
    pode_obs_foto = ts not in ("CO", "CA")           # Chamado encerrado? Bloqueia obs/foto
    pode_cancelar = ts in ("AB", "EA")                # So cancela se aberto ou em atendimento
    pode_avaliar = ts == "CO" and ch.nota_avaliacao is None  # So avalia se concluido e nunca avaliado

    if request.method == "POST":
        acao = request.POST.get("acao")
        if acao == "obs" and pode_obs_foto:
            form_o = ObservacaoForm(request.POST)
            if form_o.is_valid():
                # INSERT observacao: mantem o status atual, apenas adiciona texto
                # [!] id_servidor=None porque quem escreveu foi o cidadao (nao e servidor)
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
                with connection.cursor() as cursor:
                    # Busca o ID do status 'CA' na tabela status_chamado
                    cursor.execute(
                        "SELECT id_status FROM status_chamado WHERE sigla = 'CA'"
                    )
                    ca_id = cursor.fetchone()[0]
                    # INSERT historico com status CA → muda o status para Cancelado
                    # [!] Trigger 2B dispara automaticamente:
                    #     → UPDATE chamado SET dt_conclusao = NOW()
                    #     → INSERT notificacao ("Chamado XXXX: status alterado para Cancelado")
                    cursor.execute(
                        "INSERT INTO historico_chamado "
                        "(id_chamado, id_servidor, id_status, observacao, dt_alteracao) "
                        "VALUES (%s, %s, %s, %s, %s)",
                        [pk, None, ca_id, form_c.cleaned_data["motivo"], timezone.now()],
                    )
                    # UPDATE resolucao: salva o motivo do cancelamento no chamado
                    # [!] Trigger 2A dispara: atualiza atualizado_em automaticamente
                    cursor.execute(
                        "UPDATE chamado SET resolucao = %s WHERE id_chamado = %s",
                        [form_c.cleaned_data["motivo"], pk],
                    )
                messages.success(request, "Chamado cancelado.")
            return redirect("portal:cidadao_chamado", pk=pk)
        if acao == "avaliar" and pode_avaliar:
            form_a = AvaliacaoForm(request.POST)
            if form_a.is_valid():
                # UPDATE direto na tabela chamado (avaliacao NAO e historico)
                # [!] Trigger 2A dispara: atualiza atualizado_em
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


# ═══════════════════════════════════════════════════════════════
# NOTIFICACOES — Rota: /cidadao/notificacoes/
# ═══════════════════════════════════════════════════════════════
# [!] Notificacoes sao criadas AUTOMATICAMENTE pelo Trigger 2B
#     sempre que um status e alterado. Aqui apenas exibe e exclui.
@autenticado
@perfis("CID")
@require_http_methods(["GET", "POST"])
def cidadao_notificacoes(request):
    uid = request.portal_user.pk
    # SELECT notificacoes nao-arquivadas dos chamados deste cidadao
    # [!] Subquery garante privacidade: so ve notificacoes dos SEUS chamados
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
            # DELETE notificacao — a subquery impede que um cidadao
            # delete notificacao de outro cidadao manipulando o POST
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