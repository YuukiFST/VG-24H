"""
views_cidadao.py — Views do cidadao (Portal VG 24H)

Este modulo atende as rotas acessiveis apenas por cidadaos autenticados
(perfil "CID"). Colaboradores e gestores sao bloqueados pelo decorator
@perfis("CID").

As operacoes disponiveis sao:
- Listar chamados do proprio cidadao (com filtros e paginacao)
- Abrir novo chamado (com upload de foto)
- Ver detalhe de um chamado (historico, fotos, observacoes)
- Cancelar chamado aberto ou em atendimento
- Avaliar chamado concluido (nota 1-5)
- Listar e excluir notificacoes

O status de um chamado nao eh armazenado como campo direto na tabela
chamado. Em vez disso, o status atual eh determinado pelo registro mais
recente na tabela historico_chamado (padrao event sourcing). Toda mudanca
de status gera um novo INSERT em historico_chamado, nunca um UPDATE.
Isso garante um log completo de auditoria.

O trigger Trigger 1 (AFTER INSERT ON chamado) cria automaticamente o
primeiro registro em historico_chamado com status "AB" (Aberto). A view
de criacao nao precisa se preocupar com o historico inicial.

Cada cidadao acessa somente seus proprios chamados. Todas as queries
incluem WHERE c.id_cidadao = %s para garantir privacidade. A funcao
auxiliar _chamado_do_cidadao() valida propriedade e retorna HTTP 404
quando o chamado nao pertence ao usuario (em vez de 403, para nao
revelar a existencia do recurso).
"""

from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render
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
from portal.services import chamado as chamado_service


def _chamado_do_cidadao(request, pk):
    """Busca um chamado e valida que pertence ao cidadao logado.

    Retorna o objeto SimpleNamespace do chamado (com JOINs em servico e
   bairro) ou levanta Http404 se o chamado nao existir ou pertencer
    a outro usuario. Retorna 404 em vez de 403 para nao revelar se
    o recurso existe (seguranca por obscuridade).
    """
    ch = db.buscar_chamado(pk)
    if not ch:
        raise Http404()
    if ch.id_cidadao_id != request.portal_user.pk:
        raise Http404()
    return ch


# ------------------------------------------------------------------
# Listar chamados do cidadao (GET /cidadao/chamados/)
# ------------------------------------------------------------------

@autenticado
@perfis("CID")
def cidadao_chamados_lista(request):
    """Lista os chamados do cidadao logado com filtros e paginacao.

    A query usa JOIN LATERAL (PostgreSQL) para buscar o ultimo historico
    de cada chamado em uma unica query, evitando o problema N+1.
    A subquery LATERAL executa ORDER BY dt_alteracao DESC LIMIT 1
    para pegar o registro mais recente de historico_chamado.

    Filtros disponiveis (todos opcionais, via query string):
    - status: sigla do status (ex: AB, EA, CO)
    - data: data de abertura (YYYY-MM-DD)
    - q: busca por numero de protocolo (ILIKE case-insensitive)
    """
    uid = request.portal_user.pk
    try:
        pagina = max(1, int(request.GET.get("pagina") or 1))
    except (ValueError, TypeError):
        pagina = 1
    por_pagina = 15
    chamados, total_count = db.listar_chamados_cidadao(
        uid,
        status=request.GET.get("status"),
        data=request.GET.get("data"),
        q=request.GET.get("q"),
        pagina=pagina,
        por_pagina=por_pagina,
    )
    page_obj, _ = db.paginar(chamados, pagina, por_pagina=por_pagina, total_count=total_count)
    stats = db.calcular_stats_semaforo(cidadao_id=uid)
    return render(request, "portal/cidadao/dashboard.html",
                  {"lista": page_obj, "total_count": total_count, "page_obj": page_obj, "stats": stats})


# ------------------------------------------------------------------
# Abrir novo chamado (GET/POST /cidadao/chamados/novo/)
# ------------------------------------------------------------------

@autenticado
@perfis("CID")
@require_http_methods(["GET", "POST"])
def cidadao_chamado_novo(request):
    """Formulario de abertura de novo chamado.

    GET: exibe o formulario com categorias, servicos (select cascata),
    bairros, descricao e campo de foto.

    POST: valida, salva a foto, gera protocolo e insere o chamado.
    O trigger Trigger 1 (AFTER INSERT ON chamado) cria automaticamente
    o registro em historico_chamado com status "AB".

    O numero de protocolo eh gerado atomicamente por proximo_protocolo()
    (INSERT ... ON CONFLICT DO UPDATE RETURNING), evitando race conditions
    entre duas requisicoes simultaneas.
    """
    categorias_list = db.listar_categorias_com_servicos()

    # Busca bairros ativos para o select de bairro.
    bairros = db.listar_bairros_ativos()

    if request.method == "POST":
        form = ChamadoNovoForm(request.POST, request.FILES)
        if form.is_valid():
            d = form.cleaned_data

            try:
                chamado_id, protocolo = chamado_service.criar_novo_chamado(
                    cidadao=request.portal_user,
                    servico=d["id_servico"],
                    bairro=d["id_bairro"],
                    descricao=d["descricao"],
                    ponto_referencia=d.get("ponto_de_referencia"),
                    foto_file=request.FILES.get("foto"),
                    request=request,
                )
            except ValueError as e:
                messages.error(request, str(e))
                return render(
                    request,
                    "portal/cidadao/novo_chamado.html",
                    {"form": form, "categorias": categorias_list, "bairros": bairros},
                )

            messages.success(request, f"Chamado aberto. Protocolo: {protocolo}")
            return redirect("portal:cidadao_chamado", pk=chamado_id)
    else:
        form = ChamadoNovoForm()

    return render(
        request,
        "portal/cidadao/novo_chamado.html",
        {"form": form, "categorias": categorias_list, "bairros": bairros},
    )


