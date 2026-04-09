"""
decorators.py — Controle de Acesso do Portal VG 24H

Estes decoradores são usados nas views para BLOQUEAR o acesso
de usuários não autorizados. São colocados acima da função da view.

Exemplo de uso:
    @perfis("GES", "COL")          # só gestores e colaboradores podem acessar
    def equipe_chamados_lista(request):
        ...

Existem 3 decoradores:
    @anonimo     → só acessa se NÃO estiver logado (login, cadastro)
    @autenticado → só acessa se ESTIVER logado (qualquer tipo)
    @perfis(...) → só acessa se o perfil do usuário for um dos listados
"""

from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def perfil_codigo(u):
    """Retorna o perfil do usuário: 'CID', 'GES' ou 'COL'."""
    return (u.perfil or "").strip() if u else ""


# Decorador @anonimo — usado em login, cadastro, recuperar senha
# Se o usuário JÁ está logado ele redireciona para home (não precisa logar de novo)
def anonimo(view):
    @wraps(view)
    def w(request, *args, **kwargs):
        if request.portal_user:
            # Já está logado, não retorna o usuario no login/cadastro
            return redirect("portal:root")
        return view(request, *args, **kwargs)

    return w


# Decorador @autenticado — bloqueia acesso se NÃO estiver logado
# Se portal_user é None, ele redireciona para /accounts/login/
def autenticado(view):
    @wraps(view)
    def w(request, *args, **kwargs):
        if not request.portal_user:
            # Não está logado, ele redireciona para a tela de login
            return redirect("portal:login")
        return view(request, *args, **kwargs)

    return w


# Decorador @perfis("GES", "COL") — verifica se o perfil do usuário é permitido
# Exemplo: @perfis("GES") → apenas Gestores podem acessar
#          @perfis("COL", "GES") → Colaboradores e Gestores podem acessar
# Se não for o perfil certo → mostra "Sem permissão" e volta para home
def perfis(*codigos):
    def dec(view):
        @wraps(view)
        def w(request, *args, **kwargs):
            u = request.portal_user
            if not u:
                # Não está logado → manda para login
                return redirect("portal:login")
            if perfil_codigo(u) not in codigos:
                # Está logado, mas o perfil não tem permissão
                messages.error(request, "Sem permissão para acessar esta área.")
                return redirect("portal:root")
            # Perfil autorizado → permite acessar a view normalmente
            return view(request, *args, **kwargs)

        return w

    return dec
