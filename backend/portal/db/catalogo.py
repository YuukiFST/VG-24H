"""portal.db.catalogo — extraido de db.py (camada SQL pura).
Veja portal/db/__init__.py para a fachada publica."""


# SimpleNamespace eu uso pra criar objetinhos com atributos sem precisar de classe nem ORM
from types import SimpleNamespace

from django.db import connection
from django.utils import timezone

# fetch_all/fetch_one sao meus helpers que rodam o SELECT e ja mapeiam pra
# objeto; _buscar_secretaria_id acha a secretaria padrao
from portal.db._shared import _buscar_secretaria_id, fetch_all, fetch_one


def listar_categorias_ativas():
    """Lista categorias ativas ordenadas por nome."""
    # SELECT simples de categorias ativas, fetch_all ja transforma cada row num objeto com os fields
    return fetch_all(
        "SELECT id_categoria, nome, descricao "
        "FROM categoria_servico WHERE ativo = TRUE ORDER BY nome",
        fields=("id_categoria", "nome", "descricao"),
    )

def listar_bairros_ativos():
    """Lista bairros ativos ordenados por nome. Usado em formularios e filtros."""
    # bairros ativos ordenados por nome
    return fetch_all(
        "SELECT id_bairro, nome_bairro, cep, regiao, ativo "
        "FROM bairro WHERE ativo = TRUE ORDER BY nome_bairro",
        fields=("id_bairro", "nome_bairro", "cep", "regiao", "ativo"),
    )

def listar_statuses():
    """Lista todos os status de chamado. Retorna os 5 status fixos: AB, EA, EE, CO, CA."""
    # pego todos os status ordenados por id (sao fixos: AB, EA, EE, CO, CA)
    return fetch_all(
        "SELECT id_status, sigla, descricao FROM status_chamado ORDER BY id_status",
        fields=("id_status", "sigla", "descricao"),
    )

def listar_servicos_ativos():
    """Lista servicos ativos com id e nome para uso em filtros."""
    # so id e nome dos servicos ativos, pra preencher select de filtro
    return fetch_all(
        "SELECT id_servico, nome FROM servico WHERE ativo = TRUE ORDER BY nome",
        fields=("id_servico", "nome"),
    )

def listar_banners_ativos():
    """Retorna banners ativos ordenados por ordem."""
    return fetch_all(
        "SELECT id_banner, titulo, descricao, url_imagem, link "
        "FROM banner_publicacao "
        # ordeno pela coluna ordem crescente e, em empate, pelo mais recente
        "WHERE ativo = TRUE ORDER BY ordem ASC, dt_criacao DESC",
        fields=("id_banner", "titulo", "descricao", "url_imagem", "link"),
    )

def listar_categorias_com_servicos():
    """Retorna categorias ativas com seus servicos aninhados.

    Usa duas queries (categorias + servicos) agrupadas em Python, em vez de
    uma query por categoria (N+1). A ordenacao global por nome preserva a
    ordem por nome dentro de cada categoria.
    """
    with connection.cursor() as cursor:
        # query 1: pego todas as categorias ativas
        cursor.execute(
            "SELECT id_categoria, nome, descricao "
            "FROM categoria_servico WHERE ativo = TRUE ORDER BY nome"
        )
        cat_rows = cursor.fetchall()
        # query 2: pego todos os servicos ativos (so 2 queries no total, evitando o N+1)
        cursor.execute(
            "SELECT id_categoria, id_servico, nome, descricao FROM servico "
            "WHERE ativo = TRUE ORDER BY nome"
        )
        srv_rows = cursor.fetchall()

    # aqui agrupo os servicos por categoria num dict {id_categoria: [servicos]}
    servicos_por_cat = {}
    for s in srv_rows:
        # setdefault cria a lista se ainda nao existe, dai eu adiciono o servico como objeto
        servicos_por_cat.setdefault(s[0], []).append(
            SimpleNamespace(id_servico=s[1], pk=s[1], nome=s[2], descricao=s[3])
        )

    # agora monto a lista final juntando cada categoria com seus servicos
    categorias = []
    for cat_row in cat_rows:
        cat = SimpleNamespace(id_categoria=cat_row[0], pk=cat_row[0],
                              nome=cat_row[1], descricao=cat_row[2])
        # busco os servicos dessa categoria no dict (lista vazia se nao tiver nenhum)
        servicos = servicos_por_cat.get(cat.pk, [])
        cat.servicos_list = servicos
        categorias.append({"categoria": cat, "servicos": servicos})
    return categorias

