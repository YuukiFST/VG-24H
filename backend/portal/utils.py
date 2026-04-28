import os
import uuid

from django.conf import settings
from django.core.files.storage import default_storage
from django.db import connection
from django.utils import timezone


def proximo_protocolo():
    """Gera o próximo número de protocolo no formato ANO + sequencial."""
    y = timezone.now().year
    prefix = str(y)
    # SQL puro: busca o maior protocolo do ano atual
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT MAX(num_protocolo) FROM chamado "
            "WHERE num_protocolo LIKE %s",
            [f"{prefix}%"],
        )
        row = cursor.fetchone()
        ultimo = row[0] if row else None
    if not ultimo:
        n = 1
    else:
        try:
            n = int(ultimo[len(prefix):]) + 1
        except ValueError:
            n = 1
    return f"{prefix}{n:06d}"


def salvar_foto_upload(arquivo, request=None):
    """Salva foto via Cloudinary (se configurado) ou filesystem local.

    >>> url = salvar_foto_upload(uploaded_file, request=request)
    """
    if not arquivo:
        raise ValueError("Foto obrigatória.")
    cu = os.environ.get("CLOUDINARY_URL")
    if cu:
        import cloudinary
        import cloudinary.uploader

        cloudinary.config(cloudinary_url=cu)
        r = cloudinary.uploader.upload(
            arquivo, folder="vg_portal", resource_type="image"
        )
        return r["secure_url"]
    ext = os.path.splitext(arquivo.name)[1][:12] or ".jpg"
    nome = f"chamados/{uuid.uuid4().hex}{ext}"
    caminho = default_storage.save(nome, arquivo)
    if request:
        return request.build_absolute_uri(f"{settings.MEDIA_URL}{caminho}")
    return f"{settings.MEDIA_URL}{caminho}"
