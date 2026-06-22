"""
views_equipe.py — aqui ficam as views da equipe (gestor GES e colaborador COL)

Anotacao minha pra lembrar: essas rotas sao da EQUIPE, nao do cidadao.
A diferenca que importa eh que a equipe:
- ve TODOS os chamados, nao so os dela
- pode mudar o status dos chamados (eh tipo uma maquina de estados)
- pode botar observacao e foto em qualquer chamado
- tem o dashboard com os graficos e numeros

O cidadao so cancela os chamados dele e avalia quando conclui. Quem
controla o atendimento todo eh a equipe.

Detalhe importante que eu sempre esqueco: mudar status NAO faz UPDATE,
faz um INSERT novo em historico_chamado (estilo event sourcing, fica o
historico todo). Ai os triggers do banco disparam sozinhos depois:
- Trigger 2A: atualiza atualizado_em na tabela chamado
- Trigger 2B: se o status virou CO ou CA, seta dt_conclusao = NOW() e
  cria a notificacao pro cidadao

Outra regra: colaborador (COL) NAO pode mexer no status de chamado que
ja ta encerrado (Concluido ou Cancelado). So o gestor (GES) pode. E essa
regra eu faco no Python mesmo, nao no banco.
"""

# imports padrao + coisas do Django + os helpers meus do portal
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
    """Pega um parametro da query string e transforma em int ou None.

    Lembrete: os select mandam string vazia quando ta em "Todos". Ai eu
    trato string vazia e None como None (pra esse filtro nao entrar no
    WHERE do SQL) e o resto eu tento converter pra int.
    """
    # se veio vazio ou None, eu ja devolvo None e nem tento converter
    if v is None or v == "":
        return None
    # tento virar int; se vier lixo (ex: texto), devolvo None tambem
    try:
        return int(v)
    except ValueError:
        return None


# ------------------------------------------------------------------
# Listar todos os chamados (GET /equipe/chamados/)
# ------------------------------------------------------------------

