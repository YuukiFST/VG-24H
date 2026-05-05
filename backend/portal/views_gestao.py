"""
views_gestao.py — Views de Gestao (Portal VG 24H)

[!] @perfis("GES") — APENAS Gestores acessam. CID e COL sao bloqueados.
[!] Todas as operacoes usam SQL puro (NEM models Django ORM).
[!] A view de estatisticas consulta a view SQL vw_estatisticas_chamados
    (criada por Rafael em 05_views.sql — JOIN LATERAL no ultimo historico).

Operacoes:
  - CRUD de Categorias, Servicos, Bairros, Colaboradores e Banners
  - Visualizacao de estatisticas via view SQL
"""

from types import SimpleNamespace

from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.db import connection
from django.db.utils import ProgrammingError
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from portal.decorators import perfis
from portal.forms import (
    BairroForm,
    CategoriaForm,
    ColaboradorNovoForm,
    ServicoForm,
)
from portal.models import (
    Bairro,
    BannerPublicacao,
    CategoriaServico,
    Secretaria,
    Servico,
    Servidor,
)
from portal.utils import salvar_foto_upload


# ─── Estatísticas ────────────────────────────────────────────
@perfis("GES")
def gestao_estatisticas(request):
    rows = []
    try:
        with connection.cursor() as c:
            # SQL puro: consulta a view materializada de estatísticas
            c.execute("SELECT * FROM vw_estatisticas_chamados ORDER BY categoria, bairro")
            cols = [d[0] for d in c.description]
            rows = [dict(zip(cols, r)) for r in c.fetchall()]
    except ProgrammingError:
        pass
    return render(
        request,
        "portal/gestao/estatisticas.html",
        {"rows": rows},
    )


# ─── Categorias ──────────────────────────────────────────────
@perfis("GES")
@require_http_methods(["GET", "POST"])
def gestao_categorias(request):
    if request.method == "POST":
        form = CategoriaForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            # SQL puro: busca a primeira secretaria disponível
            with connection.cursor() as cursor:
                cursor.execute("SELECT id_secretaria FROM secretaria LIMIT 1")
                sec_row = cursor.fetchone()
                sec_id = sec_row[0] if sec_row else None
                # SQL puro: INSERT na tabela categoria_servico
                cursor.execute(
                    "INSERT INTO categoria_servico (nome, descricao, ativo, id_secretaria) "
                    "VALUES (%s, %s, %s, %s)",
                    [d["nome"], d.get("descricao"), True, sec_id],
                )
            messages.success(request, "Categoria criada.")
        return redirect("portal:gestao_categorias")
    form = CategoriaForm()
    # SQL puro: SELECT categorias ativas
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_categoria, nome, descricao, ativo "
            "FROM categoria_servico "
            "WHERE ativo = TRUE ORDER BY nome"
        )
        lista = [
            SimpleNamespace(id_categoria=r[0], pk=r[0], nome=r[1], descricao=r[2], ativo=r[3])
            for r in cursor.fetchall()
        ]
    return render(
        request,
        "portal/gestao/categorias.html",
        {"form": form, "lista": lista},
    )


@perfis("GES")
@require_http_methods(["GET", "POST"])
def gestao_categoria_edit(request, pk):
    # SQL puro: SELECT categoria por ID
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_categoria, nome, descricao, ativo, id_secretaria "
            "FROM categoria_servico WHERE id_categoria = %s",
            [pk],
        )
        row = cursor.fetchone()
    if not row:
        raise Http404()

    obj = CategoriaServico()
    obj.id_categoria = row[0]
    obj.nome = row[1]
    obj.descricao = row[2]
    obj.ativo = row[3]
    obj.id_secretaria_id = row[4]
    obj._state.adding = False

    if request.method == "POST":
        form = CategoriaForm(request.POST, instance=obj)
        if form.is_valid():
            d = form.cleaned_data
            # SQL puro: UPDATE categoria_servico
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE categoria_servico SET nome = %s, descricao = %s "
                    "WHERE id_categoria = %s",
                    [d["nome"], d.get("descricao"), pk],
                )
            messages.success(request, "Categoria atualizada.")
            return redirect("portal:gestao_categorias")
    else:
        form = CategoriaForm(instance=obj)
    return render(
        request,
        "portal/gestao/categoria_form.html",
        {"form": form, "obj": obj},
    )


