"""portal.db — minha camada de acesso a dados em SQL puro (pacote).

Anotacao pra mim: eu tinha um db.py gigante (~1600 linhas) e quebrei ele
em varios submodulos separados por dominio (chamado, cidadao, foto, etc).
Esse __init__ aqui eh a "fachada": ele re-exporta tudo que eh publico, entao
quem importa continua fazendo `from portal import db` e `db.<funcao>(...)`
igual antes, sem precisar mudar nada nas views. Foi so pra organizar.
"""

# aqui eu puxo TODO o conteudo publico de cada submodulo com import *
# (o noqa eh so pra calar o flake8 que reclama de import * e nome nao usado).
# primeiro o _shared, que tem os helpers que os outros modulos usam.
from portal.db._shared import *  # noqa: F401,F403

# esses nomes do _shared comecam com _ ou nao entram no import *, entao
# eu importo eles na mao pra deixar acessivel pela fachada tambem.
from portal.db._shared import (  # noqa: F401
    COLUNAS_LATERAL_VALIDAS,
    TABELAS_VALIDAS,
    _validar_tabela,
    sql_lateral_ultimo_status,
)

# agora cada submodulo de dominio, um por um. ordem alfabetica so pra ficar limpo.
from portal.db.catalogo import *  # noqa: F401,F403
from portal.db.chamado import *  # noqa: F401,F403
from portal.db.cidadao import *  # noqa: F401,F403
from portal.db.config import *  # noqa: F401,F403
from portal.db.foto import *  # noqa: F401,F403
from portal.db.historico import *  # noqa: F401,F403
from portal.db.notificacao import *  # noqa: F401,F403
from portal.db.pagination import *  # noqa: F401,F403

# o _PageObj comeca com _ entao o import * nao pega, importo na mao tambem.
from portal.db.pagination import _PageObj  # noqa: F401
from portal.db.senha import *  # noqa: F401,F403
from portal.db.servidor import *  # noqa: F401,F403
from portal.db.stats import *  # noqa: F401,F403
