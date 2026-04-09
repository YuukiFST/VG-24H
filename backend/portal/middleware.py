"""
middleware.py — Middleware de Autenticação do Portal VG 24H

Este middleware é executado AUTOMATICAMENTE em TODA requisição HTTP.
Ele lê o cookie de sessão do navegador e carrega o usuário logado
em request.portal_user, que fica disponível para todas as views e templates.

Fluxo:
1. Usuário faz login → session['usuario_id'] e session['usuario_tipo'] são salvos
2. Toda requisição seguinte → middleware lê a sessão e busca o usuário no banco
3. Coloca em request.portal_user → views podem verificar quem está logado
"""

from django.db import connection

from portal.models import Cidadao, Servidor


def _usuario_da_sessao(request):
    """
    Lê o cookie de sessão e busca o usuário correspondente no banco.
    Retorna um objeto Cidadao ou Servidor, ou None se não estiver logado.
    """
    uid = request.session.get("usuario_id")       # ID salvo no login
    tipo = request.session.get("usuario_tipo")    # 'cidadao' ou 'servidor'
    if not uid or not tipo:
        return None  # nao esta logado
    try:
        if tipo == "servidor":
            # SELECT * FROM servidor WHERE id = uid AND ativo = true
            return Servidor.objects.get(pk=uid, ativo=True)
        else:
            # SELECT * FROM cidadao WHERE id = uid AND ativo = true
            return Cidadao.objects.get(pk=uid, ativo=True)
    except (Cidadao.DoesNotExist, Servidor.DoesNotExist):
        # usuario foi desativado ou removido? Ele limpa a sessão
        request.session.flush()
        return None


def _postgres_sessao(perfil, id_acao):
    """
    Define variáveis de sessão no PostgreSQL.
    Isso permite que triggers e functions no banco saibam
    qual usuário está fazendo a operação (para auditoria/log).
    """
    perfil = perfil or ""
    id_acao = "" if id_acao is None else str(id_acao)
    with connection.cursor() as c:
        c.execute("SELECT set_config('portal.perfil', %s, true)", [perfil])
        c.execute("SELECT set_config('portal.id_usuario_acao', %s, true)", [id_acao])


class PortalUserMiddleware:
    """
    Middleware registrado no settings.py (MIDDLEWARE).
    Executado em TODA requisição antes de chegar na view.
    Resultado: request.portal_user contém o objeto do usuário logado.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Busca o usuário logado a partir da sessão
        user = _usuario_da_sessao(request)

        # 2. Disponibiliza em request.portal_user para todas as views/templates
        request.portal_user = user

        # 3. Informa ao PostgreSQL quem está operando (para triggers)
        if user:
            _postgres_sessao((user.perfil or "").strip(), user.pk)
        else:
            _postgres_sessao(None, None)

        return self.get_response(request)
