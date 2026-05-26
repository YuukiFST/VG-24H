"""
views_equipe.py — Views da Equipe (Gestores e Colaboradores)

[!] @perfis("COL", "GES") — APENAS servidores acessam. Cidadaos sao bloqueados.
[!] Ao contrario de views_cidadao: aqui NAO filtra por id_cidadao — ve TODOS os chamados.
[!] Mudanca de status = INSERT em historico_chamado (NAO update em chamado).
    Trigger 2B trata dt_conclusao e notificacao automaticamente.

Diferenca chave:
  - Cidadao: filtra WHERE c.id_cidadao = %s (privacidade)
  - Equipe: sem filtro de cidadao (ve todos)
"""

from types import SimpleNamespace

import json
from datetime import timedelta

from django.contrib import messages
from django.db import connection, transaction
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from portal import db
from portal.decorators import perfil_codigo, perfis
from portal.forms import EquipeStatusForm, FotoForm, ObservacaoForm
from portal.utils import salvar_foto_upload


def _int_none(v):
    """Converte string da query string para int, ou None se vazio/invalido."""
    if v is None or v == "":
        return None
    try:
        return int(v)
    except ValueError:
        return None



# ═══════════════════════════════════════════════════════════════
# READ — Listar TODOS os chamados — Rota: /equipe/chamados/
# ═══════════════════════════════════════════════════════════════
# [!] Diferenca do cidadao: aqui NAO filtra por id_cidadao (ve TODOS)
#     WHERE TRUE permite concatenar filtros opcionais com AND
@perfis("COL", "GES")
def equipe_chamados_lista(request):
    stats = db.calcular_stats_semaforo()
    try:
        pagina = max(1, int(request.GET.get("pagina") or 1))
    except (ValueError, TypeError):
        pagina = 1
    por_pagina = 15
    offset = (pagina - 1) * por_pagina

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
        "s.nome AS servico_nome, s.prazo_amarelo_dias, s.prazo_vermelho_dias, "
        "b.nome_bairro, "
        "ci.nome_completo AS cidadao_nome, "
        "ultimo.sigla AS sigla_status, "
        "ultimo.descricao AS status_descricao "
    )
    params = []

    bairro = _int_none(request.GET.get("bairro"))
    st = _int_none(request.GET.get("status"))
    d0 = request.GET.get("de")
    d1 = request.GET.get("ate")

    if bairro:
        sql_base += "AND c.id_bairro = %s "
        params.append(bairro)
    if st:
        sql_base += "AND ultimo.id_status = %s "
        params.append(st)
    if d0:
        sql_base += "AND c.dt_abertura::date >= %s "
        params.append(d0)
    if d1:
        sql_base += "AND c.dt_abertura::date <= %s "
        params.append(d1)

    count_sql = "SELECT COUNT(*) " + sql_base
    with connection.cursor() as cursor:
        cursor.execute(count_sql, params)
        total_count = cursor.fetchone()[0]

    data_sql = select_cols + sql_base + "ORDER BY c.dt_abertura DESC LIMIT %s OFFSET %s"
    data_params = params + [por_pagina, offset]

    with connection.cursor() as cursor:
        cursor.execute(data_sql, data_params)
        rows = cursor.fetchall()

    linhas = []
    for r in rows:
        cor = db.cor_semaforo(r[4], r[10], r[11])
        sigla = r[14] or ""
        status_desc = r[15] or ""
        ch = SimpleNamespace(
            id_chamado=r[0], pk=r[0], num_protocolo=r[1], prioridade=r[2],
            descricao=r[3], dt_abertura=r[4], atualizado_em=r[5],
            id_servico=SimpleNamespace(id_servico=r[6], pk=r[6], nome=r[9]),
            id_bairro=SimpleNamespace(id_bairro=r[7], pk=r[7], nome_bairro=r[12]),
            id_cidadao=SimpleNamespace(id_cidadao=r[8], pk=r[8], nome_completo=r[13]),
            sigla_status=sigla, cor_semaforo=cor,
            status_atual=SimpleNamespace(sigla=sigla, descricao=status_desc),
        )
        linhas.append({"ch": ch, "cor": cor})

    # Catalogo de bairros e statuses para os filtros do template
    bairros_lista = db.listar_bairros_ativos()
    statuses_lista = db.listar_statuses()

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
            "filtro_de": d0 or "",
            "filtro_ate": d1 or "",
        },
    )
