"""
utils.py — minhas funcoes auxiliares do Portal VG 24H

Aqui eu junto as funcoes soltas que varias views minhas usam:
- escape_like: escapar os caracteres chatos do LIKE/ILIKE
- proximo_protocolo: gerar numero de protocolo de forma atomica
- salvar_foto_upload: salvar foto no Cloudinary
"""

# os pra ler a env do Cloudinary
import os

# connection pro SQL puro, timezone pras datas
from django.db import connection
from django.utils import timezone
from django.utils.timezone import is_naive, make_aware


def escape_like(valor):
    """Escapo os caracteres chatos do LIKE/ILIKE no PostgreSQL.

    O %, o _ e a \\ tem significado especial no LIKE. Aqui eu coloco uma
    barra invertida na frente deles pra virarem texto normal. Tenho que
    chamar isso ANTES de envolver o valor com %...% pra busca parcial.
    Exemplo: escape_like("100%") me devolve "100\\%".
    """
    # escapo a barra primeiro (senao eu escaparia as barras que eu mesmo coloco), dai % e _
    return valor.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def proximo_protocolo():
    """Gero o proximo protocolo no formato ANO + sequencial de 6 digitos.

    Exemplo: 2026000001 (ano 2026, sequencial 000001).

    O passo principal e atomico (INSERT ... ON CONFLICT DO UPDATE RETURNING),
    entao dois pedidos ao mesmo tempo nao pegam o mesmo numero. Se mesmo assim
    o numero ja existir em chamado (algo dessincronizou), eu avanco sozinho pro
    proximo. Pode ficar buraco na sequencia, pra mim ta de boa.
    """
    # ano de agora, e o protocolo comeca com ele
    y = timezone.now().year
    # tento ate 100 vezes pra achar um numero que ainda nao foi usado
    for _ in range(100):
        with connection.cursor() as cursor:
            # se nao tem linha pro ano eu crio com 1, se ja tem eu somo +1 -- tudo atomico
            cursor.execute(
                "INSERT INTO protocolo_seq (ano, ultimo_numero) VALUES (%s, 1) "
                "ON CONFLICT (ano) DO UPDATE SET ultimo_numero = protocolo_seq.ultimo_numero + 1 "
                "RETURNING ultimo_numero",
                [y],
            )
            row = cursor.fetchone()
            # o RETURNING sempre tem que vir com algo; se vier vazio e bug feio
            if not row:
                raise RuntimeError("protocolo_seq INSERT/RETURNING nao retornou linha")
            n = row[0]
        # monto o protocolo: ano grudado no sequencial com zeros a esquerda (6 digitos)
        protocolo = f"{y}{n:06d}"
        with connection.cursor() as cursor:
            # confiro se por acaso esse protocolo ja existe em chamado
            cursor.execute(
                "SELECT 1 FROM chamado WHERE num_protocolo = %s",
                [protocolo],
            )
            # nao achou? entao ta livre, devolvo ele
            if not cursor.fetchone():
                return protocolo
    # se em 100 tentativas eu nao consegui, ai realmente tem algo muito errado
    raise RuntimeError("Nao foi possivel gerar protocolo unico apos 100 tentativas")


def formatar_dias_em_aberto(dt_abertura):
    """Me devolve um texto de quanto tempo faz que o chamado foi aberto.

    Exemplos: "5 minuto(s)", "3 hora(s)", "12 dia(s)".
    A view de detalhe e a listagem da equipe usam isso.
    """
    # se a data vier sem fuso eu coloco UTC, senao o subtrai abaixo quebra
    if is_naive(dt_abertura):
        dt_abertura = make_aware(dt_abertura, timezone=timezone.utc)
    # quanto tempo passou desde a abertura
    delta = timezone.now() - dt_abertura
    # menos de 1 hora -> mostro em minutos
    if delta.total_seconds() < 3600:
        return f"{int(delta.total_seconds() // 60)} minuto(s)"
    # menos de 1 dia -> mostro em horas
    if delta.total_seconds() < 86400:
        return f"{int(delta.total_seconds() // 3600)} hora(s)"
    # de 1 dia pra cima -> mostro em dias
    return f"{delta.days} dia(s)"


def salvar_foto_upload(arquivo):
    """Salvo a foto no Cloudinary e devolvo a URL segura (https).

    Exijo a env CLOUDINARY_URL: mando a imagem pro Cloudinary e devolvo a
    secure_url (https).

    Solto ValueError se nao vier arquivo, se o Cloudinary nao estiver
    configurado, ou se o upload falhar (timeout, rede, erro da API). Solto
    ImportError se o pacote cloudinary nao estiver instalado.
    """
    # sem arquivo nem comeco
    if not arquivo:
        raise ValueError("Foto obrigatoria.")

    # Cloudinary e obrigatorio: sem a env nao tem onde salvar a foto
    cu = os.environ.get("CLOUDINARY_URL")
    if not cu:
        raise ValueError("CLOUDINARY_URL nao configurado.")

    try:
        # importo aqui dentro pra so exigir o pacote quando realmente for usar
        import cloudinary
        import cloudinary.uploader
    except ImportError as exc:
        # ta configurado mas nao instalado: aviso como instalar
        raise ImportError(
            "Cloudinary nao instalado. Execute: pip install cloudinary"
        ) from exc
    # configuro o cloudinary com a url que veio da env
    cloudinary.config(cloudinary_url=cu)
    try:
        # mando a imagem pra pasta vg_portal, com 30s de timeout
        r = cloudinary.uploader.upload(
            arquivo, folder="vg_portal", resource_type="image", timeout=30
        )
        # devolvo o link https que o cloudinary me deu
        return r["secure_url"]
    except Exception as e:
        # qualquer erro no upload vira ValueError com a mensagem (ou uma generica)
        msg = str(e) or "Erro ao fazer upload da foto."
        raise ValueError(msg) from e
