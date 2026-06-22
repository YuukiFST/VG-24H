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

import contextlib
import json

from django.contrib import messages
from django.db import connection, transaction
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from portal import db
from portal.decorators import perfil_codigo, perfis
from portal.forms import EquipeStatusForm, FotoForm, ObservacaoForm
from portal.models import ConfiguracaoSemaforo
from portal.services import chamado as chamado_service
from portal.utils import formatar_dias_em_aberto


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

    filtros = {
        "bairro": _int_none(request.GET.get("bairro")),
        "status": _int_none(request.GET.get("status")),
        "servico": _int_none(request.GET.get("servico")),
        "de": request.GET.get("de"),
        "ate": request.GET.get("ate"),
        "mostrar_encerrados": request.GET.get("mostrar_encerrados") == "1",
        "ordenar_por": request.GET.get("ordenar_por", "prioridade"),
        "direcao": request.GET.get("direcao", "desc"),
    }

    linhas, total_count = db.listar_chamados_equipe(filtros, pagina=pagina, por_pagina=por_pagina)

    bairros_lista = db.listar_bairros_ativos()
    statuses_lista = db.listar_statuses()
    stats = db.calcular_stats_semaforo()
    servicos_stats = db.calcular_stats_semaforo_por_servico()
    servicos_catalogo = db.listar_servicos_ativos()
    config = ConfiguracaoSemaforo.get_singleton()

    pct_no_prazo = round(stats["no_prazo"] / max(total_count, 1) * 100)
    pct_atencao = round(stats["atencao"] / max(total_count, 1) * 100)
    pct_critico = round(stats["critico"] / max(total_count, 1) * 100)

    page_obj, _ = db.paginar(linhas, pagina, por_pagina=por_pagina, total_count=total_count)

    return render(request, "portal/equipe/dashboard.html", {
        "linhas": page_obj, "stats": stats, "total_count": total_count,
        "page_obj": page_obj, "bairros": bairros_lista, "statuses": statuses_lista,
        "filtro_bairro": filtros["bairro"], "filtro_status": filtros["status"],
        "filtro_servico": filtros["servico"], "filtro_de": filtros["de"] or "",
        "filtro_ate": filtros["ate"] or "", "ordenar_por": filtros["ordenar_por"],
        "direcao": filtros["direcao"], "servicos_stats": servicos_stats,
        "servicos": servicos_catalogo, "pct_no_prazo": pct_no_prazo,
        "pct_atencao": pct_atencao, "pct_critico": pct_critico,
        "mostrar_encerrados": filtros["mostrar_encerrados"], "config_semaforo": config,
    })


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

        db.atualizar_configuracao_prazos(prazo_amarelo, prazo_vermelho)
        messages.success(request, "Prazos atualizados.")
        return redirect("portal:gestao_prazos")

    config = db.buscar_configuracao_prazos()

    return render(
        request,
        "portal/equipe/servico_prazos.html",
        {"config": config},
    )


# ------------------------------------------------------------------
# Detalhe do chamado + acoes (GET/POST /equipe/chamados/<pk>/)
# ------------------------------------------------------------------

@perfis("COL", "GES")
@require_http_methods(["GET"])
def equipe_chamado_detalhe(request, pk):
    """Exibe detalhes do chamado para a equipe."""
    ch = db.buscar_chamado_detalhe_equipe(pk)
    if not ch:
        raise Http404()

    dias_aberto = formatar_dias_em_aberto(ch.dt_abertura)

    p = perfil_codigo(request.portal_user)
    ts = ch.sigla_status
    bloqueia_status_col = p == "COL" and ts in ("CO", "CA")
    pode_status = not bloqueia_status_col

    historicos = db.buscar_historicos(pk)
    fotos = db.buscar_fotos(pk)
    observacoes = [h for h in historicos if h.observacao]

    form_status = EquipeStatusForm(
        initial={
            "id_status": ch.status_atual,
            "resolucao": ch.resolucao or "",
        }
    )

    # Prioridades para o select no template.
    prioridades = [
        (0, "0 — Sem classificacao"),
        (1, "1 — Muito baixa"),
        (2, "2 — Baixa"),
        (3, "3 — Media"),
        (4, "4 — Alta"),
        (5, "5 — Urgente"),
    ]

    # Mapa PK → sigla para o JavaScript saber quais status sao finais.
    # Usado no frontend para mostrar/ocultar o campo de resolucao.
    status_sigla_map = db.listar_status_com_sigla_map()

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
            "prioridades": prioridades,
            "status_sigla_map_json": json.dumps(status_sigla_map),
        },
    )