def listar_categorias_todas():
    """Lista todas as categorias (ativas e inativas).

    Diferente de listar_categorias_ativas, nao filtra por ativo = TRUE.
    O gestor precisa ver tambem as categorias desativadas para poder reativa-las.
    """
    return fetch_all(
        "SELECT id_categoria, nome, descricao, ativo "
        "FROM categoria_servico ORDER BY ativo DESC, nome",
        fields=("id_categoria", "nome", "descricao", "ativo"),
    )

def inserir_categoria(nome, descricao):
    """Cria nova categoria."""
    # toda categoria tem que pertencer a uma secretaria, entao busco a padrao
    sec_id = _buscar_secretaria_id()
    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO categoria_servico (nome, descricao, ativo, id_secretaria) "
            "VALUES (%s, %s, %s, %s)",
            # descricao or None: se vier string vazia eu salvo NULL no banco
            [nome, descricao or None, True, sec_id],
        )

def atualizar_categoria(pk, nome, descricao):
    """Atualiza categoria."""
    with connection.cursor() as cursor:
        # UPDATE so do nome e descricao, filtrando pelo id
        cursor.execute(
            "UPDATE categoria_servico SET nome = %s, descricao = %s "
            "WHERE id_categoria = %s", [nome, descricao or None, pk]
        )

def listar_servicos_todos():
    """Lista todos os servicos (ativos e inativos) com nome da categoria.

    NAO filtra por ativo = TRUE: traz ativos e inativos, porque o gestor
    precisa ver tambem os servicos desativados para saber o que ja foi
    inativado e eventualmente reativar.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT s.id_servico, s.nome, s.descricao, s.ativo, "
            "s.id_categoria, cat.nome AS categoria_nome "
            "FROM servico s "
            "JOIN categoria_servico cat ON s.id_categoria = cat.id_categoria "
            "ORDER BY s.ativo DESC, s.nome"
        )
        return [SimpleNamespace(id_servico=r[0], pk=r[0], nome=r[1], descricao=r[2],
                ativo=r[3], id_categoria=SimpleNamespace(id_categoria=r[4], pk=r[4], nome=r[5]))
                for r in cursor.fetchall()]

def inserir_servico(nome, descricao, categoria_id):
    """Cria novo servico."""
    with connection.cursor() as cursor:
        # INSERT do servico ja ligando na categoria escolhida
        cursor.execute(
            "INSERT INTO servico (nome, descricao, ativo, id_categoria) "
            "VALUES (%s, %s, %s, %s)",
            [nome, descricao or None, True, categoria_id],
        )

def atualizar_servico(pk, nome, descricao, categoria_id):
    """Atualiza servico."""
    with connection.cursor() as cursor:
        # atualizo nome, descricao e a categoria do servico
        cursor.execute(
            "UPDATE servico SET nome = %s, descricao = %s, id_categoria = %s "
            "WHERE id_servico = %s",
            [nome, descricao or None, categoria_id, pk],
        )

def desativar_servico(pk):
    """Desativa servico (soft delete)."""
    with connection.cursor() as cursor:
        # primeiro confiro se o servico existe
        cursor.execute("SELECT id_servico FROM servico WHERE id_servico = %s", [pk])
        if not cursor.fetchone():
            return False
        # soft delete: nao deleto de verdade, so marco ativo = FALSE
        cursor.execute("UPDATE servico SET ativo = FALSE WHERE id_servico = %s", [pk])
        return True

def contar_chamados_por_servico(pk):
    """Conta quantos chamados estao vinculados a um servico.

    Retorna (total, ativos) onde:
      total  = todos os chamados (abertos + encerrados)
      ativos = apenas chamados ainda nao encerrados (AB, EA, EE)

    Usado para avisar o gestor antes de desativar um servico que possui
    chamados vinculados. O soft delete preserva o historico de qualquer
    forma, mas o aviso impede desativacao acidental de servico em uso.
    """
    with connection.cursor() as cursor:
        # total de chamados (qualquer status)
        cursor.execute(
            "SELECT COUNT(*) FROM chamado WHERE id_servico = %s", [pk]
        )
        total = cursor.fetchone()[0]
        # chamados ativos: aqueles cujo status atual NAO eh concluido (CO) nem cancelado (CA)
        cursor.execute(
            "SELECT COUNT(*) FROM chamado c WHERE c.id_servico = %s AND ("
            "  SELECT sc.sigla FROM historico_chamado hc "
            "  JOIN status_chamado sc ON hc.id_status = sc.id_status "
            "  WHERE hc.id_chamado = c.id_chamado "
            "  ORDER BY hc.dt_alteracao DESC LIMIT 1"
            ") NOT IN ('CO', 'CA')",
            [pk],
        )
        ativos = cursor.fetchone()[0]
        return total, ativos

def desativar_categoria(pk):
    """Desativa categoria (soft delete)."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_categoria FROM categoria_servico WHERE id_categoria = %s", [pk]
        )
        if not cursor.fetchone():
            return False
        cursor.execute(
            "UPDATE categoria_servico SET ativo = FALSE WHERE id_categoria = %s", [pk]
        )
        return True

