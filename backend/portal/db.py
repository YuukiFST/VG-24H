"""
db.py — Camada de acesso a dados SQL puro (Portal VG 24H)

Este modulo concentra todas as consultas SQL do sistema. As views
chamam funcoes deste modulo em vez de escrever SQL inline, seguindo
o principio de separacao de responsabilidades.

O projeto usa SQL puro (cursor.execute) em vez do Django ORM como
requisito academico. Isso permite que as queries sejam avaliadas
diretamente no codigo Python.

Cada funcao executa um SELECT e converte as linhas (tuplas) em objetos
SimpleNamespace, que funcionam como objetos com atributos nomeados.
Exemplo: row[0] vira obj.id_chamado, o que torna o codigo mais legivel
nos templates.
"""

from types import SimpleNamespace

from django.db import connection
from django.utils import timezone


# ------------------------------------------------------------------
# Cidadao — consultas na tabela cidadao
# ------------------------------------------------------------------

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


# ------------------------------------------------------------------
# Servidor — consultas na tabela servidor
# ------------------------------------------------------------------

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


# ------------------------------------------------------------------
# Chamado — consultas na tabela chamado (tabela central do sistema)
# ------------------------------------------------------------------

def buscar_chamado(pk):
    """Busca chamado por ID com JOIN em servico e bairro.

    Retorna um SimpleNamespace com todos os campos do chamado,
    incluindo dados do servico (nome, prazos) e bairro. Tambem
    popula status_atual, sigla_status e cor_semaforo via popular_status().

    Usado por views_cidadao e views_equipe para detalhe do chamado.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT c.id_chamado, c.num_protocolo, c.prioridade, "
            "c.ponto_de_referencia, c.descricao, c.resolucao, "
            "c.nota_avaliacao, c.comentario_avaliacao, "
            "c.dt_abertura, c.dt_conclusao, c.dt_avaliacao, c.atualizado_em, "
            "c.id_servico, c.id_bairro, c.id_cidadao, "
            "s.nome AS servico_nome, s.descricao AS servico_descricao, "
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
            descricao=row[16],
        ),
        id_bairro=SimpleNamespace(id_bairro=row[13], pk=row[13], nome_bairro=row[17]),
    )
    popular_status(ch)
    return ch


def popular_status(ch):
    """Busca o status atual do chamado via ultimo registro de historico.

    O chamado nao tem campo de status direto. O status eh determinado
    pelo registro mais recente na tabela historico_chamado (event sourcing).
    Esta funcao popula tres atributos no objeto ch:
    - status_atual: objeto com id_status, sigla e descricao
    - sigla_status: string da sigla (ex: 'AB', 'CO')
    - cor_semaforo: 'verde', 'amarelo' ou 'vermelho'
    """
    with connection.cursor() as cursor:
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

    from portal.models import ConfiguracaoSemaforo

    config = ConfiguracaoSemaforo.get_singleton()
    ch.cor_semaforo = cor_semaforo(
        ch.dt_abertura,
        config.prazo_amarelo_dias,
        config.prazo_vermelho_dias,
    )


def cor_semaforo(dt_abertura, prazo_amarelo_dias, prazo_vermelho_dias):
    """Classifica a urgencia do chamado com base nos prazos do servico.

    Retorna 'verde' (dentro do prazo), 'amarelo' (atencao) ou 'vermelho' (critico).
    Funcao pura, sem efeitos colaterais.
    """
    dias = (timezone.now() - dt_abertura).days
    if dias >= prazo_vermelho_dias:
        return "vermelho"
    if dias >= prazo_amarelo_dias:
        return "amarelo"
    return "verde"


def calcular_stats_semaforo(cidadao_id=None):
    """Calcula estatisticas do semaforo para chamados em aberto.

    Usa os prazos globais da configuracao_semaforo (CROSS JOIN com singleton).
    Retorna dict com tres chaves: no_prazo, atencao, critico.
    Se cidadao_id for informado, filtra apenas os chamados desse cidadao.
    """
    where = ""
    where_params = []
    if cidadao_id:
        where = "AND c.id_cidadao = %s"
        where_params = [cidadao_id]

    now = timezone.now()
    params = [now, now, now, now] + where_params

    sql = (
        "SELECT "
        "  COALESCE(SUM(CASE WHEN (%s - c.dt_abertura) < make_interval(days := cfg.prazo_amarelo_dias) THEN 1 ELSE 0 END), 0), "
        "  COALESCE(SUM(CASE WHEN (%s - c.dt_abertura) >= make_interval(days := cfg.prazo_amarelo_dias) "
        "    AND (%s - c.dt_abertura) < make_interval(days := cfg.prazo_vermelho_dias) THEN 1 ELSE 0 END), 0), "
        "  COALESCE(SUM(CASE WHEN (%s - c.dt_abertura) >= make_interval(days := cfg.prazo_vermelho_dias) THEN 1 ELSE 0 END), 0) "
        "FROM chamado c "
        "CROSS JOIN configuracao_semaforo cfg "
        "WHERE TRUE " + where
    )

    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        row = cursor.fetchone()
    return {"no_prazo": row[0], "atencao": row[1], "critico": row[2]}


def calcular_stats_semaforo_por_servico():
    """Retorna estatisticas do semaforo agregadas por servico.

    Usa prazos globais da configuracao_semaforo (CROSS JOIN).
    Cada linha contem: id_servico, nome, no_prazo, atencao, critico, total.
    Ordenado por nome do servico.
    """
    now = timezone.now()
    sql = (
        "SELECT "
        "  s.id_servico, s.nome, "
        "  COALESCE(SUM(CASE WHEN (%s - c.dt_abertura) < make_interval(days := cfg.prazo_amarelo_dias) THEN 1 ELSE 0 END), 0), "
        "  COALESCE(SUM(CASE WHEN (%s - c.dt_abertura) >= make_interval(days := cfg.prazo_amarelo_dias) "
        "    AND (%s - c.dt_abertura) < make_interval(days := cfg.prazo_vermelho_dias) THEN 1 ELSE 0 END), 0), "
        "  COALESCE(SUM(CASE WHEN (%s - c.dt_abertura) >= make_interval(days := cfg.prazo_vermelho_dias) THEN 1 ELSE 0 END), 0), "
        "  COUNT(*) "
        "FROM chamado c "
        "CROSS JOIN configuracao_semaforo cfg "
        "JOIN servico s ON c.id_servico = s.id_servico "
        "GROUP BY s.id_servico, s.nome "
        "ORDER BY s.nome"
    )
    with connection.cursor() as cursor:
        cursor.execute(sql, [now, now, now, now])
        rows = cursor.fetchall()
    return [
        {
            "id_servico": r[0],
            "nome": r[1],
            "no_prazo": r[2],
            "atencao": r[3],
            "critico": r[4],
            "total": r[5],
        }
        for r in rows
    ]


def buscar_historicos(chamado_pk):
    """Busca historicos de um chamado com JOIN em servidor e status.

    Retorna lista de SimpleNamespace ordenada por data (mais antigo primeiro).
    LEFT JOIN em servidor permite que registros sem servidor (ex: abertura
    automatica pelo Trigger 1) aparecam normalmente.
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
    """Busca fotos de um chamado ordenadas por data de upload.

    As fotos sao armazenadas como URLs (Cloudinary ou filesystem local).
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


# ------------------------------------------------------------------
# Catalogo — categorias, servicos, bairros, status
# ------------------------------------------------------------------

def listar_categorias_ativas():
    """Lista categorias ativas ordenadas por nome."""
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
    """Lista servicos ativos de uma categoria especifica."""
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
    """Lista bairros ativos ordenados por nome. Usado em formularios e filtros."""
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
    """Lista todos os status de chamado. Retorna os 5 status fixos: AB, EA, EE, CO, CA."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_status, sigla, descricao "
            "FROM status_chamado ORDER BY id_status"
        )
        return [
            SimpleNamespace(id_status=r[0], pk=r[0], sigla=r[1], descricao=r[2])
            for r in cursor.fetchall()
        ]


