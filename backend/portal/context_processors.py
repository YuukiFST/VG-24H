"""
context_processors.py — variaveis que aparecem em TODO template meu

Eu registrei isso no settings.py como 'portal.context_processors.navegacao'.
Com ele eu jogo automaticamente em qualquer template:
- nav_user: o usuario logado (ou None)
- nav_perfil: a string do perfil ('CID', 'GES', 'COL' ou None)
- notif_count: quantas notificacoes nao lidas (so faz sentido pro cidadao)
"""

# connection pro SQL puro da contagem
from django.db import connection

# reaproveito o meu helper de perfil pra nao repetir logica
from portal.decorators import perfil_codigo


def navegacao(request):
    """Jogo as variaveis de navegacao em todas as views.

    A contagem de notificacao eu faco com SQL puro (subconsulta), nao ORM,
    pra ficar igual ao resto do projeto e nao cair em N+1. A subquery pega
    so as notificacoes dos chamados do cidadao que ta logado.
    """
    # pego o usuario com getattr porque em algum caso o middleware pode nao ter rodado
    u = getattr(request, "portal_user", None)
    # se nao for cidadao logado, fica 0 mesmo
    notif_count = 0

    # so cidadao tem notificacao pra contar; gestor/colaborador nem entra aqui
    if u and perfil_codigo(u) == "CID":
        # conto as nao lidas e nao arquivadas dos chamados desse cidadao
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
            # COUNT sempre volta uma linha com um numero, pego ele
            notif_count = cursor.fetchone()[0]

    # devolvo o dicionario que o Django junta no contexto de todo template
    return {
        "nav_user": u,
        "nav_perfil": perfil_codigo(u) if u else None,
        "notif_count": notif_count,
    }
