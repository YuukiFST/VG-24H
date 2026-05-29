"""
views_root.py — Views publicas e de raiz do projeto (Portal VG 24H)

Este modulo contem as views que nao exigem autenticacao e as rotas
de raiz do sistema: pagina inicial, troca forcada de senha, painel
do cidadao (acesso rapido) e gestao de notificacoes.

As views de troca de senha sao obrigatorias para servidores com
senha_temporaria='1' (colaboradores recem-criados). O decorator
@exige_troca_senha intercepta QUALQUER requisicao e redireciona
o servidor para a tela de troca ate que ele defina uma nova senha.

As notificacoes sao criadas automaticamente pelo banco de dados
(Trigger 2B: fn_notificar_status_update) toda vez que o status
de um chamado muda. Estas views apenas listam e deletam — nunca
criam notificacoes diretamente.
"""

from types import SimpleNamespace

from django.contrib import messages
from django.db import connection, transaction
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from portal import db
from portal.decorators import autenticado
from portal.forms import NovaSenhaForm
from portal.models import Cidadao
from portal.utils import salvar_foto_upload


def root_view(request):
    """Pagina inicial (root) — Publica, nao requer login.

    Consulta os banners ativos ordenados pela ordem definida pelo gestor,
    as categorias com seus respectivos servicos para navegacao, e
    as estatisticas da plataforma (chamados resolvidos, bairros e servicos).
    Tudo feito utilizando SQL puro com hidratacao manual para objetos simples.
    """
    banners = []
    categorias = []
    stats = {}

    with connection.cursor() as cursor:
        # 1. Busca banners ativos ordenados por ordem
        cursor.execute(
            "SELECT id_banner, titulo, descricao, url_imagem, link "
            "FROM banner_publicacao "
            "WHERE ativo = TRUE "
            "ORDER BY ordem ASC, dt_criacao DESC"
        )
        for row in cursor.fetchall():
            banners.append(
                SimpleNamespace(
                    id_banner=row[0], titulo=row[1], descricao=row[2],
                    url_imagem=row[3], link=row[4], pk=row[0]
                )
            )

        # 2. Busca categorias ativas com seus respectivos servicos
        cursor.execute(
            "SELECT id_categoria, nome, descricao "
            "FROM categoria_servico "
            "WHERE ativo = TRUE "
            "ORDER BY nome"
        )
        cats = cursor.fetchall()

        for cat_row in cats:
            cat = SimpleNamespace(
                id_categoria=cat_row[0], nome=cat_row[1],
                descricao=cat_row[2], pk=cat_row[0]
            )
            cursor.execute(
                "SELECT id_servico, nome, descricao "
                "FROM servico "
                "WHERE id_categoria = %s AND ativo = TRUE "
                "ORDER BY nome",
                [cat.pk]
            )
            svcs = [
                SimpleNamespace(id_servico=r[0], nome=r[1], descricao=r[2], pk=r[0])
                for r in cursor.fetchall()
            ]
            categorias.append({"categoria": cat, "servicos": svcs})

        # 3. Busca estatisticas
        # Conta total de chamados resolvidos (sigla de status 'CO')
        cursor.execute(
            "SELECT COUNT(*) FROM chamado c "
            "WHERE ("
            "  SELECT sc.sigla FROM historico_chamado hc "
            "  JOIN status_chamado sc ON hc.id_status = sc.id_status "
            "  WHERE hc.id_chamado = c.id_chamado "
            "  ORDER BY hc.dt_alteracao DESC LIMIT 1"
            ") = 'CO'"
        )
        total_resolvidos = cursor.fetchone()[0]

        # Conta bairros ativos
        cursor.execute("SELECT COUNT(*) FROM bairro WHERE ativo = TRUE")
        total_bairros = cursor.fetchone()[0]

        # Conta servicos ativos
        cursor.execute("SELECT COUNT(*) FROM servico WHERE ativo = TRUE")
        total_servicos = cursor.fetchone()[0]

        stats = {
            "total_resolvidos": total_resolvidos,
            "total_bairros": total_bairros,
            "total_servicos": total_servicos,
        }

    return render(request, "portal/root.html", {
        "banners": banners,
        "categorias": categorias,
        "stats": stats,
    })

# ------------------------------------------------------------------
# TROCA DE SENHA (obrigatoria para servidores com senha_temporaria='1')
# ------------------------------------------------------------------

