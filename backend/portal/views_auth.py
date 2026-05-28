"""
views_auth.py — Autenticacao do Portal VG 24H

Este modulo gerencia login, logout, cadastro de cidadaos, recuperacao
e redefinicao de senha, e troca obrigatoria de senha no primeiro acesso.

O sistema NAO usa o django.contrib.auth padrao. Em vez disso, utiliza
as tabelas proprias "cidadao" e "servidor" com senhas armazenadas como
hash bcrypt. As sessoes sao gerenciadas via cookie (request.session),
nao via o User model do Django.

O login eh dual: primeiro busca o email na tabela cidadao; se nao
encontrar, busca na tabela servidor. Isso permite que cidadaos e
servidores usem a mesma tela de login.
"""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.core import signing
from django.core.mail import send_mail
from django.db import connection
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from portal import db
from portal.decorators import anonimo, autenticado, perfil_codigo
from portal.forms import (
    CadastroCidadaoForm,
    RecuperarSenhaForm,
    RedefinirSenhaForm,
    TrocaSenhaObrigatoriaForm,
)


# ------------------------------------------------------------------
# Login (GET/POST /accounts/login/)
# ------------------------------------------------------------------

@require_http_methods(["GET", "POST"])
def login_view(request):
    """Tela de login dual (cidadao e servidor).

    Fluxo completo:
    1. Usuario digita email + senha e envia o formulario.
    2. Busca o email primeiro na tabela cidadao, depois na tabela servidor.
    3. Se encontrou, compara a senha digitada com o hash bcrypt salvo
       no banco usando check_password().
    4. Se a senha confere, cria a sessao com o ID e tipo do usuario.
    5. Se o servidor tem senha_temporaria preenchida, redireciona
       para a tela de troca obrigatoria de senha.
    6. Se nao encontrou ou a senha nao confere, mostra erro genérico
       (nao revela se o email existe por seguranca).
    """
    # Se ja esta logado, redireciona para a home.
    if request.portal_user:
        return redirect("portal:root")

    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        senha = request.POST.get("password") or ""

        user = None
        tipo = None

        # Busca dual: primeiro cidadao, depois servidor.
        user, tipo = db.buscar_cidadao_por_email(email)
        if not user:
            user, tipo = db.buscar_servidor_por_email(email)

        if user is None:
            # Email nao encontrado em nenhuma tabela.
            messages.error(request, "E-mail ou senha incorretos.")

        elif check_password(senha, user.senha_hash):
            # Senha confere. Cria a sessao no cookie.
            request.session.cycle_key()  # Novo sessionid (previne Session Fixation)
            request.session["usuario_id"] = user.pk
            request.session["usuario_tipo"] = tipo

            # Se o servidor tem senha temporaria (primeiro acesso),
            # obriga a trocar antes de usar o sistema.
            if (user.senha_temporaria or "").strip():
                request.session["forcar_troca_senha"] = True
                return redirect("portal:troca_senha_obrigatoria")

            messages.success(request, f"Ola, {user.nome_completo}.")

            # Redireciona conforme o perfil.
            if tipo == "servidor":
                return redirect("portal:equipe_dashboard")
            return redirect("portal:root")
        else:
            # Senha incorreta (email existe, mas senha nao confere).
            messages.error(request, "E-mail ou senha incorretos.")

    return render(request, "portal/auth/login.html")


# ------------------------------------------------------------------
# Logout (POST /accounts/logout/)
# ------------------------------------------------------------------

@require_http_methods(["POST"])
def logout_view(request):
    """Encerra a sessao do usuario (apaga o cookie).

    request.session.flush() remove todos os dados da sessao,
    incluindo usuario_id e usuario_tipo.
    """
    request.session.flush()
    messages.info(request, "Sessao encerrada.")
    return redirect("portal:login")


# ------------------------------------------------------------------
# Cadastro de cidadao (GET/POST /accounts/cadastro/)
# ------------------------------------------------------------------

@anonimo
@require_http_methods(["GET", "POST"])
def cadastro_view(request):
    """Cadastro de novos cidadaos pelo site.

    Apenas cidadaos se cadastram pelo site. Servidores sao criados
    por gestores no painel administrativo.

    Antes de inserir, verifica se email ou CPF ja existem no banco
    para evitar erros de constraint UNIQUE. A senha eh armazenada
    como hash bcrypt (make_password) — a senha original nunca fica
    no banco.
    """
    try:
        bairros = db.listar_bairros_ativos()
    except Exception:
        bairros = []

    if request.method == "POST":
        form = CadastroCidadaoForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data

            # Verifica duplicidade de email ou CPF.
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT EXISTS("
                    "  SELECT 1 FROM cidadao WHERE LOWER(email) = %s"
                    ") OR EXISTS("
                    "  SELECT 1 FROM cidadao WHERE cpf = %s"
                    ")",
                    [d["email"].lower(), d["cpf"]],
                )
                ja_existe = cursor.fetchone()[0]

            if ja_existe:
                messages.error(request, "E-mail ou CPF ja cadastrado.")
            else:
                # INSERT do novo cidadao com senha hasheada.
                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO cidadao "
                        "(nome_completo, cpf, dt_nascimento, telefone, email, "
                        "senha_hash, rua, num_endereco, complemento_endereco, "
                        "bairro_endereco, cep_endereco, perfil, ativo, dt_cadastro) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        [
                            d["nome_completo"],
                            d["cpf"],
                            d["dt_nascimento"],
                            d["telefone"],
                            d["email"].lower(),
                            make_password(d["senha"]),
                            d.get("rua"),
                            d.get("num_endereco"),
                            d.get("complemento_endereco"),
                            d.get("bairro_endereco"),
                            d.get("cep_endereco"),
                            "CID",
                            True,
                            timezone.now(),
                        ],
                    )
                messages.success(request, "Cadastro concluido. Faca login.")
                return redirect("portal:login")
    else:
        form = CadastroCidadaoForm()

    return render(
        request,
        "portal/auth/cadastro.html",
        {"form": form, "bairros": bairros},
    )


