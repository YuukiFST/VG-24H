"""portal.db.stats — extraido de db.py (camada SQL pura).
Veja portal/db/__init__.py para a fachada publica."""


from django.db import connection
from django.utils import timezone

from portal.db._shared import _validar_tabela


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
