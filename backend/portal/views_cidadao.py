"""
views_cidadao.py — minhas views do cidadao (Portal VG 24H)

Aqui ficam as rotas que so cidadao logado (perfil "CID") acessa.
Colaborador e gestor eu barro com o decorator @perfis("CID").

O que da pra fazer aqui:
- Listar os chamados do proprio cidadao (com filtro e paginacao)
- Abrir chamado novo (com upload de foto)
- Ver o detalhe de um chamado (historico, fotos, observacoes)
- Cancelar chamado aberto ou em atendimento
- Avaliar chamado concluido (nota 1-5)
- Listar e excluir notificacao

Detalhe importante do meu modelo: o status do chamado NAO eh um campo na
tabela chamado. O status atual eh sempre o registro mais novo da tabela
historico_chamado (estilo event sourcing). Toda mudanca de status eh um
INSERT novo no historico, nunca um UPDATE. Assim fica um log completo de
auditoria.

O Trigger 1 (AFTER INSERT ON chamado) ja cria sozinho o primeiro registro
no historico com status "AB" (Aberto), entao na hora de criar eu nao
preciso me preocupar com o historico inicial.

Cada cidadao so ve os chamados dele. Toda query tem WHERE c.id_cidadao = %s
pra garantir privacidade. A funcao _chamado_do_cidadao() confere se o
chamado eh dele mesmo e devolve 404 (e nao 403) quando nao eh, pra nem
revelar que o recurso existe.
"""

# imports do django + meus modulos (db = SQL puro, decorators, forms, e o
# service que concentra a regra de negocio dos chamados)
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
    """Busca o chamado e confere que ele eh do cidadao logado.

    Me devolve o SimpleNamespace do chamado (ja com JOIN em servico e
    bairro) ou estoura Http404 se nao existir ou for de outro user. Uso
    404 em vez de 403 de proposito pra nao entregar que o recurso existe.
    """
    ch = db.buscar_chamado(pk)
    if not ch:
        raise Http404()  # nem existe esse chamado
    # se o dono do chamado nao eh o user logado, finjo que nao existe
    if ch.id_cidadao_id != request.portal_user.pk:
        raise Http404()
    return ch


# ------------------------------------------------------------------
# Listar chamados do cidadao (GET /cidadao/chamados/)
# ------------------------------------------------------------------

