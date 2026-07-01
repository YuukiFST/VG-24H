"""portal.db.stats — extraido de db.py (camada SQL pura).
Veja portal/db/__init__.py para a fachada publica."""


from django.db import connection
from django.utils import timezone

# _validar_tabela checa se o nome da tabela eh permitido (uso quando preciso interpolar nome de tabela na query)
from portal.db._shared import _validar_tabela

# As 3 contagens do semaforo (no_prazo, atencao, critico) sao identicas nas duas
# funcoes de stats abaixo, entao deixo a expressao numa constante so. Cada CASE
# usa um %s pro "now" (4 no total: amarelo, amarelo+vermelho, vermelho). A
# constante termina sem virgula/espaco final pra cada call site emendar do seu
# jeito (um segue com " FROM", o outro com ", COUNT(*)").
_SEMAFORO_CASE_COLUNAS = (
    "  COALESCE(SUM(CASE WHEN (%s - c.dt_abertura) < make_interval(days := cfg.prazo_amarelo_dias) THEN 1 ELSE 0 END), 0), "
    "  COALESCE(SUM(CASE WHEN (%s - c.dt_abertura) >= make_interval(days := cfg.prazo_amarelo_dias) "
    "    AND (%s - c.dt_abertura) < make_interval(days := cfg.prazo_vermelho_dias) THEN 1 ELSE 0 END), 0), "
    "  COALESCE(SUM(CASE WHEN (%s - c.dt_abertura) >= make_interval(days := cfg.prazo_vermelho_dias) THEN 1 ELSE 0 END), 0)"
)


def cor_semaforo(dt_abertura, prazo_amarelo_dias, prazo_vermelho_dias):
    """Classifica a urgencia do chamado com base nos prazos do servico.

    Retorna 'verde' (dentro do prazo), 'amarelo' (atencao) ou 'vermelho' (critico).
    Funcao pura, sem efeitos colaterais.
    """
    # calculo quantos dias o chamado ta aberto (agora menos a abertura)
    dias = (timezone.now() - dt_abertura).days
    # passou do prazo vermelho -> critico
    if dias >= prazo_vermelho_dias:
        return "vermelho"
    # passou do amarelo (mas nao do vermelho) -> atencao
    if dias >= prazo_amarelo_dias:
        return "amarelo"
    # ainda dentro do prazo -> verde
    return "verde"

def calcular_stats_semaforo(cidadao_id=None):
    """Calcula estatisticas do semaforo para chamados em aberto.

    Usa os prazos globais da configuracao_semaforo (CROSS JOIN com singleton).
    Retorna dict com tres chaves: no_prazo, atencao, critico.
    Se cidadao_id for informado, filtra apenas os chamados desse cidadao.
    """
    # monto o filtro opcional: se veio cidadao_id eu adiciono um AND e guardo o param
    where = ""
    where_params = []
    if cidadao_id:
        where = "AND c.id_cidadao = %s"
        where_params = [cidadao_id]

    now = timezone.now()
    # uso o "now" 4 vezes (um pra cada CASE) e no fim os params do filtro, na ordem que aparecem na query
    params = [now, now, now, now] + where_params

    sql = (
        "SELECT "
        # as 3 contagens do semaforo (no_prazo, atencao, critico); ver _SEMAFORO_CASE_COLUNAS
        + _SEMAFORO_CASE_COLUNAS +
        " "
        "FROM chamado c "
        # CROSS JOIN com a config (que eh linha unica) pra ter os prazos disponiveis em cada linha
        "CROSS JOIN configuracao_semaforo cfg "
        # WHERE TRUE eh so um truque pra eu poder concatenar o "AND ..." opcional sem quebrar a sintaxe
        "WHERE TRUE " + where
    )

    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        row = cursor.fetchone()
    # a unica linha tem as 3 contagens nas posicoes 0,1,2
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
        # agrupado por servico, entao trago id e nome do servico
        "  s.id_servico, s.nome, "
        # mesmas 3 contagens do semaforo de antes (no prazo, atencao, critico)
        + _SEMAFORO_CASE_COLUNAS +
        ", "
        # total geral de chamados do servico
        "  COUNT(*) "
        "FROM chamado c "
        # CROSS JOIN com a config pra ter os prazos
        "CROSS JOIN configuracao_semaforo cfg "
        # JOIN no servico pra eu poder agrupar e mostrar o nome
        "JOIN servico s ON c.id_servico = s.id_servico "
        # agrupo por servico (uma linha por servico)
        "GROUP BY s.id_servico, s.nome "
        "ORDER BY s.nome"
    )
    with connection.cursor() as cursor:
        # passo o "now" 4 vezes igual antes, um pra cada CASE
        cursor.execute(sql, [now, now, now, now])
        rows = cursor.fetchall()
    # transformo cada linha (um servico) num dict
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

def existe_email_ou_cpf(tabela, email, cpf):
    """Verifica se email ou CPF ja existem em uma tabela de usuarios."""
    # valido o nome da tabela ANTES de interpolar (so esse vem de fora como string), senao seria SQL injection
    _validar_tabela(tabela)
    with connection.cursor() as cursor:
        # EXISTS retorna True/False; uso OR pra dar True se bater o email OU o cpf. Os valores ainda vao como %s
        cursor.execute(
            f"SELECT EXISTS("
            f"  SELECT 1 FROM {tabela} WHERE LOWER(email) = %s"
            f") OR EXISTS("
            f"  SELECT 1 FROM {tabela} WHERE cpf = %s"
            f")",
            [email.lower(), cpf],
        )
        # o resultado eh um bool na primeira coluna
        return cursor.fetchone()[0]