# ─── Serviços ────────────────────────────────────────────────
@perfis("GES")
@require_http_methods(["GET", "POST"])
def gestao_servicos(request):
    if request.method == "POST":
        form = ServicoForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            # SQL puro: INSERT na tabela servico
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO servico (nome, descricao, ativo, id_categoria, "
                    "prazo_amarelo_dias, prazo_vermelho_dias) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    [
                        d["nome"], d.get("descricao"), True,
                        d["id_categoria"].pk,
                        d.get("prazo_amarelo_dias", 15),
                        d.get("prazo_vermelho_dias", 30),
                    ],
                )
            messages.success(request, "Serviço criado.")
        return redirect("portal:gestao_servicos")
    form = ServicoForm()
    # SQL puro: SELECT serviços ativos com JOIN na categoria
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT s.id_servico, s.nome, s.descricao, s.ativo, "
            "s.id_categoria, cat.nome AS categoria_nome "
            "FROM servico s "
            "JOIN categoria_servico cat ON s.id_categoria = cat.id_categoria "
            "WHERE s.ativo = TRUE "
            "ORDER BY s.nome"
        )
        lista = [
            SimpleNamespace(
                id_servico=r[0], pk=r[0], nome=r[1], descricao=r[2],
                ativo=r[3],
                id_categoria=SimpleNamespace(id_categoria=r[4], pk=r[4], nome=r[5]),
            )
            for r in cursor.fetchall()
        ]
    return render(
        request,
        "portal/gestao/servicos.html",
        {"form": form, "lista": lista},
    )


@perfis("GES")
@require_http_methods(["GET", "POST"])
def gestao_servico_edit(request, pk):
    # SQL puro: SELECT serviço por ID
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_servico, nome, descricao, ativo, id_categoria, "
            "prazo_amarelo_dias, prazo_vermelho_dias "
            "FROM servico WHERE id_servico = %s",
            [pk],
        )
        row = cursor.fetchone()
    if not row:
        raise Http404()

    obj = Servico()
    obj.id_servico = row[0]
    obj.nome = row[1]
    obj.descricao = row[2]
    obj.ativo = row[3]
    obj.id_categoria_id = row[4]
    obj.prazo_amarelo_dias = row[5]
    obj.prazo_vermelho_dias = row[6]
    obj._state.adding = False

    if request.method == "POST":
        form = ServicoForm(request.POST, instance=obj)
        if form.is_valid():
            d = form.cleaned_data
            # SQL puro: UPDATE servico
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE servico SET nome = %s, descricao = %s, "
                    "id_categoria = %s, prazo_amarelo_dias = %s, prazo_vermelho_dias = %s "
                    "WHERE id_servico = %s",
                    [
                        d["nome"], d.get("descricao"),
                        d["id_categoria"].pk,
                        d.get("prazo_amarelo_dias", 15),
                        d.get("prazo_vermelho_dias", 30),
                        pk,
                    ],
                )
            messages.success(request, "Serviço atualizado.")
            return redirect("portal:gestao_servicos")
    else:
        form = ServicoForm(instance=obj)
    return render(
        request,
        "portal/gestao/servico_form.html",
        {"form": form, "obj": obj},
    )


# ─── Bairros ─────────────────────────────────────────────────
@perfis("GES")
@require_http_methods(["GET", "POST"])
def gestao_bairros(request):
    if request.method == "POST":
        form = BairroForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            # SQL puro: INSERT na tabela bairro
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO bairro (nome_bairro, cep, regiao, ativo) "
                    "VALUES (%s, %s, %s, %s)",
                    [d["nome_bairro"], d["cep"], d.get("regiao"), True],
                )
            messages.success(request, "Bairro criado.")
        return redirect("portal:gestao_bairros")
    form = BairroForm()
    # SQL puro: SELECT bairros ativos
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_bairro, nome_bairro, cep, regiao, ativo "
            "FROM bairro WHERE ativo = TRUE ORDER BY nome_bairro"
        )
        lista = [
            SimpleNamespace(
                id_bairro=r[0], pk=r[0], nome_bairro=r[1],
                cep=r[2], regiao=r[3], ativo=r[4],
            )
            for r in cursor.fetchall()
        ]
    return render(
        request,
        "portal/gestao/bairros.html",
        {"form": form, "lista": lista},
    )


