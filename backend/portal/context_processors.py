from portal.decorators import perfil_codigo


def navegacao(request):
    u = getattr(request, "portal_user", None)
    notif_count = 0
    if u:
        from portal.models import Notificacao

        notif_count = Notificacao.objects.filter(
            id_usuario=u, arquivada=False, lida=False
        ).count()
    return {
        "nav_user": u,
        "nav_perfil": perfil_codigo(u) if u else None,
        "notif_count": notif_count,
    }
