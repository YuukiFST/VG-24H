"""
utils.py — Funcoes utilitarias do Portal VG 24H

Este modulo contem funcoes auxiliares usadas por diversas views:
- escape_like: escapar caracteres especiais de LIKE/ILIKE
- proximo_protocolo: gerar numero de protocolo atomico
- salvar_foto_upload: salvar foto via Cloudinary ou filesystem
"""

import os
import uuid

from django.conf import settings
from django.core.files.storage import default_storage
from django.db import connection
from django.utils import timezone


def escape_like(valor):
    """Escapa caracteres especiais de LIKE/ILIKE no PostgreSQL.

    Os caracteres %, _ e \ sao especiais em patterns LIKE. Esta funcao
    os escapa com barra invertida para que sejam tratados como literais.
    Deve ser chamada ANTES de envolver o valor com %...% para busca parcial.
    Exemplo: escape_like("100%") retorna "100\\%".
    """
    return valor.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def proximo_protocolo():
    """Gera o proximo numero de protocolo no formato ANO + sequencial (6 digitos).

    Exemplo: 2026000001 (ano 2026, sequencial 000001).

    A operacao eh atomica graças ao INSERT ... ON CONFLICT DO UPDATE RETURNING.
    Se duas requisicoes concorrentes chamarem esta funcao, cada uma recebe um
    numero unico. O banco serializa o acesso via row-level lock na tabela
    protocolo_seq (criada pelo script 01_schema.sql).
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

    Se a variavel de ambiente CLOUDINARY_URL estiver definida, faz upload
    para o Cloudinary e retorna a URL segura (https). Caso contrario,
    salva localmente em MEDIA_ROOT/chamados/{uuid}.{ext} e retorna a URL.

    Levanta ValueError se nenhum arquivo for fornecido.
    Levanta ImportError se Cloudinary estiver configurado mas nao instalado.
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
                "Cloudinary nao instalado. Execute: pip install cloudinary"
            )
        cloudinary.config(cloudinary_url=cu)
        r = cloudinary.uploader.upload(
            arquivo, folder="vg_portal", resource_type="image"
        )
        return r["secure_url"]

    # Fallback: salva localmente com nome unico (UUID).
    ext_raw = os.path.splitext(arquivo.name)[1].lower()
    ext = ext_raw if ext_raw in (".jpg", ".jpeg", ".png", ".gif", ".webp") else ".jpg"
    nome = f"chamados/{uuid.uuid4().hex}{ext}"
    caminho = default_storage.save(nome, arquivo)
    if request:
        return request.build_absolute_uri(f"{settings.MEDIA_URL}{caminho}")
    return f"{settings.MEDIA_URL}{caminho}"
