"""portal.db.catalogo — extraido de db.py (camada SQL pura).
Veja portal/db/__init__.py para a fachada publica."""


from types import SimpleNamespace

from django.db import connection
from django.utils import timezone

from portal.db._shared import _buscar_secretaria_id, fetch_all, fetch_one


def listar_categorias_ativas():
    """Lista categorias ativas ordenadas por nome."""
    return fetch_all(
        "SELECT id_categoria, nome, descricao "
        "FROM categoria_servico WHERE ativo = TRUE ORDER BY nome",
        fields=("id_categoria", "nome", "descricao"),
    )

def listar_bairros_ativos():
    """Lista bairros ativos ordenados por nome. Usado em formularios e filtros."""
    return fetch_all(
        "SELECT id_bairro, nome_bairro, cep, regiao, ativo "
        "FROM bairro WHERE ativo = TRUE ORDER BY nome_bairro",
        fields=("id_bairro", "nome_bairro", "cep", "regiao", "ativo"),
    )

def listar_statuses():
    """Lista todos os status de chamado. Retorna os 5 status fixos: AB, EA, EE, CO, CA."""
    return fetch_all(
        "SELECT id_status, sigla, descricao FROM status_chamado ORDER BY id_status",
        fields=("id_status", "sigla", "descricao"),
    )

def listar_servicos_ativos():
    """Lista servicos ativos com id e nome para uso em filtros."""
    return fetch_all(
        "SELECT id_servico, nome FROM servico WHERE ativo = TRUE ORDER BY nome",
        fields=("id_servico", "nome"),
    )

def listar_banners_ativos():
    """Retorna banners ativos ordenados por ordem."""
    return fetch_all(
        "SELECT id_banner, titulo, descricao, url_imagem, link "
        "FROM banner_publicacao "
        "WHERE ativo = TRUE ORDER BY ordem ASC, dt_criacao DESC",
        fields=("id_banner", "titulo", "descricao", "url_imagem", "link"),
    )

def listar_categorias_com_servicos():
    """Retorna categorias ativas com seus servicos aninhados."""
    categorias = []
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_categoria, nome, descricao "
            "FROM categoria_servico WHERE ativo = TRUE ORDER BY nome"
        )
        cat_rows = cursor.fetchall()
    for cat_row in cat_rows:
        cat = SimpleNamespace(id_categoria=cat_row[0], pk=cat_row[0],
                              nome=cat_row[1], descricao=cat_row[2])
        with connection.cursor() as cur:
            cur.execute(
                "SELECT id_servico, nome, descricao FROM servico "
                "WHERE id_categoria = %s AND ativo = TRUE ORDER BY nome",
                [cat.pk],
            )
            servicos = [
                SimpleNamespace(id_servico=r[0], pk=r[0], nome=r[1], descricao=r[2])
                for r in cur.fetchall()
            ]
        cat.servicos_list = servicos
        categorias.append({"categoria": cat, "servicos": servicos})
    return categorias

def listar_categorias_todas():
    """Lista todas as categorias ativas."""
    return fetch_all(
        "SELECT id_categoria, nome, descricao, ativo "
        "FROM categoria_servico WHERE ativo = TRUE ORDER BY nome",
        fields=("id_categoria", "nome", "descricao", "ativo"),
    )

def inserir_categoria(nome, descricao):
    """Cria nova categoria."""
    sec_id = _buscar_secretaria_id()
    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO categoria_servico (nome, descricao, ativo, id_secretaria) "
            "VALUES (%s, %s, %s, %s)",
            [nome, descricao or None, True, sec_id],
        )

def atualizar_categoria(pk, nome, descricao):
    """Atualiza categoria."""
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE categoria_servico SET nome = %s, descricao = %s "
            "WHERE id_categoria = %s", [nome, descricao or None, pk]
        )

def listar_servicos_com_categoria():
    """Lista servicos ativos com nome da categoria."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT s.id_servico, s.nome, s.descricao, s.ativo, "
            "s.id_categoria, cat.nome AS categoria_nome "
            "FROM servico s "
            "JOIN categoria_servico cat ON s.id_categoria = cat.id_categoria "
            "WHERE s.ativo = TRUE ORDER BY s.nome"
        )
        return [SimpleNamespace(id_servico=r[0], pk=r[0], nome=r[1], descricao=r[2],
                ativo=r[3], id_categoria=SimpleNamespace(id_categoria=r[4], pk=r[4], nome=r[5]))
                for r in cursor.fetchall()]

def inserir_servico(nome, descricao, categoria_id):
    """Cria novo servico."""
    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO servico (nome, descricao, ativo, id_categoria) "
            "VALUES (%s, %s, %s, %s)",
            [nome, descricao or None, True, categoria_id],
        )

def atualizar_servico(pk, nome, descricao, categoria_id):
    """Atualiza servico."""
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE servico SET nome = %s, descricao = %s, id_categoria = %s "
            "WHERE id_servico = %s",
            [nome, descricao or None, categoria_id, pk],
        )

def desativar_servico(pk):
    """Desativa servico (soft delete)."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT id_servico FROM servico WHERE id_servico = %s", [pk])
        if not cursor.fetchone():
            return False
        cursor.execute("UPDATE servico SET ativo = FALSE WHERE id_servico = %s", [pk])
        return True

