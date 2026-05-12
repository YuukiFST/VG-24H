"""
db.py — Camada de Acesso a Dados SQL Puro (Portal VG 24H)

[!] MODULO CENTRAL: Todas as consultas SQL do sistema estao concentradas aqui.
    As views (views_*.py) chamam funcoes deste modulo em vez de escrever SQL inline.

[!] POR QUE SQL PURO?
    Este projeto usa SQL puro (cursor.execute) em vez do Django ORM como
    requisito academico. Isso demonstra dominio de SQL e permite que a
    professora avalie as queries diretamente no codigo Python.

[!] PADRAO DE HIDRATACAO:
    Cada funcao executa um SELECT e converte as linhas (tuplas) em objetos
    SimpleNamespace, que funcionam como objetos com atributos nomeados.
    Exemplo: row[0] vira obj.id_chamado — mais legivel nos templates.

Funcoes organizadas por entidade:
  - Cidadao: buscar_cidadao_por_id, buscar_cidadao_por_email
  - Servidor: buscar_servidor_por_id, buscar_servidor_por_email
  - Chamado: buscar_chamado, popular_status, calcular_stats_semaforo
  - Catalogo: listar_categorias_ativas, listar_bairros_ativos
  - Paginacao: paginar
"""

from types import SimpleNamespace

from django.db import connection
from django.utils import timezone


# ═══════════════════════════════════════════════════════════════
# CIDADAO — Consultas na tabela cidadao
# ═══════════════════════════════════════════════════════════════

def buscar_cidadao_por_id(uid):
    """
    SQL puro: SELECT cidadao por ID (usado pelo middleware a cada requisicao).

    Retorna um objeto Cidadao populado manualmente, ou None se nao encontrado.
    [!] Importa Cidadao localmente para evitar import circular com models.py.
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

    # Monta o objeto Cidadao manualmente (sem ORM)
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
    user._state.adding = False  # Informa ao Django que o objeto existe no banco
    return user


def buscar_cidadao_por_email(email):
    """
    SQL puro: SELECT cidadao por email (usado no login dual).

    Retorna (objeto Cidadao, tipo='cidadao') ou (None, None).
    [!] LOWER(email) garante busca case-insensitive.
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


# ═══════════════════════════════════════════════════════════════
# SERVIDOR — Consultas na tabela servidor
# ═══════════════════════════════════════════════════════════════

def buscar_servidor_por_id(uid):
    """
    SQL puro: SELECT servidor por ID (usado pelo middleware a cada requisicao).

    Retorna um objeto Servidor populado manualmente, ou None.
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
    """
    SQL puro: SELECT servidor por email (usado no login dual).

    Retorna (objeto Servidor, tipo='servidor') ou (None, None).
    """
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


# ═══════════════════════════════════════════════════════════════
# CHAMADO — Consultas na tabela chamado (TABELA CENTRAL)
# ═══════════════════════════════════════════════════════════════

def buscar_chamado(pk):
    """
    SQL puro: SELECT chamado por ID com JOIN em servico e bairro.

    Retorna um SimpleNamespace com todos os campos do chamado,
    incluindo dados do servico (nome, prazos) e bairro (nome_bairro).
    Tambem popula status_atual, sigla_status e cor_semaforo.

    [!] Usado por views_cidadao e views_equipe para detalhe do chamado.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT c.id_chamado, c.num_protocolo, c.prioridade, "
            "c.ponto_de_referencia, c.descricao, c.resolucao, "
            "c.nota_avaliacao, c.comentario_avaliacao, "
            "c.dt_abertura, c.dt_conclusao, c.dt_avaliacao, c.atualizado_em, "
            "c.id_servico, c.id_bairro, c.id_cidadao, "
            "s.nome AS servico_nome, s.descricao AS servico_descricao, "
            "s.prazo_amarelo_dias, s.prazo_vermelho_dias, "
            "b.nome_bairro "
            "FROM chamado c "
            "JOIN servico s ON c.id_servico = s.id_servico "
            "JOIN bairro b ON c.id_bairro = b.id_bairro "
            "WHERE c.id_chamado = %s",
            [pk],
        )
        row = cursor.fetchone()
    if not row:
        return None

    ch = SimpleNamespace(
        id_chamado=row[0], pk=row[0], num_protocolo=row[1], prioridade=row[2],
        ponto_de_referencia=row[3], descricao=row[4], resolucao=row[5],
        nota_avaliacao=row[6], comentario_avaliacao=row[7],
        dt_abertura=row[8], dt_conclusao=row[9], dt_avaliacao=row[10],
        atualizado_em=row[11], id_cidadao_id=row[14],
        id_servico=SimpleNamespace(
            id_servico=row[12], pk=row[12], nome=row[15],
            descricao=row[16], prazo_amarelo_dias=row[17],
            prazo_vermelho_dias=row[18],
        ),
        id_bairro=SimpleNamespace(id_bairro=row[13], pk=row[13], nome_bairro=row[19]),
    )
    # Popula status atual e cor do semaforo
    popular_status(ch)
    return ch


