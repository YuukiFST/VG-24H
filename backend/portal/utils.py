import os
import uuid

from django.conf import settings
from django.core.files.storage import default_storage
from django.db.models import Max
from django.utils import timezone

from portal.models import Chamado


def proximo_protocolo():
    y = timezone.now().year
    prefix = str(y)
    ultimo = Chamado.objects.filter(num_protocolo__startswith=prefix).aggregate(
        m=Max("num_protocolo")
    )["m"]
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

