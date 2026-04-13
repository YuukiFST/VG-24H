from django.db.models import Q
from django.shortcuts import redirect, render

from portal.decorators import perfil_codigo
from portal.models import BannerPublicacao, CategoriaServico, Servico


def catalogo_servicos(request):
    q_raw = (request.GET.get("q") or "").strip()
    blocos = []
    try:
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
    except Exception:
        blocos = []
    return render(
        request,
        "portal/public/catalogo_servicos.html",
        {"blocos": blocos, "q": q_raw},
    )


def root_view(request):
    from django.db.models import Count
    from portal.models import Bairro, Chamado

    try:
        from portal.models import HistoricoChamado
        from django.db.models import Subquery, OuterRef

        # Categorias com seus serviços agrupados (para os cards GOV.br)
        categorias = []
        for cat in CategoriaServico.objects.filter(ativo=True).order_by("nome"):
            svcs = list(Servico.objects.filter(id_categoria=cat, ativo=True).order_by("nome"))
            categorias.append({"categoria": cat, "servicos": svcs})

        latest_sigla = HistoricoChamado.objects.filter(
            id_chamado=OuterRef("pk")
        ).order_by("-dt_alteracao").values("id_status__sigla")[:1]
        total_resolvidos = Chamado.objects.annotate(
            _sigla=Subquery(latest_sigla)
        ).filter(_sigla="CO").count()
        stats = {
            "total_resolvidos": total_resolvidos,
            "total_bairros": Bairro.objects.filter(ativo=True).count(),
            "total_servicos": Servico.objects.filter(ativo=True).count(),
        }
    except Exception:
        categorias = []
        stats = {
            "total_resolvidos": 0,
            "total_bairros": 0,
            "total_servicos": 0,
        }

    try:
        banners = list(BannerPublicacao.objects.filter(ativo=True).order_by("ordem", "-dt_criacao"))
    except Exception:
        banners = []

    return render(
        request,
        "portal/root.html",
        {"categorias": categorias, "stats": stats, "banners": banners},
    )
