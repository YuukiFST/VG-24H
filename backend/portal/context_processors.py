"""
context_processors.py — Variaveis globais disponiveis em TODOS os templates

Registrado em settings.py: 'portal.context_processors.navegacao'
Disponibiliza automaticamente em todo template: {{ nav_user }}, {{ nav_perfil }}, {{ notif_count }}
"""

from django.db import connection

from portal.decorators import perfil_codigo


def navegacao(request):
    """
    Context processor: injeta variaveis de navegacao em todas as views.

    Variaveis:
      - nav_user:      objeto do usuario logado (ou None)
      - nav_perfil:    string do perfil ('CID', 'GES', 'COL' ou None)
      - notif_count:   qtd de notificacoes nao lidas (apenas para cidadaos)

    [!] A contagem de notificacoes usa SQL puro (subconsulta) em vez de ORM
        para evitar N+1 queries e manter a performance.
    """
    u = getattr(request, "portal_user", None)
    notif_count = 0
    if u and perfil_codigo(u) == "CID":
        # SQL puro: conta notificacoes nao lidas dos chamados do cidadao
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
