"""
views_cidadao.py — Views do cidadao (Portal VG 24H)

Este modulo atende as rotas acessiveis apenas por cidadaos autenticados
(perfil "CID"). Colaboradores e gestores sao bloqueados pelo decorator
@perfis("CID").

As operacoes disponiveis sao:
- Listar chamados do proprio cidadao (com filtros e paginacao)
- Abrir novo chamado (com upload de foto)
- Ver detalhe de um chamado (historico, fotos, observacoes)
- Cancelar chamado aberto ou em atendimento
- Avaliar chamado concluido (nota 1-5)
- Listar e excluir notificacoes

O status de um chamado nao eh armazenado como campo direto na tabela
chamado. Em vez disso, o status atual eh determinado pelo registro mais
recente na tabela historico_chamado (padrao event sourcing). Toda mudanca
de status gera um novo INSERT em historico_chamado, nunca um UPDATE.
Isso garante um log completo de auditoria.

O trigger Trigger 1 (AFTER INSERT ON chamado) cria automaticamente o
primeiro registro em historico_chamado com status "AB" (Aberto). A view
de criacao nao precisa se preocupar com o historico inicial.

Cada cidadao acessa somente seus proprios chamados. Todas as queries
incluem WHERE c.id_cidadao = %s para garantir privacidade. A funcao
auxiliar _chamado_do_cidadao() valida propriedade e retorna HTTP 404
quando o chamado nao pertence ao usuario (em vez de 403, para nao
revelar a existencia do recurso).
"""

from types import SimpleNamespace

from django.contrib import messages
from django.db import IntegrityError, connection, transaction
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from portal import db
from portal.decorators import autenticado, perfis
from portal.models import ConfiguracaoSemaforo
from portal.forms import (
    AvaliacaoForm,
    CancelarChamadoForm,
    ChamadoNovoForm,
    FotoForm,
    ObservacaoForm,
)
from portal.utils import escape_like, proximo_protocolo, salvar_foto_upload


def _chamado_do_cidadao(request, pk):
    """Busca um chamado e valida que pertence ao cidadao logado.

    Retorna o objeto SimpleNamespace do chamado (com JOINs em servico e
   bairro) ou levanta Http404 se o chamado nao existir ou pertencer
    a outro usuario. Retorna 404 em vez de 403 para nao revelar se
    o recurso existe (seguranca por obscuridade).
    """
    ch = db.buscar_chamado(pk)
    if not ch:
        raise Http404()
    if ch.id_cidadao_id != request.portal_user.pk:
        raise Http404()
    return ch


# ------------------------------------------------------------------
# Listar chamados do cidadao (GET /cidadao/chamados/)
# ------------------------------------------------------------------

