from django.conf import settings
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.core import signing
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from portal.decorators import anonimo, autenticado, perfil_codigo
from portal.forms import (
    CadastroCidadaoForm,
    RecuperarSenhaForm,
    RedefinirSenhaForm,
    TrocaSenhaObrigatoriaForm,
)
from portal.models import Bairro, Cidadao, Servidor


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.portal_user:
        return redirect("portal:root")

    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        senha = request.POST.get("password") or ""

        user = None
        tipo = None

        # Buscar primeiro em Cidadao, depois em Servidor
        try:
            user = Cidadao.objects.get(email__iexact=email, ativo=True)
            tipo = "cidadao"
        except Cidadao.DoesNotExist:
            try:
                user = Servidor.objects.get(email__iexact=email, ativo=True)
                tipo = "servidor"
            except Servidor.DoesNotExist:
                pass

        if user is None:
            messages.error(request, "E-mail ou senha incorretos.")
        elif check_password(senha, user.senha_hash):
            request.session["usuario_id"] = user.pk
            request.session["usuario_tipo"] = tipo
            if (user.senha_temporaria or "").strip():
                request.session["forcar_troca_senha"] = True
                return redirect("portal:troca_senha_obrigatoria")
            messages.success(request, f"Olá, {user.nome_completo}.")
            return redirect("portal:root")
        else:
            messages.error(request, "E-mail ou senha incorretos.")

    return render(request, "portal/auth/login.html")


@require_http_methods(["POST"])
def logout_view(request):
    request.session.flush()
    messages.info(request, "Sessão encerrada.")
    return redirect("portal:login")


@anonimo
@require_http_methods(["GET", "POST"])
def cadastro_view(request):
    try:
        bairros = list(Bairro.objects.filter(ativo=True).order_by("nome_bairro"))
    except Exception:
        # Mock data if DB tables are not ready
        class MockBairro:
            def __init__(self, id, n):
                self.pk = id
                self.nome_bairro = n
        bairros = [MockBairro(1, "Centro"), MockBairro(2, "Cristo Rei"), MockBairro(3, "Vila Arthur")]

    if request.method == "POST":
        form = CadastroCidadaoForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            if Cidadao.objects.filter(
                email__iexact=d["email"].lower()
            ).exists() or Cidadao.objects.filter(cpf=d["cpf"]).exists():
                messages.error(request, "E-mail ou CPF já cadastrado.")
            else:
                Cidadao.objects.create(
                    nome_completo=d["nome_completo"],
                    cpf=d["cpf"],
                    dt_nascimento=d["dt_nascimento"],
                    telefone=d["telefone"],
                    email=d["email"].lower(),
                    senha_hash=make_password(d["senha"]),
                    rua=d.get("rua"),
                    num_endereco=d.get("num_endereco"),
                    complemento_endereco=d.get("complemento_endereco"),
                    bairro_endereco=d.get("bairro_endereco"),
                    cep_endereco=d.get("cep_endereco"),
                    perfil="CID",
                    ativo=True,
                    dt_cadastro=timezone.now(),
                )
                messages.success(request, "Cadastro concluído. Faça login.")
                return redirect("portal:login")
    else:
        form = CadastroCidadaoForm()
    return render(
        request,
        "portal/auth/cadastro.html",
        {"form": form, "bairros": bairros},
    )


@anonimo
@require_http_methods(["GET", "POST"])
def recuperar_senha_view(request):
    if request.method == "POST":
        form = RecuperarSenhaForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"].lower()
            try:
                u = Cidadao.objects.get(email__iexact=email, ativo=True)
            except Cidadao.DoesNotExist:
                messages.info(
                    request,
                    "Se o e-mail existir, você receberá instruções em instantes.",
                )
                return redirect("portal:login")
            token = signing.dumps({"id": u.pk}, salt="vg.pwreset")
            link = request.build_absolute_uri(
                reverse("portal:redefinir_senha", args=[token])
            )
            body = f"Use o link para definir nova senha (válido por 3 dias):\n{link}"
            send_mail(
                "VG 24H — redefinição de senha",
                body,
                settings.DEFAULT_FROM_EMAIL,
                [u.email],
                fail_silently=True,
            )
            messages.info(
                request,
                "Se o e-mail existir, verifique a caixa de entrada.",
            )
            return redirect("portal:login")
    else:
        form = RecuperarSenhaForm()
    return render(request, "portal/auth/recuperar_senha.html", {"form": form})


@anonimo
@require_http_methods(["GET", "POST"])
def redefinir_senha_view(request, token):
    try:
        data = signing.loads(token, salt="vg.pwreset", max_age=86400 * 3)
    except signing.BadSignature:
        messages.error(request, "Link inválido ou expirado.")
        return redirect("portal:login")
    try:
        u = Cidadao.objects.get(pk=data["id"], ativo=True)
    except Cidadao.DoesNotExist:
        return redirect("portal:login")
    if request.method == "POST":
        form = RedefinirSenhaForm(request.POST)
        if form.is_valid():
            u.senha_hash = make_password(form.cleaned_data["senha"])
            u.save(update_fields=["senha_hash"])
            messages.success(request, "Senha atualizada. Entre com a nova senha.")
            return redirect("portal:login")
    else:
        form = RedefinirSenhaForm()
    return render(request, "portal/auth/redefinir_senha.html", {"form": form})


@autenticado
@require_http_methods(["GET", "POST"])
def troca_senha_obrigatoria_view(request):
    if not request.session.get("forcar_troca_senha"):
        return redirect("portal:root")
    if request.method == "POST":
        form = TrocaSenhaObrigatoriaForm(request.POST)
        if form.is_valid():
            u = request.portal_user
            u.senha_hash = make_password(form.cleaned_data["senha"])
            u.senha_temporaria = None
            u.save(update_fields=["senha_hash", "senha_temporaria"])
            del request.session["forcar_troca_senha"]
            messages.success(request, "Senha alterada.")
            return redirect("portal:root")
    else:
        form = TrocaSenhaObrigatoriaForm()
    return render(
        request,
        "portal/auth/troca_senha_obrigatoria.html",
        {"form": form},
    )
