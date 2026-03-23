from portal.decorators import perfil_codigo


def navegacao(request):
    u = getattr(request, "portal_user", None)
    return {
        "nav_user": u,
        "nav_perfil": perfil_codigo(u) if u else None,
    }