# ------------------------------------------------------------------
# Recuperacao de senha (GET/POST /accounts/recuperar-senha/)
# ------------------------------------------------------------------

@anonimo
@require_http_methods(["GET", "POST"])
def recuperar_senha_view(request):
    """Envia email com link para redefinicao de senha.

    O link contem um token criptografado (signing.dumps) que armazena
    o ID do cidadao. O token expira em 3 dias (max_age=259200).

    Por seguranca, sempre mostra a mesma mensagem ("se o email existir...")
    independentemente de o email existir ou nao no banco.
    """
    if request.method == "POST":
        form = RecuperarSenhaForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"].lower()

            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id_cidadao, email "
                    "FROM cidadao "
                    "WHERE LOWER(email) = %s AND ativo = TRUE",
                    [email],
                )
                row = cursor.fetchone()

            if not row:
                messages.info(
                    request,
                    "Se o e-mail existir, voce recebera instrucoes em instantes.",
                )
                return redirect("portal:login")

            uid = row[0]
            user_email = row[1]

            # Gera token criptografado com o ID do cidadao.
            token = signing.dumps({"id": uid}, salt="vg.pwreset")
            link = request.build_absolute_uri(
                reverse("portal:redefinir_senha", args=[token])
            )
            body = f"Use o link para definir nova senha (valido por 3 dias):\n{link}"
            send_mail(
                "VG 24H — redefinicao de senha",
                body,
                settings.DEFAULT_FROM_EMAIL,
                [user_email],
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


# ------------------------------------------------------------------
# Redefinicao de senha (GET/POST /accounts/redefinir-senha/<token>/)
# ------------------------------------------------------------------

@anonimo
@require_http_methods(["GET", "POST"])
def redefinir_senha_view(request, token):
    """Valida o token e permite definir uma nova senha.

    signing.loads() descriptografa o token e verifica se nao expirou
    (max_age de 3 dias). Se o token for invalido ou expirado,
    redireciona para o login com mensagem de erro.
    """
    try:
        data = signing.loads(token, salt="vg.pwreset", max_age=86400 * 3)
    except signing.BadSignature:
        messages.error(request, "Link invalido ou expirado.")
        return redirect("portal:login")

    # Verifica se o cidadao ainda existe e esta ativo.
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_cidadao FROM cidadao "
            "WHERE id_cidadao = %s AND ativo = TRUE",
            [data["id"]],
        )
        row = cursor.fetchone()
    if not row:
        return redirect("portal:login")

    uid = row[0]

    if request.method == "POST":
        form = RedefinirSenhaForm(request.POST)
        if form.is_valid():
            # Atualiza o hash da senha no banco.
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE cidadao SET senha_hash = %s "
                    "WHERE id_cidadao = %s",
                    [make_password(form.cleaned_data["senha"]), uid],
                )
            messages.success(request, "Senha atualizada. Entre com a nova senha.")
            return redirect("portal:login")
    else:
        form = RedefinirSenhaForm()

    return render(request, "portal/auth/redefinir_senha.html", {"form": form})


# ------------------------------------------------------------------
# Troca obrigatoria de senha (GET/POST /accounts/trocar-senha/)
# ------------------------------------------------------------------

@autenticado
@require_http_methods(["GET", "POST"])
def troca_senha_obrigatoria_view(request):
    """Forca a troca de senha no primeiro acesso de servidores.

    Quando um gestor cria um novo colaborador, define uma senha
    provisoria e seta senha_temporaria="1". O middleware detecta
    isso e redireciona todas as requisicoes para esta tela.

    Apos trocar a senha, remove a flag senha_temporaria e limpa
    a sessao forcar_troca_senha.
    """
    if not request.session.get("forcar_troca_senha"):
        return redirect("portal:root")

    if request.method == "POST":
        form = TrocaSenhaObrigatoriaForm(request.POST)
        if form.is_valid():
            u = request.portal_user
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE servidor SET senha_hash = %s, senha_temporaria = NULL "
                    "WHERE id_servidor = %s",
                    [make_password(form.cleaned_data["senha"]), u.pk],
                )
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
