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
    lista = (
        Chamado.objects.filter(id_usuario=request.portal_user)
        .select_related("id_status", "id_servico", "id_bairro")
        .order_by("-dt_abertura")
    )
    return render(
        request,
        "portal/cidadao/chamados_lista.html",
        {"lista": lista},
    )


@autenticado
@perfis("CID")
@require_http_methods(["GET", "POST"])
def cidadao_chamado_novo(request):
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
                    "portal/cidadao/chamado_form.html",
                    {"form": form},
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
    return render(request, "portal/cidadao/chamado_form.html", {"form": form})


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
