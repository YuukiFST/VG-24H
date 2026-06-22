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

from portal.models import ConfiguracaoSemaforo
from portal.types import (
    BairroRef,
    ChamadoDTO,
    FotoDTO,
    HistoricoDTO,
    ServicoRef,
    ServidorRef,
    StatusRef,
)

TABELAS_VALIDAS = frozenset({"cidadao", "servidor"})


def _validar_tabela(tabela):
    if tabela not in TABELAS_VALIDAS:
        raise ValueError(f"Tabela invalida: {tabela!r}. Permitidas: {sorted(TABELAS_VALIDAS)}")


COLUNAS_LATERAL_VALIDAS = frozenset({
    "sc.sigla, sc.descricao, sc.id_status",
    "sc.sigla",
})


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

    ch = ChamadoDTO(
        id_chamado=row[0], pk=row[0], num_protocolo=row[1], prioridade=row[2],
        ponto_de_referencia=row[3], descricao=row[4], resolucao=row[5],
        nota_avaliacao=row[6], comentario_avaliacao=row[7],
        dt_abertura=row[8], dt_conclusao=row[9], dt_avaliacao=row[10],
        atualizado_em=row[11], id_cidadao_id=row[14],
        id_servico=ServicoRef(
            id_servico=row[12], pk=row[12], nome=row[15],
            descricao=row[16],
        ),
        id_bairro=BairroRef(id_bairro=row[13], pk=row[13], nome_bairro=row[17]),
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
        ch.status_atual = StatusRef(
            id_status=row[0], pk=row[0], sigla=row[1], descricao=row[2],
        )
        ch.sigla_status = (row[1] or "").strip()
    else:
        ch.status_atual = None
        ch.sigla_status = ""


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
            HistoricoDTO(
                id_historico_chamado=r[0], pk=r[0], dt_alteracao=r[1],
                observacao=r[2], id_servidor_id=r[3],
                id_servidor=ServidorRef(nome_completo=r[5]) if r[3] else None,
                id_status=StatusRef(id_status=r[4], pk=r[4], sigla=r[6], descricao=r[7]),
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
            FotoDTO(id_foto=r[0], pk=r[0], url_foto=r[1], dt_upload=r[2])
            for r in cursor.fetchall()
        ]


def excluir_chamado_com_cascata(chamado_id):
    """Exclui chamado em cascata com bypass de triggers.

    Ativa a flag portal.excluindo na sessao PostgreSQL para permitir
    que os triggers de protecao (fn_historico_sem_delete) deixem
    os DELETEs passarem. A flag vale para toda a transacao atual.

    Deleta na ordem correta respeitando as FKs:
    foto_chamado → historico_chamado → notificacao → chamado.
    """
    from django.db import transaction
    with transaction.atomic(), connection.cursor() as cursor:
        cursor.execute("SELECT set_config('portal.excluindo', 'true', true)")
        cursor.execute("DELETE FROM foto_chamado WHERE id_chamado = %s", [chamado_id])
        cursor.execute("DELETE FROM historico_chamado WHERE id_chamado = %s", [chamado_id])
        cursor.execute("DELETE FROM notificacao WHERE id_chamado = %s", [chamado_id])
        cursor.execute("DELETE FROM chamado WHERE id_chamado = %s", [chamado_id])


def criar_historico(chamado_id, status_id, servidor_id=None, observacao=None, dt_alteracao=None):
    """Insere registro em historico_chamado (event sourcing).

    Cada chamada gera um INSERT na tabela historico_chamado, nunca um UPDATE.
    Os triggers Trigger 2A e 2B disparam automaticamente apos o INSERT
    para atualizar atualizado_em e, se aplicavel, dt_conclusao e notificacao.

    Parametros:
        chamado_id: PK do chamado na tabela chamado.
        status_id: PK do status na tabela status_chamado.
        servidor_id: PK do servidor (None se a acao for do cidadao).
        observacao: texto opcional (obs do cidadao, motivo de cancelamento, etc).
        dt_alteracao: data/hora da alteracao (padrao: timezone.now()).

    Retorna o id_historico_chamado gerado (via RETURNING).
    """
    if dt_alteracao is None:
        dt_alteracao = timezone.now()

    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO historico_chamado "
            "(id_chamado, id_servidor, id_status, observacao, dt_alteracao) "
            "VALUES (%s, %s, %s, %s, %s) "
            "RETURNING id_historico_chamado",
            [chamado_id, servidor_id, status_id, observacao, dt_alteracao],
        )
        return cursor.fetchone()[0]


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