@autenticado
@require_http_methods(["GET", "POST"])
def trocar_senha(request):
    """Tela de troca de senha obrigatoria.

    Disponivel para qualquer tipo de usuario logado (COL, GES, CID).
    Apos trocar a senha com sucesso, limpa a flag senha_temporaria
    no banco e atualiza o cookie de sessao.

    O campo senha_temporaria='1' eh setado quando um gestor cria um
    novo colaborador. O middleware injetado no cookie detecta isso e
    redireciona todas as requisicoes para esta tela.
    """
    if request.method == "POST":
        form = NovaSenhaForm(request.POST)
        if form.is_valid():
            nova = form.cleaned_data["nova_senha"]

            # Atualiza a senha do servidor logado (hash bcrypt via make_password).
            # Usa SQL puro: UPDATE tabela correta conforme o tipo de usuario.
            with connection.cursor() as cursor:
                if hasattr(request.portal_user, "id_servidor"):
                    cursor.execute(
                        "UPDATE servidor SET senha_hash = %s, "
                        "senha_temporaria = '0' "
                        "WHERE id_servidor = %s",
                        [__import__("django.contrib.auth.hashers", fromlist=["make_password"]).make_password(nova), request.portal_user.pk],
                    )
                else:
                    cursor.execute(
                        "UPDATE cidadao SET senha_hash = %s "
                        "WHERE id_cidadao = %s",
                        [__import__("django.contrib.auth.hashers", fromlist=["make_password"]).make_password(nova), request.portal_user.pk],
                    )

            # Atualiza o cookie de sessao para refletir que a senha
            # nao eh mais temporaria (evita redirect infinito).
            request.session.modified = True
            if hasattr(request, "_portal_user"):
                del request._portal_user

            messages.success(request, "Senha alterada com sucesso!")
            return redirect("/")
    else:
        form = NovaSenhaForm()

    return render(request, "portal/senha/trocar_senha.html", {"form": form})


# ------------------------------------------------------------------
# NOTIFICACOES (servidores) — lista e exclusao
# ------------------------------------------------------------------

@autenticado
def notificacoes(request):
    """Lista notificacoes do servidor logado.

    As notificacoes sao criadas automaticamente pelo trigger do banco
    (fn_notificar_status_update) quando o status de um chamado muda.
    Esta view so permite visualizar e deletar.

    Seguranca: a subquery garante que o servidor so ve notificacoes
    dos chamados que ele mesmo atendeu (via historico_chamado).
    """
    uid = request.portal_user.pk
    notifs = []

    # Busca notificacoes ativas (nao arquivadas) do servidor.
    # Subquery filtra por chamados que o servidor ja atendeu.
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT n.id_notificacao, n.mensagem, n.lida, n.arquivada, "
            "n.dt_envio, n.id_chamado "
            "FROM notificacao n "
            "WHERE n.arquivada = FALSE "
            "AND n.id_chamado IN ("
            "    SELECT DISTINCT hc.id_chamado "
            "    FROM historico_chamado hc "
            "    WHERE hc.id_servidor = %s"
            ") "
            "ORDER BY n.dt_envio DESC",
            [uid],
        )
        for r in cursor.fetchall():
            notifs.append(SimpleNamespace(
                id_notificacao=r[0], pk=r[0], mensagem=r[1],
                lida=r[2], arquivada=r[3], dt_envio=r[4], id_chamado_id=r[5],
            ))

    # POST: exclusao de uma notificacao especifica.
    # Seguranca: subquery garante que so pode deletar notificacoes
    # dos proprios chamados atendidos (nao de outros servidores).
    if request.method == "POST":
        nid = request.POST.get("excluir")
        if nid:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM notificacao "
                    "WHERE id_notificacao = %s "
                    "AND id_chamado IN ("
                    "    SELECT DISTINCT hc.id_chamado "
                    "    FROM historico_chamado hc "
                    "    WHERE hc.id_servidor = %s"
                    ")",
                    [nid, uid],
                )
            messages.info(request, "Notificacao removida.")
        return redirect("portal:notificacoes")

    return render(request, "portal/notificacoes.html", {"lista": notifs})


# ------------------------------------------------------------------
# PAINEL DO CIDADAO (acesso rapido — perfil CID)
# ------------------------------------------------------------------

