"""
views_auth.py — toda a parte de autenticacao do Portal VG 24H (feita por mim)

Aqui eu cuido de login, logout, cadastro de cidadao, recuperar e
redefinir senha, e a troca obrigatoria de senha no primeiro acesso.

IMPORTANTE pra eu nao esquecer: NAO uso o django.contrib.auth padrao.
Eu mesmo fiz as tabelas "cidadao" e "servidor" com a senha guardada como
hash bcrypt. A sessao eu controlo pelo cookie (request.session), nao pelo
User model do Django.

O login eh dual: primeiro procuro o email na tabela cidadao; se nao achar,
procuro na servidor. Assim os dois tipos usam a mesma tela de login.
"""

import time

# imports do django (config, messages, check_password pro bcrypt, signing
# pros tokens, send_mail, cursor cru, atalhos de view) + meus modulos
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.core import signing
from django.core.mail import send_mail
from django.db import connection
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from portal import db
from portal.decorators import anonimo, autenticado
from portal.forms import (
    CadastroCidadaoForm,
    RecuperarSenhaForm,
    RedefinirSenhaForm,
    TrocaSenhaObrigatoriaForm,
)

# regras do rate limit do login: no maximo 5 tentativas dentro de 5 minutos
MAX_LOGIN_ATTEMPTS = 5
LOGIN_TIMEOUT = 300  # 5 minutes


def _tentativas_na_janela(request):
    """Me devolve as tentativas de login que ainda estao na janela de tempo,
    ja jogando fora as que expiraram.

    Salvo a lista ja podada de volta na sessao pra que o check e o record
    olhem o mesmo estado (se eu nao salvasse, timestamp velho nunca saia)."""
    now = time.time()
    # filtro: so mantenho as tentativas que aconteceram ha menos de LOGIN_TIMEOUT
    attempts = [t for t in request.session.get("login_attempts", []) if now - t < LOGIN_TIMEOUT]
    request.session["login_attempts"] = attempts  # regravo ja podada
    return attempts


def _check_login_rate_limit(request):
    # bloqueado se ja bateu o limite de tentativas dentro da janela
    return len(_tentativas_na_janela(request)) >= MAX_LOGIN_ATTEMPTS


def _record_login_attempt(request):
    # registro mais uma tentativa: pego as validas, adiciono o agora e salvo
    attempts = _tentativas_na_janela(request)
    attempts.append(time.time())
    request.session["login_attempts"] = attempts


# ------------------------------------------------------------------
# Login (GET/POST /accounts/login/)
# ------------------------------------------------------------------

@require_http_methods(["GET", "POST"])
def login_view(request):
    """Minha tela de login dual (serve pra cidadao e pra servidor).

    Passo a passo:
    1. O cara digita email + senha e manda o form.
    2. Procuro o email primeiro na tabela cidadao, depois na servidor.
    3. Se achei, comparo a senha digitada com o hash bcrypt do banco
       usando check_password().
    4. Senha batendo, monto a sessao com o id e o tipo do usuario.
    5. Se o servidor tem senha_temporaria preenchida, jogo ele pra tela
       de troca obrigatoria.
    6. Se nao achei ou a senha nao bate, mostro erro generico de proposito
       (nao conto se o email existe, por seguranca).
    """
    # se ja ta logado nao tem porque ver o login, mando pra home
    if request.portal_user:
        return redirect("portal:root")

    if request.method == "POST":
        # antes de tudo checo o rate limit; se estourou nem tento autenticar
        if _check_login_rate_limit(request):
            messages.error(request, "Muitas tentativas. Aguarde 5 minutos.")
            return render(request, "portal/auth/login.html")

        # normalizo o email (tiro espaco e deixo minusculo); senha pego crua
        email = (request.POST.get("email") or "").strip().lower()
        senha = request.POST.get("password") or ""

        user = None
        tipo = None

        # busca dual: tento cidadao primeiro, se nao vier nada tento servidor
        user, tipo = db.buscar_cidadao_por_email(email)
        if not user:
            user, tipo = db.buscar_servidor_por_email(email)

        if user is None:
            # email nao existe em nenhuma tabela: conto a tentativa e dou erro generico
            _record_login_attempt(request)
            messages.error(request, "E-mail ou senha incorretos.")

        elif check_password(senha, user.senha_hash):
            # achou o user E a senha bate com o hash bcrypt. Login ok!
            request.session.pop("login_attempts", None)  # zero o contador de tentativas
            request.session.cycle_key()  # troco o sessionid pra evitar Session Fixation
            request.session["usuario_id"] = user.pk      # guardo quem eh na sessao
            request.session["usuario_tipo"] = tipo        # e o tipo (cidadao/servidor)

            # se for primeiro acesso (senha_temporaria preenchida) obrigo a
            # trocar a senha antes de deixar usar o sistema
            if (user.senha_temporaria or "").strip():
                request.session["forcar_troca_senha"] = True
                return redirect("portal:troca_senha_obrigatoria")

            messages.success(request, f"Olá, {user.nome_completo}.")

            # mando cada um pro lugar certo: servidor vai pro dashboard da equipe,
            # cidadao vai pra home
            if tipo == "servidor":
                return redirect("portal:equipe_dashboard")
            return redirect("portal:root")
        else:
            # achou o email mas a senha ta errada: conto tentativa e mesmo erro generico
            _record_login_attempt(request)
            messages.error(request, "E-mail ou senha incorretos.")

    # GET (ou POST que caiu sem sucesso): so mostro a tela de login
    return render(request, "portal/auth/login.html")