@autenticado
@perfis("CID")
def cidadao_chamados_lista(request):
    """Lista os chamados do cidadao logado com filtro e paginacao.

    A query usa JOIN LATERAL (Postgres) pra pegar o ultimo historico de
    cada chamado de uma vez so, fugindo do problema N+1. A subquery
    LATERAL faz ORDER BY dt_alteracao DESC LIMIT 1 pra agarrar o registro
    mais recente do historico_chamado.

    Filtros (tudo opcional, vem pela query string):
    - status: sigla do status (ex: AB, EA, CO)
    - data: data de abertura (YYYY-MM-DD)
    - q: busca por protocolo (ILIKE, nao liga pra maiuscula/minuscula)
    """
    uid = request.portal_user.pk
    try:
        # pego o numero da pagina da URL; garanto que seja pelo menos 1
        pagina = max(1, int(request.GET.get("pagina") or 1))
    except (ValueError, TypeError):
        # se mandaram lixo no ?pagina= caio no 1
        pagina = 1
    por_pagina = 15
    # busco a fatia de chamados ja aplicando os filtros que vieram na URL
    chamados, total_count = db.listar_chamados_cidadao(
        uid,
        status=request.GET.get("status"),
        data=request.GET.get("data"),
        q=request.GET.get("q"),
        pagina=pagina,
        por_pagina=por_pagina,
    )
    # monto o page_obj pra paginacao no template (passo o total que ja tenho)
    page_obj, _ = db.paginar(chamados, pagina, por_pagina=por_pagina, total_count=total_count)
    # stats do semaforo (contadores por status) so desse cidadao
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
    """Tela de abrir chamado novo.

    GET: mostro o form com categorias, servicos (select em cascata),
    bairros, descricao e o campo de foto.

    POST: valido, salvo a foto, gero o protocolo e insiro o chamado.
    O Trigger 1 (AFTER INSERT ON chamado) ja cria o registro no
    historico_chamado com status "AB" sozinho.

    O protocolo eh gerado de forma atomica pelo proximo_protocolo()
    (INSERT ... ON CONFLICT DO UPDATE RETURNING), assim duas requisicoes
    ao mesmo tempo nao geram o mesmo numero (sem race condition).
    """
    categorias_list = db.listar_categorias_com_servicos()

    # bairros ativos pro select de bairro
    bairros = db.listar_bairros_ativos()

    if request.method == "POST":
        # passo request.FILES tambem porque tem upload de foto
        form = ChamadoNovoForm(request.POST, request.FILES)
        if form.is_valid():
            d = form.cleaned_data

            # delego a criacao toda pro service (ele salva foto, gera protocolo
            # e faz o insert); se algo der errado ele estoura ValueError
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
                # deu ruim: re-renderizo o form com a msg de erro e os selects
                messages.error(request, str(e))
                return render(
                    request,
                    "portal/cidadao/novo_chamado.html",
                    {"form": form, "categorias": categorias_list, "bairros": bairros},
                )

            # criou! mostro o protocolo e mando pro detalhe do chamado
            messages.success(request, f"Chamado aberto. Protocolo: {protocolo}")
            return redirect("portal:cidadao_chamado", pk=chamado_id)
    else:
        # GET: form vazio
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
    """Mostra o detalhe do chamado pro cidadao."""
    ch = _chamado_do_cidadao(request, pk)  # ja valida que o chamado eh dele
    ts = ch.sigla_status  # status atual (sigla)

    # aqui decido o que liberar na tela conforme o status:
    pode_obs_foto = ts not in ("CO", "CA")  # so mexe se nao ta concluido nem cancelado
    pode_cancelar = ts in ("AB", "EA")       # so cancela se aberto ou em atendimento
    pode_avaliar = ts == "CO" and ch.nota_avaliacao is None  # avalia so se concluido e sem nota ainda

    # busco o historico e as fotos pra renderizar o detalhe
    historicos = db.buscar_historicos(pk)
    fotos = db.buscar_fotos(pk)

    # observacoes = os registros do historico que tem texto em observacao
    observacoes = [h for h in historicos if h.observacao]
    # historico_status = so mudancas reais de status (pula observacoes que reusam o mesmo status)
    historico_status = []
    prev_id = None
    for h in historicos:
        if h.id_status.pk != prev_id or h.observacao:
            historico_status.append(h)
            prev_id = h.id_status.pk

    return render(
        request,
        "portal/cidadao/chamado_detalhe.html",
        {
            "ch": ch,
            "historicos": historicos,
            "historico_status": historico_status,
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
    """Adiciona uma observacao no chamado (cidadao)."""
    ch = _chamado_do_cidadao(request, pk)  # confere dono
    # se ja ta concluido ou cancelado nao deixo mexer (404 pra esconder)
    if ch.sigla_status in ("CO", "CA"):
        raise Http404()
    form_o = ObservacaoForm(request.POST)
    if form_o.is_valid():
        # service registra a observacao (gera entrada no historico)
        chamado_service.adicionar_observacao(
            pk, form_o.cleaned_data["texto"],
        )
        messages.success(request, "Observação registrada.")
    return redirect("portal:cidadao_chamado", pk=pk)  # volto pro detalhe


@autenticado
@perfis("CID")
@require_http_methods(["POST"])
def cidadao_chamado_foto(request, pk):
    """Upload de foto pra um chamado (cidadao)."""
    ch = _chamado_do_cidadao(request, pk)  # confere dono
    if ch.sigla_status in ("CO", "CA"):  # concluido/cancelado nao aceita foto
        raise Http404()
    form_f = FotoForm(request.POST, request.FILES)
    # so sigo se o form ta ok E veio mesmo um arquivo de foto
    if form_f.is_valid() and request.FILES.get("foto"):
        try:
            chamado_service.adicionar_foto(pk, request.FILES["foto"], request=request)
        except ValueError as e:
            # foto invalida (tipo/tamanho) -> service estoura ValueError
            messages.error(request, str(e))
        else:
            messages.success(request, "Foto adicionada.")
    else:
        # caiu aqui: ou nao mandou foto, ou o form tem erros
        if not request.FILES.get("foto"):
            messages.error(request, "Selecione uma imagem.")
        else:
            # jogo na tela cada erro de validacao do form
            for errors in form_f.errors.values():
                for error in errors:
                    messages.error(request, error)
    return redirect("portal:cidadao_chamado", pk=pk)


@autenticado
@perfis("CID")
@require_http_methods(["POST"])
def cidadao_chamado_cancelar(request, pk):
    ch = _chamado_do_cidadao(request, pk)  # confere dono
    # so deixo cancelar se ta aberto (AB) ou em atendimento (EA)
    if ch.sigla_status not in ("AB", "EA"):
        raise Http404()
    form_c = CancelarChamadoForm(request.POST)
    if form_c.is_valid():
        try:
            # service faz o cancelamento (novo INSERT no historico com status CA)
            chamado_service.cancelar_chamado_cidadao(pk, form_c.cleaned_data["motivo"])
        except ValueError as e:
            # se nao deu pra cancelar, mostro o erro e volto pro detalhe
            messages.error(request, str(e))
            return redirect("portal:cidadao_chamado", pk=pk)
        messages.success(request, "Chamado cancelado.")
    return redirect("portal:cidadao_chamado", pk=pk)


@autenticado
@perfis("CID")
@require_http_methods(["POST"])
def cidadao_chamado_avaliar(request, pk):
    """Avalia chamado concluido (nota 1-5 + comentario opcional)."""
    ch = _chamado_do_cidadao(request, pk)  # confere dono
    # so avalia se ta concluido (CO) e ainda nao tem nota (nao deixo avaliar 2x)
    if ch.sigla_status != "CO" or ch.nota_avaliacao is not None:
        raise Http404()
    form_a = AvaliacaoForm(request.POST)
    if form_a.is_valid():
        # gravo a nota e o comentario (comentario vazio vira None)
        db.avaliar_chamado(pk, form_a.cleaned_data["nota"], form_a.cleaned_data.get("comentario") or None)
        messages.success(request, "Avaliação registrada.")
    return redirect("portal:cidadao_chamado", pk=pk)


# ------------------------------------------------------------------
# Notificacoes do cidadao (GET/POST /cidadao/notificacoes/)
# ------------------------------------------------------------------

@autenticado
@perfis("CID")
@require_http_methods(["GET", "POST"])
def cidadao_notificacoes(request):
    """Lista e exclui as notificacoes do cidadao logado.

    Quem cria as notificacao eh o Trigger 2B toda vez que o status de um
    chamado muda. Aqui eu so vejo e deleto, nunca crio.

    Seguranca (lembrete): a subquery no WHERE garante que o cidadao so ve
    notificacao dos chamados dele. O DELETE usa a mesma subquery pra
    impedir que ele mexa no POST e apague notificacao dos outros.
    """
    uid = request.portal_user.pk  # id do cidadao logado

    lista = db.listar_notificacoes_cidadao(uid)

    # marco como lidas as que ainda nao tinham sido lidas
    nids = [n.pk for n in lista if not n.lida]
    if nids:
        db.marcar_notificacoes_lidas(nids)

    if request.method == "POST":
        # POST = excluir uma notificacao; passo uid_cidadao pra so apagar a dele
        nid = request.POST.get("excluir")
        if nid:
            db.excluir_notificacao(nid, uid_cidadao=uid)
            messages.info(request, "Notificação removida.")
        return redirect("portal:cidadao_notificacoes")  # PRG depois do POST

    return render(
        request,
        "portal/cidadao/notificacoes.html",
        {"lista": lista},
    )
