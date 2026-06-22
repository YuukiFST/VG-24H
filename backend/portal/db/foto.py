"""portal.db.foto — extraido de db.py (camada SQL pura).
Veja portal/db/__init__.py para a fachada publica."""


from django.db import connection
from django.utils import timezone

from portal.types import (
    FotoDTO,
)


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

def inserir_foto_chamado(chamado_id, url):
    """Insere foto em um chamado."""
    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO foto_chamado (id_chamado, url_foto, dt_upload) "
            "VALUES (%s, %s, %s)",
            [chamado_id, url, timezone.now()],
        )