@autenticado
@perfis("CID")
def cidadao_chamados_lista(request):
    """Lista os chamados do cidadao logado com filtros e paginacao.

    A query usa JOIN LATERAL (PostgreSQL) para buscar o ultimo historico
    de cada chamado em uma unica query, evitando o problema N+1.
    A subquery LATERAL executa ORDER BY dt_alteracao DESC LIMIT 1
    para pegar o registro mais recente de historico_chamado.

    Filtros disponiveis (todos opcionais, via query string):
    - status: sigla do status (ex: AB, EA, CO)
    - data: data de abertura (YYYY-MM-DD)
    - q: busca por numero de protocolo (ILIKE case-insensitive)
    """
    uid = request.portal_user.pk

    # Paginacao: le o parametro "pagina" da URL, com minimo de 1.
    try:
        pagina = max(1, int(request.GET.get("pagina") or 1))
    except (ValueError, TypeError):
        pagina = 1
    por_pagina = 15
    offset = (pagina - 1) * por_pagina

    # Clase base do FROM/WHERE (reutilizada no COUNT e no SELECT).
    # JOIN LATERAL busca o ultimo status de cada chamado.
    sql_base = (
        "FROM chamado c "
        "JOIN servico s ON c.id_servico = s.id_servico "
        "JOIN bairro b ON c.id_bairro = b.id_bairro "
        "JOIN LATERAL ("
        "  SELECT sc.sigla, sc.descricao, sc.id_status FROM historico_chamado hc "
        "  JOIN status_chamado sc ON hc.id_status = sc.id_status "
        "  WHERE hc.id_chamado = c.id_chamado "
        "  ORDER BY hc.dt_alteracao DESC LIMIT 1"
        ") ultimo ON TRUE "
        "WHERE c.id_cidadao = %s "
    )
    select_cols = (
        "SELECT c.id_chamado, c.num_protocolo, c.prioridade, "
        "c.descricao, c.dt_abertura, c.atualizado_em, "
        "c.id_servico, c.id_bairro, "
        "s.nome AS servico_nome, "
        "b.nome_bairro, "
        "ultimo.sigla AS sigla_status, "
        "ultimo.descricao AS status_descricao "
    )
    params = [uid]

    # Filtros opcionais: cada um adiciona uma clausula AND ao WHERE.
    st_filter = request.GET.get("status")
    dt_filter = request.GET.get("data")
    q_filter = request.GET.get("q")

    if st_filter:
        sql_base += "AND ultimo.sigla = %s "
        params.append(st_filter)
    if dt_filter:
        # ::date faz o cast para comparar apenas o dia, ignorando a hora.
        sql_base += "AND c.dt_abertura::date = %s "
        params.append(dt_filter)
    if q_filter:
        # ILIKE faz busca case-insensitive no PostgreSQL.
        sql_base += "AND c.num_protocolo ILIKE %s "
        params.append(f"%{escape_like(q_filter)}%")

    # Conta o total de registros para a paginacao (sem LIMIT/OFFSET).
    count_sql = "SELECT COUNT(*) " + sql_base
    with connection.cursor() as cursor:
        cursor.execute(count_sql, params)
        total_count = cursor.fetchone()[0]

    # Busca apenas a pagina atual (LIMIT + OFFSET no proprio SQL).
    data_sql = select_cols + sql_base + "ORDER BY c.dt_abertura DESC LIMIT %s OFFSET %s"
    data_params = params + [por_pagina, offset]

    with connection.cursor() as cursor:
        cursor.execute(data_sql, data_params)
        rows = cursor.fetchall()

    # Hidratacao: cada tupla do banco vira um SimpleNamespace com atributos
    # nomeados, para que o template acesse ch.num_protocolo em vez de ch[1].
    config = ConfiguracaoSemaforo.get_singleton()
    chamados = []
    for r in rows:
        cor = db.cor_semaforo(r[4], config.prazo_amarelo_dias, config.prazo_vermelho_dias)
        sigla = r[10] or ""
        status_desc = r[11] or sigla
        chamados.append(SimpleNamespace(
            id_chamado=r[0], pk=r[0], num_protocolo=r[1], prioridade=r[2],
            descricao=r[3], dt_abertura=r[4], atualizado_em=r[5],
            id_servico=SimpleNamespace(id_servico=r[6], pk=r[6], nome=r[8]),
            id_bairro=SimpleNamespace(id_bairro=r[7], pk=r[7], nome_bairro=r[9]),
            sigla_status=sigla, cor_semaforo=cor,
            status_atual=SimpleNamespace(sigla=sigla, descricao=status_desc),
        ))

    # db.paginar() cria um objeto page_obj compativel com os templates
    # de paginacao padrao do Django.
    page_obj, _ = db.paginar(chamados, pagina, por_pagina=por_pagina, total_count=total_count)

    # Estatisticas do semaforo para os cards no topo da pagina.
    stats = db.calcular_stats_semaforo(cidadao_id=uid)

    return render(
        request,
        "portal/cidadao/dashboard.html",
        {"lista": page_obj, "total_count": total_count, "page_obj": page_obj, "stats": stats},
    )


# ------------------------------------------------------------------
# Abrir novo chamado (GET/POST /cidadao/chamados/novo/)
# ------------------------------------------------------------------

