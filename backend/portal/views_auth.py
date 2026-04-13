"""
views_auth.py — Autenticação do Portal VG 24H

Este módulo gerencia todo o fluxo de autenticação do sistema:
- Login / Logout (cidadãos e servidores)
- Cadastro de novos cidadãos
- Recuperação e redefinição de senha
- Troca de senha obrigatória (primeiro acesso de servidores)

NOTA: NÃO usamos o django.contrib.auth padrão.
Usamos um sistema próprio com as tabelas 'cidadao' e 'servidor' do banco.
As senhas são armazenadas com hash bcrypt via django.contrib.auth.hashers.
"""

from django.conf import settings
from django.contrib import messages
# check_password: compara senha digitada com o hash salvo no banco
# make_password: gera hash bcrypt da senha ao cadastrar/alterar
from django.contrib.auth.hashers import check_password, make_password
from django.core import signing  # Gera tokens seguros para recuperação de senha
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
# Cidadao e Servidor: as duas tabelas de usuários do sistema
# O sistema verifica em qual tabela o email existe para determinar o tipo
from portal.models import Bairro, Cidadao, Servidor


# ═══════════════════════════════════════════════════════════════
# LOGIN — Rota: /accounts/login/
# ═══════════════════════════════════════════════════════════════
# FLUXO COMPLETO:
#   1. Usuário digita email + senha no formulário e clica "Entrar"
#   2. O formulário envia um POST para esta view (/accounts/login/)
#   3. A view faz um SELECT no banco para buscar o usuário pelo email
#   4. Se encontrou, compara a senha digitada com o hash salvo
#   5. Se a senha bate, cria a sessão e redireciona para a home
#   6. Se não bate ou não encontrou, mostra mensagem de erro
# ═══════════════════════════════════════════════════════════════
@require_http_methods(["GET", "POST"])
def login_view(request):
    # Se já está logado (middleware já carregou o user), redireciona para home
    if request.portal_user:
        return redirect("portal:root")

    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        senha = request.POST.get("password") or ""

        user = None
        tipo = None

        # ┌─────────────────────────────────────────────────────┐
        # │  BUSCA NO BANCO DE DADOS (SELECT)                  │
        # │  Aqui é onde o sistema consulta o PostgreSQL/Neon   │
        # │  para verificar se o email existe nas tabelas.      │
        # │                                                     │
        # │  Primeiro tenta na tabela 'cidadao',                │
        # │  se não encontrar, tenta na tabela 'servidor'.      │
        # └─────────────────────────────────────────────────────┘
        from django.db import connection
        with connection.cursor() as cursor:
            # SELECT na tabela 'cidadao' — busca pelo email informado
            cursor.execute(
                "SELECT id_cidadao, nome_completo, senha_hash, perfil, senha_temporaria "
                "FROM cidadao "
                "WHERE LOWER(email) = %s AND ativo = TRUE",
                [email],
            )
            row = cursor.fetchone()

            if row:
                # Encontrou na tabela cidadao → monta o objeto manualmente
                user = Cidadao.objects.get(pk=row[0])
                tipo = "cidadao"
            else:
                # Não encontrou em cidadao → tenta SELECT na tabela 'servidor'
                cursor.execute(
                    "SELECT id_servidor, nome_completo, senha_hash, perfil, senha_temporaria "
                    "FROM servidor "
                    "WHERE LOWER(email) = %s AND ativo = TRUE",
                    [email],
                )
                row = cursor.fetchone()
                if row:
                    # Encontrou na tabela servidor
                    user = Servidor.objects.get(pk=row[0])
                    tipo = "servidor"

        # ┌─────────────────────────────────────────────────────┐
        # │  TRATAMENTO DE ERRO — Usuário NÃO encontrado       │
        # │  Se user é None, o email não existe em nenhuma      │
        # │  das duas tabelas (cidadao/servidor).               │
        # └─────────────────────────────────────────────────────┘
        if user is None:
            messages.error(request, "E-mail ou senha incorretos.")

        # ┌─────────────────────────────────────────────────────┐
        # │  VERIFICAÇÃO DA SENHA                               │
        # │  check_password() compara a senha digitada com o    │
        # │  hash bcrypt salvo no campo 'senha_hash' do banco.  │
        # │  Retorna True se a senha está correta.              │
        # └─────────────────────────────────────────────────────┘
        elif check_password(senha, user.senha_hash):
            # ┌─────────────────────────────────────────────────┐
            # │  LOGIN BEM-SUCEDIDO                             │
            # │  Salva na sessão (cookie) o ID e o tipo do      │
            # │  usuário. O middleware.py lê esses valores em   │
            # │  TODA requisição seguinte para saber quem está  │
            # │  logado e qual perfil ele tem (CID/COL/GES).    │
            # └─────────────────────────────────────────────────┘
            request.session["usuario_id"] = user.pk       # ID no banco
            request.session["usuario_tipo"] = tipo        # 'cidadao' ou 'servidor'
            # Se o servidor tem senha temporária (primeiro acesso),
            # força a troca antes de usar o sistema
            if (user.senha_temporaria or "").strip():
                request.session["forcar_troca_senha"] = True
                return redirect("portal:troca_senha_obrigatoria")

            messages.success(request, f"Olá, {user.nome_completo}.")

            # ┌─────────────────────────────────────────────────┐
            # │  REDIRECIONAMENTO POR PERFIL                    │
            # │  Após o login, o middleware carrega o usuário    │
            # │  e cada view usa @perfis() para controlar quem  │
            # │  pode acessar. Veja decorators.py para detalhes.│
            # │                                                 │
            # │  CID → /cidadao/chamados/ (meus chamados)       │
            # │  COL → /equipe/chamados/ (dashboard equipe)     │
            # │  GES → /equipe/chamados/ + /gestao/ (admin)     │
            # └─────────────────────────────────────────────────┘
            return redirect("portal:root")
        else:
            # ┌─────────────────────────────────────────────────┐
            # │  SENHA INCORRETA                                │
            # │  A conta existe no banco, mas a senha digitada  │
            # │  não confere com o hash armazenado.             │
            # └─────────────────────────────────────────────────┘
            messages.error(request, "E-mail ou senha incorretos.")

    return render(request, "portal/auth/login.html")