def existe_nome(tabela, campo, nome, *, extra_where="", extra_params=None):
    """Verifica se um nome ja existe em uma tabela (case-insensitive).

    Usado para validar unicidade de nome em CategoriaServico, Servico e Bairro
    ANTES do INSERT/UPDATE, evitando IntegrityError e mostrando mensagem amigavel.

    Args:
        tabela: nome da tabela (precisa estar na TABELAS_VALIDAS).
        campo: nome da coluna a verificar (ex: 'nome', 'nome_bairro').
        nome: valor a conferir (ja normalizado em lowercase pelo caller).
        extra_where: clausula WHERE adicional (ex: 'AND id_categoria = %s').
        extra_params: parametros correspondentes ao extra_where.
    """
    # defesa contra SQL injection: so tabelas na lista branca passam
    _validar_tabela(tabela)
    params = [nome.lower()]
    if extra_params:
        params.extend(extra_params)
    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT EXISTS("
            f"  SELECT 1 FROM {tabela} WHERE LOWER({campo}) = %s"
            f"  {extra_where}"
            f")",
            params,
        )
        return cursor.fetchone()[0]

def buscar_stats_publicas():
    """Retorna estatisticas da pagina inicial."""
    with connection.cursor() as cursor:
        # conto chamados resolvidos: aqui uso uma subquery no WHERE que pega o ultimo status de cada chamado
        cursor.execute(
            "SELECT COUNT(*) FROM chamado c WHERE ("
            # subquery: o ultimo historico (ORDER DESC LIMIT 1) me da a sigla do status atual
            "  SELECT sc.sigla FROM historico_chamado hc "
            "  JOIN status_chamado sc ON hc.id_status = sc.id_status "
            "  WHERE hc.id_chamado = c.id_chamado "
            "  ORDER BY hc.dt_alteracao DESC LIMIT 1"
            # e so conto se esse status atual for 'CO' (concluido)
            ") = 'CO'"
        )
        total_resolvidos = cursor.fetchone()[0]
        # conto bairros ativos
        cursor.execute("SELECT COUNT(*) FROM bairro WHERE ativo = TRUE")
        total_bairros = cursor.fetchone()[0]
        # conto servicos ativos
        cursor.execute("SELECT COUNT(*) FROM servico WHERE ativo = TRUE")
        total_servicos = cursor.fetchone()[0]
    return {"total_resolvidos": total_resolvidos, "total_bairros": total_bairros, "total_servicos": total_servicos}

def buscar_stats_dashboard():
    """Retorna metricas do dashboard da equipe."""
    from datetime import timedelta
    agora = timezone.now()
    hoje = agora.date()
    # inicio da semana = 7 dias atras, pra contar o que foi atendido na ultima semana
    inicio_semana = hoje - timedelta(days=7)
    with connection.cursor() as cursor:
        # conto quantos foram concluidos HOJE: mesmo truque do ultimo status = 'CO' e dt_conclusao do dia
        cursor.execute('''
            SELECT COUNT(*) FROM chamado c
            WHERE (
                SELECT sc.sigla FROM historico_chamado hc
                JOIN status_chamado sc ON hc.id_status = sc.id_status
                WHERE hc.id_chamado = c.id_chamado
                ORDER BY hc.dt_alteracao DESC LIMIT 1
            ) = 'CO' AND c.dt_conclusao::date = %s
        ''', [hoje])
        # se vier None caio pro 0
        atendidas_hoje = cursor.fetchone()[0] or 0
        # mesma ideia, mas concluidos de uma semana pra ca (>= inicio_semana)
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
        # aqui agrupo os chamados pela descricao do status ATUAL pra montar um grafico de status
        cursor.execute('''
            SELECT sc.descricao, COUNT(c.id_chamado)
            FROM chamado c
            JOIN historico_chamado hc ON hc.id_chamado = c.id_chamado
            JOIN status_chamado sc ON sc.id_status = hc.id_status
            -- so considero a linha de historico que eh a mais recente do chamado (o status atual)
            WHERE hc.id_historico_chamado = (
                SELECT id_historico_chamado FROM historico_chamado
                WHERE id_chamado = c.id_chamado ORDER BY dt_alteracao DESC LIMIT 1
            ) GROUP BY sc.descricao
        ''')
        status_rows = cursor.fetchall()
        # top 10 bairros com mais chamados: junto com bairro, agrupo e ordeno pela quantidade
        cursor.execute('''
            SELECT b.nome_bairro, COUNT(c.id_chamado) as qtd
            FROM chamado c JOIN bairro b ON c.id_bairro = b.id_bairro
            GROUP BY b.nome_bairro ORDER BY qtd DESC LIMIT 10
        ''')
        bairros_rows = cursor.fetchall()
    # separo cada lista em labels (nomes) e data (numeros) pro front montar os graficos
    return {
        "atendidas_hoje": atendidas_hoje,
        "atendidas_semana": atendidas_semana,
        "status_labels": [r[0] for r in status_rows],
        "status_data": [r[1] for r in status_rows],
        "bairros_labels": [r[0] for r in bairros_rows],
        "bairros_data": [r[1] for r in bairros_rows],
    }
