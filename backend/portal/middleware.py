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

from portal.models import Cidadao, Servidor


def _usuario_da_sessao(request):
    """
    Le o cookie de sessao e busca o usuario correspondente no banco via SQL puro.
    Retorna um objeto Cidadao ou Servidor, ou None se nao estiver logado.
    [!] Usa SQL puro (nao ORM) porque o login e baseado em sessao Django,
        nao em django.contrib.auth.
    """
    uid = request.session.get("usuario_id")         # ID salvo no login
    tipo = request.session.get("usuario_tipo")      # 'cidadao' ou 'servidor'
    if not uid or not tipo:
        return None                                 # Nao esta logado

    try:
        with connection.cursor() as cursor:
            if tipo == "servidor":
                # SELECT na tabela servidor — busca pelo ID armazenado na sessao
                # [!] SQL puro porque o model Servidor e managed = False
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
                    request.session.flush()         # Sessao invalida
                    return None
                # Monta o objeto Servidor manualmente (sem ORM)
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
                user._state.adding = False          # Informa ao Django que o objeto existe no banco
                return user
            else:
                # SELECT na tabela cidadao — busca pelo ID armazenado na sessao
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
                # Monta o objeto Cidadao manualmente
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