@perfis("COL", "GES")
@require_http_methods(["GET", "POST"])
def equipe_chamado_detalhe(request, pk):
    # SELECT chamado com JOINs completos (servico + bairro + cidadao + categoria)
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

    # Busca status atual e semaforo (via db.py — logica centralizada)
    db.popular_status(ch)

    # [!] REGRA DE NEGOCIO: COL nao pode alterar status de chamado encerrado (CO/CA)
    #     GES pode sempre (isento). Essa validacao e feita na view (Python),
    #     NAO no banco — substitui a Rule R4 que foi removida.
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
                # [!] MUDANCA DE STATUS = INSERT em historico_chamado
                #     NAO e UPDATE em chamado! O status atual = ULTIMO registro.
                #     Trigger 2B dispara automaticamente:
                #       → Se CO/CA: UPDATE chamado SET dt_conclusao = NOW()
                #       → Se AB/EA/EE: UPDATE chamado SET dt_conclusao = NULL
                #       → INSERT notificacao (aviso ao cidadao)
                #     id_servidor = quem esta logado (rastreabilidade)
                with transaction.atomic(), connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO historico_chamado "
                        "(id_chamado, id_servidor, id_status, dt_alteracao) "
                        "VALUES (%s, %s, %s, %s)",
                        [pk, request.portal_user.pk, novo.pk, timezone.now()],
                    )
                    # UPDATE resolução (somente para CO/CA) e prioridade
                    nova_sigla = novo.sigla.strip().upper()
                    pri = request.POST.get("prioridade")
                    prioridade_val = ch.prioridade
                    if pri is not None:
                        try:
                            prioridade_val = max(0, min(5, int(pri)))
                        except (ValueError, TypeError):
                            pass
                    if nova_sigla in ("CO", "CA"):
                        resolucao = form_s.cleaned_data.get("resolucao") or None
                        cursor.execute(
                            "UPDATE chamado SET resolucao = %s, prioridade = %s "
                            "WHERE id_chamado = %s",
                            [resolucao, prioridade_val, pk],
                        )
                    else:
                        cursor.execute(
                            "UPDATE chamado SET prioridade = %s "
                            "WHERE id_chamado = %s",
                            [prioridade_val, pk],
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
                    for field, errors in form_f.errors.items():
                        for error in errors:
                            messages.error(request, error)
            else:
                messages.error(request, "Selecione uma imagem.")
            return redirect("portal:equipe_chamado", pk=pk)

    # SQL puro: busca historicos e fotos (via db.py)
    historicos = db.buscar_historicos(pk)
    fotos = db.buscar_fotos(pk)

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

    # Mapa PK → sigla para o JS saber quais status são CO/CA
    with connection.cursor() as cursor:
        cursor.execute("SELECT id_status, sigla FROM status_chamado")
        status_sigla_map = {r[0]: r[1].strip() for r in cursor.fetchall()}

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
            "status_sigla_map_json": json.dumps(status_sigla_map),
        },
    )
# ========================================================================
# DELETE — Exclusao de chamado — Rota: /equipe/chamados/<pk>/excluir/
# ========================================================================
# [!] Somente GES (Gestor). Requer justificativa obrigatoria.
#     Fluxo: log de auditoria -> DELETE filhos -> DELETE chamado
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
        messages.error(request, "E obrigatorio informar uma justificativa para excluir o chamado.")
        return redirect("portal:equipe_chamado", pk=pk)

    # Log de auditoria + delecao atomica
    with transaction.atomic():
        with connection.cursor() as cursor:
            # Habilita bypass dos triggers de protecao DELETE
            # (fn_historico_sem_delete + fn_chamado_sem_delete)
            cursor.execute("SELECT set_config('portal.excluindo', 'true', true)")

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
                 f"[EXCLUSAO] Chamado excluido. Justificativa: {justificativa}",
                 timezone.now()],
            )

            # DELETE via SQL direto — triggers so permitem com portal.excluindo='true'
            cursor.execute("DELETE FROM foto_chamado WHERE id_chamado = %s", [pk])
            cursor.execute("DELETE FROM historico_chamado WHERE id_chamado = %s", [pk])
            cursor.execute("DELETE FROM notificacao WHERE id_chamado = %s", [pk])
            cursor.execute("DELETE FROM chamado WHERE id_chamado = %s", [pk])

    messages.success(request, f"Chamado {protocolo} excluido com sucesso.")
    return redirect("portal:equipe_chamados")
