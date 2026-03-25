from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def perfil_codigo(u):
    return (u.perfil or "").strip() if u else ""


def anonimo(view):
    @wraps(view)
    def w(request, *args, **kwargs):
        if request.portal_user:
            return redirect("portal:root")
        return view(request, *args, **kwargs)

    return w


def autenticado(view):
    @wraps(view)
    def w(request, *args, **kwargs):
        if not request.portal_user:
            return redirect("portal:login")
        return view(request, *args, **kwargs)

    return w


def perfis(*codigos):
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
