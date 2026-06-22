"""portal.db._shared — extraido de db.py (camada SQL pura).
Veja portal/db/__init__.py para a fachada publica."""


from django.db import connection

TABELAS_VALIDAS = frozenset({"cidadao", "servidor"})

def _validar_tabela(tabela):
    if tabela not in TABELAS_VALIDAS:
        raise ValueError(f"Tabela invalida: {tabela!r}. Permitidas: {sorted(TABELAS_VALIDAS)}")

COLUNAS_LATERAL_VALIDAS = frozenset({
    "sc.sigla, sc.descricao, sc.id_status",
    "sc.sigla",
})

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

def _buscar_secretaria_id():
    """Retorna o ID da primeira secretaria."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT id_secretaria FROM secretaria LIMIT 1")
        row = cursor.fetchone()
    return row[0] if row else None