def listar_servicos_ativos():
    """Lista servicos ativos com id e nome para uso em filtros."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_servico, nome FROM servico WHERE ativo = TRUE ORDER BY nome"
        )
        return [
            SimpleNamespace(id_servico=r[0], pk=r[0], nome=r[1])
            for r in cursor.fetchall()
        ]


# ------------------------------------------------------------------
# Utilitarios de validacao
# ------------------------------------------------------------------

def existe_email_ou_cpf(tabela, email, cpf):
    """Verifica se email ou CPF ja existem em uma tabela de usuarios."""
    _validar_tabela(tabela)
    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT EXISTS("
            f"  SELECT 1 FROM {tabela} WHERE LOWER(email) = %s"
            f") OR EXISTS("
            f"  SELECT 1 FROM {tabela} WHERE cpf = %s"
            f")",
            [email.lower(), cpf],
        )
        return cursor.fetchone()[0]


# ------------------------------------------------------------------
# SQL helpers — fragmentos reutilizaveis
# ------------------------------------------------------------------

def sql_lateral_ultimo_status(colunas="sc.sigla, sc.descricao, sc.id_status", alias="c"):
    """Retorna fragmento SQL para JOIN LATERAL que busca o ultimo status do chamado.

    Usado por varias views que listam chamados com seu status atual.
    Aceita colunas personalizadas e alias da tabela chamado para flexibilidade.

    ATENCAO: colunas e alias sao interpolados via f-string — jamais passe
    dados de entrada do usuario aqui. Use apenas literais do codigo.
    """
    if colunas not in COLUNAS_LATERAL_VALIDAS:
        raise ValueError(f"Colunas invalidas: {colunas!r}")
    if alias != "c":
        raise ValueError(f"Injection detection: alias inesperado {alias!r}")
    return (
        "JOIN LATERAL ("
        f"  SELECT {colunas} FROM historico_chamado hc "
        "  JOIN status_chamado sc ON hc.id_status = sc.id_status "
        f"  WHERE hc.id_chamado = {alias}.id_chamado "
        "  ORDER BY hc.dt_alteracao DESC LIMIT 1"
        ") ultimo ON TRUE "
    )


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


# ------------------------------------------------------------------
# Views publicas (root) — banners, categorias, stats
# ------------------------------------------------------------------

def listar_banners_ativos():
    """Retorna banners ativos ordenados por ordem."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_banner, titulo, descricao, url_imagem, link "
            "FROM banner_publicacao "
            "WHERE ativo = TRUE ORDER BY ordem ASC, dt_criacao DESC"
        )
        return [
            SimpleNamespace(id_banner=r[0], pk=r[0], titulo=r[1], descricao=r[2],
                            url_imagem=r[3], link=r[4])
            for r in cursor.fetchall()
        ]


def listar_categorias_com_servicos():
    """Retorna categorias ativas com seus servicos aninhados."""
    from types import SimpleNamespace
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


