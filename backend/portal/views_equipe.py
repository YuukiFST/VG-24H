"""
views_equipe.py — Views da Equipe (Gestores e Colaboradores)

Este módulo contém as views acessíveis apenas por servidores.
O decorador @perfis("COL", "GES") garante que APENAS usuários com perfil
'COL' (Colaborador) ou 'GES' (Gestor) podem acessar estas rotas.
Cidadãos são automaticamente bloqueados.

Diferença chave em relação ao views_cidadao.py:
  - Cidadão vê apenas SEUS próprios chamados (filter id_cidadao=request.portal_user)
  - Equipe vê TODOS os chamados do sistema (sem filtro de cidadão)
"""

from types import SimpleNamespace

from django.contrib import messages
from django.db import connection
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from portal.decorators import perfil_codigo, perfis
from portal.forms import EquipeStatusForm, FotoForm, ObservacaoForm
from portal.utils import salvar_foto_upload


def _int_none(v):
    if v is None or v == "":
        return None
    try:
        return int(v)
    except ValueError:
        return None


def _calcular_stats_sql():
    """SQL puro: calcula estatísticas do semáforo para TODOS os chamados."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT c.id_chamado, c.dt_abertura, "
            "s.prazo_amarelo_dias, s.prazo_vermelho_dias "
            "FROM chamado c "
            "JOIN servico s ON c.id_servico = s.id_servico"
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


# LISTAR TODOS OS CHAMADOS — Rota: /equipe/chamados/
# @perfis("COL", "GES") = SÓ colaboradores e gestores podem acessar
# Diferença do cidadão: aqui NÃO filtra por id_cidadao (vê TODOS os chamados)
@perfis("COL", "GES")
def equipe_chamados_lista(request):
    # Stats (Semáforo) — antes de aplicar filtros
    stats = _calcular_stats_sql()

    # SQL puro: SELECT todos os chamados com JOINs
    sql = (
        "SELECT c.id_chamado, c.num_protocolo, c.prioridade, "
        "c.descricao, c.dt_abertura, c.atualizado_em, "
        "c.id_servico, c.id_bairro, c.id_cidadao, "
        "s.nome AS servico_nome, s.prazo_amarelo_dias, s.prazo_vermelho_dias, "
        "b.nome_bairro, "
        "ci.nome_completo AS cidadao_nome, "
        "("
        "  SELECT sc.sigla FROM historico_chamado hc "
        "  JOIN status_chamado sc ON hc.id_status = sc.id_status "
        "  WHERE hc.id_chamado = c.id_chamado "
        "  ORDER BY hc.dt_alteracao DESC LIMIT 1"
        ") AS sigla_status "
        "FROM chamado c "
        "JOIN servico s ON c.id_servico = s.id_servico "
        "JOIN bairro b ON c.id_bairro = b.id_bairro "
        "JOIN cidadao ci ON c.id_cidadao = ci.id_cidadao "
        "WHERE TRUE "
    )
    params = []

    # Filtros
    bairro = _int_none(request.GET.get("bairro"))
    st = _int_none(request.GET.get("status"))
    d0 = request.GET.get("de")
    d1 = request.GET.get("ate")

    if bairro:
        sql += "AND c.id_bairro = %s "
        params.append(bairro)
    if st:
        sql += (
            "AND ("
            "  SELECT hc2.id_status FROM historico_chamado hc2 "
            "  WHERE hc2.id_chamado = c.id_chamado "
            "  ORDER BY hc2.dt_alteracao DESC LIMIT 1"
            ") = %s "
        )
        params.append(st)
    if d0:
        sql += "AND c.dt_abertura::date >= %s "
        params.append(d0)
    if d1:
        sql += "AND c.dt_abertura::date <= %s "
        params.append(d1)

    sql += "ORDER BY c.dt_abertura DESC"

    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        # SQL puro: total de chamados (sem filtros)
        cursor.execute("SELECT COUNT(*) FROM chamado")
        total_count = cursor.fetchone()[0]

    # Monta lista para o template
    now = timezone.now()
    linhas = []
    for r in rows:
        dias = (now - r[4]).days
        if dias >= r[11]:
            cor = "vermelho"
        elif dias >= r[10]:
            cor = "amarelo"
        else:
            cor = "verde"
        ch = SimpleNamespace(
            id_chamado=r[0], pk=r[0], num_protocolo=r[1], prioridade=r[2],
            descricao=r[3], dt_abertura=r[4], atualizado_em=r[5],
            id_servico=SimpleNamespace(id_servico=r[6], pk=r[6], nome=r[9]),
            id_bairro=SimpleNamespace(id_bairro=r[7], pk=r[7], nome_bairro=r[12]),
            id_cidadao=SimpleNamespace(id_cidadao=r[8], pk=r[8], nome_completo=r[13]),
            sigla_status=r[14] or "", cor_semaforo=cor,
        )
        linhas.append({"ch": ch, "cor": cor})

    # SQL puro: busca bairros e statuses para os filtros
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_bairro, nome_bairro FROM bairro "
            "WHERE ativo = TRUE ORDER BY nome_bairro"
        )
        bairros_lista = [
            SimpleNamespace(id_bairro=r[0], pk=r[0], nome_bairro=r[1])
            for r in cursor.fetchall()
        ]
        cursor.execute(
            "SELECT id_status, sigla, descricao "
            "FROM status_chamado ORDER BY id_status"
        )
        statuses_lista = [
            SimpleNamespace(id_status=r[0], pk=r[0], sigla=r[1], descricao=r[2])
            for r in cursor.fetchall()
        ]

    return render(
        request,
        "portal/equipe/dashboard.html",
        {
            "linhas": linhas,
            "stats": stats,
            "total_count": total_count,
            "bairros": bairros_lista,
            "statuses": statuses_lista,
            "filtro_bairro": bairro,
            "filtro_status": st,
            "filtro_de": d0 or "",
            "filtro_ate": d1 or "",
        },
    )


@perfis("COL", "GES")
@require_http_methods(["GET", "POST"])
def equipe_chamado_detalhe(request, pk):
    # SQL puro: busca chamado com JOINs completos
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT c.id_chamado, c.num_protocolo, c.prioridade, "
            "c.ponto_de_referencia, c.descricao, c.resolucao, "
            "c.nota_avaliacao, c.comentario_avaliacao, "
            "c.dt_abertura, c.dt_conclusao, c.dt_avaliacao, c.atualizado_em, "
            "c.id_servico, c.id_bairro, c.id_cidadao, "
            "s.nome AS servico_nome, s.descricao AS servico_descricao, "
            "s.prazo_amarelo_dias, s.prazo_vermelho_dias, "
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

    ch = SimpleNamespace(
        id_chamado=row[0], pk=row[0], num_protocolo=row[1], prioridade=row[2],
        ponto_de_referencia=row[3], descricao=row[4], resolucao=row[5],
        nota_avaliacao=row[6], comentario_avaliacao=row[7],
        dt_abertura=row[8], dt_conclusao=row[9], dt_avaliacao=row[10],
        atualizado_em=row[11],
        id_servico=SimpleNamespace(
            id_servico=row[12], pk=row[12], nome=row[15],
            descricao=row[16], prazo_amarelo_dias=row[17],
            prazo_vermelho_dias=row[18],
            id_categoria=SimpleNamespace(nome=row[23]),
        ),
        id_bairro=SimpleNamespace(id_bairro=row[13], pk=row[13], nome_bairro=row[19]),
        id_cidadao=SimpleNamespace(
            id_cidadao=row[14], pk=row[14], nome_completo=row[20],
            email=row[21], telefone=row[22],
        ),
    )

    # Busca status atual
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT sc.id_status, sc.sigla, sc.descricao "
            "FROM historico_chamado hc "
            "JOIN status_chamado sc ON hc.id_status = sc.id_status "
            "WHERE hc.id_chamado = %s "
            "ORDER BY hc.dt_alteracao DESC LIMIT 1",
            [pk],
        )
        st_row = cursor.fetchone()
    if st_row:
        ch.status_atual = SimpleNamespace(id_status=st_row[0], pk=st_row[0], sigla=st_row[1], descricao=st_row[2])
        ch.sigla_status = (st_row[1] or "").strip()
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

    p = perfil_codigo(request.portal_user)
    ts = ch.sigla_status
    bloqueia_status_col = p == "COL" and ts in ("CO", "CA")
    pode_status = not bloqueia_status_col

    form_status_erro = None
    if request.method == "POST":
        acao = request.POST.get("acao")
        if acao == "status" and pode_status:
            form_s = EquipeStatusForm(request.POST)
            if form_s.is_valid():
                novo = form_s.cleaned_data["id_status"]
                # SQL puro: INSERT historico para mudança de status
                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO historico_chamado "
                        "(id_chamado, id_servidor, id_status, dt_alteracao) "
                        "VALUES (%s, %s, %s, %s)",
                        [pk, request.portal_user.pk, novo.pk, timezone.now()],
                    )
                    # UPDATE resolução e prioridade
                    resolucao = form_s.cleaned_data.get("resolucao") or None
                    pri = request.POST.get("prioridade")
                    prioridade_val = ch.prioridade
                    if pri is not None:
                        try:
                            prioridade_val = max(0, min(5, int(pri)))
                        except (ValueError, TypeError):
                            pass
                    cursor.execute(
                        "UPDATE chamado SET resolucao = %s, prioridade = %s "
                        "WHERE id_chamado = %s",
                        [resolucao, prioridade_val, pk],
                    )
                messages.success(request, "Status atualizado.")
                return redirect("portal:equipe_chamado", pk=pk)
            form_status_erro = form_s
            for e in form_s.non_field_errors():
                messages.error(request, e)
        if acao == "obs":
            form_o = ObservacaoForm(request.POST)
            if form_o.is_valid():
                # SQL puro: INSERT observação no historico_chamado
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
        if acao == "foto":
            if request.FILES.get("foto"):
                form_f = FotoForm(request.POST, request.FILES)
                if form_f.is_valid():
                    try:
                        url = salvar_foto_upload(request.FILES["foto"], request=request)
                    except ValueError as e:
                        messages.error(request, str(e))
                    else:
                        # SQL puro: INSERT foto no foto_chamado
                        with connection.cursor() as cursor:
                            cursor.execute(
                                "INSERT INTO foto_chamado "
                                "(id_chamado, url_foto, dt_upload) "
                                "VALUES (%s, %s, %s)",
                                [pk, url, timezone.now()],
                            )
                        messages.success(request, "Foto registrada.")
            else:
                messages.error(request, "Selecione uma imagem.")
            return redirect("portal:equipe_chamado", pk=pk)

    # SQL puro: busca históricos do chamado com JOINs
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

        # SQL puro: busca fotos
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

    observacoes = [h for h in historicos if h.observacao]

    if form_status_erro:
        form_status = form_status_erro
    else:
        form_status = EquipeStatusForm(
            initial={
                "id_status": ch.status_atual,
                "resolucao": ch.resolucao or "",
            }
        )

    PRIORIDADES = [
        (0, "0 — Sem classificação"),
        (1, "1 — Muito baixa"),
        (2, "2 — Baixa"),
        (3, "3 — Média"),
        (4, "4 — Alta"),
        (5, "5 — Urgente"),
    ]

    return render(
        request,
        "portal/equipe/chamado_detalhe.html",
        {
            "ch": ch,
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
        },
    )


# ═══════════════════════════════════════════════════════════════
# EXCLUSÃO DE CHAMADO (somente GES — Gestor/Administrador)
# ═══════════════════════════════════════════════════════════════
@perfis("GES")
@require_http_methods(["POST"])
def gestao_chamado_excluir(request, pk):
    # SQL puro: busca o chamado para verificar se existe
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

    # ┌─────────────────────────────────────────────────────────┐
    # │  LOG DE AUDITORIA — Registra no histórico ANTES de     │
    # │  apagar, para que fique documentado quem excluiu,      │
    # │  quando e por quê.                                     │
    # └─────────────────────────────────────────────────────────┘
    with connection.cursor() as cursor:
        # Busca status atual para o log
        cursor.execute(
            "SELECT hc.id_status FROM historico_chamado hc "
            "WHERE hc.id_chamado = %s "
            "ORDER BY hc.dt_alteracao DESC LIMIT 1",
            [pk],
        )
        st_row = cursor.fetchone()
        status_id = st_row[0] if st_row else None

        # INSERT log de auditoria
        cursor.execute(
            "INSERT INTO historico_chamado "
            "(id_chamado, id_servidor, id_status, observacao, dt_alteracao) "
            "VALUES (%s, %s, %s, %s, %s)",
            [pk, request.portal_user.pk, status_id,
             f"[EXCLUSÃO] Chamado excluído. Justificativa: {justificativa}",
             timezone.now()],
        )

        # ┌─────────────────────────────────────────────────────────┐
        # │  DELETE via SQL direto — apaga registros filhos         │
        # │  (fotos, histórico, notificações), depois o chamado.   │
        # └─────────────────────────────────────────────────────────┘
        cursor.execute("DELETE FROM foto_chamado WHERE id_chamado = %s", [pk])
        cursor.execute("DELETE FROM historico_chamado WHERE id_chamado = %s", [pk])
        cursor.execute("DELETE FROM notificacao WHERE id_chamado = %s", [pk])
        cursor.execute("DELETE FROM chamado WHERE id_chamado = %s", [pk])

    messages.success(request, f"Chamado {protocolo} excluído com sucesso.")
    return redirect("portal:equipe_chamados")