@perfis("GES")
@require_http_methods(["GET", "POST"])
def gestao_bairro_edit(request, pk):
    # SQL puro: SELECT bairro por ID
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_bairro, nome_bairro, cep, regiao, ativo "
            "FROM bairro WHERE id_bairro = %s",
            [pk],
        )
        row = cursor.fetchone()
    if not row:
        raise Http404()

    obj = Bairro()
    obj.id_bairro = row[0]
    obj.nome_bairro = row[1]
    obj.cep = row[2]
    obj.regiao = row[3]
    obj.ativo = row[4]
    obj._state.adding = False

    if request.method == "POST":
        form = BairroForm(request.POST, instance=obj)
        if form.is_valid():
            d = form.cleaned_data
            # SQL puro: UPDATE bairro
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE bairro SET nome_bairro = %s, cep = %s, regiao = %s "
                    "WHERE id_bairro = %s",
                    [d["nome_bairro"], d["cep"], d.get("regiao"), pk],
                )
            messages.success(request, "Bairro atualizado.")
            return redirect("portal:gestao_bairros")
    else:
        form = BairroForm(instance=obj)
    return render(
        request,
        "portal/gestao/bairro_form.html",
        {"form": form, "obj": obj},
    )


# ─── Colaboradores ───────────────────────────────────────────
@perfis("GES")
@require_http_methods(["GET", "POST"])
def gestao_colaboradores(request):
    if request.method == "POST":
        form = ColaboradorNovoForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            # SQL puro: verifica duplicidade de email/CPF na tabela servidor
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT EXISTS("
                    "  SELECT 1 FROM servidor WHERE LOWER(email) = %s"
                    ") OR EXISTS("
                    "  SELECT 1 FROM servidor WHERE cpf = %s"
                    ")",
                    [d["email"].lower(), d["cpf"]],
                )
                ja_existe = cursor.fetchone()[0]

            if ja_existe:
                messages.error(request, "E-mail ou CPF já existe.")
            else:
                # SQL puro: busca primeira secretaria + INSERT servidor
                with connection.cursor() as cursor:
                    cursor.execute("SELECT id_secretaria FROM secretaria LIMIT 1")
                    sec_row = cursor.fetchone()
                    sec_id = sec_row[0] if sec_row else None

                    cursor.execute(
                        "INSERT INTO servidor "
                        "(nome_completo, cpf, dt_nascimento, telefone, email, "
                        "senha_hash, senha_temporaria, perfil, ativo, dt_cadastro, "
                        "id_secretaria) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        [
                            d["nome_completo"],
                            d["cpf"],
                            d["dt_nascimento"],
                            d["telefone"],
                            d["email"].lower(),
                            make_password(d["senha_provisoria"]),
                            "1",
                            "COL",
                            True,
                            timezone.now(),
                            sec_id,
                        ],
                    )
                messages.success(request, "Colaborador criado. Deve trocar a senha no 1º acesso.")
        return redirect("portal:gestao_colaboradores")
    form = ColaboradorNovoForm()
    # SQL puro: SELECT colaboradores (perfil COL)
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_servidor, nome_completo, cpf, email, telefone, "
            "perfil, ativo, dt_cadastro "
            "FROM servidor "
            "WHERE perfil = 'COL' "
            "ORDER BY ativo DESC, nome_completo"
        )
        lista = [
            SimpleNamespace(
                id_servidor=r[0], pk=r[0], nome_completo=r[1],
                cpf=r[2], email=r[3], telefone=r[4],
                perfil=r[5], ativo=r[6], dt_cadastro=r[7],
            )
            for r in cursor.fetchall()
        ]
    return render(
        request,
        "portal/gestao/colaboradores.html",
        {"form": form, "lista": lista},
    )


@perfis("GES")
@require_http_methods(["POST"])
def gestao_colaborador_toggle(request, pk):
    # SQL puro: busca colaborador e inverte o campo ativo
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_servidor, nome_completo, ativo "
            "FROM servidor WHERE id_servidor = %s",
            [pk],
        )
        row = cursor.fetchone()
    if not row:
        raise Http404()

    novo_ativo = not row[2]
    nome = row[1]
    # SQL puro: UPDATE servidor SET ativo = ...
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE servidor SET ativo = %s WHERE id_servidor = %s",
            [novo_ativo, pk],
        )
    status = "ativado" if novo_ativo else "inativado"
    messages.success(request, f"Colaborador {nome} {status}.")
    return redirect("portal:gestao_colaboradores")


@perfis("GES")
@require_http_methods(["POST"])
def gestao_servico_desativar(request, pk):
    # SQL puro: verifica existência e desativa serviço
    with connection.cursor() as cursor:
        cursor.execute("SELECT id_servico FROM servico WHERE id_servico = %s", [pk])
        if not cursor.fetchone():
            raise Http404()
        cursor.execute(
            "UPDATE servico SET ativo = FALSE WHERE id_servico = %s", [pk]
        )
    messages.info(request, "Serviço inativado.")
    return redirect("portal:gestao_servicos")


