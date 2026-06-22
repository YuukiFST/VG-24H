"""
middleware.py — Middleware de autenticacao do Portal VG 24H

Este middleware eh executado automaticamente em toda requisicao HTTP.
Suas responsabilidades sao:

1. Ler o cookie de sessao e buscar o usuario correspondente no banco
   (via db.buscar_cidadao_por_id ou db.buscar_servidor_por_id).
2. Disponibilizar o usuario em request.portal_user para todas as views.
3. Injetar variaveis de sessao no PostgreSQL via set_config() para que
   as triggers e funcoes PL/pgSQL saibam qual usuario esta executando
   a acao (variaveis portal.perfil e portal.id_usuario_acao).

O login salva usuario_id e usuario_tipo no cookie de sessao.
Este middleware le esses valores a cada requisicao e reconstrói
o objeto do usuario.
"""

from django.db import connection

from portal import db


def _usuario_da_sessao(request):
    """Le o cookie de sessao e busca o usuario no banco via SQL puro.

    Retorna um objeto Cidadao ou Servidor populado manualmente,
    ou None se o usuario nao estiver logado. Se a sessao conter
    um ID invalido (usuario desativado ou removido), limpa o cookie.
    """
    uid = request.session.get("usuario_id")
    tipo = request.session.get("usuario_tipo")
    if not uid or not tipo:
        return None

    try:
        user = (
            db.buscar_servidor_por_id(uid)
            if tipo == "servidor"
            else db.buscar_cidadao_por_id(uid)
        )

        if not user:
            request.session.flush()
        return user
    except Exception:
        request.session.flush()
        return None


def _postgres_sessao(perfil, id_acao):
    """Injeta variaveis de sessao no PostgreSQL para uso nas triggers.

    As triggers e funcoes PL/pgSQL (03_functions_triggers.sql) acessam
    essas variaveis via current_setting() para saber qual usuario e
    perfil estao executando a acao. Isso eh usado para:
    - Bloquear operacoes indevidas (ex: cidadao nao pode mudar status)
    - Registrar quem fez cada alteracao (auditoria)
    - Gerar notificacoes para o cidadao correto

    O terceiro parametro (true) indica que a variavel eh local a esta
    conexao, ou seja, nao afeta outras requisicoes simultaneas.
    """
    perfil = perfil or ""
    id_acao = "" if id_acao is None else str(id_acao)
    with connection.cursor() as c:
        c.execute("SELECT set_config('portal.perfil', %s, true)", [perfil])
        c.execute("SELECT set_config('portal.id_usuario_acao', %s, true)", [id_acao])


class PortalUserMiddleware:
    """Middleware registrado em settings.py. Executado em toda requisicao.

    Efeitos:
    - request.portal_user: objeto do usuario logado (ou None)
    - set_config() no PostgreSQL: triggers sabem quem esta agindo
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = _usuario_da_sessao(request)
        request.portal_user = user

        if user:
            _postgres_sessao((user.perfil or "").strip(), user.pk)
        else:
            _postgres_sessao(None, None)

        return self.get_response(request)
