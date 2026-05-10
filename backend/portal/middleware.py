"""
middleware.py — Middleware de Autenticacao do Portal VG 24H

[!] PONTO CRUCIAL: Este middleware injeta variaveis de sessao no PostgreSQL
    via set_config(). As triggers e functions do banco (ver 03 e 04) usam
    essas variaveis para saber qual usuario/pefil esta executando a acao.

Executado AUTOMATICAMENTE em TODA requisicao HTTP.
Fluxo:
1. Usuario faz login → session['usuario_id'] e session['usuario_tipo'] salvos
2. Toda requisicao → middleware le a sessao e busca o usuario no banco
3. Coloca em request.portal_user → views podem verificar quem esta logado
4. Chama set_config() no PostgreSQL para auditoria nas triggers
"""

from django.db import connection

from portal import db


def _usuario_da_sessao(request):
    """
    Le o cookie de sessao e busca o usuario correspondente no banco via SQL puro.
    Retorna um objeto Cidadao ou Servidor, ou None se nao estiver logado.

    [!] Delega para db.buscar_cidadao_por_id / db.buscar_servidor_por_id
        que executam SELECT SQL puro e montam o objeto manualmente.
    """
    uid = request.session.get("usuario_id")         # ID salvo no login
    tipo = request.session.get("usuario_tipo")      # 'cidadao' ou 'servidor'
    if not uid or not tipo:
        return None                                 # Nao esta logado

    try:
        if tipo == "servidor":
            user = db.buscar_servidor_por_id(uid)
        else:
            user = db.buscar_cidadao_por_id(uid)

        if not user:
            request.session.flush()                 # Sessao invalida — limpa cookie
        return user
    except Exception:
        # Usuario foi desativado ou removido? Limpa a sessao
        request.session.flush()
        return None


def _postgres_sessao(perfil, id_acao):
    """
    [!] DESTAQUE: Injeta variaveis de sessao no PostgreSQL.
    As triggers e functions (03_functions_triggers.sql, 04_rules.sql)
    acessam essas variaveis para saber qual usuario/perfil esta agindo.

    Exemplo de uso na trigger:
        SELECT current_setting('portal.perfil', true);  -- retorna 'CID'
        SELECT current_setting('portal.id_usuario_acao', true);  -- retorna '5'

    terceiro argumento = true → variavel local (so existe nesta conexao)
    """
    perfil = perfil or ""
    id_acao = "" if id_acao is None else str(id_acao)
    with connection.cursor() as c:
        c.execute("SELECT set_config('portal.perfil', %s, true)", [perfil])
        c.execute("SELECT set_config('portal.id_usuario_acao', %s, true)", [id_acao])


class PortalUserMiddleware:
    """
    Middleware registrado em settings.py (MIDDLEWARE).
    [!] Executado em TODA requisicao ANTES de chegar na view.

    Efeitos:
      - request.portal_user → objeto do usuario logado (ou None)
      - set_config() no PG → triggers sabem quem esta agindo
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Busca o usuario logado a partir da sessao
        user = _usuario_da_sessao(request)

        # 2. Disponibiliza em request.portal_user para todas as views/templates
        request.portal_user = user

        # 3. [!] Informa ao PostgreSQL quem esta operando (para triggers/functions)
        #     As variaveis 'portal.perfil' e 'portal.id_usuario_acao' ficam
        #     disponiveis via current_setting() nas funcoes PL/pgSQL.
        if user:
            _postgres_sessao((user.perfil or "").strip(), user.pk)
        else:
            _postgres_sessao(None, None)

        return self.get_response(request)