# Logout — /accounts/logout/
# Apaga toda a sessão do navegador (cookie), deslogando o usuário
@require_http_methods(["POST"])
def logout_view(request):
    #apaga o cookie de sessão e usuario_id e usuario_tipo somem
    request.session.flush()
    messages.info(request, "Sessão encerrada.")
    return redirect("portal:login")


# CADASTRO — Rota: /accounts/cadastro/
# Apenas cidadãos se cadastram pelo site. Servidores são criados por gestores.
# @anonimo = decorador que impede acesso de quem já está logado (ver decorators.py)
@anonimo
@require_http_methods(["GET", "POST"])
def cadastro_view(request):
    # SELECT * FROM bairro WHERE ativo = true ORDER BY nome_bairro
    # Carrega os bairros para o formulário de endereço
    try:
        bairros = list(Bairro.objects.filter(ativo=True).order_by("nome_bairro"))
    except Exception:
        class MockBairro:
            def __init__(self, id, n):
                self.pk = id
                self.nome_bairro = n
        bairros = [MockBairro(1, "Centro"), MockBairro(2, "Cristo Rei"), MockBairro(3, "Vila Arthur")]

    if request.method == "POST":
        form = CadastroCidadaoForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            # VALIDAÇÃO DE DUPLICIDADE no banco antes de inserir:
            # SQL: SELECT 1 FROM cidadao WHERE LOWER(email) = '...' LIMIT 1
            # SQL: SELECT 1 FROM cidadao WHERE cpf = '...' LIMIT 1
            # .exists() retorna True/False SEM carregar o registro inteiro (mais eficiente)
            if Cidadao.objects.filter(
                email__iexact=d["email"].lower()
            ).exists() or Cidadao.objects.filter(cpf=d["cpf"]).exists():
                messages.error(request, "E-mail ou CPF já cadastrado.")
            else:
                # INSERÇÃO DO NOVO CIDADÃO NO BANCO DE DADOS
                # SQL equivalente:
                # INSERT INTO cidadao (nome_completo, cpf, dt_nascimento, telefone,
                #   email, senha_hash, rua, perfil, ativo, dt_cadastro)
                # VALUES ('João Silva', '12345678901', '1990-01-15', '65999990000',
                #   'joao@email.com', 'pbkdf2_sha256$720000$...', 'Rua A', 'CID', true, NOW())
                #
                # make_password(senha) transforma 'minhasenha123' em hash bcrypt
                # para nunca armazenar a senha real no banco (segurança)
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


