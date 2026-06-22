"""portal.db.foto — parte do db.py que mexe com as fotos dos chamados (SQL puro).
A fachada publica fica em portal/db/__init__.py."""


# connection pro SQL na mao e timezone pra pegar a hora certa do upload.
from django.db import connection
from django.utils import timezone

# FotoDTO eh o objeto que eu uso pra carregar a foto pros templates,
# em vez de devolver tupla crua do banco.
from portal.types import (
    FotoDTO,
)


def buscar_fotos(chamado_pk):
    """Pega as fotos de um chamado, ordenadas pela data de upload.

    Lembrete: a foto em si nao fica no banco, o que eu guardo eh a URL dela
    (pode ser do Cloudinary ou do filesystem local). O banco so tem o link.
    """
    with connection.cursor() as cursor:
        # filtro pelas fotos do chamado (id_chamado = %s, parametrizado) e
        # ordeno por data pra mostrar na ordem que foram enviadas.
        cursor.execute(
            "SELECT id_foto, url_foto, dt_upload "
            "FROM foto_chamado WHERE id_chamado = %s "
            "ORDER BY dt_upload",
            [chamado_pk],
        )
        # transformo cada linha num FotoDTO. Repito o id em id_foto e pk porque
        # o template usa .pk, igual a convencao do resto do projeto.
        return [
            FotoDTO(id_foto=r[0], pk=r[0], url_foto=r[1], dt_upload=r[2])
            for r in cursor.fetchall()
        ]

def inserir_foto_chamado(chamado_id, url):
    """Grava uma foto nova (a URL dela) num chamado."""
    with connection.cursor() as cursor:
        # uso timezone.now() pra carimbar a hora do upload na hora de inserir.
        # tudo via %s pra ficar parametrizado e seguro.
        cursor.execute(
            "INSERT INTO foto_chamado (id_chamado, url_foto, dt_upload) "
            "VALUES (%s, %s, %s)",
            [chamado_id, url, timezone.now()],
        )