# ------------------------------------------------------------------
# Detalhe do chamado + acoes (GET/POST /cidadao/chamados/<pk>/)
# ------------------------------------------------------------------

@autenticado
@perfis("CID")
@require_http_methods(["GET"])
def cidadao_chamado_detalhe(request, pk):
    """Exibe detalhes do chamado para o cidadao."""
    ch = _chamado_do_cidadao(request, pk)
    ts = ch.sigla_status

    pode_obs_foto = ts not in ("CO", "CA")
    pode_cancelar = ts in ("AB", "EA")
    pode_avaliar = ts == "CO" and ch.nota_avaliacao is None

    # GET: busca historicos e fotos para renderizar o detalhe.
    historicos = db.buscar_historicos(pk)
    fotos = db.buscar_fotos(pk)

    # Observacoes = registros do historico que possuem texto no campo observacao.
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


# ------------------------------------------------------------------
# Acoes do cidadao (POST — cada acao tem sua propria URL)
# ------------------------------------------------------------------


@autenticado
@perfis("CID")
@require_http_methods(["POST"])
def cidadao_chamado_obs(request, pk):
    """Adiciona observacao a um chamado (cidadao)."""
    ch = _chamado_do_cidadao(request, pk)
    if ch.sigla_status in ("CO", "CA"):
        raise Http404()
    form_o = ObservacaoForm(request.POST)
    if form_o.is_valid():
        chamado_service.adicionar_observacao(
            pk, form_o.cleaned_data["texto"],
        )
        messages.success(request, "Observação registrada.")
    return redirect("portal:cidadao_chamado", pk=pk)


@autenticado
@perfis("CID")
@require_http_methods(["POST"])
def cidadao_chamado_foto(request, pk):
    """Upload de foto para um chamado (cidadao)."""
    ch = _chamado_do_cidadao(request, pk)
    if ch.sigla_status in ("CO", "CA"):
        raise Http404()
    form_f = FotoForm(request.POST, request.FILES)
    if form_f.is_valid() and request.FILES.get("foto"):
        try:
            chamado_service.adicionar_foto(pk, request.FILES["foto"], request=request)
        except ValueError as e:
            messages.error(request, str(e))
        else:
            messages.success(request, "Foto adicionada.")
    else:
        if not request.FILES.get("foto"):
            messages.error(request, "Selecione uma imagem.")
        else:
            for field, errors in form_f.errors.items():
                for error in errors:
                    messages.error(request, error)
    return redirect("portal:cidadao_chamado", pk=pk)


@autenticado
@perfis("CID")
@require_http_methods(["POST"])
def cidadao_chamado_cancelar(request, pk):
    ch = _chamado_do_cidadao(request, pk)
    if ch.sigla_status not in ("AB", "EA"):
        raise Http404()
    form_c = CancelarChamadoForm(request.POST)
    if form_c.is_valid():
        try:
            chamado_service.cancelar_chamado_cidadao(pk, form_c.cleaned_data["motivo"])
        except ValueError as e:
            messages.error(request, str(e))
            return redirect("portal:cidadao_chamado", pk=pk)
        messages.success(request, "Chamado cancelado.")
    return redirect("portal:cidadao_chamado", pk=pk)


@autenticado
@perfis("CID")
@require_http_methods(["POST"])
def cidadao_chamado_avaliar(request, pk):
    """Avalia chamado concluido (nota 1-5 + comentario opcional)."""
    ch = _chamado_do_cidadao(request, pk)
    if ch.sigla_status != "CO" or ch.nota_avaliacao is not None:
        raise Http404()
    form_a = AvaliacaoForm(request.POST)
    if form_a.is_valid():
        chamado_service.avaliar_chamado(pk, form_a.cleaned_data["nota"], form_a.cleaned_data.get("comentario") or None)
        messages.success(request, "Avaliação registrada.")
    return redirect("portal:cidadao_chamado", pk=pk)


# ------------------------------------------------------------------
# Notificacoes do cidadao (GET/POST /cidadao/notificacoes/)
# ------------------------------------------------------------------

@autenticado
@perfis("CID")
@require_http_methods(["GET", "POST"])
def cidadao_notificacoes(request):
    """Lista e exclui notificacoes do cidadao logado.

    As notificacoes sao criadas automaticamente pelo trigger Trigger 2B
    toda vez que o status de um chamado muda. Esta view so permite
    visualizar e deletar — nunca cria notificacoes.

    Seguranca: a subquery no WHERE garante que o cidadao so ve
    notificacoes dos seus proprios chamados. O DELETE tambem usa a
    mesma subquery para impedir que um cidadao manipule o POST e
    delete notificacoes de outros.
    """
    uid = request.portal_user.pk

    lista = db.listar_notificacoes_cidadao(uid)

    nids = [n.pk for n in lista if not n.lida]
    if nids:
        db.marcar_notificacoes_lidas(nids)

    if request.method == "POST":
        nid = request.POST.get("excluir")
        if nid:
            db.excluir_notificacao(nid, uid_cidadao=uid)
            messages.info(request, "Notificação removida.")
        return redirect("portal:cidadao_notificacoes")

    return render(
        request,
        "portal/cidadao/notificacoes.html",
        {"lista": lista},
    )