def buscar_stats_publicas():
    """Retorna estatisticas da pagina inicial."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) FROM chamado c WHERE ("
            "  SELECT sc.sigla FROM historico_chamado hc "
            "  JOIN status_chamado sc ON hc.id_status = sc.id_status "
            "  WHERE hc.id_chamado = c.id_chamado "
            "  ORDER BY hc.dt_alteracao DESC LIMIT 1"
            ") = 'CO'"
        )
        total_resolvidos = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM bairro WHERE ativo = TRUE")
        total_bairros = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM servico WHERE ativo = TRUE")
        total_servicos = cursor.fetchone()[0]
    return {"total_resolvidos": total_resolvidos, "total_bairros": total_bairros, "total_servicos": total_servicos}


# ------------------------------------------------------------------
# Listagem de chamados (cidadao) — com filtros e paginacao
# ------------------------------------------------------------------

def listar_chamados_cidadao(uid, status=None, data=None, q=None, pagina=1, por_pagina=15):
    """Lista chamados do cidadao com filtros e paginacao.

    Retorna (lista_de_chamados, total_count) — ambos ja paginados.
    Cada chamado inclui cor_semaforo e sigla_status.
    """
    offset = (pagina - 1) * por_pagina
    sql_base = (
        "FROM chamado c "
        "JOIN servico s ON c.id_servico = s.id_servico "
        "JOIN bairro b ON c.id_bairro = b.id_bairro "
        + sql_lateral_ultimo_status()
        + "WHERE c.id_cidadao = %s "
    )
    select_cols = (
        "SELECT c.id_chamado, c.num_protocolo, c.prioridade, "
        "c.descricao, c.dt_abertura, c.atualizado_em, "
        "c.id_servico, c.id_bairro, "
        "s.nome AS servico_nome, b.nome_bairro, "
        "ultimo.sigla AS sigla_status, "
        "ultimo.descricao AS status_descricao "
    )
    params = [uid]

    if status:
        sql_base += "AND ultimo.sigla = %s "
        params.append(status)
    if data:
        sql_base += "AND c.dt_abertura::date = %s "
        params.append(data)
    if q:
        from portal.utils import escape_like
        sql_base += "AND c.num_protocolo ILIKE %s "
        params.append(f"%{escape_like(q)}%")

    count_sql = "SELECT COUNT(*) " + sql_base
    with connection.cursor() as cursor:
        cursor.execute(count_sql, params)
        total_count = cursor.fetchone()[0]
        data_sql = select_cols + sql_base + "ORDER BY c.dt_abertura DESC LIMIT %s OFFSET %s"
        cursor.execute(data_sql, params + [por_pagina, offset])
        rows = cursor.fetchall()

    config = ConfiguracaoSemaforo.get_singleton()
    from types import SimpleNamespace
    chamados = []
    for r in rows:
        cor = cor_semaforo(r[4], config.prazo_amarelo_dias, config.prazo_vermelho_dias)
        sigla = (r[10] or "").strip()
        chamados.append(SimpleNamespace(
            id_chamado=r[0], pk=r[0], num_protocolo=r[1], prioridade=r[2],
            descricao=r[3], dt_abertura=r[4], atualizado_em=r[5],
            id_servico=SimpleNamespace(id_servico=r[6], pk=r[6], nome=r[8]),
            id_bairro=SimpleNamespace(id_bairro=r[7], pk=r[7], nome_bairro=r[9]),
            sigla_status=sigla, cor_semaforo=cor,
            status_atual=SimpleNamespace(sigla=sigla, descricao=r[11]),
        ))
    return chamados, total_count


# ------------------------------------------------------------------
# Listagem de chamados (equipe) — com filtros, ordenacao, paginacao
# ------------------------------------------------------------------

def listar_chamados_equipe(filtros, pagina=1, por_pagina=15):
    """Lista todos os chamados com filtros para a equipe.

    filtros = dict com chaves: bairro, status, servico, de, ate,
              mostrar_encerrados, ordenar_por, direcao
    Retorna (lista_de_chamados, total_count).
    """
    from portal.utils import formatar_dias_em_aberto
    offset = (pagina - 1) * por_pagina

    sql_base = (
        "FROM chamado c "
        "JOIN servico s ON c.id_servico = s.id_servico "
        "JOIN bairro b ON c.id_bairro = b.id_bairro "
        "JOIN cidadao ci ON c.id_cidadao = ci.id_cidadao "
        + sql_lateral_ultimo_status()
        + "WHERE TRUE "
    )
    select_cols = (
        "SELECT c.id_chamado, c.num_protocolo, c.prioridade, "
        "c.descricao, c.dt_abertura, c.atualizado_em, "
        "c.id_servico, c.id_bairro, c.id_cidadao, "
        "s.nome AS servico_nome, b.nome_bairro, "
        "ci.nome_completo AS cidadao_nome, "
        "ultimo.sigla AS sigla_status, "
        "ultimo.descricao AS status_descricao "
    )
    params = []

    bairro = filtros.get("bairro")
    st = filtros.get("status")
    servico_filter = filtros.get("servico")
    d0 = filtros.get("de")
    d1 = filtros.get("ate")
    mostrar_encerrados = filtros.get("mostrar_encerrados", False)
    ordenar_por = filtros.get("ordenar_por", "prioridade")
    direcao = filtros.get("direcao", "desc")

    if bairro:
        sql_base += "AND c.id_bairro = %s "; params.append(bairro)
    if st:
        sql_base += "AND ultimo.id_status = %s "; params.append(st)
    if servico_filter:
        sql_base += "AND c.id_servico = %s "; params.append(servico_filter)
    if d0:
        sql_base += "AND c.dt_abertura::date >= %s "; params.append(d0)
    if d1:
        sql_base += "AND c.dt_abertura::date <= %s "; params.append(d1)
    if not mostrar_encerrados:
        sql_base += "AND ultimo.sigla NOT IN ('CO', 'CA') "

    count_sql = "SELECT COUNT(*) " + sql_base
    coluna_ordem = {
        "prioridade": "c.prioridade", "dt_abertura": "c.dt_abertura",
        "protocolo": "c.num_protocolo", "dias_aberto": "NOW() - c.dt_abertura",
    }.get(ordenar_por, "c.prioridade")
    ordem_direcao = "DESC" if direcao == "desc" else "ASC"
    order_fixo = "CASE WHEN ultimo.sigla IN ('CO','CA') THEN 1 ELSE 0 END"
    order_clause = f"ORDER BY {order_fixo}, {coluna_ordem} {ordem_direcao}"
    if ordenar_por == "prioridade":
        order_clause += ", c.dt_abertura DESC"

    data_sql = select_cols + sql_base + order_clause + " LIMIT %s OFFSET %s"
    with connection.cursor() as cursor:
        cursor.execute(count_sql, params)
        total_count = cursor.fetchone()[0]
        cursor.execute(data_sql, params + [por_pagina, offset])
        rows = cursor.fetchall()

    config = ConfiguracaoSemaforo.get_singleton()
    from types import SimpleNamespace
    linhas = []
    for r in rows:
        cor = cor_semaforo(r[4], config.prazo_amarelo_dias, config.prazo_vermelho_dias)
        sigla = (r[12] or "").strip()
        ch = SimpleNamespace(
            id_chamado=r[0], pk=r[0], num_protocolo=r[1], prioridade=r[2],
            descricao=r[3], dt_abertura=r[4], atualizado_em=r[5],
            id_servico=SimpleNamespace(id_servico=r[6], pk=r[6], nome=r[9]),
            id_bairro=SimpleNamespace(id_bairro=r[7], pk=r[7], nome_bairro=r[10]),
            id_cidadao=SimpleNamespace(id_cidadao=r[8], pk=r[8], nome_completo=r[11]),
            sigla_status=sigla, cor_semaforo=cor,
            status_atual=SimpleNamespace(sigla=sigla, descricao=r[13]),
        )
        linhas.append({"ch": ch, "cor": cor, "dias_aberto": formatar_dias_em_aberto(ch.dt_abertura)})
    return linhas, total_count


# ------------------------------------------------------------------
# Chamado detail (equipe) — com dados completos
# ------------------------------------------------------------------

def buscar_chamado_detalhe_equipe(pk):
    """Busca chamado completo para a view da equipe, com servico/bairro/cidadao/categoria."""
    from types import SimpleNamespace
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT c.id_chamado, c.num_protocolo, c.prioridade, "
            "c.ponto_de_referencia, c.descricao, c.resolucao, "
            "c.nota_avaliacao, c.comentario_avaliacao, "
            "c.dt_abertura, c.dt_conclusao, c.dt_avaliacao, c.atualizado_em, "
            "c.id_servico, c.id_bairro, c.id_cidadao, "
            "s.nome AS servico_nome, s.descricao AS servico_descricao, "
            "b.nome_bairro, "
            "ci.nome_completo AS cidadao_nome, ci.email AS cidadao_email, "
            "ci.telefone AS cidadao_telefone, "
            "cat.nome AS categoria_nome "
            "FROM chamado c "
            "JOIN servico s ON c.id_servico = s.id_servico "
            "JOIN bairro b ON c.id_bairro = b.id_bairro "
            "JOIN cidadao ci ON c.id_cidadao = ci.id_cidadao "
            "JOIN categoria_servico cat ON s.id_categoria = cat.id_categoria "
            "WHERE c.id_chamado = %s", [pk]
        )
        row = cursor.fetchone()
    if not row:
        return None
    ch = SimpleNamespace(
        id_chamado=row[0], pk=row[0], num_protocolo=row[1], prioridade=row[2],
        ponto_de_referencia=row[3], descricao=row[4], resolucao=row[5],
        nota_avaliacao=row[6], comentario_avaliacao=row[7],
        dt_abertura=row[8], dt_conclusao=row[9], dt_avaliacao=row[10],
        atualizado_em=row[11],
        id_servico=SimpleNamespace(id_servico=row[12], pk=row[12], nome=row[15],
                                   descricao=row[16],
                                   id_categoria=SimpleNamespace(nome=row[21])),
        id_bairro=SimpleNamespace(id_bairro=row[13], pk=row[13], nome_bairro=row[17]),
        id_cidadao=SimpleNamespace(id_cidadao=row[14], pk=row[14],
                                   nome_completo=row[18], email=row[19], telefone=row[20]),
    )
    popular_status(ch)
    return ch


# ------------------------------------------------------------------
# Verificacoes e status
# ------------------------------------------------------------------

def chamado_existe(pk):
    """Retorna True se o chamado existe."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1 FROM chamado WHERE id_chamado = %s", [pk])
        return cursor.fetchone() is not None


