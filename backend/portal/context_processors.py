"""
context_processors.py — Variaveis globais disponiveis em todos os templates

Registrado em settings.py como 'portal.context_processors.navegacao'.
Disponibiliza automaticamente em todo template as variaveis:
- nav_user: objeto do usuario logado (ou None)
- nav_perfil: string do perfil ('CID', 'GES', 'COL' ou None)
- notif_count: quantidade de notificacoes nao lidas (apenas para cidadaos)
"""

from django.db import connection

from portal.decorators import perfil_codigo


def navegacao(request):
    """Injeta variaveis de navegacao em todas as views.

    A contagem de notificacoes usa SQL puro (subconsulta) em vez de ORM
    para manter a consistencia com o resto do projeto e evitar N+1 queries.
    A subquery filtra notificacoes dos chamados do cidadao logado.
    """
    u = getattr(request, "portal_user", None)
    notif_count = 0

    if u and perfil_codigo(u) == "CID":
        # Conta notificacoes nao lidas e nao arquivadas dos chamados do cidadao.
        with connection.cursor() as cursor:
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
