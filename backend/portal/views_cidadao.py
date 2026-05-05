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

from portal.decorators import autenticado, perfis
from portal.forms import (
    AvaliacaoForm,
    CancelarChamadoForm,
    ChamadoNovoForm,
    FotoForm,
    ObservacaoForm,
)
from portal.utils import proximo_protocolo, salvar_foto_upload


# ─── Helpers SQL ─────────────────────────────────────────────
def _buscar_chamado_por_pk(pk):
    """SQL puro: busca um chamado pelo ID com dados do serviço e bairro (JOIN)."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT c.id_chamado, c.num_protocolo, c.prioridade, "
            "c.ponto_de_referencia, c.descricao, c.resolucao, "
            "c.nota_avaliacao, c.comentario_avaliacao, "
            "c.dt_abertura, c.dt_conclusao, c.dt_avaliacao, c.atualizado_em, "
            "c.id_servico, c.id_bairro, c.id_cidadao, "
            "s.nome AS servico_nome, s.descricao AS servico_descricao, "
            "s.prazo_amarelo_dias, s.prazo_vermelho_dias, "
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
    ch = SimpleNamespace(
        id_chamado=row[0], pk=row[0], num_protocolo=row[1], prioridade=row[2],
        ponto_de_referencia=row[3], descricao=row[4], resolucao=row[5],
        nota_avaliacao=row[6], comentario_avaliacao=row[7],
        dt_abertura=row[8], dt_conclusao=row[9], dt_avaliacao=row[10],
        atualizado_em=row[11], id_cidadao_id=row[14],
        id_servico=SimpleNamespace(
            id_servico=row[12], pk=row[12], nome=row[15],
            descricao=row[16], prazo_amarelo_dias=row[17],
            prazo_vermelho_dias=row[18],
        ),
        id_bairro=SimpleNamespace(id_bairro=row[13], pk=row[13], nome_bairro=row[19]),
    )
    # Calcula status atual e cor do semáforo
    _popular_status(ch)
    return ch


def _popular_status(ch):
    """
    [!] SQL puro: busca o status ATUAL do chamado via ULTIMO historico.
    Equivalente funcional da property status_atual em models.py (usada em Rafael).
    """
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT sc.id_status, sc.sigla, sc.descricao "
            "FROM historico_chamado hc "
            "JOIN status_chamado sc ON hc.id_status = sc.id_status "
            "WHERE hc.id_chamado = %s "
            "ORDER BY hc.dt_alteracao DESC LIMIT 1",  # [!] Pega o registro mais recente
            [ch.pk],
        )
        row = cursor.fetchone()
    if row:
        ch.status_atual = SimpleNamespace(id_status=row[0], pk=row[0], sigla=row[1], descricao=row[2])
        ch.sigla_status = (row[1] or "").strip()     # Ex: 'AB', 'CO'
    else:
        ch.status_atual = None
        ch.sigla_status = ""
    # Semáforo
    dias = (timezone.now() - ch.dt_abertura).days
    if dias >= ch.id_servico.prazo_vermelho_dias:
        ch.cor_semaforo = "vermelho"
    elif dias >= ch.id_servico.prazo_amarelo_dias:
        ch.cor_semaforo = "amarelo"
    else:
        ch.cor_semaforo = "verde"


# FUNCAO AUXILIAR DE SEGURANCA:
# [!] Verifica se o chamado pertence ao cidadao logado.
# Impede que um cidadao acesse chamados de outros cidadaos pela URL.
# Retorna 404 (em vez de 403) para nao revelar se o chamado existe.
def _chamado_do_cidadao(request, pk):
    ch = _buscar_chamado_por_pk(pk)
    if not ch:
        raise Http404()
    if ch.id_cidadao_id != request.portal_user.pk:
        raise Http404()
    return ch


def _calcular_stats_sql(cidadao_id=None):
    """SQL puro: calcula estatísticas do semáforo (no_prazo, atencao, critico)."""
    where = ""
    params = []
    if cidadao_id:
        where = "WHERE c.id_cidadao = %s"
        params = [cidadao_id]
    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT c.id_chamado, c.dt_abertura, "
            f"s.prazo_amarelo_dias, s.prazo_vermelho_dias "
            f"FROM chamado c "
            f"JOIN servico s ON c.id_servico = s.id_servico "
            f"{where}",
            params,
        )
        stats = {"no_prazo": 0, "atencao": 0, "critico": 0}
        now = timezone.now()
        for row in cursor.fetchall():
            dias = (now - row[1]).days
            if dias >= row[3]:
                stats["critico"] += 1
            elif dias >= row[2]:
                stats["atencao"] += 1
            else:
                stats["no_prazo"] += 1
    return stats


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
        ") AS sigla_status "
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
        chamados.append(SimpleNamespace(
            id_chamado=r[0], pk=r[0], num_protocolo=r[1], prioridade=r[2],
            descricao=r[3], dt_abertura=r[4], atualizado_em=r[5],
            id_servico=SimpleNamespace(id_servico=r[6], pk=r[6], nome=r[8]),
            id_bairro=SimpleNamespace(id_bairro=r[7], pk=r[7], nome_bairro=r[11]),
            sigla_status=r[12] or "", cor_semaforo=cor,
        ))

    # Paginação manual
    total_count = len(chamados)
    per_page = 15
    try:
        page_number = int(request.GET.get("pagina", 1))
    except (ValueError, TypeError):
        page_number = 1
    total_pages = max(1, (total_count + per_page - 1) // per_page)
    page_number = max(1, min(page_number, total_pages))
    start = (page_number - 1) * per_page
    end = start + per_page
    page_items = chamados[start:end]

    page_obj = SimpleNamespace(
        object_list=page_items,
        number=page_number,
        paginator=SimpleNamespace(num_pages=total_pages, page_range=range(1, total_pages + 1)),
        has_previous=page_number > 1,
        has_next=page_number < total_pages,
        previous_page_number=page_number - 1 if page_number > 1 else None,
        next_page_number=page_number + 1 if page_number < total_pages else None,
    )
    # Tornar page_obj iterável (para {% for ch in lista %})
    page_obj.__iter__ = lambda self: iter(self.object_list)
    page_obj.__len__ = lambda self: len(self.object_list)

    # Stats (Semáforo)
    stats = _calcular_stats_sql(cidadao_id=uid)

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

    # SQL puro: busca históricos do chamado com JOIN em servidor e status
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
            [pk],
        )
        historicos = [
            SimpleNamespace(
                id_historico_chamado=r[0], pk=r[0], dt_alteracao=r[1],
                observacao=r[2], id_servidor_id=r[3],
                id_servidor=SimpleNamespace(nome_completo=r[5]) if r[3] else None,
                id_status=SimpleNamespace(id_status=r[4], sigla=r[6], descricao=r[7]),
            )
            for r in cursor.fetchall()
        ]

        # SQL puro: busca fotos do chamado
        cursor.execute(
            "SELECT id_foto, url_foto, dt_upload "
            "FROM foto_chamado WHERE id_chamado = %s "
            "ORDER BY dt_upload",
            [pk],
        )
        fotos = [
            SimpleNamespace(id_foto=r[0], pk=r[0], url_foto=r[1], dt_upload=r[2])
            for r in cursor.fetchall()
        ]

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