# ═══════════════════════════════════════════════════════════════
# ESTATISTICAS — Dashboard com graficos — Rota: /equipe/
# ═══════════════════════════════════════════════════════════════
# [!] Calcula 4 metricas via SQL puro:
#     1. Atendidas hoje (COUNT com dt_conclusao = hoje)
#     2. Atendidas semana (COUNT com dt_conclusao >= 7 dias atras)
#     3. Status geral (GROUP BY para grafico de pizza)
#     4. Distribuicao por bairro (TOP 10 para grafico de barras)
#
# [!] dt_conclusao e preenchido AUTOMATICAMENTE pelo Trigger 2B
#     quando um INSERT em historico_chamado tem status CO ou CA.
#     O Python NUNCA seta dt_conclusao para conclusao — so o trigger.
@perfis("COL", "GES")
@require_http_methods(["GET"])
def equipe_dashboard(request):
    agora = timezone.now()
    hoje = agora.date()                         # Data de hoje (so dia, sem hora)
    inicio_semana = hoje - timedelta(days=7)    # 7 dias atras

    with connection.cursor() as cursor:
            # METRICA 1: Chamados concluidos HOJE
            # Conta chamados cujo status atual = 'CO' E dt_conclusao = hoje
            # [!] Subquery busca o status ATUAL (ultimo historico)
            # [!] dt_conclusao::date = cast para comparar so o dia (sem hora)
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
            atendidas_hoje_row = cursor.fetchone()
            atendidas_hoje = atendidas_hoje_row[0] if atendidas_hoje_row else 0

            # METRICA 2: Chamados concluidos nos ultimos 7 DIAS
            # Mesma logica, mas com >= (a partir de 7 dias atras ate hoje)
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
            atendidas_semana_row = cursor.fetchone()
            atendidas_semana = atendidas_semana_row[0] if atendidas_semana_row else 0

            # METRICA 3: Distribuicao por status (para grafico de pizza/barras)
            # Resultado: [("Aberto", 15), ("Concluido", 42), ...]
            # [!] Subquery no WHERE garante que pega APENAS o ultimo historico de cada chamado
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
            status_labels = [row[0] for row in status_geral_rows]  # ["Aberto", "Concluido", ...]
            status_data = [row[1] for row in status_geral_rows]    # [15, 42, ...]

            # METRICA 4: Top 10 bairros com mais chamados (para grafico de barras)
            cursor.execute('''
                SELECT b.nome_bairro, COUNT(c.id_chamado) as qtd
                FROM chamado c
                JOIN bairro b ON c.id_bairro = b.id_bairro
                GROUP BY b.nome_bairro
                ORDER BY qtd DESC
                LIMIT 10
            ''')
            bairros_rows = cursor.fetchall()
            bairros_labels = [row[0] for row in bairros_rows]  # ["Centro", "Jardim", ...]
            bairros_data = [row[1] for row in bairros_rows]    # [30, 25, ...]

    # Converte listas para JSON (usado pelo Chart.js no template)
    context = {
            'atendidas_hoje': atendidas_hoje,          # Numero inteiro
            'atendidas_semana': atendidas_semana,      # Numero inteiro
            'status_labels_json': json.dumps(status_labels),   # JSON para Chart.js
            'status_data_json': json.dumps(status_data),       # JSON para Chart.js
            'bairros_labels_json': json.dumps(bairros_labels),
            'bairros_data_json': json.dumps(bairros_data),
    }

    return render(request, "portal/equipe/estatisticas_graficos.html", context)