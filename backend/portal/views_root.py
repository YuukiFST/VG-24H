from django.db.models import Q
from django.shortcuts import redirect, render

from portal.decorators import perfil_codigo
from portal.models import CategoriaServico, Servico


def catalogo_servicos(request):
    q_raw = (request.GET.get("q") or "").strip()
    blocos = []
    for cat in CategoriaServico.objects.filter(ativo=True).order_by("nome"):
        base = Servico.objects.filter(id_categoria=cat, ativo=True)
        if not q_raw:
            servicos = list(base.order_by("nome"))
        else:
            q_lower = q_raw.lower()
            cat_match = q_lower in cat.nome.lower()
            if cat.descricao:
                cat_match = cat_match or q_lower in cat.descricao.lower()
            svc_q = base.filter(
                Q(nome__icontains=q_raw) | Q(descricao__icontains=q_raw)
            )
            if cat_match:
                servicos = list(base.order_by("nome"))
            elif svc_q.exists():
                servicos = list(svc_q.order_by("nome"))
            else:
                continue
        blocos.append((cat, servicos))
    return render(
        request,
        "portal/public/catalogo_servicos.html",
        {"blocos": blocos, "q": q_raw},
    )


def root_view(request):
    servicos = Servico.objects.filter(ativo=True).order_by("nome")[:5]
    from django.db.models import Count
    from portal.models import Chamado, BairroRegiao
    
    # Basic stats for the landing page
    stats = {
        "total_resolvidos": Chamado.objects.filter(id_status__tipo_status="CO").count(),
        "total_bairros": BairroRegiao.objects.filter(ativo=True).count(),
        "total_servicos": Servico.objects.filter(ativo=True).count(),
    }
    
    return render(
        request, 
        "portal/root.html", 
        {"servicos": servicos, "stats": stats}
    )