@autenticado
@perfis("CID")
@require_http_methods(["GET", "POST"])
def cidadao_chamado_novo(request):
    """Formulario de abertura de novo chamado.

    GET: exibe o formulario com categorias, servicos (select cascata),
    bairros, descricao e campo de foto.

    POST: valida, salva a foto, gera protocolo e insere o chamado.
    O trigger Trigger 1 (AFTER INSERT ON chamado) cria automaticamente
    o registro em historico_chamado com status "AB".

    O numero de protocolo eh gerado atomicamente por proximo_protocolo()
    (INSERT ... ON CONFLICT DO UPDATE RETURNING), evitando race conditions
    entre duas requisicoes simultaneas.
    """
    # Busca categorias ativas com seus servicos (para o select cascata).
    categorias_list = []
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_categoria, nome, descricao "
            "FROM categoria_servico WHERE ativo = TRUE "
            "ORDER BY nome"
        )
        cats = cursor.fetchall()
        for cat_row in cats:
            cat = SimpleNamespace(id_categoria=cat_row[0], pk=cat_row[0], nome=cat_row[1], descricao=cat_row[2])
            cursor.execute(
                "SELECT id_servico, nome "
                "FROM servico "
                "WHERE id_categoria = %s AND ativo = TRUE ORDER BY nome",
                [cat.pk],
            )
            # Simula o queryset.all() do ORM para compatibilidade com templates.
            cat.servicos = SimpleNamespace(all=lambda rows=[
                SimpleNamespace(id_servico=r[0], pk=r[0], nome=r[1]) for r in cursor.fetchall()
            ]: rows)
            categorias_list.append(cat)

    # Busca bairros ativos para o select de bairro.
    bairros = db.listar_bairros_ativos()

    if request.method == "POST":
        form = ChamadoNovoForm(request.POST, request.FILES)
        if form.is_valid():
            d = form.cleaned_data

            # Salva a foto (Cloudinary ou filesystem local).
            try:
                url = salvar_foto_upload(request.FILES.get("foto"), request=request)
            except ValueError as e:
                messages.error(request, str(e))
                return render(
                    request,
                    "portal/cidadao/novo_chamado.html",
                    {"form": form, "categorias": categorias_list, "bairros": bairros},
                )

            now = timezone.now()

            # Gera protocolo FORA do atomic() para que o incremento em
            # protocolo_seq persista mesmo se a transacao abaixo falhar.
            # Se houver colisao com protocolo existente, proximo_protocolo()
            # consome o numero conflitante e tenta o proximo automaticamente.
            protocolo = proximo_protocolo()
            chamado_id = None

            # Retry loop: em condicao de corrida rara (dois requests
            # simultaneos obterem o mesmo protocolo), capturamos o
            # IntegrityError e tentamos com o proximo numero.
            for _ in range(100):
                try:
                    with transaction.atomic(), connection.cursor() as cursor:
                        # INSERT na tabela chamado. Nao insere status aqui
                        # porque o Trigger 1 cria automaticamente o historico
                        # com status "AB".
                        # RETURNING id_chamado evita uma segunda query para
                        # descobrir o ID gerado pelo SERIAL.
                        cursor.execute(
                            "INSERT INTO chamado "
                            "(num_protocolo, prioridade, ponto_de_referencia, descricao, "
                            "dt_abertura, atualizado_em, id_cidadao, id_servico, id_bairro) "
                            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) "
                            "RETURNING id_chamado",
                            [
                                protocolo, 0,
                                d.get("ponto_de_referencia") or None,
                                d["descricao"], now, now,
                                request.portal_user.pk,
                                d["id_servico"].pk,
                                d["id_bairro"].pk,
                            ],
                        )
                        chamado_id = cursor.fetchone()[0]

                        # Registra a foto associada ao chamado.
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

            messages.success(request, f"Chamado aberto. Protocolo: {protocolo}")
            return redirect("portal:cidadao_chamado", pk=chamado_id)
    else:
        form = ChamadoNovoForm()

    return render(
        request,
        "portal/cidadao/novo_chamado.html",
        {"form": form, "categorias": categorias_list, "bairros": bairros},
    )


# ------------------------------------------------------------------
# Detalhe do chamado + acoes (GET/POST /cidadao/chamados/<pk>/)
# ------------------------------------------------------------------

