"""portal.db.servidor — extraido de db.py (camada SQL pura).
Veja portal/db/__init__.py para a fachada publica."""


from types import SimpleNamespace

from django.db import connection
from django.utils import timezone

from portal.db._shared import _buscar_secretaria_id


def buscar_servidor_por_id(uid):
    """Busca servidor por ID. Usado pelo middleware a cada requisicao.

    Retorna um objeto Servidor populado manualmente ou None.
    """
    from portal.models import Servidor

    with connection.cursor() as cursor:
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
        return None

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

def buscar_servidor_por_email(email):
    """Busca servidor por email (login dual). Retorna (objeto, 'servidor') ou (None, None)."""
    from portal.models import Servidor

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_servidor, nome_completo, senha_hash, perfil, senha_temporaria "
            "FROM servidor "
            "WHERE LOWER(email) = %s AND ativo = TRUE",
            [email],
        )
        row = cursor.fetchone()
    if not row:
        return None, None

    user = Servidor()
    user.id_servidor = row[0]
    user.nome_completo = row[1]
    user.senha_hash = row[2]
    user.perfil = row[3]
    user.senha_temporaria = row[4]
    user._state.adding = False
    return user, "servidor"

def listar_colaboradores():
    """Lista servidores com perfil COL."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_servidor, nome_completo, cpf, email, telefone, "
            "perfil, ativo, dt_cadastro "
            "FROM servidor WHERE perfil = 'COL' "
            "ORDER BY ativo DESC, nome_completo"
        )
        return [SimpleNamespace(id_servidor=r[0], pk=r[0], nome_completo=r[1],
                cpf=r[2], email=r[3], telefone=r[4], perfil=r[5], ativo=r[6], dt_cadastro=r[7])
                for r in cursor.fetchall()]

def inserir_colaborador(dados):
    """Cria novo colaborador com senha provisoria."""
    from django.contrib.auth.hashers import make_password
    sec_id = _buscar_secretaria_id()
    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO servidor (nome_completo, cpf, dt_nascimento, telefone, "
            "email, senha_hash, senha_temporaria, perfil, ativo, dt_cadastro, id_secretaria) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            [dados["nome_completo"], dados["cpf"], dados["dt_nascimento"],
             dados["telefone"], dados["email"].lower(),
             make_password(dados["senha_provisoria"]), "1", "COL", True,
             timezone.now(), sec_id],
        )

def alternar_colaborador_ativo(pk):
    """Alterna status ativo de um colaborador. Retorna (nome, novo_status) ou None."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_servidor, nome_completo, ativo "
            "FROM servidor WHERE id_servidor = %s", [pk]
        )
        row = cursor.fetchone()
        if not row:
            return None
        novo_ativo = not row[2]
        cursor.execute(
            "UPDATE servidor SET ativo = %s WHERE id_servidor = %s",
            [novo_ativo, pk],
        )
        return row[1], "ativado" if novo_ativo else "inativado"

def resetar_senha_colaborador(pk, nova_senha):
    """Redefine senha de colaborador com senha provisoria."""
    from django.contrib.auth.hashers import make_password
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE servidor SET senha_hash = %s, senha_temporaria = '1' "
            "WHERE id_servidor = %s AND perfil = 'COL'",
            [make_password(nova_senha), pk],
        )
        return cursor.rowcount > 0