def buscar_sigla_status_atual(chamado_id):
    """Retorna a sigla do status atual do chamado."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT sc.sigla FROM historico_chamado hc "
            "JOIN status_chamado sc ON hc.id_status = sc.id_status "
            "WHERE hc.id_chamado = %s "
            "ORDER BY hc.dt_alteracao DESC LIMIT 1", [chamado_id]
        )
        row = cursor.fetchone()
    return row[0].strip() if row else ""


def listar_status_com_sigla_map():
    """Retorna dict {id_status: sigla} para uso no JS de status."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT id_status, sigla FROM status_chamado")
        return {r[0]: r[1].strip() for r in cursor.fetchall()}


def buscar_configuracao_prazos():
    """Retorna configuracao de prazos do semaforo ou defaults."""
    from types import SimpleNamespace
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT prazo_amarelo_dias, prazo_vermelho_dias "
            "FROM configuracao_semaforo WHERE id = 1"
        )
        row = cursor.fetchone()
    return SimpleNamespace(
        prazo_amarelo_dias=row[0] if row else 15,
        prazo_vermelho_dias=row[1] if row else 30,
    )


def atualizar_configuracao_prazos(prazo_amarelo, prazo_vermelho):
    """Atualiza prazos globais do semaforo."""
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE configuracao_semaforo SET prazo_amarelo_dias = %s, "
            "prazo_vermelho_dias = %s WHERE id = 1",
            [prazo_amarelo, prazo_vermelho],
        )


