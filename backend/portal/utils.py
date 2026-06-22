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
from django.utils.timezone import is_naive, make_aware


def escape_like(valor):
    """Escapa caracteres especiais de LIKE/ILIKE no PostgreSQL.

    Os caracteres %, _ e \\ sao especiais em patterns LIKE. Esta funcao
    os escapa com barra invertida para que sejam tratados como literais.
    Deve ser chamada ANTES de envolver o valor com %...% para busca parcial.
    Exemplo: escape_like("100%") retorna "100\\%".
    """
    return valor.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def proximo_protocolo():
    """Gera o proximo numero de protocolo no formato ANO + sequencial (6 digitos).

    Exemplo: 2026000001 (ano 2026, sequencial 000001).

    A operacao base eh atomica (INSERT ... ON CONFLICT DO UPDATE RETURNING).
    Se o numero gerado ja existir em chamado (dessincronizacao), avanca
    automaticamente para o proximo. Gaps na sequencia sao aceitaveis.
    """
    y = timezone.now().year
    for _ in range(100):
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
        protocolo = f"{y}{n:06d}"
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM chamado WHERE num_protocolo = %s",
                [protocolo],
            )
            if not cursor.fetchone():
                return protocolo
    raise RuntimeError("Nao foi possivel gerar protocolo unico apos 100 tentativas")


def formatar_dias_em_aberto(dt_abertura):
    """Retorna string formatada do tempo desde a abertura do chamado.

    Exemplos: "5 minuto(s)", "3 hora(s)", "12 dia(s)".
    Usado pela view de detalhe e listagem da equipe.
    """
    if is_naive(dt_abertura):
        dt_abertura = make_aware(dt_abertura, timezone=timezone.utc)
    delta = timezone.now() - dt_abertura
    if delta.total_seconds() < 3600:
        return f"{int(delta.total_seconds() // 60)} minuto(s)"
    if delta.total_seconds() < 86400:
        return f"{int(delta.total_seconds() // 3600)} hora(s)"
    return f"{delta.days} dia(s)"


def salvar_foto_upload(arquivo, request=None):
    """Salva foto via Cloudinary (se configurado) ou filesystem local.

    Se a variavel de ambiente CLOUDINARY_URL estiver definida, faz upload
    para o Cloudinary e retorna a URL segura (https). Caso contrario,
    salva localmente em MEDIA_ROOT/chamados/{uuid}.{ext} e retorna a URL.

    Levanta ValueError se nenhum arquivo for fornecido, ou se o upload
    falhar (timeout, erro de rede, erro da API).
    Levanta ImportError se Cloudinary estiver configurado mas nao instalado.
    """
    if not arquivo:
        raise ValueError("Foto obrigatoria.")

    cu = os.environ.get("CLOUDINARY_URL")
    if cu:
        try:
            import cloudinary
            import cloudinary.uploader
        except ImportError as exc:
            raise ImportError(
                "Cloudinary nao instalado. Execute: pip install cloudinary"
            ) from exc
        cloudinary.config(cloudinary_url=cu)
        try:
            r = cloudinary.uploader.upload(
                arquivo, folder="vg_portal", resource_type="image", timeout=30
            )
            return r["secure_url"]
        except Exception as e:
            msg = str(e) or "Erro ao fazer upload da foto."
            raise ValueError(msg) from e

    # Fallback: salva localmente com nome unico (UUID).
    ext_raw = os.path.splitext(arquivo.name)[1].lower()
    ext = ext_raw if ext_raw in (".jpg", ".jpeg", ".png", ".gif", ".webp") else ".jpg"
    nome = f"chamados/{uuid.uuid4().hex}{ext}"
    caminho = default_storage.save(nome, arquivo)
    if request:
        return request.build_absolute_uri(f"{settings.MEDIA_URL}{caminho}")
    return f"{settings.MEDIA_URL}{caminho}"
