# tudo aqui eh SQL puro: cursor, transaction.atomic e IntegrityError do Django.
# db tem meus helpers de historico/status e utils tem o gerador de protocolo
# e o upload de foto
from django.db import IntegrityError, connection, transaction
from django.utils import timezone

from portal import db
from portal.utils import proximo_protocolo, salvar_foto_upload


def criar_novo_chamado(cidadao, servico, bairro, descricao, ponto_referencia, foto_file):
    """Cria o chamado com a foto e um protocolo unico.

    Faco o INSERT do chamado e da foto dentro de uma transacao so. Se dois
    chamados tentarem o mesmo protocolo, o banco solta IntegrityError, e eu
    gero outro protocolo e tento de novo (por isso o loop de retry).
    Depois do INSERT, o Trigger 1 (AFTER INSERT) cria sozinho o primeiro
    registro la em historico_chamado (o status inicial AB).
    """
    url = salvar_foto_upload(foto_file)  # subo a foto antes de tudo
    now = timezone.now()  # mesma hora pra abertura e atualizacao
    protocolo = proximo_protocolo()  # primeiro palpite de protocolo
    chamado_id = None  # guardo aqui pra saber se o INSERT do chamado ja passou

    # tento ate 100 vezes pra fugir de colisao de protocolo
    for _ in range(100):
        try:
            # chamado + foto na mesma transacao: ou entra os dois ou nenhum
            with transaction.atomic(), connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO chamado "
                    "(num_protocolo, prioridade, ponto_de_referencia, descricao, "
                    "dt_abertura, atualizado_em, id_cidadao, id_servico, id_bairro) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) "
                    "RETURNING id_chamado",  # RETURNING pra ja pegar o id gerado
                    [
                        protocolo, 0,
                        ponto_referencia or None,  # se vier vazio, gravo NULL
                        descricao, now, now,
                        cidadao.pk,
                        # aceito tanto objeto (uso .pk) quanto id cru
                        servico.pk if hasattr(servico, "pk") else servico,
                        bairro.pk if hasattr(bairro, "pk") else bairro,
                    ],
                )
                chamado_id = cursor.fetchone()[0]  # id que o RETURNING devolveu
                # ja insiro a foto apontando pro chamado recem-criado
                cursor.execute(
                    "INSERT INTO foto_chamado (id_chamado, url_foto, dt_upload) "
                    "VALUES (%s, %s, %s)",
                    [chamado_id, url, now],
                )
            break  # deu tudo certo, saio do loop
        except IntegrityError:
            # se o chamado JA entrou, o erro nao eh de protocolo -> repasso
            if chamado_id is not None:
                raise
            # senao foi colisao de protocolo: gero outro e tento de novo
            protocolo = proximo_protocolo()

    return chamado_id, protocolo


def alterar_status(chamado_id, novo_status, servidor_id, prioridade=None, resolucao=None, observacao=None):
    """Muda o status do chamado seguindo o event sourcing.

    Eu nao escrevo o status no chamado: insiro um historico novo (esse eh o
    novo status) e, se precisar, dou UPDATE so na prioridade/resolucao. O
    resto (atualizado_em, dt_conclusao, notificacao) os triggers 2A/2B fazem.
    """
    # historico + update na mesma transacao pra ficar tudo atomico
    with transaction.atomic(), connection.cursor() as cursor:
        # cria o registro do novo status (aceita objeto ou id cru)
        db.criar_historico(
            chamado_id, novo_status.pk if hasattr(novo_status, "pk") else novo_status,
            servidor_id=servidor_id,
            observacao=observacao,
        )

        # monto o UPDATE dinamico: so adiciono coluna que realmente mudou
        update_fields = []
        update_params = []
        if prioridade is not None:
            update_fields.append("prioridade = %s")
            # clampo a prioridade entre 0 e 5 pra nao entrar valor doido
            update_params.append(max(0, min(5, int(prioridade))))
        if resolucao is not None:
            update_fields.append("resolucao = %s")
            update_params.append(resolucao)

        # so disparo o UPDATE se tiver pelo menos um campo pra mudar
        if update_fields:
            update_params.append(chamado_id)  # o id vai por ultimo, pro WHERE
            cursor.execute(
                f"UPDATE chamado SET {', '.join(update_fields)} "  # noqa: S608 (update_fields sao literais do codigo; valores parametrizados)
                f"WHERE id_chamado = %s",
                update_params,
            )


def adicionar_observacao(chamado_id, texto, servidor_id=None):
    """Adiciona uma observacao SEM mudar o status (repito o status atual)."""
    # primeiro descubro qual eh o status atual: o do historico mais recente
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_status FROM historico_chamado "
            "WHERE id_chamado = %s "
            "ORDER BY dt_alteracao DESC LIMIT 1",  # o mais novo primeiro
            [chamado_id],
        )
        row = cursor.fetchone()
    # se nao tem nenhum historico, tem algo errado com esse chamado
    if not row:
        raise ValueError("Chamado sem historico")
    # crio um historico repetindo o mesmo status, so pra registrar o texto
    db.criar_historico(chamado_id, row[0], servidor_id=servidor_id, observacao=texto)


def cancelar_chamado_cidadao(chamado_id, motivo):
    """Cancelamento feito pelo proprio cidadao: cria historico CA + grava resolucao."""
    ca_id = db.buscar_status_ca()  # pego o id do status CA (Cancelado)
    # se nao achei o CA no banco, nao da pra cancelar
    if not ca_id:
        raise ValueError("Status CA não encontrado")
    # historico CA + update da resolucao juntos na transacao
    with transaction.atomic():
        db.criar_historico(chamado_id, ca_id, observacao=motivo)
        with connection.cursor() as cursor:
            # guardo o motivo do cancelamento como resolucao do chamado
            cursor.execute(
                "UPDATE chamado SET resolucao = %s WHERE id_chamado = %s",
                [motivo, chamado_id],
            )


def adicionar_foto(chamado_id, arquivo_foto):
    """Sobe mais uma foto e anexa ao chamado."""
    url = salvar_foto_upload(arquivo_foto)  # faz o upload
    db.inserir_foto_chamado(chamado_id, url)  # grava a URL via helper
    return url
