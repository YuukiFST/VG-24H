from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from portal.decorators import perfil_codigo, perfis
from portal.forms import EquipeStatusForm, FotoForm, ObservacaoForm
from portal.models import (
    Bairro,
    Chamado,
    FotoChamado,
    HistoricoChamado,
    StatusChamado,
)
from portal.utils import cor_semaforo, salvar_foto_upload, sigla_status


def _int_none(v):
    if v is None or v == "":
        return None
    try:
        return int(v)
    except ValueError:
        return None


@perfis("COL", "GES")
def equipe_chamados_lista(request):
    qs = Chamado.objects.select_related(
        "id_servico", "id_bairro", "id_cidadao"
    ).prefetch_related("historicos__id_status").order_by("-dt_abertura")

    # Calculate global stats (Semáforo) before filtering
    stats = {"no_prazo": 0, "atencao": 0, "critico": 0}
    now = timezone.now()
    for ch in qs:
        dias = (now - ch.dt_abertura).days
        s = ch.id_servico
        if dias >= s.prazo_vermelho_dias:
            stats["critico"] += 1
        elif dias >= s.prazo_amarelo_dias:
            stats["atencao"] += 1
        else:
            stats["no_prazo"] += 1
    total_count = qs.count()

    # Apply Filters
    bairro = _int_none(request.GET.get("bairro"))
    st = _int_none(request.GET.get("status"))
    d0 = request.GET.get("de")
    d1 = request.GET.get("ate")
    if bairro:
        qs = qs.filter(id_bairro_id=bairro)
    if st:
        from portal.models import HistoricoChamado
        from django.db.models import Subquery, OuterRef
        latest_status = HistoricoChamado.objects.filter(
            id_chamado=OuterRef("pk")
        ).order_by("-dt_alteracao").values("id_status_id")[:1]
        qs = qs.annotate(_st_id=Subquery(latest_status)).filter(_st_id=st)
    if d0:
        qs = qs.filter(dt_abertura__date__gte=d0)
    if d1:
        qs = qs.filter(dt_abertura__date__lte=d1)

    linhas = []
    for ch in qs:
        linhas.append({"ch": ch, "cor": cor_semaforo(ch)})

    return render(
        request,
        "portal/equipe/dashboard.html",
        {
            "linhas": linhas,
            "stats": stats,
            "total_count": total_count,
            "bairros": Bairro.objects.filter(ativo=True).order_by("nome_bairro"),
            "statuses": StatusChamado.objects.order_by("id_status"),
            "filtro_bairro": bairro,
            "filtro_status": st,
            "filtro_de": d0 or "",
            "filtro_ate": d1 or "",
        },
    )


@perfis("COL", "GES")
@require_http_methods(["GET", "POST"])
def equipe_chamado_detalhe(request, pk):
    ch = get_object_or_404(
        Chamado.objects.select_related(
            "id_servico", "id_servico__id_categoria", "id_cidadao", "id_bairro"
        ).prefetch_related("historicos__id_status"),
        pk=pk,
    )
    p = perfil_codigo(request.portal_user)
    ts = sigla_status(ch)
    bloqueia_status_col = p == "COL" and ts in ("CO", "CA")
    pode_status = not bloqueia_status_col

    form_status_erro = None
    if request.method == "POST":
        acao = request.POST.get("acao")
        if acao == "status" and pode_status:
            form_s = EquipeStatusForm(request.POST)
            if form_s.is_valid():
                novo = form_s.cleaned_data["id_status"]
                # Insert historico for status change
                HistoricoChamado.objects.create(
                    id_chamado=ch,
                    id_servidor=request.portal_user,
                    id_status=novo,
                    dt_alteracao=timezone.now(),
                )
                ch.resolucao = form_s.cleaned_data.get("resolucao") or None
                # Priority
                pri = request.POST.get("prioridade")
                if pri is not None:
                    try:
                        ch.prioridade = max(0, min(5, int(pri)))
                    except (ValueError, TypeError):
                        pass
                ch.save()
                messages.success(request, "Status atualizado.")
                return redirect("portal:equipe_chamado", pk=pk)
            form_status_erro = form_s
            for e in form_s.non_field_errors():
                messages.error(request, e)
        if acao == "obs":
            form_o = ObservacaoForm(request.POST)
            if form_o.is_valid():
                # Observação centralizada em historico_chamado (Plano v6)
                HistoricoChamado.objects.create(
                    id_chamado=ch,
                    id_servidor=request.portal_user,
                    id_status=ch.status_atual,
                    observacao=form_o.cleaned_data["texto"],
                    dt_alteracao=timezone.now(),
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

    historicos = (
        HistoricoChamado.objects.filter(id_chamado=ch)
        .select_related("id_servidor", "id_status")
        .order_by("dt_alteracao")
    )
    fotos = FotoChamado.objects.filter(id_chamado=ch).order_by("dt_upload")

    # Observações = registros com observacao preenchida
    observacoes = historicos.filter(observacao__isnull=False).exclude(observacao="")

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