# ------------------------------------------------------------------
# Dashboard — metricas e charts
# ------------------------------------------------------------------

def buscar_stats_dashboard():
    """Retorna metricas do dashboard da equipe."""
    from datetime import timedelta
    agora = timezone.now()
    hoje = agora.date()
    inicio_semana = hoje - timedelta(days=7)
    with connection.cursor() as cursor:
        cursor.execute('''
            SELECT COUNT(*) FROM chamado c
            WHERE (
                SELECT sc.sigla FROM historico_chamado hc
                JOIN status_chamado sc ON hc.id_status = sc.id_status
                WHERE hc.id_chamado = c.id_chamado
                ORDER BY hc.dt_alteracao DESC LIMIT 1
            ) = 'CO' AND c.dt_conclusao::date = %s
        ''', [hoje])
        atendidas_hoje = cursor.fetchone()[0] or 0
        cursor.execute('''
            SELECT COUNT(*) FROM chamado c
            WHERE (
                SELECT sc.sigla FROM historico_chamado hc
                JOIN status_chamado sc ON hc.id_status = sc.id_status
                WHERE hc.id_chamado = c.id_chamado
                ORDER BY hc.dt_alteracao DESC LIMIT 1
            ) = 'CO' AND c.dt_conclusao::date >= %s
        ''', [inicio_semana])
        atendidas_semana = cursor.fetchone()[0] or 0
        cursor.execute('''
            SELECT sc.descricao, COUNT(c.id_chamado)
            FROM chamado c
            JOIN historico_chamado hc ON hc.id_chamado = c.id_chamado
            JOIN status_chamado sc ON sc.id_status = hc.id_status
            WHERE hc.id_historico_chamado = (
                SELECT id_historico_chamado FROM historico_chamado
                WHERE id_chamado = c.id_chamado ORDER BY dt_alteracao DESC LIMIT 1
            ) GROUP BY sc.descricao
        ''')
        status_rows = cursor.fetchall()
        cursor.execute('''
            SELECT b.nome_bairro, COUNT(c.id_chamado) as qtd
            FROM chamado c JOIN bairro b ON c.id_bairro = b.id_bairro
            GROUP BY b.nome_bairro ORDER BY qtd DESC LIMIT 10
        ''')
        bairros_rows = cursor.fetchall()
    return {
        "atendidas_hoje": atendidas_hoje,
        "atendidas_semana": atendidas_semana,
        "status_labels": [r[0] for r in status_rows],
        "status_data": [r[1] for r in status_rows],
        "bairros_labels": [r[0] for r in bairros_rows],
        "bairros_data": [r[1] for r in bairros_rows],
    }


