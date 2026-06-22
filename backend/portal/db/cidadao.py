"""portal.db.cidadao — extraido de db.py (camada SQL pura).
Veja portal/db/__init__.py para a fachada publica."""


# aqui eu pego o cursor pra rodar SQL puro e o timezone pra data de cadastro
from django.db import connection
from django.utils import timezone


def buscar_cidadao_por_id(uid):
    """Busca cidadao por ID. Usado pelo middleware a cada requisicao.

    Retorna um objeto Cidadao populado manualmente (sem ORM) ou None
    se nao encontrado ou inativo. O import local de Cidadao evita
    import circular com models.py.
    """
    # importo o model aqui dentro de proposito pra nao dar import circular com models.py
    from portal.models import Cidadao

    with connection.cursor() as cursor:
        # monto o SELECT na unha pegando todas as colunas que eu preciso do cidadao
        cursor.execute(
            "SELECT id_cidadao, nome_completo, cpf, dt_nascimento, "
            "telefone, email, senha_hash, senha_temporaria, perfil, "
            "rua, num_endereco, complemento_endereco, bairro_endereco, "
            "cep_endereco, dt_cadastro, ativo "
            "FROM cidadao "
            # filtro pelo id que veio E so quem ta ativo (uso %s pra escapar e nao tomar SQL injection)
            "WHERE id_cidadao = %s AND ativo = TRUE",
            [uid],
        )
        # pego uma linha so, ja que id eh unico
        row = cursor.fetchone()
    # se nao achou nada (ou ta inativo) eu devolvo None
    if not row:
        return None

    # aqui eu monto o objeto Cidadao na mao, campo por campo, sem usar o ORM
    user = Cidadao()
    # vou mapeando cada posicao da tupla row pra um atributo, na mesma ordem do SELECT
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
    # esse truque diz pro Django que o objeto ja existe no banco (nao eh INSERT novo)
    user._state.adding = False
    return user

def buscar_cidadao_por_email(email):
    """Busca cidadao por email (login dual). Retorna (objeto, 'cidadao') ou (None, None).

    LOWER(email) garante busca case-insensitive no PostgreSQL.
    """
    from portal.models import Cidadao

    with connection.cursor() as cursor:
        # aqui so pego o que preciso pro login (hash da senha, perfil etc), nao o cidadao inteiro
        cursor.execute(
            "SELECT id_cidadao, nome_completo, senha_hash, perfil, senha_temporaria "
            "FROM cidadao "
            # uso LOWER(email) pra comparar sem ligar pra maiuscula/minuscula, e so quem ta ativo
            "WHERE LOWER(email) = %s AND ativo = TRUE",
            [email],
        )
        row = cursor.fetchone()
    # se nao achou devolvo a tupla (None, None) pra view saber que nao eh cidadao
    if not row:
        return None, None

    # mesmo esquema: monto o objeto na mao so com os campos do login
    user = Cidadao()
    user.id_cidadao = row[0]
    user.nome_completo = row[1]
    user.senha_hash = row[2]
    user.perfil = row[3]
    user.senha_temporaria = row[4]
    user._state.adding = False
    # retorno o user e a string "cidadao" pra identificar o tipo (login dual com servidor)
    return user, "cidadao"

def inserir_cidadao(dados):
    """Cria novo cidadao."""
    # importo o make_password aqui pra nunca salvar senha em texto puro, sempre hash
    from django.contrib.auth.hashers import make_password
    with connection.cursor() as cursor:
        cursor.execute(
            # INSERT listando todas as colunas e seus %s na mesma ordem dos valores la embaixo
            "INSERT INTO cidadao (nome_completo, cpf, dt_nascimento, telefone, email, "
            "senha_hash, rua, num_endereco, complemento_endereco, "
            "bairro_endereco, cep_endereco, perfil, ativo, dt_cadastro) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
            # uso RETURNING pra ja pegar o id gerado pelo banco e devolver
            "RETURNING id_cidadao",
            # aqui ligo cada %s ao valor: email vai minusculo, senha vira hash, endereco eh opcional (.get)
            [dados["nome_completo"], dados["cpf"], dados["dt_nascimento"],
             dados["telefone"], dados["email"].lower(),
             make_password(dados["senha"]),
             dados.get("rua"), dados.get("num_endereco"), dados.get("complemento_endereco"),
             dados.get("bairro_endereco"), dados.get("cep_endereco"),
             # forco perfil "CID" (cidadao), ativo True e a data de cadastro como agora
              "CID", True, timezone.now()],
        )
        # pego o id_cidadao novo que o RETURNING me deu
        return cursor.fetchone()[0]
