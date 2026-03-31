from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.db import IntegrityError
from django.db.utils import ProgrammingError
from django.db.models.functions import Trim
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from portal.decorators import perfis
from portal.forms import (
    BairroForm,
    CategoriaForm,
    ColaboradorNovoForm,
    ServicoForm,
)
from portal.models import (
    Bairro,
    BannerPublicacao,
    CategoriaServico,
    Secretaria,
    Servico,
    Servidor,
)


# ─── Estatísticas ────────────────────────────────────────────
@perfis("GES")
def gestao_estatisticas(request):
    from django.db import connection

    rows = []
    try:
        with connection.cursor() as c:
            c.execute("SELECT * FROM vw_estatisticas_chamados ORDER BY categoria, bairro")
            cols = [d[0] for d in c.description]
            rows = [dict(zip(cols, r)) for r in c.fetchall()]
    except ProgrammingError:
        pass
    return render(
        request,
        "portal/gestao/estatisticas.html",
        {"rows": rows},
    )


# ─── Categorias ──────────────────────────────────────────────
@perfis("GES")
@require_http_methods(["GET", "POST"])
def gestao_categorias(request):
    if request.method == "POST":
        form = CategoriaForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            # Vincular à primeira secretaria disponível
            obj.id_secretaria = Secretaria.objects.first()
            obj.save()
            messages.success(request, "Categoria criada.")
        return redirect("portal:gestao_categorias")
    form = CategoriaForm()
    lista = CategoriaServico.objects.filter(ativo=True).order_by("nome")
    return render(
        request,
        "portal/gestao/categorias.html",
        {"form": form, "lista": lista},
    )


@perfis("GES")
@require_http_methods(["GET", "POST"])
def gestao_categoria_edit(request, pk):
    obj = get_object_or_404(CategoriaServico, pk=pk)
    if request.method == "POST":
        form = CategoriaForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Categoria atualizada.")
            return redirect("portal:gestao_categorias")
    else:
        form = CategoriaForm(instance=obj)
    return render(
        request,
        "portal/gestao/categoria_form.html",
        {"form": form, "obj": obj},
    )


# ─── Serviços ────────────────────────────────────────────────
@perfis("GES")
@require_http_methods(["GET", "POST"])
def gestao_servicos(request):
    if request.method == "POST":
        form = ServicoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Serviço criado.")
        return redirect("portal:gestao_servicos")
    form = ServicoForm()
    lista = Servico.objects.filter(ativo=True).select_related("id_categoria").order_by("nome")
    return render(
        request,
        "portal/gestao/servicos.html",
        {"form": form, "lista": lista},
    )


@perfis("GES")
@require_http_methods(["GET", "POST"])
def gestao_servico_edit(request, pk):
    obj = get_object_or_404(Servico, pk=pk)
    if request.method == "POST":
        form = ServicoForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Serviço atualizado.")
            return redirect("portal:gestao_servicos")
    else:
        form = ServicoForm(instance=obj)
    return render(
        request,
        "portal/gestao/servico_form.html",
        {"form": form, "obj": obj},
    )


# ─── Bairros ─────────────────────────────────────────────────
@perfis("GES")
@require_http_methods(["GET", "POST"])
def gestao_bairros(request):
    if request.method == "POST":
        form = BairroForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Bairro criado.")
        return redirect("portal:gestao_bairros")
    form = BairroForm()
    lista = Bairro.objects.filter(ativo=True).order_by("nome_bairro")
    return render(
        request,
        "portal/gestao/bairros.html",
        {"form": form, "lista": lista},
    )


@perfis("GES")
@require_http_methods(["GET", "POST"])
def gestao_bairro_edit(request, pk):
    obj = get_object_or_404(Bairro, pk=pk)
    if request.method == "POST":
        form = BairroForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Bairro atualizado.")
            return redirect("portal:gestao_bairros")
    else:
        form = BairroForm(instance=obj)
    return render(
        request,
        "portal/gestao/bairro_form.html",
        {"form": form, "obj": obj},
    )