# ------------------------------------------------------------------
# Logout (POST /accounts/logout/)
# ------------------------------------------------------------------

@require_http_methods(["POST"])
def logout_view(request):
    """Faz logout: derruba a sessao e apaga o cookie.

    o flush() limpa tudo da sessao, inclusive usuario_id e usuario_tipo.
    """
    request.session.flush()  # mata a sessao inteira
    messages.info(request, "Sessão encerrada.")
    return redirect("portal:login")


# ------------------------------------------------------------------
# Cadastro de cidadao (GET/POST /accounts/cadastro/)
# ------------------------------------------------------------------

@anonimo
@require_http_methods(["GET", "POST"])
def cadastro_view(request):
    """Cadastro de cidadao novo pelo site.

    So cidadao se cadastra pelo site. Servidor quem cria eh o gestor la
    no painel admin.

    Antes de inserir eu checo se email ou CPF ja existem, pra nao tomar
    erro de constraint UNIQUE. A senha vai como hash bcrypt (make_password),
    a senha original nunca fica salva.
    """
    try:
        # carrego os bairros pro select; se der erro deixo lista vazia
        # pra pelo menos a tela abrir
        bairros = db.listar_bairros_ativos()
    except Exception:
        bairros = []

    if request.method == "POST":
        form = CadastroCidadaoForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data

            # checo duplicidade de email OU cpf antes de tentar inserir
            ja_existe = db.existe_email_ou_cpf("cidadao", d["email"].lower(), d["cpf"])

            if ja_existe:
                messages.error(request, "E-mail ou CPF já cadastrado.")
            else:
                # insiro o cidadao e ja deixo ele logado direto:
                cidadao_id = db.inserir_cidadao(d)
                request.session.pop("login_attempts", None)  # limpo tentativas antigas
                request.session.cycle_key()                  # sessionid novo (anti fixation)
                request.session["usuario_id"] = cidadao_id   # gravo o id na sessao
                request.session["usuario_tipo"] = "cidadao"  # e o tipo
                messages.success(request, f"Olá, {d['nome_completo']}. Cadastro concluído com sucesso!")
                return redirect("portal:root")
    else:
        # GET: form em branco
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
    """Manda email com o link pra redefinir a senha.

    O link leva um token criptografado (signing.dumps) com o id do cidadao
    dentro. O token vence em 3 dias.

    Por seguranca eu mostro SEMPRE a mesma mensagem ("se o email existir...")
    exista o email ou nao, pra ninguem descobrir quais emails sao cadastrados.
    """
    if request.method == "POST":
        form = RecuperarSenhaForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"].lower()

            # procuro o cidadao pra reset (me devolve id e email se existir)
            row = db.buscar_cidadao_para_reset(email)

            if not row:
                # nao achei: mesmo assim respondo a msg neutra e volto pro login
                messages.info(
                    request,
                    "Se o e-mail existir, você receberá instruções em instantes.",
                )
                return redirect("portal:login")

            uid = row[0]
            user_email = row[1]

            # gero o token assinado com o id do cidadao (salt proprio do reset)
            token = signing.dumps({"id": uid}, salt="vg.pwreset")
            # monto a url absoluta apontando pra view de redefinir com o token
            link = request.build_absolute_uri(
                reverse("portal:redefinir_senha", args=[token])
            )
            body = f"Use o link para definir nova senha (valido por 3 dias):\n{link}"
            # disparo o email; fail_silently pra um erro de SMTP nao quebrar a tela
            send_mail(
                "VG 24H — redefinicao de senha",
                body,
                settings.DEFAULT_FROM_EMAIL,
                [user_email],
                fail_silently=True,
            )
            # de novo a mesma mensagem neutra
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
    """Confere o token do link e deixa definir a senha nova.

    o signing.loads() abre o token e ja verifica se nao venceu (max_age de
    3 dias). Se o token for falso ou velho, jogo de volta pro login com erro.
    """
    try:
        # tento abrir o token; o max_age = 3 dias em segundos
        data = signing.loads(token, salt="vg.pwreset", max_age=86400 * 3)
    except signing.BadSignature:
        # assinatura nao bate ou expirou
        messages.error(request, "Link inválido ou expirado.")
        return redirect("portal:login")

    # confiro se o cidadao do token ainda existe e ta ativo (query crua aqui mesmo)
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_cidadao FROM cidadao "
            "WHERE id_cidadao = %s AND ativo = TRUE",
            [data["id"]],
        )
        row = cursor.fetchone()
    if not row:
        # sumiu ou foi desativado: nem deixo redefinir
        return redirect("portal:login")

    uid = row[0]

    if request.method == "POST":
        form = RedefinirSenhaForm(request.POST)
        if form.is_valid():
            # gravo o hash da senha nova (e isso ja zera senha_temporaria)
            db.atualizar_senha_usuario("cidadao", uid, form.cleaned_data["senha"])
            messages.success(request, "Senha atualizada. Entre com a nova senha.")
            return redirect("portal:login")
    else:
        # GET com token valido: mostro o form pra digitar a senha nova
        form = RedefinirSenhaForm()

    return render(request, "portal/auth/redefinir_senha.html", {"form": form})


