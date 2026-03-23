from django.contrib import messages
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
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
from portal.models import (
    BairroRegiao,
    CategoriaServico,
    Chamado,
    FotoChamado,
    HistoricoChamado,
    Notificacao,
    ObservacaoChamado,
    StatusChamado,
)
from portal.utils import proximo_protocolo, salvar_foto_upload, tipo_status


def _chamado_do_cidadao(request, pk):
    ch = get_object_or_404(Chamado, pk=pk)
    if ch.id_usuario_id != request.portal_user.pk:
        raise Http404()
    return ch


@autenticado
@perfis("CID")
def cidadao_chamados_lista(request):
    qs = (
        Chamado.objects.filter(id_usuario=request.portal_user)
        .select_related("id_status", "id_servico", "id_bairro")
        .order_by("-dt_abertura")
    )

    # Filters
    st_filter = request.GET.get("status")
    if st_filter:
        qs = qs.filter(id_status__tipo_status=st_filter)
    
    dt_filter = request.GET.get("data")
    if dt_filter:
        qs = qs.filter(dt_abertura__date=dt_filter)
        
    q_filter = request.GET.get("q")
    if q_filter:
        qs = qs.filter(protocolo__icontains=q_filter)

    # Stats calculation (Semáforo)
    # We calculate stats on the unfiltered list of user's active tickets
    base_qs = Chamado.objects.filter(id_usuario=request.portal_user)
    stats = {"no_prazo": 0, "atencao": 0, "critico": 0}
    now = timezone.now()
    
    for ch in base_qs.select_related("id_servico"):
        dias = (now - ch.dt_abertura).days
        s = ch.id_servico
        if dias >= s.prazo_vermelho_dias:
            stats["critico"] += 1
        elif dias >= s.prazo_amarelo_dias:
            stats["atencao"] += 1
        else:
            stats["no_prazo"] += 1

    return render(
        request,
        "portal/cidadao/dashboard.html",
        {"lista": qs, "stats": stats},
    )


@autenticado
@perfis("CID")
@require_http_methods(["GET", "POST"])
def cidadao_chamado_novo(request):
    categorias = CategoriaServico.objects.filter(ativo=True).prefetch_related(
        "servicos"
    )
    bairros = BairroRegiao.objects.filter(ativo=True).order_by("nome")

    if request.method == "POST":
        form = ChamadoNovoForm(request.POST, request.FILES)
        if form.is_valid():
            d = form.cleaned_data
            try:
                url = salvar_foto_upload(request, request.FILES.get("foto"))
            except ValueError as e:
                messages.error(request, str(e))
                return render(
                    request,
                    "portal/cidadao/novo_chamado.html",
                    {"form": form, "categorias": categorias, "bairros": bairros},
                )
            ab = StatusChamado.objects.get(tipo_status="AB")
            now = timezone.now()
            with transaction.atomic():
                ch = Chamado.objects.create(
                    protocolo=proximo_protocolo(),
                    prioridade=0,
                    rua=d["rua"],
                    numero=d["numero"],
                    complemento=d.get("complemento") or None,
                    ponto_referencia=d.get("ponto_referencia") or None,
                    descricao=d["descricao"],
                    dt_abertura=now,
                    atualizado_em=now,
                    id_usuario=request.portal_user,
                    id_servico=d["id_servico"],
                    id_status=ab,
                    id_bairro=d["id_bairro"],
                )
                FotoChamado.objects.create(
                    id_chamado=ch,
                    url_foto=url,
                    dt_upload=now,
                )
            messages.success(
                request,
                f"Chamado aberto. Protocolo: {ch.protocolo}",
            )
            return redirect("portal:cidadao_chamado", pk=ch.pk)
    else:
        form = ChamadoNovoForm()
    return render(
        request, 
        "portal/cidadao/novo_chamado.html", 
        {"form": form, "categorias": categorias, "bairros": bairros}
    )


@autenticado
@perfis("CID")
@require_http_methods(["GET", "POST"])
def cidadao_chamado_detalhe(request, pk):
    ch = _chamado_do_cidadao(request, pk)
    ts = tipo_status(ch)
    pode_obs_foto = ts not in ("CO", "CA")
    pode_cancelar = ts in ("AB", "AN")
    pode_avaliar = ts == "CO" and ch.nota_avaliacao is None

    if request.method == "POST":
        acao = request.POST.get("acao")
        if acao == "obs" and pode_obs_foto:
            form_o = ObservacaoForm(request.POST)
            if form_o.is_valid():
                ObservacaoChamado.objects.create(
                    id_chamado=ch,
                    id_usuario_autor=request.portal_user,
                    texto_observacao=form_o.cleaned_data["texto"],
                    criado_em=timezone.now(),
                )
                messages.success(request, "Observação registrada.")
            return redirect("portal:cidadao_chamado", pk=pk)
        if acao == "foto" and pode_obs_foto:
            form_f = FotoForm(request.POST, request.FILES)
            if form_f.is_valid() and request.FILES.get("foto"):
                try:
                    url = salvar_foto_upload(request, request.FILES["foto"])
                except ValueError as e:
                    messages.error(request, str(e))
                else:
                    FotoChamado.objects.create(
                        id_chamado=ch,
                        url_foto=url,
                        dt_upload=timezone.now(),
                    )
                    messages.success(request, "Foto adicionada.")
            return redirect("portal:cidadao_chamado", pk=pk)
        if acao == "cancelar" and pode_cancelar:
            form_c = CancelarChamadoForm(request.POST)
            if form_c.is_valid():
                ca = StatusChamado.objects.get(tipo_status="CA")
                ch.id_status = ca
                ch.resolucao = form_c.cleaned_data["motivo"]
                ch.save()
                messages.success(request, "Chamado cancelado.")
            return redirect("portal:cidadao_chamado", pk=pk)
        if acao == "avaliar" and pode_avaliar:
            form_a = AvaliacaoForm(request.POST)
            if form_a.is_valid():
                ch.nota_avaliacao = form_a.cleaned_data["nota"]
                ch.comentario_avaliacao = (
                    form_a.cleaned_data.get("comentario") or None
                )
                ch.dt_avaliacao = timezone.now()
                ch.save(
                    update_fields=[
                        "nota_avaliacao",
                        "comentario_avaliacao",
                        "dt_avaliacao",
                    ]
                )
                messages.success(request, "Avaliação registrada.")
            return redirect("portal:cidadao_chamado", pk=pk)

    historicos = HistoricoChamado.objects.filter(id_chamado=ch).order_by(
        "dt_alteracao"
    )
    fotos = FotoChamado.objects.filter(id_chamado=ch).order_by("dt_upload")
    obs = ObservacaoChamado.objects.filter(id_chamado=ch).order_by(
        "criado_em"
    ).select_related("id_usuario_autor")

    return render(
        request,
        "portal/cidadao/chamado_detalhe.html",
        {
            "ch": ch,
            "historicos": historicos,
            "fotos": fotos,
            "observacoes": obs,
            "tipo_status": ts,
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
    qs = Notificacao.objects.filter(
        id_usuario=request.portal_user,
        arquivada=False,
    ).order_by("-dt_envio")
    if request.method == "POST":
        nid = request.POST.get("excluir")
        if nid:
            Notificacao.objects.filter(
                pk=nid,
                id_usuario=request.portal_user,
            ).delete()
            messages.info(request, "Notificação removida.")
        return redirect("portal:cidadao_notificacoes")
    return render(
        request,
        "portal/cidadao/notificacoes.html",
        {"lista": qs},
    )