def popular_status(ch):
    """
    SQL puro: busca o status ATUAL do chamado via ULTIMO registro de historico.

    [!] LOGICA CENTRAL DO SISTEMA:
        O chamado NAO tem campo de status direto. O status e determinado
        pelo registro mais recente na tabela historico_chamado.
        Esta funcao popula:
          - ch.status_atual   → objeto com id_status, sigla, descricao
          - ch.sigla_status   → string da sigla (ex: 'AB', 'CO')
          - ch.cor_semaforo   → 'verde', 'amarelo' ou 'vermelho'

    [!] SEMAFORO:
        - 'verde':    dias aberto < prazo_amarelo_dias do servico
        - 'amarelo':  dias aberto >= prazo_amarelo_dias e < prazo_vermelho_dias
        - 'vermelho': dias aberto >= prazo_vermelho_dias
    """
    with connection.cursor() as cursor:
        # Busca o historico mais recente (ORDER BY DESC LIMIT 1)
        cursor.execute(
            "SELECT sc.id_status, sc.sigla, sc.descricao "
            "FROM historico_chamado hc "
            "JOIN status_chamado sc ON hc.id_status = sc.id_status "
            "WHERE hc.id_chamado = %s "
            "ORDER BY hc.dt_alteracao DESC LIMIT 1",
            [ch.pk],
        )
        row = cursor.fetchone()

    if row:
        ch.status_atual = SimpleNamespace(
            id_status=row[0], pk=row[0], sigla=row[1], descricao=row[2],
        )
        ch.sigla_status = (row[1] or "").strip()
    else:
        ch.status_atual = None
        ch.sigla_status = ""

    # Calculo do semaforo baseado nos prazos do servico
    dias = (timezone.now() - ch.dt_abertura).days
    if dias >= ch.id_servico.prazo_vermelho_dias:
        ch.cor_semaforo = "vermelho"
    elif dias >= ch.id_servico.prazo_amarelo_dias:
        ch.cor_semaforo = "amarelo"
    else:
        ch.cor_semaforo = "verde"


def calcular_stats_semaforo(cidadao_id=None):
    """
    SQL puro: calcula estatisticas do semaforo para chamados.

    Retorna dict: {'no_prazo': N, 'atencao': N, 'critico': N}

    [!] Se cidadao_id for informado, filtra apenas os chamados daquele cidadao.
        Se None, calcula para TODOS os chamados (usado pela equipe/gestao).

    [!] A classificacao usa os prazos do servico vinculado ao chamado:
        - no_prazo (verde):  dias < prazo_amarelo_dias
        - atencao (amarelo): prazo_amarelo_dias <= dias < prazo_vermelho_dias
        - critico (vermelho): dias >= prazo_vermelho_dias
    """
    where = ""
    params = []
    if cidadao_id:
        where = "WHERE c.id_cidadao = %s"
        params = [cidadao_id]

    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT c.id_chamado, c.dt_abertura, "
            f"s.prazo_amarelo_dias, s.prazo_vermelho_dias "
            f"FROM chamado c "
            f"JOIN servico s ON c.id_servico = s.id_servico "
            f"{where}",
            params,
        )
        stats = {"no_prazo": 0, "atencao": 0, "critico": 0}
        now = timezone.now()
        for row in cursor.fetchall():
            dias = (now - row[1]).days
            if dias >= row[3]:
                stats["critico"] += 1
            elif dias >= row[2]:
                stats["atencao"] += 1
            else:
                stats["no_prazo"] += 1
    return stats


def buscar_historicos(chamado_pk):
    """
    SQL puro: SELECT historicos de um chamado com JOIN em servidor e status.

    Retorna lista de SimpleNamespace com dados do historico,
    servidor responsavel e status associado.

    [!] LEFT JOIN em servidor: pode ser NULL quando o historico
        foi criado pelo sistema (ex: abertura automatica pelo Trigger 1).
    """
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT hc.id_historico_chamado, hc.dt_alteracao, hc.observacao, "
            "hc.id_servidor, hc.id_status, "
            "sv.nome_completo AS servidor_nome, "
            "sc.sigla AS status_sigla, sc.descricao AS status_descricao "
            "FROM historico_chamado hc "
            "LEFT JOIN servidor sv ON hc.id_servidor = sv.id_servidor "
            "JOIN status_chamado sc ON hc.id_status = sc.id_status "
            "WHERE hc.id_chamado = %s "
            "ORDER BY hc.dt_alteracao",
            [chamado_pk],
        )
        return [
            SimpleNamespace(
                id_historico_chamado=r[0], pk=r[0], dt_alteracao=r[1],
                observacao=r[2], id_servidor_id=r[3],
                id_servidor=SimpleNamespace(nome_completo=r[5]) if r[3] else None,
                id_status=SimpleNamespace(id_status=r[4], sigla=r[6], descricao=r[7]),
            )
            for r in cursor.fetchall()
        ]


