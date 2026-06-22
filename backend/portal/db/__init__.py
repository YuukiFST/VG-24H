"""portal.db — camada de acesso a dados SQL pura (pacote).

Decomposto de um modulo unico (db.py, ~1600 linhas) em submodulos por
dominio. A fachada re-exporta todos os nomes publicos, entao os callers
continuam usando `from portal import db` e `db.<funcao>(...)` sem mudanca.
"""

from portal.db._shared import *  # noqa: F401,F403
from portal.db._shared import (  # noqa: F401
    COLUNAS_LATERAL_VALIDAS,
    TABELAS_VALIDAS,
    _validar_tabela,
    sql_lateral_ultimo_status,
)
from portal.db.catalogo import *  # noqa: F401,F403
from portal.db.chamado import *  # noqa: F401,F403
from portal.db.cidadao import *  # noqa: F401,F403
from portal.db.config import *  # noqa: F401,F403
from portal.db.foto import *  # noqa: F401,F403
from portal.db.historico import *  # noqa: F401,F403
from portal.db.notificacao import *  # noqa: F401,F403
from portal.db.pagination import *  # noqa: F401,F403
from portal.db.pagination import _PageObj  # noqa: F401
from portal.db.senha import *  # noqa: F401,F403
from portal.db.servidor import *  # noqa: F401,F403
from portal.db.stats import *  # noqa: F401,F403