# ------------------------------------------------------------------
# Notificacoes
# ------------------------------------------------------------------

def listar_notificacoes_cidadao(uid):
    """Lista notificacoes nao arquivadas de um cidadao."""
    from types import SimpleNamespace
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT n.id_notificacao, n.mensagem, n.lida, n.arquivada, "
            "n.dt_envio, n.id_chamado "
            "FROM notificacao n "
            "WHERE n.arquivada = FALSE "
            "AND n.id_chamado IN (SELECT c.id_chamado FROM chamado c WHERE c.id_cidadao = %s) "
            "ORDER BY n.dt_envio DESC", [uid]
        )
        return [SimpleNamespace(id_notificacao=r[0], pk=r[0], mensagem=r[1],
                lida=r[2], arquivada=r[3], dt_envio=r[4], id_chamado_id=r[5])
                for r in cursor.fetchall()]


def listar_notificacoes_servidor(uid):
    """Lista notificacoes nao arquivadas de um servidor."""
    from types import SimpleNamespace
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT n.id_notificacao, n.mensagem, n.lida, n.arquivada, "
            "n.dt_envio, n.id_chamado "
            "FROM notificacao n "
            "WHERE n.arquivada = FALSE "
            "AND n.id_chamado IN ("
            "  SELECT DISTINCT hc.id_chamado FROM historico_chamado hc WHERE hc.id_servidor = %s"
            ") ORDER BY n.dt_envio DESC", [uid]
        )
        return [SimpleNamespace(id_notificacao=r[0], pk=r[0], mensagem=r[1],
                lida=r[2], arquivada=r[3], dt_envio=r[4], id_chamado_id=r[5])
                for r in cursor.fetchall()]


