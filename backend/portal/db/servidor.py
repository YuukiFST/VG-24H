"""portal.db.servidor — extraido de db.py (camada SQL pura).
Veja portal/db/__init__.py para a fachada publica."""


# cursor pro SQL puro, timezone pra datas
from django.db import connection
from django.utils import timezone

# helpers compartilhados: _buscar_secretaria_id acha a secretaria padrao, fetch_all roda SELECT e mapeia
from portal.db._shared import _buscar_secretaria_id, fetch_all


def buscar_servidor_por_id(uid):
    """Busca servidor por ID. Usado pelo middleware a cada requisicao.

    Retorna um objeto Servidor populado manualmente ou None.
    """
    # import local de novo pra evitar import circular
    from portal.models import Servidor

    with connection.cursor() as cursor:
        # pego todas as colunas do servidor que eu vou precisar
        cursor.execute(
            "SELECT id_servidor, nome_completo, cpf, dt_nascimento, "
            "telefone, email, senha_hash, senha_temporaria, perfil, "
            "dt_cadastro, ativo, id_secretaria "
            "FROM servidor "
            # filtro pelo id e so quem ta ativo, %s escapado
            "WHERE id_servidor = %s AND ativo = TRUE",
            [uid],
        )
        row = cursor.fetchone()
    # nada encontrado -> None
    if not row:
        return None

    # monto o Servidor na mao mapeando row[i] -> atributo
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
    # cuidado: o atributo da FK no Django termina com _id, por isso id_secretaria_id
    user.id_secretaria_id = row[11]
    user._state.adding = False
    return user

def buscar_servidor_por_email(email):
    """Busca servidor por email (login dual). Retorna (objeto, 'servidor') ou (None, None)."""
    from portal.models import Servidor

    with connection.cursor() as cursor:
        # so as colunas do login, igual fiz no cidadao
        cursor.execute(
            "SELECT id_servidor, nome_completo, senha_hash, perfil, senha_temporaria "
            "FROM servidor "
            # LOWER pra email case-insensitive e so ativo
            "WHERE LOWER(email) = LOWER(%s) AND ativo = TRUE",
            [email],
        )
        row = cursor.fetchone()
    # nao achou -> (None, None)
    if not row:
        return None, None

    user = Servidor()
    user.id_servidor = row[0]
    user.nome_completo = row[1]
    user.senha_hash = row[2]
    user.perfil = row[3]
    user.senha_temporaria = row[4]
    user._state.adding = False
    # devolvo "servidor" pra view saber que esse login eh de servidor e nao cidadao
    return user, "servidor"

def listar_colaboradores():
    """Lista servidores com perfil COL."""
    # uso o helper fetch_all que ja roda o SELECT e transforma cada row num objeto com esses fields
    return fetch_all(
        "SELECT id_servidor, nome_completo, cpf, email, telefone, "
        "perfil, ativo, dt_cadastro "
        # so quem tem perfil COL (colaborador)
        "FROM servidor WHERE perfil = 'COL' "
        # ordeno os ativos primeiro (ativo DESC) e depois por nome
        "ORDER BY ativo DESC, nome_completo",
        # esses fields viram os nomes dos atributos na mesma ordem das colunas
        fields=("id_servidor", "nome_completo", "cpf", "email", "telefone",
                "perfil", "ativo", "dt_cadastro"),
    )

def inserir_colaborador(dados):
    """Cria novo colaborador com senha provisoria."""
    from django.contrib.auth.hashers import make_password
    # busco a secretaria padrao pra ligar o colaborador a ela
    sec_id = _buscar_secretaria_id()
    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO servidor (nome_completo, cpf, dt_nascimento, telefone, "
            "email, senha_hash, senha_temporaria, perfil, ativo, dt_cadastro, id_secretaria) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            # email minusculo, senha vira hash; "1" marca senha_temporaria, "COL" o perfil, e ligo a secretaria
            [dados["nome_completo"], dados["cpf"], dados["dt_nascimento"],
             dados["telefone"], dados["email"].lower(),
             make_password(dados["senha_provisoria"]), "1", "COL", True,
             timezone.now(), sec_id],
        )

def alternar_colaborador_ativo(pk):
    """Alterna status ativo de um colaborador. Retorna (nome, novo_status) ou None."""
    with connection.cursor() as cursor:
        # primeiro leio o estado atual do colaborador pra saber se ta ativo ou nao
        cursor.execute(
            "SELECT id_servidor, nome_completo, ativo "
            "FROM servidor WHERE id_servidor = %s", [pk]
        )
        row = cursor.fetchone()
        # se nao existe, nao tem o que alternar
        if not row:
            return None
        # inverto o ativo: se era True vira False e vice-versa
        novo_ativo = not row[2]
        # gravo o valor invertido de volta
        cursor.execute(
            "UPDATE servidor SET ativo = %s WHERE id_servidor = %s",
            [novo_ativo, pk],
        )
        # devolvo o nome e um texto bonitinho pro feedback dependendo do novo estado
        return row[1], "ativado" if novo_ativo else "inativado"

def resetar_senha_colaborador(pk, nova_senha):
    """Redefine senha de colaborador com senha provisoria."""
    from django.contrib.auth.hashers import make_password
    with connection.cursor() as cursor:
        # gravo a nova senha (hash) e marco senha_temporaria = '1' pra forcar troca no proximo login
        cursor.execute(
            "UPDATE servidor SET senha_hash = %s, senha_temporaria = '1' "
            # so atualizo se for mesmo um colaborador (perfil COL), pra nao mexer em outro perfil
            "WHERE id_servidor = %s AND perfil = 'COL'",
            [make_password(nova_senha), pk],
        )
        # rowcount > 0 me diz se realmente atualizou alguma linha (ou seja, achou o colaborador)
        return cursor.rowcount > 0