# ------------------------------------------------------------------
# Acoes da equipe (POST — cada acao tem sua propria URL)
# ------------------------------------------------------------------


@perfis("COL", "GES")
@require_http_methods(["POST"])
def equipe_chamado_status(request, pk):
    """Altera o status de um chamado."""
    if not db.chamado_existe(pk):
        raise Http404()
    p = perfil_codigo(request.portal_user)

    # Verifica bloqueio de COL para chamados encerrados.
    sigla_atual = db.buscar_sigla_status_atual(pk)
    if p == "COL" and sigla_atual in ("CO", "CA"):
        raise Http404()

    form_s = EquipeStatusForm(request.POST)
    if form_s.is_valid():
        novo = form_s.cleaned_data["id_status"]
        pri = request.POST.get("prioridade")
        prioridade_val = 0
        if pri is not None:
            with contextlib.suppress(ValueError, TypeError):
                prioridade_val = max(0, min(5, int(pri)))

        nova_sigla = novo.sigla.strip().upper()
        obs_texto = form_s.cleaned_data.get("resolucao")
        if obs_texto:
            obs_texto = obs_texto.strip()
        if not obs_texto:
            obs_texto = None

        resolucao = obs_texto if nova_sigla in ("CO", "CA") else None

        chamado_service.alterar_status(
            pk, novo, servidor_id=request.portal_user.pk,
            prioridade=prioridade_val,
            resolucao=resolucao,
            observacao=obs_texto,
        )

        messages.success(request, "Status atualizado.")
    else:
        for e in form_s.non_field_errors():
            messages.error(request, e)
    return redirect("portal:equipe_chamado", pk=pk)


@perfis("COL", "GES")
@require_http_methods(["POST"])
def equipe_chamado_obs(request, pk):
    """Adiciona observacao a um chamado (equipe)."""
    if not db.chamado_existe(pk):
        raise Http404()
    form_o = ObservacaoForm(request.POST)
    if form_o.is_valid():
        chamado_service.adicionar_observacao(
            pk, form_o.cleaned_data["texto"],
            servidor_id=request.portal_user.pk,
        )
        messages.success(request, "Observação registrada.")
    return redirect("portal:equipe_chamado", pk=pk)


@perfis("COL", "GES")
@require_http_methods(["POST"])
def equipe_chamado_foto(request, pk):
    """Upload de foto para um chamado (equipe)."""
    if not db.chamado_existe(pk):
        raise Http404()
    if request.FILES.get("foto"):
        form_f = FotoForm(request.POST, request.FILES)
        if form_f.is_valid():
            try:
                chamado_service.adicionar_foto(pk, request.FILES["foto"], request=request)
            except ValueError as e:
                messages.error(request, str(e))
            else:
                messages.success(request, "Foto registrada.")
        else:
            for errors in form_f.errors.values():
                for error in errors:
                    messages.error(request, error)
    else:
        messages.error(request, "Selecione uma imagem.")
    return redirect("portal:equipe_chamado", pk=pk)


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
            "SELECT id_chamado, num_protocolo FROM chamado WHERE id_chamado = %s", [pk]
        )
        row = cursor.fetchone()
    if not row:
        raise Http404()

    protocolo = row[1]
    justificativa = (request.POST.get("justificativa") or "").strip()

    if not justificativa:
        messages.error(request, "É obrigatório informar uma justificativa para excluir o chamado.")
        return redirect("portal:equipe_chamado", pk=pk)

    with transaction.atomic(), connection.cursor() as cursor:
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
        db.criar_historico(
            pk, status_id, servidor_id=request.portal_user.pk,
            observacao=f"[EXCL] Chamado excluído. Justificativa: {justificativa}",
        )

        # Delete em cascata com bypass de triggers encapsulado em db.py.
        db.excluir_chamado_com_cascata(pk)

    messages.success(request, f"Chamado {protocolo} excluído com sucesso.")
    return redirect("portal:equipe_chamados")


# ------------------------------------------------------------------
# Dashboard com graficos (GET /equipe/)
# ------------------------------------------------------------------

@perfis("COL", "GES")
@require_http_methods(["GET"])
def equipe_dashboard(request):
    import json
    stats = db.buscar_stats_dashboard()
    context = {
        'atendidas_hoje': stats['atendidas_hoje'],
        'atendidas_semana': stats['atendidas_semana'],
        'status_labels_json': json.dumps(stats['status_labels']),
        'status_data_json': json.dumps(stats['status_data']),
        'bairros_labels_json': json.dumps(stats['bairros_labels']),
        'bairros_data_json': json.dumps(stats['bairros_data']),
    }
    return render(request, "portal/equipe/estatisticas_graficos.html", context)
