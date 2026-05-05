"""
decorators.py — Controle de Acesso do Portal VG 24H

Decorators usados nas views para BLOQUEAR acesso de usuarios nao autorizados.
Sao colocados ACIMA da funcao da view (@"decorator").

[!] Substituem as Rules R4 e R6 que foram removidas do banco de dados.
    O controle de perfil agora e feito na camada de aplicacao (Django),
    nao no PostgreSQL.

3 decorators:
    @anonimo     → so acessa se NAO estiver logado (login, cadastro)
    @autenticado → so acessa se ESTIVER logado (qualquer tipo)
    @perfis(...) → so acessa se o perfil do usuario for um dos listados
"""

from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def perfil_codigo(u):
    """Retorna o perfil do usuario: 'CID', 'GES' ou 'COL'."""
    return (u.perfil or "").strip() if u else ""


# ========================================================================
# Decorador @anonimo — usado em login, cadastro, recuperar senha
# Se o usuario JA esta logado → redireciona para home
# ========================================================================
def anonimo(view):
    @wraps(view)
    def w(request, *args, **kwargs):
        if request.portal_user:
            # Ja esta logado, nao precisa acessar login/cadastro
            return redirect("portal:root")
        return view(request, *args, **kwargs)

    return w


# ========================================================================
# Decorador @autenticado — bloqueia acesso se NAO estiver logado
# Se portal_user e None → redireciona para /accounts/login/
# ========================================================================
def autenticado(view):
    @wraps(view)
    def w(request, *args, **kwargs):
        if not request.portal_user:
            # Nao esta logado → redireciona para tela de login
            return redirect("portal:login")
        return view(request, *args, **kwargs)

    return w


# ========================================================================
# Decorador @perfis("GES", "COL") — verifica se o perfil e permitido
# ========================================================================
# [!] Substitui a Rule R4 (removida do banco), que antes controlava
#     permissoes de mudanca de status por perfil no PostgreSQL.
#
# Exemplo: @perfis("GES")          → apenas Gestores
#          @perfis("COL", "GES")   → Colaboradores e Gestores
#          @perfis("CID")          → apenas Cidadaos
# Se nao for o perfil certo → mensagem "Sem permissao" e volta para home
# ========================================================================
def perfis(*codigos):
    def dec(view):
        @wraps(view)
        def w(request, *args, **kwargs):
            u = request.portal_user
            if not u:
                # Nao esta logado → manda para login
                return redirect("portal:login")
            if perfil_codigo(u) not in codigos:
                # Logado mas sem permissao para esta area
                messages.error(request, "Sem permissao para acessar esta area.")
                return redirect("portal:root")
            # Perfil autorizado → permite acessar a view normalmente
            return view(request, *args, **kwargs)

        return w

    return dec
