"""
decorators.py — meu controle de acesso do Portal VG 24H

Aqui ficam os decorators que eu boto em cima das views pra barrar quem nao
pode entrar. Eu coloco logo acima da funcao da view (tipo @perfis("GES")).

Esses decorators sao o que sobrou das antigas Rules R4 e R6 que eu tirei do
banco. Agora eu faco esse controle de perfil aqui no Django mesmo, nao mais
no PostgreSQL.

O que eu tenho aqui:
- anonimo: so deixa entrar quem NAO ta logado (login, cadastro)
- autenticado: so deixa entrar quem TA logado (qualquer tipo)
- perfis(...): so deixa entrar se o perfil do cara for um dos que eu listei
"""

# wraps eu uso pra nao perder o nome/docstring da view quando eu embrulho ela
from functools import wraps

# messages pra avisar "sem permissao", redirect pra mandar o cara pra outra pagina
from django.contrib import messages
from django.shortcuts import redirect


def perfil_codigo(u):
    """Me devolve o perfil do cara como string: 'CID', 'GES' ou 'COL'.

    Se o usuario for None ou nao tiver perfil eu retorno string vazia.
    """
    # se nao tem usuario ja volto "", senao pego o perfil e tiro os espacos
    return (u.perfil or "").strip() if u else ""


def anonimo(view):
    """Barra quem ja ta logado.

    Eu uso isso no login, cadastro e recuperar senha. Se o cara ja ta
    logado nao faz sentido ver essas paginas, entao mando pra home.
    """
    @wraps(view)
    def w(request, *args, **kwargs):
        # o middleware ja botou o usuario aqui; se tem alguem logado eu chuto pra home
        if request.portal_user:
            return redirect("portal:root")
        # nao ta logado, beleza, deixo a view rodar normal
        return view(request, *args, **kwargs)
    return w


def autenticado(view):
    """So deixa entrar quem ta logado, tanto faz o perfil.

    Se portal_user for None (ninguem logado) eu mando pro /accounts/login/.
    """
    @wraps(view)
    def w(request, *args, **kwargs):
        # se nao tem ninguem logado eu barro e mando pro login
        if not request.portal_user:
            return redirect("portal:login")
        # ta logado, pode passar
        return view(request, *args, **kwargs)
    return w


def perfis(*codigos):
    """So deixa entrar se o perfil do cara for um dos que eu passei.

    Como eu uso:
    - @perfis("GES")          → so gestor
    - @perfis("COL", "GES")   → colaborador e gestor
    - @perfis("CID")          → so cidadao

    Se nao ta logado eu mando pro login.
    Se ta logado mas com perfil errado eu mostro "Sem permissao".
    """
    # esse e um decorator com argumento, entao tenho que ter uma funcao a mais por fora
    def dec(view):
        @wraps(view)
        def w(request, *args, **kwargs):
            # pego o usuario que o middleware deixou no request
            u = request.portal_user
            # nao ta logado? vai pro login
            if not u:
                return redirect("portal:login")
            # ta logado mas o perfil dele nao ta na lista que eu permiti
            if perfil_codigo(u) not in codigos:
                messages.error(request, "Sem permissão para acessar esta área.")
                return redirect("portal:root")
            # passou nas duas checagens, libero a view
            return view(request, *args, **kwargs)
        return w
    return dec
