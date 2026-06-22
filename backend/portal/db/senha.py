"""portal.db.senha — extraido de db.py (camada SQL pura).
Veja portal/db/__init__.py para a fachada publica."""


from django.db import connection

from portal.db._shared import _validar_tabela


def atualizar_senha_usuario(tabela, pk, senha_hash):
    """Atualiza senha de cidadao ou servidor."""
    _validar_tabela(tabela)
    from django.contrib.auth.hashers import make_password
    hashed = make_password(senha_hash)
    with connection.cursor() as cursor:
        cursor.execute(
            f"UPDATE {tabela} SET senha_hash = %s WHERE "
            f"{'id_cidadao' if tabela == 'cidadao' else 'id_servidor'} = %s",
            [hashed, pk],
        )

def atualizar_senha_servidor(pk, senha_hash):
    """Atualiza senha de servidor e limpa flag temporaria."""
    from django.contrib.auth.hashers import make_password
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE servidor SET senha_hash = %s, senha_temporaria = NULL "
            "WHERE id_servidor = %s", [make_password(senha_hash), pk]
        )

def buscar_cidadao_para_reset(email):
    """Busca cidadao ativo por email para reset de senha."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_cidadao, email FROM cidadao "
            "WHERE LOWER(email) = %s AND ativo = TRUE", [email]
        )
        return cursor.fetchone()

def atualizar_senha_cidadao(uid, senha_hash):
    """Atualiza senha do cidadao."""
    from django.contrib.auth.hashers import make_password
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE cidadao SET senha_hash = %s WHERE id_cidadao = %s",
            [make_password(senha_hash), uid]
        )

def atualizar_foto_perfil(tabela, pk, url):
    """Atualiza foto de perfil (cidadao ou servidor)."""
    _validar_tabela(tabela)
    col = "id_cidadao" if tabela == "cidadao" else "id_servidor"
    with connection.cursor() as cursor:
        cursor.execute(
            f"UPDATE {tabela} SET foto_perfil = %s WHERE {col} = %s", [url, pk]
        )

def remover_foto_perfil(tabela, pk):
    """Remove foto de perfil."""
    _validar_tabela(tabela)
    col = "id_cidadao" if tabela == "cidadao" else "id_servidor"
    with connection.cursor() as cursor:
        cursor.execute(
            f"UPDATE {tabela} SET foto_perfil = NULL WHERE {col} = %s", [pk]
        )
