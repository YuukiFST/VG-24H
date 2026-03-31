from portal.decorators import perfil_codigo


def navegacao(request):
    u = getattr(request, "portal_user", None)
    notif_count = 0
    if u and perfil_codigo(u) == "CID":
        from portal.models import Notificacao, Chamado

        # Notificações vinculadas a chamados do cidadão
        chamado_ids = Chamado.objects.filter(id_cidadao=u).values_list(
            "id_chamado", flat=True
        )
        notif_count = Notificacao.objects.filter(
            id_chamado__in=chamado_ids, arquivada=False, lida=False
        ).count()
    return {
        "nav_user": u,
        "nav_perfil": perfil_codigo(u) if u else None,
        "notif_count": notif_count,
    }