@perfis("COL", "GES")
def equipe_chamados_lista(request):
    """Lista TODOS os chamados, com filtro, paginacao e ordenacao.

    Diferente da view do cidadao, aqui eu nao filtro por id_cidadao porque
    a equipe ve tudo. La no SQL o WHERE comeca com TRUE pra eu poder ir
    colando os filtros com AND sem ter que fazer if pra cada um.

    Ordenacao padrao eh prioridade DESC (urgente primeiro) e desempata por
    dt_abertura DESC. O usuario muda isso clicando no cabecalho (vem nos
    parametros ordenar_por e direcao da query string).

    A coluna "Dias em Aberto" eu calculo no Python ((hoje - dt_abertura).days),
    sem os pontinhos coloridos do semaforo velho.
    """
    # pego a pagina da query string; se vier vazio ou lixo eu caio no 1
    try:
        pagina = max(1, int(request.GET.get("pagina") or 1))
    except (ValueError, TypeError):
        pagina = 1
    por_pagina = 15

    # monto o dict de filtros lendo a query string. os _int_none sao os
    # selects (viram None se for "Todos"); de/ate sao datas; mostrar_encerrados
    # eh checkbox ("1" = marcado); ordenar_por/direcao tem default
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

    # mando os filtros pro db e ja volto as linhas da pagina + o total geral
    linhas, total_count = db.listar_chamados_equipe(filtros, pagina=pagina, por_pagina=por_pagina)

    # busco tudo que o template precisa pra montar os selects e os cards do topo
    bairros_lista = db.listar_bairros_ativos()
    statuses_lista = db.listar_statuses()
    stats = db.calcular_stats_semaforo()
    servicos_stats = db.calcular_stats_semaforo_por_servico()
    servicos_catalogo = db.listar_servicos_ativos()
    config = ConfiguracaoSemaforo.get_singleton()

    # calculo a porcentagem de cada faixa do semaforo. uso max(total,1) pra
    # nao dar divisao por zero quando nao tem chamado nenhum
    pct_no_prazo = round(stats["no_prazo"] / max(total_count, 1) * 100)
    pct_atencao = round(stats["atencao"] / max(total_count, 1) * 100)
    pct_critico = round(stats["critico"] / max(total_count, 1) * 100)

    # monto o objeto de paginacao (ja passo total_count porque as linhas
    # ja vieram paginadas do banco, nao sao a lista toda)
    page_obj, _ = db.paginar(linhas, pagina, por_pagina=por_pagina, total_count=total_count)

    # jogo tudo pro template do dashboard
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
    """Configura os prazos do semaforo (amarelo/vermelho).

    Agora eh global (um ConfiguracaoSemaforo singleton), nao mais um por
    servico. So o gestor (GES) pode mexer.
    """
    # essa view nao usa o @perfis, entao eu checo o login e o perfil na mao
    u = request.portal_user
    if not u:
        # nao logado -> manda pro login
        return redirect("portal:login")
    if u.perfil != "GES":
        # logado mas nao eh gestor -> barra com mensagem e volta pra lista
        messages.error(
            request,
            "Você não tem permissão para alterar os prazos. "
            "Apenas o Gestor pode realizar esta configuração."
        )
        return redirect("portal:equipe_chamados")

    if request.method == "POST":
        # tento ler os dois prazos como int (default 15 e 30 se nao vier)
        try:
            prazo_amarelo = int(request.POST.get("prazo_amarelo_dias", 15))
            prazo_vermelho = int(request.POST.get("prazo_vermelho_dias", 30))
        except (ValueError, TypeError):
            # veio algo que nao eh numero -> avisa e volta pro form
            messages.error(request, "Valores inválidos.")
            return redirect("portal:gestao_prazos")

        # salvo no banco, aviso que deu certo e recarrego a pagina (PRG)
        db.atualizar_configuracao_prazos(prazo_amarelo, prazo_vermelho)
        messages.success(request, "Prazos atualizados.")
        return redirect("portal:gestao_prazos")

    # GET: so busco a config atual pra preencher o form e mostro a pagina
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
    """Mostra a pagina de detalhe do chamado pra equipe."""
    # busco o chamado; se nao achar eh 404
    ch = db.buscar_chamado_detalhe_equipe(pk)
    if not ch:
        raise Http404()

    # texto tipo "ha X dias" pra mostrar na tela
    dias_aberto = formatar_dias_em_aberto(ch.dt_abertura)

    # aqui eu aplico aquela regra: se for COL e o chamado ja ta CO/CA, ele
    # nao pode mexer no status. guardo os dois flags pro template usar
    p = perfil_codigo(request.portal_user)
    ts = ch.sigla_status
    bloqueia_status_col = p == "COL" and ts in ("CO", "CA")
    pode_status = not bloqueia_status_col

    # historico, fotos e as observacoes (que sao os historicos que tem texto)
    historicos = db.buscar_historicos(pk)
    fotos = db.buscar_fotos(pk)
    observacoes = [h for h in historicos if h.observacao]

    # ja deixo o form de status preenchido com o status e a resolucao atuais
    form_status = EquipeStatusForm(
        initial={
            "id_status": ch.status_atual,
            "resolucao": ch.resolucao or "",
        }
    )

    # lista fixa de prioridades pro select la no template
    prioridades = [
        (0, "0 — Sem classificacao"),
        (1, "1 — Muito baixa"),
        (2, "2 — Baixa"),
        (3, "3 — Media"),
        (4, "4 — Alta"),
        (5, "5 — Urgente"),
    ]

    # mapa id->sigla pro JS saber quais status sao finais (CO/CA). uso isso
    # no front pra mostrar/esconder o campo de resolucao na hora certa
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
    """Muda o status de um chamado (so POST)."""
    # se o chamado nem existe ja corto com 404
    if not db.chamado_existe(pk):
        raise Http404()
    p = perfil_codigo(request.portal_user)

    # de novo a regra do COL: se ja ta encerrado (CO/CA), colaborador nao
    # mexe. aqui eu corto com 404 mesmo (nao deixo nem tentar)
    sigla_atual = db.buscar_sigla_status_atual(pk)
    if p == "COL" and sigla_atual in ("CO", "CA"):
        raise Http404()

    # valido o form que veio do POST
    form_s = EquipeStatusForm(request.POST)
    if form_s.is_valid():
        # status novo escolhido
        novo = form_s.cleaned_data["id_status"]
        # prioridade vem solta no POST; tento converter e travo entre 0 e 5.
        # se vier lixo eu suppress o erro e fica no 0 que ja era o default
        pri = request.POST.get("prioridade")
        prioridade_val = 0
        if pri is not None:
            with contextlib.suppress(ValueError, TypeError):
                prioridade_val = max(0, min(5, int(pri)))

        # pego a sigla do status novo e o texto de resolucao (limpo espacos;
        # se sobrar vazio vira None pra nao gravar string vazia)
        nova_sigla = novo.sigla.strip().upper()
        obs_texto = form_s.cleaned_data.get("resolucao")
        if obs_texto:
            obs_texto = obs_texto.strip()
        if not obs_texto:
            obs_texto = None

        # resolucao so faz sentido se ta encerrando (CO/CA); senao mando None
        resolucao = obs_texto if nova_sigla in ("CO", "CA") else None

        # chamo o service que faz o INSERT no historico (e os triggers rodam)
        chamado_service.alterar_status(
            pk, novo, servidor_id=request.portal_user.pk,
            prioridade=prioridade_val,
            resolucao=resolucao,
            observacao=obs_texto,
        )

        messages.success(request, "Status atualizado.")
    else:
        # form invalido: jogo os erros gerais pra tela como message
        for e in form_s.non_field_errors():
            messages.error(request, e)
    # volto pro detalhe do chamado em qualquer caso
    return redirect("portal:equipe_chamado", pk=pk)


@perfis("COL", "GES")
@require_http_methods(["POST"])
def equipe_chamado_obs(request, pk):
    """Adiciona uma observacao no chamado (equipe)."""
    # chamado tem que existir
    if not db.chamado_existe(pk):
        raise Http404()
    # valido o form da observacao
    form_o = ObservacaoForm(request.POST)
    if form_o.is_valid():
        # service registra a obs no historico
        chamado_service.adicionar_observacao(
            pk, form_o.cleaned_data["texto"],
            servidor_id=request.portal_user.pk,
        )
        messages.success(request, "Observação registrada.")
    # volto pro detalhe (se o form for invalido, so nao salva e volta)
    return redirect("portal:equipe_chamado", pk=pk)


