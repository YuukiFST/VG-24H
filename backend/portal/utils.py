import os
import uuid

from django.conf import settings
from django.core.files.storage import default_storage
from django.db import connection
from django.utils import timezone


def proximo_protocolo():
    """
    Gera o proximo numero de protocolo no formato ANO + sequencial (6 digitos).
    Ex: 2026000001 (ano 2026, sequencial 00001).

    [!] Usa SQL puro (MAX(num_protocolo)) para evitar condicao de corrida
        em requisicoes simultaneas — o banco garante a atomicidade.
    """
    y = timezone.now().year
    prefix = str(y)
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT MAX(num_protocolo) FROM chamado "
            "WHERE num_protocolo LIKE %s",
            [f"{prefix}%"],
        )
        row = cursor.fetchone()
        ultimo = row[0] if row else None
    if not ultimo:
        n = 1                                         # Primeiro protocolo do ano
    else:
        try:
            n = int(ultimo[len(prefix):]) + 1          # Incrementa o sequencial
        except ValueError:
            n = 1
    return f"{prefix}{n:06d}"                          # Ex: 2026000001


def salvar_foto_upload(arquivo, request=None):
    """Salva foto via Cloudinary (se configurado) ou filesystem local.

    Fluxo:
    1. Se CLOUDINARY_URL estiver configurado → upload para nuvem
    2. Senao → salva em MEDIA_ROOT/chamados/{uuid}.{ext}
    """
    if not arquivo:
        raise ValueError("Foto obrigatoria.")
    cu = os.environ.get("CLOUDINARY_URL")
    if cu:
        # Upload para Cloudinary (nuvem)
        import cloudinary
        import cloudinary.uploader

        cloudinary.config(cloudinary_url=cu)
        r = cloudinary.uploader.upload(
            arquivo, folder="vg_portal", resource_type="image"
        )
        return r["secure_url"]
    # Fallback: salva localmente com nome unico (UUID)
    ext = os.path.splitext(arquivo.name)[1][:12] or ".jpg"
    nome = f"chamados/{uuid.uuid4().hex}{ext}"
    caminho = default_storage.save(nome, arquivo)
    if request:
        return request.build_absolute_uri(f"{settings.MEDIA_URL}{caminho}")
    return f"{settings.MEDIA_URL}{caminho}"
