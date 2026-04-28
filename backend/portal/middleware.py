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
    Lê o cookie de sessão e busca o usuário correspondente no banco via SQL puro.
    Retorna um objeto Cidadao ou Servidor, ou None se não estiver logado.
    """
    uid = request.session.get("usuario_id")       # ID salvo no login
    tipo = request.session.get("usuario_tipo")    # 'cidadao' ou 'servidor'
    if not uid or not tipo:
        return None  # nao esta logado
    try:
        with connection.cursor() as cursor:
            if tipo == "servidor":
                # SELECT na tabela servidor — busca pelo ID armazenado na sessão
                cursor.execute(
                    "SELECT id_servidor, nome_completo, cpf, dt_nascimento, "
                    "telefone, email, senha_hash, senha_temporaria, perfil, "
                    "dt_cadastro, ativo, id_secretaria "
                    "FROM servidor "
                    "WHERE id_servidor = %s AND ativo = TRUE",
                    [uid],
                )
                row = cursor.fetchone()
                if not row:
                    request.session.flush()
                    return None
                # Monta o objeto Servidor com os dados retornados pelo SQL
                user = Servidor()
                user.id_servidor = row[0]
                user.nome_completo = row[1]
                user.cpf = row[2]
                user.dt_nascimento = row[3]
                user.telefone = row[4]
                user.email = row[5]
                user.senha_hash = row[6]
                user.senha_temporaria = row[7]
                user.perfil = row[8]
                user.dt_cadastro = row[9]
                user.ativo = row[10]
                user.id_secretaria_id = row[11]
                user._state.adding = False
                return user
            else:
                # SELECT na tabela cidadao — busca pelo ID armazenado na sessão
                cursor.execute(
                    "SELECT id_cidadao, nome_completo, cpf, dt_nascimento, "
                    "telefone, email, senha_hash, senha_temporaria, perfil, "
                    "rua, num_endereco, complemento_endereco, bairro_endereco, "
                    "cep_endereco, dt_cadastro, ativo "
                    "FROM cidadao "
                    "WHERE id_cidadao = %s AND ativo = TRUE",
                    [uid],
                )
                row = cursor.fetchone()
                if not row:
                    request.session.flush()
                    return None
                # Monta o objeto Cidadao com os dados retornados pelo SQL
                user = Cidadao()
                user.id_cidadao = row[0]
                user.nome_completo = row[1]
                user.cpf = row[2]
                user.dt_nascimento = row[3]
                user.telefone = row[4]
                user.email = row[5]
                user.senha_hash = row[6]
                user.senha_temporaria = row[7]
                user.perfil = row[8]
                user.rua = row[9]
                user.num_endereco = row[10]
                user.complemento_endereco = row[11]
                user.bairro_endereco = row[12]
                user.cep_endereco = row[13]
                user.dt_cadastro = row[14]
                user.ativo = row[15]
                user._state.adding = False
                return user
    except Exception:
        # usuario foi desativado ou removido? Limpa a sessão
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