@autenticado
@perfis("CID")
@require_http_methods(["GET", "POST"])
def cidadao_chamado_detalhe(request, pk):
    """Exibe detalhes do chamado e processa acoes do cidadao.

    Esta view eh hibrida: GET mostra o detalhe, POST executa uma acao
    determinada pelo campo oculto "acao" no formulario HTML.

    Acoes disponiveis (cada uma condicionada ao status atual):

    - obs: Adiciona observacao (INSERT historico com o mesmo status).
      Disponivel enquanto o chamado nao estiver concluido ou cancelado.

    - foto: Upload de nova foto (INSERT foto_chamado).
      Mesma restricao de status que obs.

    - cancelar: Cancela o chamado (INSERT historico com status "CA").
      O trigger Trigger 2B seta dt_conclusao = NOW() e gera notificacao.
      Disponivel apenas para status "AB" ou "EA".

    - avaliar: Avalia chamado concluido (UPDATE chamado com nota e comentario).
      Disponivel apenas para status "CO" e quando nota_avaliacao eh NULL.
    """
    ch = _chamado_do_cidadao(request, pk)
    ts = ch.sigla_status

    # Calcula permissoes com base no status atual.
    # Encerrado = CO (Concluido) ou CA (Cancelado).
    pode_obs_foto = ts not in ("CO", "CA")
    pode_cancelar = ts in ("AB", "EA")
    pode_avaliar = ts == "CO" and ch.nota_avaliacao is None

    if request.method == "POST":
        acao = request.POST.get("acao")

        # Acao: adicionar observacao.
        # INSERT historico mantendo o mesmo status, so com o texto.
        # id_servidor=None indica que foi o cidadao quem escreveu.
        if acao == "obs" and pode_obs_foto:
            form_o = ObservacaoForm(request.POST)
            if form_o.is_valid():
                status_id = ch.status_atual.pk if ch.status_atual else None
                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO historico_chamado "
                        "(id_chamado, id_servidor, id_status, observacao, dt_alteracao) "
                        "VALUES (%s, %s, %s, %s, %s)",
                        [pk, None, status_id, form_o.cleaned_data["texto"], timezone.now()],
                    )
                messages.success(request, "Observacao registrada.")
            return redirect("portal:cidadao_chamado", pk=pk)

        # Acao: upload de foto.
        if acao == "foto" and pode_obs_foto:
            form_f = FotoForm(request.POST, request.FILES)
            if form_f.is_valid() and request.FILES.get("foto"):
                try:
                    url = salvar_foto_upload(request.FILES["foto"], request=request)
                except ValueError as e:
                    messages.error(request, str(e))
                else:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "INSERT INTO foto_chamado (id_chamado, url_foto, dt_upload) "
                            "VALUES (%s, %s, %s)",
                            [pk, url, timezone.now()],
                        )
                    messages.success(request, "Foto adicionada.")
            else:
                if not request.FILES.get("foto"):
                    messages.error(request, "Selecione uma imagem.")
                else:
                    for field, errors in form_f.errors.items():
                        for error in errors:
                            messages.error(request, error)
            return redirect("portal:cidadao_chamado", pk=pk)

        # Acao: cancelar chamado.
        # Busca o ID do status "CA" e faz INSERT no historico.
        # O trigger Trigger 2B cuida de setar dt_conclusao e gerar notificacao.
        if acao == "cancelar" and pode_cancelar:
            form_c = CancelarChamadoForm(request.POST)
            if form_c.is_valid():
                with transaction.atomic(), connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT id_status FROM status_chamado WHERE sigla = 'CA'"
                    )
                    ca_row = cursor.fetchone()
                    if not ca_row:
                        messages.error(request, "Erro interno: status CA nao encontrado.")
                        return redirect("portal:cidadao_chamado", pk=pk)
                    ca_id = ca_row[0]

                    cursor.execute(
                        "INSERT INTO historico_chamado "
                        "(id_chamado, id_servidor, id_status, observacao, dt_alteracao) "
                        "VALUES (%s, %s, %s, %s, %s)",
                        [pk, None, ca_id, form_c.cleaned_data["motivo"], timezone.now()],
                    )

                    # Salva o motivo do cancelamento no campo resolucao do chamado.
                    # O trigger Trigger 2A atualiza atualizado_em automaticamente.
                    cursor.execute(
                        "UPDATE chamado SET resolucao = %s WHERE id_chamado = %s",
                        [form_c.cleaned_data["motivo"], pk],
                    )
                messages.success(request, "Chamado cancelado.")
            return redirect("portal:cidadao_chamado", pk=pk)

        # Acao: avaliar chamado concluido.
        # UPDATE direto na tabela chamado (avaliacao nao gera historico).
        if acao == "avaliar" and pode_avaliar:
            form_a = AvaliacaoForm(request.POST)
            if form_a.is_valid():
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE chamado SET nota_avaliacao = %s, "
                        "comentario_avaliacao = %s, dt_avaliacao = %s "
                        "WHERE id_chamado = %s",
                        [
                            form_a.cleaned_data["nota"],
                            form_a.cleaned_data.get("comentario") or None,
                            timezone.now(),
                            pk,
                        ],
                    )
                messages.success(request, "Avaliacao registrada.")
            return redirect("portal:cidadao_chamado", pk=pk)

    # GET: busca historicos e fotos para renderizar o detalhe.
    historicos = db.buscar_historicos(pk)
    fotos = db.buscar_fotos(pk)

    # Observacoes = registros do historico que possuem texto no campo observacao.
    observacoes = [h for h in historicos if h.observacao]

    return render(
        request,
        "portal/cidadao/chamado_detalhe.html",
        {
            "ch": ch,
            "historicos": historicos,
            "fotos": fotos,
            "observacoes": observacoes,
            "sigla_status": ts,
            "pode_obs_foto": pode_obs_foto,
            "pode_cancelar": pode_cancelar,
            "pode_avaliar": pode_avaliar,
            "form_obs": ObservacaoForm(),
            "form_foto": FotoForm(),
            "form_cancelar": CancelarChamadoForm(),
            "form_avaliar": AvaliacaoForm(),
        },
    )