# RECUPERAÇÃO DE SENHA — Rota: /accounts/recuperar-senha/
# Gera um token criptografado com o ID do usuário e envia por email.
# O token expira em 3 dias (86400 * 3 segundos).
@anonimo
@require_http_methods(["GET", "POST"])
def recuperar_senha_view(request):
    if request.method == "POST":
        form = RecuperarSenhaForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"].lower()
            try:
                # SELECT * FROM cidadao WHERE LOWER(email) = '...' AND ativo = true
                u = Cidadao.objects.get(email__iexact=email, ativo=True)
            except Cidadao.DoesNotExist:
                messages.info(
                    request,
                    "Se o e-mail existir, você receberá instruções em instantes.",
                )
                return redirect("portal:login")
            # signing.dumps() gera um token criptografado com o ID do cidadão
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


# REDEFINIÇÃO DE SENHA — Rota: /accounts/redefinir-senha/<token>/
# Valida o token e permite definir nova senha.
@anonimo
@require_http_methods(["GET", "POST"])
def redefinir_senha_view(request, token):
    try:
        # signing.loads() descriptografa o token e verifica se não expirou
        data = signing.loads(token, salt="vg.pwreset", max_age=86400 * 3)
    except signing.BadSignature:
        messages.error(request, "Link inválido ou expirado.")
        return redirect("portal:login")
    try:
        # SELECT * FROM cidadao WHERE id_cidadao = X AND ativo = true
        u = Cidadao.objects.get(pk=data["id"], ativo=True)
    except Cidadao.DoesNotExist:
        return redirect("portal:login")
    if request.method == "POST":
        form = RedefinirSenhaForm(request.POST)
        if form.is_valid():
            # UPDATE cidadao SET senha_hash = 'novo_hash' WHERE id_cidadao = X
            u.senha_hash = make_password(form.cleaned_data["senha"])
            u.save(update_fields=["senha_hash"])
            messages.success(request, "Senha atualizada. Entre com a nova senha.")
            return redirect("portal:login")
    else:
        form = RedefinirSenhaForm()
    return render(request, "portal/auth/redefinir_senha.html", {"form": form})


# TROCA DE SENHA OBRIGATÓRIA — Rota: /accounts/trocar-senha/
# Usado quando um servidor recebe senha temporária no primeiro acesso.
# O sistema obriga a trocar antes de usar qualquer funcionalidade.
@autenticado
@require_http_methods(["GET", "POST"])
def troca_senha_obrigatoria_view(request):
    if not request.session.get("forcar_troca_senha"):
        return redirect("portal:root")
    if request.method == "POST":
        form = TrocaSenhaObrigatoriaForm(request.POST)
        if form.is_valid():
            u = request.portal_user
            # UPDATE servidor SET senha_hash = 'novo_hash', senha_temporaria = NULL
            # WHERE id_servidor = X
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