@perfis("COL", "GES")
@require_http_methods(["POST"])
def equipe_chamado_foto(request, pk):
    """Sobe uma foto pro chamado (equipe)."""
    # chamado tem que existir
    if not db.chamado_existe(pk):
        raise Http404()
    # so faz alguma coisa se realmente veio um arquivo no campo "foto"
    if request.FILES.get("foto"):
        form_f = FotoForm(request.POST, request.FILES)
        if form_f.is_valid():
            # o service pode estourar ValueError (ex: tipo invalido); ai eu
            # mostro o erro. se nao estourar, cai no else e avisa sucesso
            try:
                chamado_service.adicionar_foto(pk, request.FILES["foto"], request=request)
            except ValueError as e:
                messages.error(request, str(e))
            else:
                messages.success(request, "Foto registrada.")
        else:
            # form invalido: desenrolo todos os erros e mando pra tela
            for errors in form_f.errors.values():
                for error in errors:
                    messages.error(request, error)
    else:
        # nem mandou arquivo -> aviso pra selecionar uma imagem
        messages.error(request, "Selecione uma imagem.")
    return redirect("portal:equipe_chamado", pk=pk)


# ------------------------------------------------------------------
# Excluir chamado (POST /equipe/chamados/<pk>/excluir/)
# ------------------------------------------------------------------

@perfis("GES")
@require_http_methods(["POST"])
def gestao_chamado_excluir(request, pk):
    """Apaga o chamado de vez (so gestor).

    Lembrete pra mim do passo a passo (e por que cada coisa):
    1. confiro se o chamado existe.
    2. la no db.py liga a flag portal.excluindo na sessao do Postgres pros
       triggers de protecao (fn_historico_sem_delete) deixarem o DELETE
       passar. Sem essa flag eles bloqueiam o delete.
    3. gravo um log de auditoria no historico com a justificativa.
    4. apago em cascata na mao: fotos, historicos, notificacoes e por fim o
       chamado. A ORDEM importa por causa das foreign keys.

    Tudo dentro de transaction.atomic() -> se um passo quebra, desfaz tudo.
    """
    # primeiro busco o chamado so pra confirmar que existe e pegar o protocolo
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_chamado, num_protocolo FROM chamado WHERE id_chamado = %s", [pk]
        )
        row = cursor.fetchone()
    if not row:
        raise Http404()

    protocolo = row[1]
    # justificativa eh obrigatoria; limpo os espacos
    justificativa = (request.POST.get("justificativa") or "").strip()

    if not justificativa:
        # sem justificativa eu nem comeco a exclusao, volto pro detalhe
        messages.error(request, "É obrigatório informar uma justificativa para excluir o chamado.")
        return redirect("portal:equipe_chamado", pk=pk)

    # abro a transacao: log de auditoria + delete em cascata, tudo junto
    with transaction.atomic(), connection.cursor() as cursor:
        # pego o ultimo status do chamado so pra registrar no log
        cursor.execute(
            "SELECT hc.id_status FROM historico_chamado hc "
            "WHERE hc.id_chamado = %s "
            "ORDER BY hc.dt_alteracao DESC LIMIT 1",
            [pk],
        )
        st_row = cursor.fetchone()
        status_id = st_row[0] if st_row else None

        # gravo o historico de exclusao ANTES de apagar (senao some junto)
        db.criar_historico(
            pk, status_id, servidor_id=request.portal_user.pk,
            observacao=f"[EXCL] Chamado excluído. Justificativa: {justificativa}",
        )

        # delete em cascata; o bypass dos triggers ta encapsulado no db.py
        db.excluir_chamado_com_cascata(pk)

    # deu certo: aviso com o protocolo e volto pra lista
    messages.success(request, f"Chamado {protocolo} excluído com sucesso.")
    return redirect("portal:equipe_chamados")


# ------------------------------------------------------------------
# Dashboard com graficos (GET /equipe/)
# ------------------------------------------------------------------

@perfis("COL", "GES")
@require_http_methods(["GET"])
def equipe_dashboard(request):
    # dashboard dos graficos. busco os numeros de uma vez no db
    import json
    stats = db.buscar_stats_dashboard()
    # monto o context; os campos *_json eu serializo pro Chart.js ler no front.
    # labels = nomes dos eixos, data = os valores
    context = {
        'atendidas_hoje': stats['atendidas_hoje'],
        'atendidas_semana': stats['atendidas_semana'],
        'status_labels_json': json.dumps(stats['status_labels']),
        'status_data_json': json.dumps(stats['status_data']),
        'bairros_labels_json': json.dumps(stats['bairros_labels']),
        'bairros_data_json': json.dumps(stats['bairros_data']),
    }
    return render(request, "portal/equipe/estatisticas_graficos.html", context)
