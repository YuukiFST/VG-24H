from django.db import IntegrityError, connection, transaction
from django.utils import timezone

from portal import db
from portal.utils import proximo_protocolo, salvar_foto_upload


def criar_novo_chamado(cidadao, servico, bairro, descricao, ponto_referencia, foto_file, request=None):
    """Cria chamado com foto e protocolo unico.

    Gera protocolo atomicamente (INSERT ... ON CONFLICT DO UPDATE RETURNING).
    Retry loop em caso de colisao de protocolo (IntegrityError).
    O Trigger 1 (AFTER INSERT) cria o registro inicial em historico_chamado.
    """
    url = salvar_foto_upload(foto_file, request=request)
    now = timezone.now()
    protocolo = proximo_protocolo()
    chamado_id = None

    for _ in range(100):
        try:
            with transaction.atomic(), connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO chamado "
                    "(num_protocolo, prioridade, ponto_de_referencia, descricao, "
                    "dt_abertura, atualizado_em, id_cidadao, id_servico, id_bairro) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) "
                    "RETURNING id_chamado",
                    [
                        protocolo, 0,
                        ponto_referencia or None,
                        descricao, now, now,
                        cidadao.pk,
                        servico.pk if hasattr(servico, "pk") else servico,
                        bairro.pk if hasattr(bairro, "pk") else bairro,
                    ],
                )
                chamado_id = cursor.fetchone()[0]
                cursor.execute(
                    "INSERT INTO foto_chamado (id_chamado, url_foto, dt_upload) "
                    "VALUES (%s, %s, %s)",
                    [chamado_id, url, now],
                )
            break
        except IntegrityError:
            if chamado_id is not None:
                raise
            protocolo = proximo_protocolo()

    return chamado_id, protocolo


def alterar_status(chamado_id, novo_status, servidor_id, prioridade=None, resolucao=None, observacao=None):
    """Altera o status de um chamado com event sourcing.

    INSERT em historico_chamado (novo status) + UPDATE chamado
    (prioridade, resolucao se final). Os triggers 2A/2B cuidam de
    atualizado_em, dt_conclusao e notificacao.
    """
    with transaction.atomic(), connection.cursor() as cursor:
        db.criar_historico(
            chamado_id, novo_status.pk if hasattr(novo_status, "pk") else novo_status,
            servidor_id=servidor_id,
            observacao=observacao,
        )

        update_fields = []
        update_params = []
        if prioridade is not None:
            update_fields.append("prioridade = %s")
            update_params.append(max(0, min(5, int(prioridade))))
        if resolucao is not None:
            update_fields.append("resolucao = %s")
            update_params.append(resolucao)

        if update_fields:
            update_params.append(chamado_id)
            cursor.execute(
                f"UPDATE chamado SET {', '.join(update_fields)} "
                f"WHERE id_chamado = %s",
                update_params,
            )


def adicionar_observacao(chamado_id, texto, servidor_id=None):
    """Adiciona observacao mantendo o status atual."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_status FROM historico_chamado "
            "WHERE id_chamado = %s "
            "ORDER BY dt_alteracao DESC LIMIT 1",
            [chamado_id],
        )
        row = cursor.fetchone()
    if not row:
        raise ValueError("Chamado sem historico")
    db.criar_historico(chamado_id, row[0], servidor_id=servidor_id, observacao=texto)


def cancelar_chamado_cidadao(chamado_id, motivo):
    """Cancela chamado (cidadão). Insere historico CA e atualiza resolucao."""
    ca_id = db.buscar_status_ca()
    if not ca_id:
        raise ValueError("Status CA não encontrado")
    with transaction.atomic():
        db.criar_historico(chamado_id, ca_id, observacao=motivo)
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE chamado SET resolucao = %s WHERE id_chamado = %s",
                [motivo, chamado_id],
            )


def avaliar_chamado(chamado_id, nota, comentario):
    """Registra avaliação de chamado concluído."""
    db.avaliar_chamado(chamado_id, nota, comentario)


def adicionar_foto(chamado_id, arquivo_foto, request=None):
    """Adiciona foto a um chamado com upload."""
    url = salvar_foto_upload(arquivo_foto, request=request)
    db.inserir_foto_chamado(chamado_id, url)
    return url
