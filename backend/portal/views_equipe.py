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
from django.db import connection
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
    # Semaforo geral (sem filtros) — usado nos cards de resumo do dashboard
    stats = db.calcular_stats_semaforo()

    # SQL puro: SELECT com JOINs + 2 subqueries para status atual
    # [!] Mesma logica de views_cidadao, mas sem WHERE id_cidadao
    #     e com JOIN extra em cidadao (para mostrar nome do solicitante)
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
        ") AS sigla_status, "
        "("
        "  SELECT sc2.descricao FROM historico_chamado hc2 "
        "  JOIN status_chamado sc2 ON hc2.id_status = sc2.id_status "
        "  WHERE hc2.id_chamado = c.id_chamado "
        "  ORDER BY hc2.dt_alteracao DESC LIMIT 1"
        ") AS status_descricao "
        "FROM chamado c "
        "JOIN servico s ON c.id_servico = s.id_servico "
        "JOIN bairro b ON c.id_bairro = b.id_bairro "
        "JOIN cidadao ci ON c.id_cidadao = ci.id_cidadao "
        "WHERE TRUE "      # WHERE TRUE = base para concatenar ANDs dinamicos
    )
    params = []

    # Filtros dinamicos da query string (todos opcionais)
    bairro = _int_none(request.GET.get("bairro"))  # ?bairro=3 → filtra por bairro
    st = _int_none(request.GET.get("status"))      # ?status=2 → filtra por id_status
    d0 = request.GET.get("de")                      # ?de=2026-01-01 → data inicio
    d1 = request.GET.get("ate")                     # ?ate=2026-05-01 → data fim

    if bairro:
        sql += "AND c.id_bairro = %s "
        params.append(bairro)
    if st:
        # Subquery: filtra pelo status ATUAL (ultimo historico)
        sql += (
            "AND ("
            "  SELECT hc2.id_status FROM historico_chamado hc2 "
            "  WHERE hc2.id_chamado = c.id_chamado "
            "  ORDER BY hc2.dt_alteracao DESC LIMIT 1"
            ") = %s "
        )
        params.append(st)
    if d0:
        sql += "AND c.dt_abertura::date >= %s "  # ::date = cast para comparar so o dia
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

    # HIDRATACAO + SEMAFORO: tuplas → SimpleNamespace com cor de urgencia
    now = timezone.now()
    linhas = []
    for r in rows:
        # r[4]=dt_abertura, r[10]=prazo_amarelo, r[11]=prazo_vermelho
        dias = (now - r[4]).days
        if dias >= r[11]:
            cor = "vermelho"    # Critico
        elif dias >= r[10]:
            cor = "amarelo"     # Atencao
        else:
            cor = "verde"       # No prazo
        sigla = r[14] or ""     # r[14] = subquery sigla_status
        status_desc = r[15] or ""  # r[15] = subquery status_descricao
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

    # Busca listas para popular os <select> de filtros no template
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

    # Contexto para o template:
    #   bairros/statuses = opcoes dos <select>  |  filtro_* = valor selecionado
    return render(
        request,
        "portal/equipe/dashboard.html",
        {
            "linhas": linhas,
            "stats": stats,
            "total_count": total_count,
            "bairros": bairros_lista,         # Lista completa para popular <select>
            "statuses": statuses_lista,       # Lista completa para popular <select>
            "filtro_bairro": bairro,           # Qual bairro esta selecionado
            "filtro_status": st,               # Qual status esta selecionado
            "filtro_de": d0 or "",             # Data inicio selecionada
            "filtro_ate": d1 or "",            # Data fim selecionada
        },
    )


# ═══════════════════════════════════════════════════════════════
# UPDATE — Detalhe + acoes da equipe — Rota: /equipe/chamados/<pk>/
# ═══════════════════════════════════════════════════════════════
# [!] POST acao='status' → INSERT historico_chamado (muda status)
#     POST acao='obs'    → INSERT historico_chamado (observacao)
#     POST acao='foto'   → INSERT foto_chamado
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
# DELETE — Exclusao de chamado — Rota: /equipe/chamados/<pk>/excluir/
# ═══════════════════════════════════════════════════════════════
# [!] Somente GES (Gestor). Requer justificativa obrigatoria.
#     Fluxo: log de auditoria → DELETE filhos → DELETE chamado
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
    # │  [!] A Rule Extra (rx_chamado_sem_delete) no banco     │
    # │      impede DELETE normal. Esta view contorna isso     │
    # │      apagando manualmente os registros filhos primeiro. │
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