@autenticado
def painel_cidadao(request):
    """Dashboard do cidadao com chamados do usuario logado.

    Exibe todos os chamados do cidadao (incluindo cancelados)
    ordenados por data de abertura. Usa JOIN LATERAL para trazer
    o ultimo status de cada chamado em uma unica query.

    O campo dias_em_aberto eh calculado no Python: (hoje - dt_abertura).
    O campo cor_semaforo indica o nivel de urgencia:
    - verde: dentro do prazo
    - amarelo: proximo do limite
    - vermelho: atrasado
    """
    cidadao = request.portal_user
    chamados = []

    # Busca todos os chamados do cidadao com status atual.
    # JOIN LATERAL: busca o ultimo historico de cada chamado (evita N+1 queries).
    # LEFT JOIN em servico e bairro: preserva chamado mesmo se servico/bairro
    # forem deletados (nao deveria acontecer, mas previne erro).
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT c.id_chamado, c.num_protocolo, c.descricao, "
            "c.prioridade, c.dt_abertura, "
            "s.nome AS servico_nome, b.nome_bairro, "
            "ultimo.sigla AS sigla_status, "
            "s.prazo_amarelo_dias, s.prazo_vermelho_dias "
            "FROM chamado c "
            "LEFT JOIN servico s ON c.id_servico = s.id_servico "
            "LEFT JOIN bairro b ON c.id_bairro = b.id_bairro "
            "JOIN LATERAL ("
            "    SELECT sc.sigla "
            "    FROM historico_chamado hc "
            "    JOIN status_chamado sc ON hc.id_status = sc.id_status "
            "    WHERE hc.id_chamado = c.id_chamado "
            "    ORDER BY hc.dt_alteracao DESC "
            "    LIMIT 1"
            ") ultimo ON TRUE "
            "WHERE c.id_cidadao = %s "
            "ORDER BY c.dt_abertura DESC",
            [cidadao.pk],
        )
        for row in cursor.fetchall():
            # Calcula a cor do semaforo com base nos prazos do servico.
            # cor_semaforo retorna 'verde', 'amarelo' ou 'vermelho'.
            cor = db.cor_semaforo(row[4], row[8], row[9])
            dias = (timezone.now().date() - row[4].date()).days

            chamados.append(SimpleNamespace(
                id_chamado=row[0], num_protocolo=row[1], descricao=row[2],
                prioridade=row[3], dt_abertura=row[4],
                servico_nome=row[5], nome_bairro=row[6],
                sigla_status=row[7], cor_semaforo=cor, dias_em_aberto=dias,
            ))

    return render(request, "portal/cidadao/painel.html", {
        "cidadao": cidadao,
        "chamados": chamados,
    })


# ------------------------------------------------------------------
# UPLOAD DE FOTO DO PERFIL (cidadao e servidor)
# ------------------------------------------------------------------

@autenticado
@require_http_methods(["POST"])
def upload_foto_perfil(request):
    """Salva ou substitui a foto de perfil do usuario logado.

    Detecta automaticamente se o usuario eh cidadao ou servidor
    e atualiza a tabela correta. O upload pode ir para Cloudinary
    (se configurado) ou para o filesystem local.
    """
    foto = request.FILES.get("foto")
    if not foto:
        messages.error(request, "Nenhuma foto selecionada.")
        return redirect("/")

    try:
        url = salvar_foto_upload(foto, request=request)
    except ValueError as e:
        messages.error(request, str(e))
        return redirect("/")

    user = request.portal_user

    # Atualiza o campo foto_perfil na tabela correta conforme o tipo de usuario.
    if isinstance(user, Cidadao):
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE cidadao SET foto_perfil = %s WHERE id_cidadao = %s",
                [url, user.pk],
            )
    else:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE servidor SET foto_perfil = %s WHERE id_servidor = %s",
                [url, user.pk],
            )

    # Invalida o cache do middleware para que a proxima requisicao
    # ja reflita a nova foto.
    if hasattr(request, "_portal_user"):
        del request._portal_user

    messages.success(request, "Foto atualizada com sucesso!")
    return redirect("/")


# ------------------------------------------------------------------
# EXCLUIR FOTO DO PERFIL
# ------------------------------------------------------------------

@autenticado
@require_http_methods(["POST"])
def excluir_foto_perfil(request):
    """Remove a foto de perfil do usuario (define como NULL no banco)."""
    user = request.portal_user

    if isinstance(user, Cidadao):
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE cidadao SET foto_perfil = NULL WHERE id_cidadao = %s",
                [user.pk],
            )
    else:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE servidor SET foto_perfil = NULL WHERE id_servidor = %s",
                [user.pk],
            )

    if hasattr(request, "_portal_user"):
        del request._portal_user

    messages.success(request, "Foto removida com sucesso!")
    return redirect("/")

def catalogo_servicos(request):
    """Catalogo publico de servicos."""
    servicos = db.listar_categorias_ativas()
    return render(request, "portal/public/catalogo_servicos.html", {"categorias": servicos})
