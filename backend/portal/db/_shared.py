"""portal.db._shared — modulo dos helpers que eu reaproveito em todo lado.
Saiu do db.py original. A fachada publica ta em portal/db/__init__.py."""


# SimpleNamespace eu uso pra transformar tupla do banco em objeto com .atributo
# (assim o template consegue fazer obj.url_foto em vez de obj[1]).
from types import SimpleNamespace

# connection eh a conexao do Django, dela eu pego o cursor pra rodar SQL na mao.
from django.db import connection


def fetch_all(sql, params=None, *, fields, pk_alias=True):
    """Roda um SELECT e transforma cada linha num SimpleNamespace.

    Anotacao: eu cansei de repetir o `with connection.cursor()` + montar
    objeto em todo lugar, entao centralizei aqui. O `fields` eh a lista com
    o nome das colunas NA MESMA ORDEM do SELECT. Se `pk_alias` for True, eu
    coloco tambem um `.pk` apontando pra primeira coluna (o id da tabela),
    porque os templates do Django esperam esse `.pk`.
    """
    # abro o cursor, executo a query e ja pego todas as linhas de uma vez.
    # params or [] eh pra nunca passar None (senao o execute reclama).
    with connection.cursor() as cursor:
        cursor.execute(sql, params or [])
        rows = cursor.fetchall()
    resultado = []
    # pra cada linha (tupla) eu caso o nome do campo com o valor usando zip.
    # strict=True garante que fields e a linha tem o mesmo tamanho, senao estoura
    # (bom pra eu pegar erro cedo se eu errar a contagem de colunas).
    for r in rows:
        ns = SimpleNamespace(**dict(zip(fields, r, strict=True)))
        # aqui eu jogo o id (primeira coluna) tambem em .pk pro template.
        if pk_alias:
            ns.pk = r[0]
        resultado.append(ns)
    return resultado


def fetch_one(sql, params=None, *, fields, pk_alias=True):
    """Igual o fetch_all mas pra UMA linha so. Devolve None se nao achar nada."""
    with connection.cursor() as cursor:
        cursor.execute(sql, params or [])
        # fetchone pega so o primeiro registro (ou None se a query nao retornou nada).
        row = cursor.fetchone()
    # se nao veio nada do banco, eu devolvo None e nem tento montar o objeto.
    if row is None:
        return None
    ns = SimpleNamespace(**dict(zip(fields, row, strict=True)))
    if pk_alias:
        ns.pk = row[0]
    return ns


# lista branca das tabelas que eu deixo passar no SQL dinamico.
# expandida para incluir as tabelas de catalogo (categoria_servico, servico, bairro)
# alem das de usuario (cidadao, servidor). uso frozenset porque eh imutavel.
TABELAS_VALIDAS = frozenset({
    "cidadao", "servidor",
    "categoria_servico", "servico", "bairro",
})

def _validar_tabela(tabela):
    # IMPORTANTE: isso aqui eh minha defesa contra SQL injection. Em alguns
    # UPDATEs eu coloco o nome da tabela direto na string (f-string), e nome de
    # tabela NAO da pra passar como %s. Entao antes eu confirmo que a tabela ta
    # na lista branca; se nao tiver, estoura erro e nem chega no banco.
    if tabela not in TABELAS_VALIDAS:
        raise ValueError(f"Tabela invalida: {tabela!r}. Permitidas: {sorted(TABELAS_VALIDAS)}")

# mesma ideia da lista branca, mas pra quais colunas eu aceito no JOIN LATERAL.
# so esses dois conjuntos exatos de colunas sao permitidos.
COLUNAS_LATERAL_VALIDAS = frozenset({
    "sc.sigla, sc.descricao, sc.id_status",
    "sc.sigla",
})

def sql_lateral_ultimo_status(colunas="sc.sigla, sc.descricao, sc.id_status", alias="c"):
    """Devolve um pedaco de SQL (JOIN LATERAL) que pega o ULTIMO status do chamado.

    Eu uso isso em varias views que listam chamados com o status atual. Como
    o historico guarda varios status por chamado, esse lateral pega so o mais
    recente (ORDER BY dt_alteracao DESC LIMIT 1).

    CUIDADO: aqui colunas e alias entram na string via f-string, entao NUNCA
    posso passar dado vindo do usuario. So literais do meu proprio codigo.
    Por isso valido os dois logo abaixo antes de montar a query.
    """
    # so deixo passar as combinacoes de colunas que estao na lista branca.
    if colunas not in COLUNAS_LATERAL_VALIDAS:
        raise ValueError(f"Colunas invalidas: {colunas!r}")
    # o alias tem que ser exatamente "c", qualquer outra coisa eu trato como
    # tentativa de injection e barro na hora.
    if alias != "c":
        raise ValueError(f"Injection detection: alias inesperado {alias!r}")
    # aqui eu monto o fragmento na mao. O subselect pega o status mais recente
    # do historico_chamado, junta com status_chamado pra pegar a sigla/descricao,
    # casa pelo id_chamado do chamado de fora (alias c) e limita a 1 linha.
    return (
        "JOIN LATERAL ("
        f"  SELECT {colunas} FROM historico_chamado hc "
        "  JOIN status_chamado sc ON hc.id_status = sc.id_status "
        f"  WHERE hc.id_chamado = {alias}.id_chamado "
        "  ORDER BY hc.dt_alteracao DESC LIMIT 1"
        ") ultimo ON TRUE "
    )

def _buscar_secretaria_id():
    """Me devolve o id da primeira secretaria que tiver no banco."""
    with connection.cursor() as cursor:
        # LIMIT 1 porque eu so quero uma; o sistema hoje so tem uma secretaria mesmo.
        cursor.execute("SELECT id_secretaria FROM secretaria LIMIT 1")
        row = cursor.fetchone()
    # se achou retorna o id, se nao achou retorna None pra nao quebrar.
    return row[0] if row else None
