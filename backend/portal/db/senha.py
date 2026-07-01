"""portal.db.senha — parte do db.py que cuida de senha (SQL puro).
A fachada publica fica em portal/db/__init__.py."""


# connection pro SQL na mao.
from django.db import connection

# _validar_tabela eh meu guardiao contra injection no nome da tabela.
# uso ele em toda funcao que coloca a tabela direto na string.
from portal.db._shared import _validar_tabela


def atualizar_senha_usuario(tabela, pk, nova_senha):
    """Troca a senha do usuario (cidadao ou servidor) e zera a flag temporaria.

    Detalhe: `nova_senha` chega em texto puro e eu gero o hash bcrypt aqui
    dentro com o make_password (nunca salvo senha crua no banco!). Sempre que
    a pessoa define uma senha propria eu limpo o senha_temporaria (= NULL),
    senao no proximo login o sistema ia mandar ela trocar a senha de novo.
    """
    # primeiro valido a tabela porque ela vai entrar na f-string da query.
    _validar_tabela(tabela)
    # importo o make_password aqui dentro (import tardio) so quando precisa.
    from django.contrib.auth.hashers import make_password
    # escolho a coluna de id certa dependendo se eh cidadao ou servidor.
    id_col = "id_cidadao" if tabela == "cidadao" else "id_servidor"
    with connection.cursor() as cursor:
        # tabela e id_col entram via f-string (ja validados), mas o valor da
        # senha e o pk vao parametrizados (%s) que eh a parte sensivel.
        cursor.execute(
            f"UPDATE {tabela} SET senha_hash = %s, senha_temporaria = NULL "  # noqa: S608 (tabela/id_col ja validados; valores parametrizados)
            f"WHERE {id_col} = %s",
            [make_password(nova_senha), pk],
        )

def buscar_cidadao_para_reset(email):
    """Acha um cidadao ATIVO pelo email, pra fluxo de reset de senha."""
    with connection.cursor() as cursor:
        # uso LOWER no email pra comparacao nao depender de maiuscula/minuscula
        # (entao quem cadastrou aqui ja precisa mandar o email em minusculo).
        # ativo = TRUE pra nao deixar resetar senha de conta desativada.
        cursor.execute(
            "SELECT id_cidadao, email FROM cidadao "
            "WHERE LOWER(email) = %s AND ativo = TRUE", [email]
        )
        return cursor.fetchone()
