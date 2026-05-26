import os
import uuid

from django.conf import settings
from django.core.files.storage import default_storage
from django.db import connection
from django.utils import timezone


def escape_like(valor):
    """Escapa caracteres especiais de LIKE/ILIKE (%  _  \\) em input do usuario.

    Deve ser chamado ANTES de envolver o valor com %...% para busca parcial.
    Ex: escape_like("100%") → "100\\%"
    """
    return valor.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def proximo_protocolo():
    """
    Gera o proximo numero de protocolo no formato ANO + sequencial (6 digitos).
    Ex: 2026000001 (ano 2026, sequencial 00001).

    [!] INSERT ... ON CONFLICT DO UPDATE RETURNING garante atomicidade.
        Se duas requisicoes concorrentes chamam esta funcao, cada uma
        recebe um numero unico — o banco serializa o LOCK na linha do ano.
        A tabela protocolo_seq e criada pelo schema (01_schema.sql).
    """
    y = timezone.now().year
    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO protocolo_seq (ano, ultimo_numero) VALUES (%s, 1) "
            "ON CONFLICT (ano) DO UPDATE SET ultimo_numero = protocolo_seq.ultimo_numero + 1 "
            "RETURNING ultimo_numero",
            [y],
        )
        row = cursor.fetchone()
        if not row:
            raise RuntimeError("protocolo_seq INSERT/RETURNING nao retornou linha")
        n = row[0]
    return f"{y}{n:06d}"


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
        try:
            import cloudinary
            import cloudinary.uploader
        except ImportError:
            raise ImportError(
                "Cloudinary não instalado. Execute: pip install cloudinary"
            )
        cloudinary.config(cloudinary_url=cu)
        r = cloudinary.uploader.upload(
            arquivo, folder="vg_portal", resource_type="image"
        )
        return r["secure_url"]
    # Fallback: salva localmente com nome unico (UUID)
    ext_raw = os.path.splitext(arquivo.name)[1].lower()
    ext = ext_raw if ext_raw in (".jpg", ".jpeg", ".png", ".gif", ".webp") else ".jpg"
    nome = f"chamados/{uuid.uuid4().hex}{ext}"
    caminho = default_storage.save(nome, arquivo)
    if request:
        return request.build_absolute_uri(f"{settings.MEDIA_URL}{caminho}")
    return f"{settings.MEDIA_URL}{caminho}"