def ativar_categoria(pk):
    """Reativa categoria."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_categoria FROM categoria_servico WHERE id_categoria = %s", [pk]
        )
        if not cursor.fetchone():
            return False
        cursor.execute(
            "UPDATE categoria_servico SET ativo = TRUE WHERE id_categoria = %s", [pk]
        )
        return True

def listar_bairros_todos():
    """Lista todos os bairros (sem filtro de ativo)."""
    # aqui NAO filtro por ativo, trago todos (inclusive os desativados) pro admin ver
    return fetch_all(
        "SELECT id_bairro, nome_bairro, cep, regiao, ativo "
        "FROM bairro ORDER BY nome_bairro",
        fields=("id_bairro", "nome_bairro", "cep", "regiao", "ativo"),
    )

def inserir_bairro(nome_bairro, cep, regiao):
    """Cria novo bairro."""
    with connection.cursor() as cursor:
        # bairro novo ja entra ativo; cep e regiao viram NULL se vierem vazios
        cursor.execute(
            "INSERT INTO bairro (nome_bairro, cep, regiao, ativo) "
            "VALUES (%s, %s, %s, %s)",
            [nome_bairro, cep or None, regiao or None, True],
        )

def atualizar_bairro(pk, nome_bairro, cep, regiao, ativo=True):
    """Atualiza bairro."""
    with connection.cursor() as cursor:
        # atualizo tudo do bairro de uma vez, inclusive o ativo
        cursor.execute(
            "UPDATE bairro SET nome_bairro = %s, cep = %s, regiao = %s, ativo = %s "
            "WHERE id_bairro = %s",
            [nome_bairro, cep or None, regiao or None, ativo, pk],
        )

def desativar_bairro(pk):
    """Desativa bairro."""
    with connection.cursor() as cursor:
        # confiro se existe antes de mexer
        cursor.execute("SELECT id_bairro FROM bairro WHERE id_bairro = %s", [pk])
        if not cursor.fetchone():
            return False
        # soft delete de novo: so marco ativo = FALSE
        cursor.execute("UPDATE bairro SET ativo = FALSE WHERE id_bairro = %s", [pk])
        return True

def ativar_bairro(pk):
    """Reativa bairro."""
    with connection.cursor() as cursor:
        # confiro existencia
        cursor.execute("SELECT id_bairro FROM bairro WHERE id_bairro = %s", [pk])
        if not cursor.fetchone():
            return False
        # o oposto do desativar: volto pra ativo = TRUE
        cursor.execute("UPDATE bairro SET ativo = TRUE WHERE id_bairro = %s", [pk])
        return True

# deixo os campos do banner numa constante pra reaproveitar nas duas funcoes (listar e buscar) e nao repetir
_BANNER_FIELDS = (
    "id_banner", "titulo", "descricao", "url_imagem", "link",
    "ordem", "ativo", "dt_criacao",
)

def listar_banners_todos():
    """Lista todos os banners ordenados."""
    # todos os banners (sem filtro de ativo), ordenados pela ordem e depois pelo mais recente
    return fetch_all(
        "SELECT id_banner, titulo, descricao, url_imagem, link, "
        "ordem, ativo, dt_criacao "
        "FROM banner_publicacao ORDER BY ordem, dt_criacao DESC",
        fields=_BANNER_FIELDS,
    )

def buscar_banner(pk):
    """Busca banner por ID."""
    # fetch_one pega um unico banner pelo id (ou None se nao achar)
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
        # descubro a proxima ordem: pego o MAX atual (ou -1 se nao tem nenhum) e somo 1
        cursor.execute("SELECT COALESCE(MAX(ordem), -1) + 1 FROM banner_publicacao")
        ordem = cursor.fetchone()[0]
        # insiro o banner ja com essa ordem calculada, ativo e data de agora
        cursor.execute(
            "INSERT INTO banner_publicacao (titulo, descricao, url_imagem, link, "
            "ordem, ativo, dt_criacao) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            [titulo, descricao or None, url_imagem, link or None, ordem, True,
             timezone.now()],
        )

def atualizar_banner(pk, titulo, descricao, url_imagem, link, ordem):
    """Atualiza banner."""
    with connection.cursor() as cursor:
        # atualizo os campos editaveis do banner de uma vez
        cursor.execute(
            "UPDATE banner_publicacao SET titulo = %s, descricao = %s, "
            "url_imagem = %s, link = %s, ordem = %s WHERE id_banner = %s",
            [titulo, descricao or None, url_imagem, link or None, ordem, pk],
        )

def excluir_banner(pk):
    """Exclui banner."""
    with connection.cursor() as cursor:
        # banner eu deleto de verdade (nao eh soft delete), entao confiro se existe antes
        cursor.execute("SELECT id_banner FROM banner_publicacao WHERE id_banner = %s", [pk])
        if not cursor.fetchone():
            return False
        # DELETE de verdade
        cursor.execute("DELETE FROM banner_publicacao WHERE id_banner = %s", [pk])
        return True

def reordenar_banner(pk, direcao):
    """Move banner para cima (-1) ou baixo (+1) por swap de ordens."""
    with connection.cursor() as cursor:
        # pego o banner que quero mover junto com a ordem atual dele
        cursor.execute(
            "SELECT id_banner, ordem FROM banner_publicacao WHERE id_banner = %s", [pk]
        )
        row = cursor.fetchone()
        # se nao existe nao faco nada
        if not row:
            return
        ordem_atual = row[1]
        # subir (-1): acho o vizinho imediatamente acima (maior ordem que ainda eh menor que a minha)
        if direcao == -1:
            cursor.execute(
                "SELECT id_banner, ordem FROM banner_publicacao "
                "WHERE ordem < %s ORDER BY ordem DESC LIMIT 1", [ordem_atual]
            )
        # descer (+1): acho o vizinho imediatamente abaixo (menor ordem que ainda eh maior que a minha)
        elif direcao == 1:
            cursor.execute(
                "SELECT id_banner, ordem FROM banner_publicacao "
                "WHERE ordem > %s ORDER BY ordem ASC LIMIT 1", [ordem_atual]
            )
        else:
            # direcao invalida -> saio
            return
        vizinho = cursor.fetchone()
        # se existe vizinho, eu troco as ordens dos dois (swap): o vizinho fica com a minha e eu com a dele
        if vizinho:
            cursor.execute("UPDATE banner_publicacao SET ordem = %s WHERE id_banner = %s",
                           [ordem_atual, vizinho[0]])
            cursor.execute("UPDATE banner_publicacao SET ordem = %s WHERE id_banner = %s",
                           [vizinho[1], pk])
