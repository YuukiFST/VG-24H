"""
middleware.py — meu middleware de autenticacao do Portal VG 24H

Esse middleware roda sozinho em TODA requisicao HTTP. O que ele faz pra mim:

1. Le o cookie de sessao e busca o usuario certo no banco
   (com db.buscar_cidadao_por_id ou db.buscar_servidor_por_id).
2. Deixa esse usuario em request.portal_user pra todas as minhas views usarem.
3. Joga umas variaveis de sessao no PostgreSQL com set_config() pra que as
   minhas triggers e funcoes PL/pgSQL saibam quem ta fazendo a acao
   (as variaveis portal.perfil e portal.id_usuario_acao).

No login eu salvo usuario_id e usuario_tipo no cookie de sessao. Aqui no
middleware eu leio esses valores toda requisicao e monto o objeto do usuario
de novo.
"""

# connection eu uso pra rodar SQL puro (set_config) direto na conexao
from django.db import connection

# db e o meu modulo com as funcoes de busca em SQL puro
from portal import db


def _usuario_da_sessao(request):
    """Le o cookie de sessao e vai buscar o usuario no banco com SQL puro.

    Me devolve um objeto Cidadao ou Servidor que eu monto na mao, ou None
    se ninguem ta logado. Se a sessao tiver um ID que nao presta (usuario
    desativado ou apagado) eu limpo o cookie.
    """
    # leio o id e o tipo que eu salvei na sessao la no login
    uid = request.session.get("usuario_id")
    tipo = request.session.get("usuario_tipo")
    # faltou algum dos dois? entao nao tem ninguem logado
    if not uid or not tipo:
        return None

    try:
        # dependendo do tipo eu busco em uma tabela ou na outra
        user = (
            db.buscar_servidor_por_id(uid)
            if tipo == "servidor"
            else db.buscar_cidadao_por_id(uid)
        )

        # achei o id na sessao mas nao tem mais no banco -> limpo a sessao
        if not user:
            request.session.flush()
        return user
    except Exception:
        # deu qualquer erro na busca: por seguranca eu limpo a sessao e volto None
        request.session.flush()
        return None


def _postgres_sessao(perfil, id_acao):
    """Jogo variaveis de sessao no PostgreSQL pra minhas triggers usarem.

    Minhas triggers e funcoes PL/pgSQL (03_functions_triggers.sql) leem
    essas variaveis com current_setting() pra saber qual usuario e perfil
    ta fazendo a acao. Eu uso isso pra:
    - Barrar coisa errada (tipo cidadao querendo mudar status)
    - Anotar quem mexeu em cada alteracao (auditoria)
    - Gerar notificacao pro cidadao certo

    O terceiro parametro (true) diz que a variavel e local dessa conexao,
    ou seja, nao vaza pra outras requisicoes rodando ao mesmo tempo.
    """
    # se vier None eu troco por string vazia pra nao quebrar o set_config
    perfil = perfil or ""
    id_acao = "" if id_acao is None else str(id_acao)
    with connection.cursor() as c:
        # gravo o perfil de quem ta agindo
        c.execute("SELECT set_config('portal.perfil', %s, true)", [perfil])
        # e o id de quem ta agindo, pra auditoria e notificacao
        c.execute("SELECT set_config('portal.id_usuario_acao', %s, true)", [id_acao])


class PortalUserMiddleware:
    """A classe do middleware que eu registrei no settings.py. Roda em toda req.

    No fim das contas ela:
    - bota o usuario logado (ou None) em request.portal_user
    - chama set_config() no PostgreSQL pras triggers saberem quem ta agindo
    """
    def __init__(self, get_response):
        # o Django me passa a proxima coisa da cadeia uma vez so, eu guardo aqui
        self.get_response = get_response

    def __call__(self, request):
        # descubro quem ta logado lendo a sessao
        user = _usuario_da_sessao(request)
        # e deixo disponivel pra qualquer view/decorator pegar
        request.portal_user = user

        if user:
            # tem usuario: passo perfil e id dele pro postgres
            _postgres_sessao((user.perfil or "").strip(), user.pk)
        else:
            # ninguem logado: limpo as variaveis no postgres
            _postgres_sessao(None, None)

        # sigo o fluxo normal e devolvo a resposta
        return self.get_response(request)
