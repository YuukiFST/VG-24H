from django.db import connection

from portal.models import Cidadao, Servidor


def _usuario_da_sessao(request):
    """Recupera o usuário logado da sessão (cidadão ou servidor)."""
    uid = request.session.get("usuario_id")
    tipo = request.session.get("usuario_tipo")  # 'cidadao' ou 'servidor'
    if not uid or not tipo:
        return None
    try:
        if tipo == "servidor":
            return Servidor.objects.get(pk=uid, ativo=True)
        else:
            return Cidadao.objects.get(pk=uid, ativo=True)
    except (Cidadao.DoesNotExist, Servidor.DoesNotExist):
        request.session.flush()
        return None


def _postgres_sessao(perfil, id_acao):
    perfil = perfil or ""
    id_acao = "" if id_acao is None else str(id_acao)
    with connection.cursor() as c:
        c.execute("SELECT set_config('portal.perfil', %s, true)", [perfil])
        c.execute("SELECT set_config('portal.id_usuario_acao', %s, true)", [id_acao])


class PortalUserMiddleware:
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