def buscar_fotos(chamado_pk):
    """
    SQL puro: SELECT fotos de um chamado ordenadas por data de upload.

    [!] Fotos armazenadas como URLs (Cloudinary ou filesystem local).
    """
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_foto, url_foto, dt_upload "
            "FROM foto_chamado WHERE id_chamado = %s "
            "ORDER BY dt_upload",
            [chamado_pk],
        )
        return [
            SimpleNamespace(id_foto=r[0], pk=r[0], url_foto=r[1], dt_upload=r[2])
            for r in cursor.fetchall()
        ]


# ═══════════════════════════════════════════════════════════════
# CATALOGO — Categorias, Servicos, Bairros
# ═══════════════════════════════════════════════════════════════

def listar_categorias_ativas():
    """
    SQL puro: SELECT categorias ativas ordenadas por nome.

    Retorna lista de SimpleNamespace com id_categoria, nome, descricao.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_categoria, nome, descricao "
            "FROM categoria_servico "
            "WHERE ativo = TRUE ORDER BY nome"
        )
        return [
            SimpleNamespace(
                id_categoria=r[0], pk=r[0], nome=r[1], descricao=r[2],
            )
            for r in cursor.fetchall()
        ]


def listar_servicos_por_categoria(categoria_pk):
    """
    SQL puro: SELECT servicos ativos de uma categoria.

    [!] Usado na pagina inicial, catalogo e formulario de novo chamado.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_servico, nome, descricao, ativo "
            "FROM servico "
            "WHERE id_categoria = %s AND ativo = TRUE "
            "ORDER BY nome",
            [categoria_pk],
        )
        return [
            SimpleNamespace(
                id_servico=r[0], pk=r[0], nome=r[1], descricao=r[2], ativo=r[3],
            )
            for r in cursor.fetchall()
        ]


def listar_bairros_ativos():
    """
    SQL puro: SELECT bairros ativos ordenados por nome.

    [!] Usado em formularios de cadastro, novo chamado e filtros.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_bairro, nome_bairro, cep, regiao, ativo "
            "FROM bairro "
            "WHERE ativo = TRUE "
            "ORDER BY nome_bairro"
        )
        return [
            SimpleNamespace(
                id_bairro=r[0], pk=r[0], nome_bairro=r[1],
                cep=r[2], regiao=r[3], ativo=r[4],
            )
            for r in cursor.fetchall()
        ]


def listar_statuses():
    """
    SQL puro: SELECT todos os status de chamado.

    [!] Retorna os 5 status fixos: AB, EA, EE, CO, CA.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_status, sigla, descricao "
            "FROM status_chamado ORDER BY id_status"
        )
        return [
            SimpleNamespace(id_status=r[0], pk=r[0], sigla=r[1], descricao=r[2])
            for r in cursor.fetchall()
        ]


# ═══════════════════════════════════════════════════════════════
# PAGINACAO — Funcao reutilizavel
# ═══════════════════════════════════════════════════════════════

def paginar(itens, pagina, por_pagina=15):
    """
    Paginacao manual para listas de objetos.

    Recebe uma lista completa de itens e retorna um objeto SimpleNamespace
    compativel com os templates Django (page_obj), contendo:
      - object_list: itens da pagina atual
      - number: numero da pagina atual
      - paginator.num_pages: total de paginas
      - has_previous / has_next: navegacao
      - previous_page_number / next_page_number

    [!] Usa SimpleNamespace em vez de django.core.paginator.Paginator
        porque a paginacao e feita em memoria (todos os itens ja foram
        carregados do banco via SQL puro).
    """
    total_count = len(itens)
    total_pages = max(1, (total_count + por_pagina - 1) // por_pagina)

    try:
        page_number = int(pagina)
    except (ValueError, TypeError):
        page_number = 1
    page_number = max(1, min(page_number, total_pages))

    start = (page_number - 1) * por_pagina
    end = start + por_pagina
    page_items = itens[start:end]

    page_obj = _PageObj(
        object_list=page_items,
        number=page_number,
        paginator=SimpleNamespace(
            num_pages=total_pages,
            page_range=range(1, total_pages + 1),
        ),
        has_previous=page_number > 1,
        has_next=page_number < total_pages,
        previous_page_number=page_number - 1 if page_number > 1 else None,
        next_page_number=page_number + 1 if page_number < total_pages else None,
    )

    return page_obj, total_count


class _PageObj(SimpleNamespace):
    """
    Pagina de resultados compativel com templates Django.

    [!] Python busca __len__ e __iter__ no TIPO (classe), nao na instancia.
        Por isso precisamos de uma classe propria em vez de SimpleNamespace
        com lambdas — len(obj) e iter(obj) so funcionam se definidos aqui.
    """

    def __iter__(self):
        return iter(self.object_list)

    def __len__(self):
        return len(self.object_list)