def listar_bairros_todos():
    """Lista todos os bairros (sem filtro de ativo)."""
    return fetch_all(
        "SELECT id_bairro, nome_bairro, cep, regiao, ativo "
        "FROM bairro ORDER BY nome_bairro",
        fields=("id_bairro", "nome_bairro", "cep", "regiao", "ativo"),
    )

def inserir_bairro(nome_bairro, cep, regiao):
    """Cria novo bairro."""
    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO bairro (nome_bairro, cep, regiao, ativo) "
            "VALUES (%s, %s, %s, %s)",
            [nome_bairro, cep or None, regiao or None, True],
        )

def atualizar_bairro(pk, nome_bairro, cep, regiao, ativo=True):
    """Atualiza bairro."""
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE bairro SET nome_bairro = %s, cep = %s, regiao = %s, ativo = %s "
            "WHERE id_bairro = %s",
            [nome_bairro, cep or None, regiao or None, ativo, pk],
        )

def desativar_bairro(pk):
    """Desativa bairro."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT id_bairro FROM bairro WHERE id_bairro = %s", [pk])
        if not cursor.fetchone():
            return False
        cursor.execute("UPDATE bairro SET ativo = FALSE WHERE id_bairro = %s", [pk])
        return True

def ativar_bairro(pk):
    """Reativa bairro."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT id_bairro FROM bairro WHERE id_bairro = %s", [pk])
        if not cursor.fetchone():
            return False
        cursor.execute("UPDATE bairro SET ativo = TRUE WHERE id_bairro = %s", [pk])
        return True

_BANNER_FIELDS = (
    "id_banner", "titulo", "descricao", "url_imagem", "link",
    "ordem", "ativo", "dt_criacao",
)

def listar_banners_todos():
    """Lista todos os banners ordenados."""
    return fetch_all(
        "SELECT id_banner, titulo, descricao, url_imagem, link, "
        "ordem, ativo, dt_criacao "
        "FROM banner_publicacao ORDER BY ordem, dt_criacao DESC",
        fields=_BANNER_FIELDS,
    )

def buscar_banner(pk):
    """Busca banner por ID."""
    return fetch_one(
        "SELECT id_banner, titulo, descricao, url_imagem, link, "
        "ordem, ativo, dt_criacao "
        "FROM banner_publicacao WHERE id_banner = %s",
        [pk],
        fields=_BANNER_FIELDS,
    )

def inserir_banner(titulo, descricao, url_imagem, link):
    """Cria novo banner com ordem auto-incrementada."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT COALESCE(MAX(ordem), -1) + 1 FROM banner_publicacao")
        ordem = cursor.fetchone()[0]
        cursor.execute(
            "INSERT INTO banner_publicacao (titulo, descricao, url_imagem, link, "
            "ordem, ativo, dt_criacao) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            [titulo, descricao or None, url_imagem, link or None, ordem, True,
             timezone.now()],
        )

def atualizar_banner(pk, titulo, descricao, url_imagem, link, ordem):
    """Atualiza banner."""
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE banner_publicacao SET titulo = %s, descricao = %s, "
            "url_imagem = %s, link = %s, ordem = %s WHERE id_banner = %s",
            [titulo, descricao or None, url_imagem, link or None, ordem, pk],
        )

def excluir_banner(pk):
    """Exclui banner."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT id_banner FROM banner_publicacao WHERE id_banner = %s", [pk])
        if not cursor.fetchone():
            return False
        cursor.execute("DELETE FROM banner_publicacao WHERE id_banner = %s", [pk])
        return True

def reordenar_banner(pk, direcao):
    """Move banner para cima (-1) ou baixo (+1) por swap de ordens."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_banner, ordem FROM banner_publicacao WHERE id_banner = %s", [pk]
        )
        row = cursor.fetchone()
        if not row:
            return
        ordem_atual = row[1]
        if direcao == -1:
            cursor.execute(
                "SELECT id_banner, ordem FROM banner_publicacao "
                "WHERE ordem < %s ORDER BY ordem DESC LIMIT 1", [ordem_atual]
            )
        elif direcao == 1:
            cursor.execute(
                "SELECT id_banner, ordem FROM banner_publicacao "
                "WHERE ordem > %s ORDER BY ordem ASC LIMIT 1", [ordem_atual]
            )
        else:
            return
        vizinho = cursor.fetchone()
        if vizinho:
            cursor.execute("UPDATE banner_publicacao SET ordem = %s WHERE id_banner = %s",
                           [ordem_atual, vizinho[0]])
            cursor.execute("UPDATE banner_publicacao SET ordem = %s WHERE id_banner = %s",
                           [vizinho[1], pk])