def marcar_notificacoes_lidas(nids):
    """Marca notificacoes como lidas."""
    if not nids:
        return
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE notificacao SET lida = TRUE WHERE id_notificacao = ANY(%s)", [nids]
        )


def excluir_notificacao(nid, uid_cidadao=None, uid_servidor=None):
    """Exclui notificacao com verificacao de permissao."""
    with connection.cursor() as cursor:
        if uid_cidadao:
            cursor.execute(
                "DELETE FROM notificacao WHERE id_notificacao = %s "
                "AND id_chamado IN (SELECT c.id_chamado FROM chamado c WHERE c.id_cidadao = %s)",
                [nid, uid_cidadao]
            )
        elif uid_servidor:
            cursor.execute(
                "DELETE FROM notificacao WHERE id_notificacao = %s "
                "AND id_chamado IN ("
                "  SELECT DISTINCT hc.id_chamado FROM historico_chamado hc WHERE hc.id_servidor = %s"
                ")", [nid, uid_servidor]
            )


# ------------------------------------------------------------------
# Painel do cidadao — lista resumida
# ------------------------------------------------------------------

def listar_chamados_painel(cidadao_pk):
    """Lista chamados do cidadao para o painel (versao resumida)."""
    from types import SimpleNamespace
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT c.id_chamado, c.num_protocolo, c.descricao, "
            "c.prioridade, c.dt_abertura, "
            "s.nome AS servico_nome, b.nome_bairro, "
            "ultimo.sigla AS sigla_status "
            "FROM chamado c "
            "LEFT JOIN servico s ON c.id_servico = s.id_servico "
            "LEFT JOIN bairro b ON c.id_bairro = b.id_bairro "
            + sql_lateral_ultimo_status(colunas="sc.sigla")
            + "WHERE c.id_cidadao = %s "
            "ORDER BY c.dt_abertura DESC", [cidadao_pk]
        )
        config = ConfiguracaoSemaforo.get_singleton()
        chamados = []
        for row in cursor.fetchall():
            cor = cor_semaforo(row[4], config.prazo_amarelo_dias, config.prazo_vermelho_dias)
            chamados.append(SimpleNamespace(
                id_chamado=row[0], num_protocolo=row[1], descricao=row[2],
                prioridade=row[3], dt_abertura=row[4],
                servico_nome=row[5], nome_bairro=row[6],
                sigla_status=row[7], cor_semaforo=cor,
                dias_em_aberto=(timezone.now().date() - row[4].date()).days,
            ))
        return chamados


# ------------------------------------------------------------------
# Senha — atualizacao
# ------------------------------------------------------------------

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


# ------------------------------------------------------------------
# Foto de perfil
# ------------------------------------------------------------------

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


# ------------------------------------------------------------------
# Chamado — acoes (avaliar, inserir foto)
# ------------------------------------------------------------------

def avaliar_chamado(chamado_id, nota, comentario):
    """Registra avaliacao de chamado."""
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE chamado SET nota_avaliacao = %s, "
            "comentario_avaliacao = %s, dt_avaliacao = %s "
            "WHERE id_chamado = %s",
            [nota, comentario, timezone.now(), chamado_id],
        )


def inserir_foto_chamado(chamado_id, url):
    """Insere foto em um chamado."""
    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO foto_chamado (id_chamado, url_foto, dt_upload) "
            "VALUES (%s, %s, %s)",
            [chamado_id, url, timezone.now()],
        )


