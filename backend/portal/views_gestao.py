from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.db import connection
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
from portal.models import BairroRegiao, CategoriaServico, Servico, Usuario


@perfis("ADM")
def gestao_estatisticas(request):
    linhas = []
    try:
        with connection.cursor() as c:
            c.execute(
                """
                SELECT categoria, bairro, tipo_status, status_descricao, total_chamados
                FROM vw_estatisticas_chamados
                ORDER BY 1, 2, 3
                """
            )
            nomes = [col[0] for col in c.description]
            linhas = [dict(zip(nomes, row)) for row in c.fetchall()]
    except ProgrammingError:
        messages.warning(
            request,
            "View vw_estatisticas_chamados indisponível. Rode o script SQL em database/.",
        )
    return render(
        request,
        "portal/gestao/estatisticas.html",
        {"linhas": linhas},
    )


@perfis("ADM")
@require_http_methods(["GET", "POST"])
def gestao_categorias(request):
    if request.method == "POST":
        if request.POST.get("desativar"):
            cat = get_object_or_404(
                CategoriaServico, pk=request.POST["desativar"]
            )
            cat.ativo = False
            cat.save(update_fields=["ativo"])
            messages.info(request, "Categoria inativada.")
        else:
            form = CategoriaForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Categoria criada.")
            else:
                messages.error(request, "Corrija os campos da nova categoria.")
        return redirect("portal:gestao_categorias")
    form = CategoriaForm()
    lista = CategoriaServico.objects.order_by("nome")
    return render(
        request,
        "portal/gestao/categorias.html",
        {"form": form, "lista": lista},
    )


@perfis("ADM")
@require_http_methods(["GET", "POST"])
def gestao_categoria_editar(request, pk):
    cat = get_object_or_404(CategoriaServico, pk=pk)
    if request.method == "POST":
        form = CategoriaForm(request.POST, instance=cat)
        if form.is_valid():
            form.save()
            messages.success(request, "Salvo.")
            return redirect("portal:gestao_categorias")
    else:
        form = CategoriaForm(instance=cat)
    return render(
        request,
        "portal/gestao/categoria_form.html",
        {"form": form, "cat": cat},
    )


@perfis("ADM")
@require_http_methods(["GET", "POST"])
def gestao_servicos(request):
    if request.method == "POST":
        form = ServicoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Serviço criado.")
        else:
            messages.error(request, "Corrija os campos do novo serviço.")
        return redirect("portal:gestao_servicos")
    form = ServicoForm()
    lista = Servico.objects.select_related("id_categoria").order_by(
        "id_categoria__nome", "nome"
    )
    return render(
        request,
        "portal/gestao/servicos.html",
        {"form": form, "lista": lista},
    )


@perfis("ADM")
@require_http_methods(["GET", "POST"])
def gestao_servico_editar(request, pk):
    srv = get_object_or_404(Servico, pk=pk)
    if request.method == "POST":
        form = ServicoForm(request.POST, instance=srv)
        if form.is_valid():
            form.save()
            messages.success(request, "Salvo.")
            return redirect("portal:gestao_servicos")
    else:
        form = ServicoForm(instance=srv)
    return render(
        request,
        "portal/gestao/servico_form.html",
        {"form": form, "srv": srv},
    )


@perfis("ADM")
@require_http_methods(["GET", "POST"])
def gestao_bairros(request):
    if request.method == "POST":
        form = BairroForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Bairro criado.")
        else:
            messages.error(request, "Corrija os campos do novo bairro.")
        return redirect("portal:gestao_bairros")
    form = BairroForm()
    lista = BairroRegiao.objects.order_by("nome")
    return render(
        request,
        "portal/gestao/bairros.html",
        {"form": form, "lista": lista},
    )


@perfis("ADM")
@require_http_methods(["GET", "POST"])
def gestao_bairro_editar(request, pk):
    b = get_object_or_404(BairroRegiao, pk=pk)
    if request.method == "POST":
        form = BairroForm(request.POST, instance=b)
        if form.is_valid():
            form.save()
            messages.success(request, "Salvo.")
            return redirect("portal:gestao_bairros")
    else:
        form = BairroForm(instance=b)
    return render(
        request,
        "portal/gestao/bairro_form.html",
        {"form": form, "bairro": b},
    )


@perfis("ADM")
@require_http_methods(["GET", "POST"])
def gestao_colaboradores(request):
    if request.method == "POST":
        form = ColaboradorNovoForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            if Usuario.objects.filter(
                email__iexact=d["email"].lower()
            ).exists() or Usuario.objects.filter(cpf=d["cpf"]).exists():
                messages.error(request, "E-mail ou CPF já existe.")
            else:
                Usuario.objects.create(
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
                )
                messages.success(request, "Colaborador criado. Deve trocar a senha no 1º acesso.")
        return redirect("portal:gestao_colaboradores")
    form = ColaboradorNovoForm()
    lista = (
        Usuario.objects.annotate(pc=Trim("perfil"))
        .filter(pc="COL", ativo=True)
        .order_by("nome_completo")
    )
    return render(
        request,
        "portal/gestao/colaboradores.html",
        {"form": form, "lista": lista},
    )


@perfis("ADM")
@require_http_methods(["POST"])
def gestao_servico_desativar(request, pk):
    s = get_object_or_404(Servico, pk=pk)
    s.ativo = False
    s.save(update_fields=["ativo"])
    messages.info(request, "Serviço inativado.")
    return redirect("portal:gestao_servicos")


@perfis("ADM")
@require_http_methods(["POST"])
def gestao_bairro_desativar(request, pk):
    b = get_object_or_404(BairroRegiao, pk=pk)
    b.ativo = False
    b.save(update_fields=["ativo"])
    messages.info(request, "Bairro inativado.")
    return redirect("portal:gestao_bairros")