# ─── Colaboradores ───────────────────────────────────────────
@perfis("GES")
@require_http_methods(["GET", "POST"])
def gestao_colaboradores(request):
    if request.method == "POST":
        form = ColaboradorNovoForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            if Servidor.objects.filter(
                email__iexact=d["email"].lower()
            ).exists() or Servidor.objects.filter(cpf=d["cpf"]).exists():
                messages.error(request, "E-mail ou CPF já existe.")
            else:
                # Vincular à primeira secretaria disponível
                sec = Secretaria.objects.first()
                Servidor.objects.create(
                    nome_completo=d["nome_completo"],
                    cpf=d["cpf"],
                    dt_nascimento=d["dt_nascimento"],
                    telefone=d["telefone"],
                    email=d["email"].lower(),
                    senha_hash=make_password(d["senha_provisoria"]),
                    senha_temporaria="1",
                    perfil="COL",
                    ativo=True,
                    dt_cadastro=timezone.now(),
                    id_secretaria=sec,
                )
                messages.success(request, "Colaborador criado. Deve trocar a senha no 1º acesso.")
        return redirect("portal:gestao_colaboradores")
    form = ColaboradorNovoForm()
    lista = (
        Servidor.objects.filter(perfil="COL")
        .order_by("-ativo", "nome_completo")
    )
    return render(
        request,
        "portal/gestao/colaboradores.html",
        {"form": form, "lista": lista},
    )


@perfis("GES")
@require_http_methods(["POST"])
def gestao_colaborador_toggle(request, pk):
    colab = get_object_or_404(Servidor, pk=pk)
    colab.ativo = not colab.ativo
    colab.save(update_fields=["ativo"])
    status = "ativado" if colab.ativo else "inativado"
    messages.success(request, f"Colaborador {colab.nome_completo} {status}.")
    return redirect("portal:gestao_colaboradores")


@perfis("GES")
@require_http_methods(["POST"])
def gestao_servico_desativar(request, pk):
    s = get_object_or_404(Servico, pk=pk)
    s.ativo = False
    s.save(update_fields=["ativo"])
    messages.info(request, "Serviço inativado.")
    return redirect("portal:gestao_servicos")


@perfis("GES")
@require_http_methods(["POST"])
def gestao_bairro_desativar(request, pk):
    b = get_object_or_404(Bairro, pk=pk)
    b.ativo = False
    b.save(update_fields=["ativo"])
    messages.info(request, "Bairro inativado.")
    return redirect("portal:gestao_bairros")


# ─── Banners ─────────────────────────────────────────────────
@perfis("GES")
def gestao_banners(request):
    banners = BannerPublicacao.objects.all().order_by("ordem", "-dt_criacao")
    return render(request, "portal/gestao/banners.html", {"banners": banners})


@perfis("GES")
@require_http_methods(["GET", "POST"])
def gestao_banner_novo(request):
    if request.method == "POST":
        titulo = request.POST.get("titulo", "").strip()
        descricao = request.POST.get("descricao", "").strip() or None
        link = request.POST.get("link", "").strip() or None
        ordem = int(request.POST.get("ordem", 0) or 0)
        foto = request.FILES.get("imagem")

        if not titulo:
            messages.error(request, "Título é obrigatório.")
            return redirect("portal:gestao_banner_novo")

        if not foto:
            messages.error(request, "Imagem é obrigatória.")
            return redirect("portal:gestao_banner_novo")

        from portal.utils import salvar_foto_upload
        url_imagem = salvar_foto_upload(foto)

        BannerPublicacao.objects.create(
            titulo=titulo,
            descricao=descricao,
            url_imagem=url_imagem,
            link=link,
            ordem=ordem,
        )
        messages.success(request, "Banner criado com sucesso!")
        return redirect("portal:gestao_banners")
    return render(request, "portal/gestao/banner_form.html", {"banner": None})


@perfis("GES")
@require_http_methods(["GET", "POST"])
def gestao_banner_editar(request, pk):
    banner = get_object_or_404(BannerPublicacao, pk=pk)
    if request.method == "POST":
        banner.titulo = request.POST.get("titulo", "").strip() or banner.titulo
        banner.descricao = request.POST.get("descricao", "").strip() or None
        banner.link = request.POST.get("link", "").strip() or None
        banner.ordem = int(request.POST.get("ordem", 0) or 0)

        foto = request.FILES.get("imagem")
        if foto:
            from portal.utils import salvar_foto_upload
            banner.url_imagem = salvar_foto_upload(foto)

        banner.save()
        messages.success(request, "Banner atualizado!")
        return redirect("portal:gestao_banners")
    return render(request, "portal/gestao/banner_form.html", {"banner": banner})


@perfis("GES")
@require_http_methods(["POST"])
def gestao_banner_excluir(request, pk):
    banner = get_object_or_404(BannerPublicacao, pk=pk)
    banner.delete()
    messages.info(request, "Banner excluído.")
    return redirect("portal:gestao_banners")