@perfis("GES")
@require_http_methods(["POST"])
def gestao_bairro_desativar(request, pk):
    # SQL puro: verifica existência e desativa bairro
    with connection.cursor() as cursor:
        cursor.execute("SELECT id_bairro FROM bairro WHERE id_bairro = %s", [pk])
        if not cursor.fetchone():
            raise Http404()
        cursor.execute(
            "UPDATE bairro SET ativo = FALSE WHERE id_bairro = %s", [pk]
        )
    messages.info(request, "Bairro inativado.")
    return redirect("portal:gestao_bairros")


# ─── Banners ─────────────────────────────────────────────────
@perfis("GES")
def gestao_banners(request):
    # SQL puro: SELECT todos os banners ordenados
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_banner, titulo, descricao, url_imagem, link, "
            "ordem, ativo, dt_criacao "
            "FROM banner_publicacao "
            "ORDER BY ordem, dt_criacao DESC"
        )
        banners = [
            SimpleNamespace(
                id_banner=r[0], pk=r[0], titulo=r[1], descricao=r[2],
                url_imagem=r[3], link=r[4], ordem=r[5],
                ativo=r[6], dt_criacao=r[7],
            )
            for r in cursor.fetchall()
        ]
    return render(request, "portal/gestao/banners.html", {"banners": banners})


@perfis("GES")
@require_http_methods(["GET", "POST"])
def gestao_banner_novo(request):
    if request.method == "POST":
        titulo = request.POST.get("titulo", "").strip()
        descricao = request.POST.get("descricao", "").strip() or None
        link = request.POST.get("link", "").strip() or None
        ordem = int(request.POST.get("ordem", 0) or 0)
        foto = request.FILES.get("imagem")

        if not titulo:
            messages.error(request, "Título é obrigatório.")
            return redirect("portal:gestao_banner_novo")

        if not foto:
            messages.error(request, "Imagem é obrigatória.")
            return redirect("portal:gestao_banner_novo")

        url_imagem = salvar_foto_upload(foto)

        # SQL puro: INSERT na tabela banner_publicacao
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO banner_publicacao "
                "(titulo, descricao, url_imagem, link, ordem, ativo, dt_criacao) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                [titulo, descricao, url_imagem, link, ordem, True, timezone.now()],
            )
        messages.success(request, "Banner criado com sucesso!")
        return redirect("portal:gestao_banners")
    return render(request, "portal/gestao/banner_form.html", {"banner": None})


@perfis("GES")
@require_http_methods(["GET", "POST"])
def gestao_banner_editar(request, pk):
    # SQL puro: SELECT banner por ID
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_banner, titulo, descricao, url_imagem, link, "
            "ordem, ativo, dt_criacao "
            "FROM banner_publicacao WHERE id_banner = %s",
            [pk],
        )
        row = cursor.fetchone()
    if not row:
        raise Http404()

    banner = SimpleNamespace(
        id_banner=row[0], pk=row[0], titulo=row[1], descricao=row[2],
        url_imagem=row[3], link=row[4], ordem=row[5],
        ativo=row[6], dt_criacao=row[7],
    )

    if request.method == "POST":
        titulo = request.POST.get("titulo", "").strip() or banner.titulo
        descricao = request.POST.get("descricao", "").strip() or None
        link = request.POST.get("link", "").strip() or None
        ordem = int(request.POST.get("ordem", 0) or 0)

        url_imagem = banner.url_imagem
        foto = request.FILES.get("imagem")
        if foto:
            url_imagem = salvar_foto_upload(foto)

        # SQL puro: UPDATE banner_publicacao
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE banner_publicacao SET titulo = %s, descricao = %s, "
                "url_imagem = %s, link = %s, ordem = %s "
                "WHERE id_banner = %s",
                [titulo, descricao, url_imagem, link, ordem, pk],
            )
        messages.success(request, "Banner atualizado!")
        return redirect("portal:gestao_banners")
    return render(request, "portal/gestao/banner_form.html", {"banner": banner})


@perfis("GES")
@require_http_methods(["POST"])
def gestao_banner_excluir(request, pk):
    # SQL puro: verifica existência e DELETE do banner
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_banner FROM banner_publicacao WHERE id_banner = %s", [pk]
        )
        if not cursor.fetchone():
            raise Http404()
        cursor.execute(
            "DELETE FROM banner_publicacao WHERE id_banner = %s", [pk]
        )
    messages.info(request, "Banner excluído.")
    return redirect("portal:gestao_banners")
