from django.db import connection

from portal.decorators import perfil_codigo


def navegacao(request):
    u = getattr(request, "portal_user", None)
    notif_count = 0
    if u and perfil_codigo(u) == "CID":
        # SQL puro: conta notificações não lidas dos chamados do cidadão
        with connection.cursor() as cursor:
            # Subconsulta: IDs dos chamados deste cidadão
            # Consulta principal: conta notificações não lidas e não arquivadas
            cursor.execute(
                "SELECT COUNT(*) FROM notificacao n "
                "WHERE n.arquivada = FALSE AND n.lida = FALSE "
                "AND n.id_chamado IN ("
                "    SELECT c.id_chamado FROM chamado c "
                "    WHERE c.id_cidadao = %s"
                ")",
                [u.pk],
            )
            notif_count = cursor.fetchone()[0]
    return {
        "nav_user": u,
        "nav_perfil": perfil_codigo(u) if u else None,
        "notif_count": notif_count,
    }