# ------------------------------------------------------------------
# Notificacoes do cidadao (GET/POST /cidadao/notificacoes/)
# ------------------------------------------------------------------

@autenticado
@perfis("CID")
@require_http_methods(["GET", "POST"])
def cidadao_notificacoes(request):
    """Lista e exclui notificacoes do cidadao logado.

    As notificacoes sao criadas automaticamente pelo trigger Trigger 2B
    toda vez que o status de um chamado muda. Esta view so permite
    visualizar e deletar — nunca cria notificacoes.

    Seguranca: a subquery no WHERE garante que o cidadao so ve
    notificacoes dos seus proprios chamados. O DELETE tambem usa a
    mesma subquery para impedir que um cidadao manipule o POST e
    delete notificacoes de outros.
    """
    uid = request.portal_user.pk

    # Busca notificacoes nao arquivadas dos chamados deste cidadao.
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT n.id_notificacao, n.mensagem, n.lida, n.arquivada, "
            "n.dt_envio, n.id_chamado "
            "FROM notificacao n "
            "WHERE n.arquivada = FALSE "
            "AND n.id_chamado IN ("
            "    SELECT c.id_chamado FROM chamado c WHERE c.id_cidadao = %s"
            ") "
            "ORDER BY n.dt_envio DESC",
            [uid],
        )
        lista = [
            SimpleNamespace(
                id_notificacao=r[0], pk=r[0], mensagem=r[1],
                lida=r[2], arquivada=r[3], dt_envio=r[4], id_chamado_id=r[5],
            )
            for r in cursor.fetchall()
        ]

    # POST: exclusao de notificacao especifica.
    if request.method == "POST":
        nid = request.POST.get("excluir")
        if nid:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM notificacao "
                    "WHERE id_notificacao = %s "
                    "AND id_chamado IN ("
                    "    SELECT c.id_chamado FROM chamado c WHERE c.id_cidadao = %s"
                    ")",
                    [nid, uid],
                )
            messages.info(request, "Notificacao removida.")
        return redirect("portal:cidadao_notificacoes")

    return render(
        request,
        "portal/cidadao/notificacoes.html",
        {"lista": lista},
    )