# ------------------------------------------------------------------
# Gestao — categorias
# ------------------------------------------------------------------

def listar_categorias_todas():
    """Lista todas as categorias ativas."""
    from types import SimpleNamespace
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_categoria, nome, descricao, ativo "
            "FROM categoria_servico WHERE ativo = TRUE ORDER BY nome"
        )
        return [SimpleNamespace(id_categoria=r[0], pk=r[0], nome=r[1], descricao=r[2], ativo=r[3])
                for r in cursor.fetchall()]


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


# ------------------------------------------------------------------
# Gestao — servicos
# ------------------------------------------------------------------

def listar_servicos_com_categoria():
    """Lista servicos ativos com nome da categoria."""
    from types import SimpleNamespace
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


# ------------------------------------------------------------------
# Gestao — bairros
# ------------------------------------------------------------------

def listar_bairros_todos():
    """Lista todos os bairros (sem filtro de ativo)."""
    from types import SimpleNamespace
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_bairro, nome_bairro, cep, regiao, ativo "
            "FROM bairro ORDER BY nome_bairro"
        )
        return [SimpleNamespace(id_bairro=r[0], pk=r[0], nome_bairro=r[1],
                cep=r[2], regiao=r[3], ativo=r[4])
                for r in cursor.fetchall()]


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


def _buscar_secretaria_id():
    """Retorna o ID da primeira secretaria."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT id_secretaria FROM secretaria LIMIT 1")
        row = cursor.fetchone()
    return row[0] if row else None


# ------------------------------------------------------------------
# Gestao — colaboradores
# ------------------------------------------------------------------

def listar_colaboradores():
    """Lista servidores com perfil COL."""
    from types import SimpleNamespace
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


# ------------------------------------------------------------------
# Gestao — banners
# ------------------------------------------------------------------

def listar_banners_todos():
    """Lista todos os banners ordenados."""
    from types import SimpleNamespace
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_banner, titulo, descricao, url_imagem, link, "
            "ordem, ativo, dt_criacao "
            "FROM banner_publicacao ORDER BY ordem, dt_criacao DESC"
        )
        return [SimpleNamespace(id_banner=r[0], pk=r[0], titulo=r[1], descricao=r[2],
                url_imagem=r[3], link=r[4], ordem=r[5], ativo=r[6], dt_criacao=r[7])
                for r in cursor.fetchall()]


def buscar_banner(pk):
    """Busca banner por ID."""
    from types import SimpleNamespace
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_banner, titulo, descricao, url_imagem, link, "
            "ordem, ativo, dt_criacao "
            "FROM banner_publicacao WHERE id_banner = %s", [pk]
        )
        row = cursor.fetchone()
    if not row:
        return None
    return SimpleNamespace(id_banner=row[0], pk=row[0], titulo=row[1], descricao=row[2],
                           url_imagem=row[3], link=row[4], ordem=row[5], ativo=row[6], dt_criacao=row[7])


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


# ------------------------------------------------------------------
# Gestao — cidadao
# ------------------------------------------------------------------

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


# ------------------------------------------------------------------
# Gestao — chamado (cancelar com status CA)
# ------------------------------------------------------------------

def buscar_status_ca():
    """Retorna o ID do status Cancelado (CA)."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT id_status FROM status_chamado WHERE sigla = 'CA'")
        row = cursor.fetchone()
    return row[0] if row else None


def cancelar_chamado(chamado_id, motivo):
    """Cancela chamado: insere historico CA + atualiza resolucao."""
    from django.db import transaction
    ca_id = buscar_status_ca()
    if not ca_id:
        raise ValueError("Status CA nao encontrado")
    with transaction.atomic(), connection.cursor() as cursor:
        criar_historico(chamado_id, ca_id, observacao=motivo)
        cursor.execute(
            "UPDATE chamado SET resolucao = %s WHERE id_chamado = %s",
            [motivo, chamado_id],
        )


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