# ------------------------------------------------------------------
# Troca obrigatoria de senha (GET/POST /accounts/trocar-senha/)
# ------------------------------------------------------------------

@autenticado
@require_http_methods(["GET", "POST"])
def troca_senha_obrigatoria_view(request):
    """Obriga o servidor a trocar a senha no primeiro acesso.

    Quando o gestor cria um colaborador novo ele poe uma senha provisoria
    e liga senha_temporaria="1". O middleware ve isso e empurra todas as
    requisicoes pra ca.

    Depois que troca eu apago a flag senha_temporaria e limpo o
    forcar_troca_senha da sessao.
    """
    # se o flag forcar_troca_senha nao ta na sessao, ninguem deveria estar
    # nessa tela: mando pra home
    if not request.session.get("forcar_troca_senha"):
        return redirect("portal:root")

    if request.method == "POST":
        form = TrocaSenhaObrigatoriaForm(request.POST)
        if form.is_valid():
            u = request.portal_user
            # gravo a senha nova do servidor (a funcao do db ja limpa senha_temporaria)
            db.atualizar_senha_usuario("servidor", u.pk, form.cleaned_data["senha"])
            del request.session["forcar_troca_senha"]  # tiro o flag, liberou o sistema
            messages.success(request, "Senha alterada.")
            return redirect("portal:root")
    else:
        form = TrocaSenhaObrigatoriaForm()

    return render(
        request,
        "portal/auth/troca_senha_obrigatoria.html",
        {"form": form},
    )
