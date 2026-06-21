"""
decorators.py — Controle de acesso do Portal VG 24H

Decorators usados nas views para bloquear acesso de usuarios nao autorizados.
Sao colocados acima da funcao da view (ex: @perfis("GES")).

Substituem as antigas Rules R4 e R6 que foram removidas do banco de dados.
O controle de perfil agora eh feito na camada de aplicacao (Django),
nao no PostgreSQL.

Decorators disponiveis:
- anonimo: so acessa se NAO estiver logado (login, cadastro)
- autenticado: so acessa se ESTIVER logado (qualquer tipo)
- perfis(...): so acessa se o perfil do usuario for um dos listados
"""

from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def perfil_codigo(u):
    """Retorna o perfil do usuario como string: 'CID', 'GES' ou 'COL'.

    Retorna string vazia se o usuario for None ou nao tiver perfil.
    """
    return (u.perfil or "").strip() if u else ""


def anonimo(view):
    """Bloqueia acesso de usuarios ja logados.

    Usado em login, cadastro e recuperacao de senha. Se o usuario
    ja estiver logado, redireciona para a home.
    """
    @wraps(view)
    def w(request, *args, **kwargs):
        if request.portal_user:
            return redirect("portal:root")
        return view(request, *args, **kwargs)
    return w


def autenticado(view):
    """Exige que o usuario esteja logado (qualquer tipo de perfil).

    Se portal_user for None (nao logado), redireciona para /accounts/login/.
    """
    @wraps(view)
    def w(request, *args, **kwargs):
        if not request.portal_user:
            return redirect("portal:login")
        return view(request, *args, **kwargs)
    return w


def perfis(*codigos):
    """Exige que o usuario tenha um dos perfis listados.

    Exemplos de uso:
    - @perfis("GES")          → apenas gestores
    - @perfis("COL", "GES")   → colaboradores e gestores
    - @perfis("CID")          → apenas cidadaos

    Se o usuario nao estiver logado, redireciona para login.
    Se estiver logado mas com perfil diferente, mostra "Sem permissao".
    """
    def dec(view):
        @wraps(view)
        def w(request, *args, **kwargs):
            u = request.portal_user
            if not u:
                return redirect("portal:login")
            if perfil_codigo(u) not in codigos:
                messages.error(request, "Sem permissão para acessar esta área.")
                return redirect("portal:root")
            return view(request, *args, **kwargs)
        return w
    return dec
