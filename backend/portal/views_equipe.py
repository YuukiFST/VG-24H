from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from portal.decorators import perfil_codigo, perfis
from portal.forms import EquipeStatusForm, FotoForm, ObservacaoForm
from portal.models import (
    Chamado,
    FotoChamado,
    HistoricoChamado,
    ObservacaoChamado,
)
from portal.utils import cor_semaforo, salvar_foto_upload, tipo_status


def _int_none(v):
    if v is None or v == "":
        return None
    try:
        return int(v)
    except ValueError:
        return None


@perfis("COL", "ADM")
def equipe_chamados_lista(request):
    qs = Chamado.objects.select_related(
        "id_status", "id_servico", "id_bairro", "id_usuario"
    ).order_by("-dt_abertura")
    bairro = _int_none(request.GET.get("bairro"))
    st = _int_none(request.GET.get("status"))
    d0 = request.GET.get("de")
    d1 = request.GET.get("ate")
    if bairro:
        qs = qs.filter(id_bairro_id=bairro)
    if st:
        qs = qs.filter(id_status_id=st)
    if d0:
        qs = qs.filter(dt_abertura__date__gte=d0)
    if d1:
        qs = qs.filter(dt_abertura__date__lte=d1)

    linhas = []
    for ch in qs:
        linhas.append({"ch": ch, "cor": cor_semaforo(ch)})

    from portal.models import BairroRegiao, StatusChamado

    return render(
        request,
        "portal/equipe/chamados_lista.html",
        {
            "linhas": linhas,
            "bairros": BairroRegiao.objects.filter(ativo=True).order_by("nome"),
            "statuses": StatusChamado.objects.order_by("id_status"),
            "filtro_bairro": bairro,
            "filtro_status": st,
            "filtro_de": d0 or "",
            "filtro_ate": d1 or "",
        },
    )


@perfis("COL", "ADM")
@require_http_methods(["GET", "POST"])
def equipe_chamado_detalhe(request, pk):
    ch = get_object_or_404(
        Chamado.objects.select_related("id_status", "id_servico", "id_usuario"),
        pk=pk,
    )
    p = perfil_codigo(request.portal_user)
    ts = tipo_status(ch)
    bloqueia_status_col = p == "COL" and ts in ("CO", "CA")
    pode_status = not bloqueia_status_col

    form_status_erro = None
    if request.method == "POST":
        acao = request.POST.get("acao")
        if acao == "status" and pode_status:
            form_s = EquipeStatusForm(request.POST)
            if form_s.is_valid():
                novo = form_s.cleaned_data["id_status"]
                ch.id_status = novo
                ch.resolucao = form_s.cleaned_data.get("resolucao") or None
                ch.save()
                messages.success(request, "Status atualizado.")
                return redirect("portal:equipe_chamado", pk=pk)
            form_status_erro = form_s
            for e in form_s.non_field_errors():
                messages.error(request, e)
        if acao == "obs":
            form_o = ObservacaoForm(request.POST)
            if form_o.is_valid():
                ObservacaoChamado.objects.create(
                    id_chamado=ch,
                    id_usuario_autor=request.portal_user,
                    texto_observacao=form_o.cleaned_data["texto"],
                    criado_em=timezone.now(),
                )
                messages.success(request, "Observação registrada.")
            return redirect("portal:equipe_chamado", pk=pk)
        if acao == "foto":
            if request.FILES.get("foto"):
                form_f = FotoForm(request.POST, request.FILES)
                if form_f.is_valid():
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
                        messages.success(request, "Foto registrada.")
            else:
                messages.error(request, "Selecione uma imagem.")
            return redirect("portal:equipe_chamado", pk=pk)

    historicos = HistoricoChamado.objects.filter(id_chamado=ch).order_by(
        "dt_alteracao"
    )
    fotos = FotoChamado.objects.filter(id_chamado=ch).order_by("dt_upload")
    obs = ObservacaoChamado.objects.filter(id_chamado=ch).order_by(
        "criado_em"
    ).select_related("id_usuario_autor")

    if form_status_erro:
        form_status = form_status_erro
    else:
        form_status = EquipeStatusForm(
            initial={
                "id_status": ch.id_status,
                "resolucao": ch.resolucao or "",
            }
        )

    return render(
        request,
        "portal/equipe/chamado_detalhe.html",
        {
            "ch": ch,
            "tipo_status": ts,
            "pode_status": pode_status,
            "bloqueia_status_col": bloqueia_status_col,
            "historicos": historicos,
            "fotos": fotos,
            "observacoes": obs,
            "form_status": form_status,
            "form_obs": ObservacaoForm(),
            "form_foto": FotoForm(),
        },
    )
