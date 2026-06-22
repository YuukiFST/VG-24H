"""portal.db.cidadao — extraido de db.py (camada SQL pura).
Veja portal/db/__init__.py para a fachada publica."""


from django.db import connection
from django.utils import timezone


def buscar_cidadao_por_id(uid):
    """Busca cidadao por ID. Usado pelo middleware a cada requisicao.

    Retorna um objeto Cidadao populado manualmente (sem ORM) ou None
    se nao encontrado ou inativo. O import local de Cidadao evita
    import circular com models.py.
    """
    from portal.models import Cidadao

    with connection.cursor() as cursor:
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
        return None

    # Monta o objeto Cidadao campo a campo (sem ORM).
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
    user._state.adding = False  # Indica ao Django que o objeto ja existe no banco.
    return user

def buscar_cidadao_por_email(email):
    """Busca cidadao por email (login dual). Retorna (objeto, 'cidadao') ou (None, None).

    LOWER(email) garante busca case-insensitive no PostgreSQL.
    """
    from portal.models import Cidadao

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_cidadao, nome_completo, senha_hash, perfil, senha_temporaria "
            "FROM cidadao "
            "WHERE LOWER(email) = %s AND ativo = TRUE",
            [email],
        )
        row = cursor.fetchone()
    if not row:
        return None, None

    user = Cidadao()
    user.id_cidadao = row[0]
    user.nome_completo = row[1]
    user.senha_hash = row[2]
    user.perfil = row[3]
    user.senha_temporaria = row[4]
    user._state.adding = False
    return user, "cidadao"

def inserir_cidadao(dados):
    """Cria novo cidadao."""
    from django.contrib.auth.hashers import make_password
    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO cidadao (nome_completo, cpf, dt_nascimento, telefone, email, "
            "senha_hash, rua, num_endereco, complemento_endereco, "
            "bairro_endereco, cep_endereco, perfil, ativo, dt_cadastro) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
            "RETURNING id_cidadao",
            [dados["nome_completo"], dados["cpf"], dados["dt_nascimento"],
             dados["telefone"], dados["email"].lower(),
             make_password(dados["senha"]),
             dados.get("rua"), dados.get("num_endereco"), dados.get("complemento_endereco"),
             dados.get("bairro_endereco"), dados.get("cep_endereco"),
              "CID", True, timezone.now()],
        )
        return cursor.fetchone()[0]