# ------------------------------------------------------------------
# Paginacao — funcao reutilizavel
# ------------------------------------------------------------------

class _PageObj:
    """Wrapper de paginacao compativel com templates Django.

    Nao pode ser SimpleNamespace porque o Python so enxerga metodos
    dunder (__len__, __iter__) definidos na classe, nao em instancias.
    """

    def __init__(self, object_list, number, paginator,
                 has_previous, has_next,
                 previous_page_number, next_page_number):
        self.object_list = object_list
        self.number = number
        self.paginator = paginator
        self.has_previous = has_previous
        self.has_next = has_next
        self.previous_page_number = previous_page_number
        self.next_page_number = next_page_number

    def __len__(self):
        return len(self.object_list)

    def __iter__(self):
        return iter(self.object_list)


def paginar(itens, pagina, por_pagina=15, total_count=None):
    """Paginacao manual para listas de objetos.

    Recebe uma lista de itens (ja filtrados ou pagina atual) e retorna
    um _PageObj compativel com os templates Django. O total_count permite
    que o chamador passe o COUNT(*) do SQL para evitar contar em Python.

    Se total_count for informado, assume que 'itens' ja contem apenas
    os registros da pagina atual (LIMIT/OFFSET feito no SQL).
    """
    if total_count is None:
        total_count = len(itens)
    total_pages = max(1, (total_count + por_pagina - 1) // por_pagina)

    try:
        page_number = int(pagina)
    except (ValueError, TypeError):
        page_number = 1
    page_number = max(1, min(page_number, total_pages))

    if total_count is not None and total_count != len(itens):
        page_items = itens
    else:
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
