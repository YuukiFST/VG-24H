"""
views_gestao.py — Views de gestao (painel administrativo — Portal VG 24H)

Este modulo atende as rotas do painel administrativo, acessiveis
principalmente por gestores (GES). Bairros tambem sao acessiveis
para colaboradores (COL).

As operacoes disponiveis sao CRUD completo para cada entidade:
- Categorias de servico: listar, criar, editar
- Servicos: listar, criar, editar, desativar (soft delete)
- Bairros: listar, criar, editar, desativar, reativar
- Colaboradores: listar, criar, ativar/desativar (toggle)
- Banners: listar, criar, editar, excluir, reordenar
- Estatisticas: visualizar view SQL materializada

Todas as operacoes usam SQL puro (cursor.execute()) em vez de Django ORM.
Os models existem apenas para formularios (ModelChoiceField precisa de
queryset do ORM para validar FKs) e metodos utilitarios. Nenhuma view
chama form.save() — os dados sao extraidos de cleaned_data e inseridos
manualmente via SQL.
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

from portal import db
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

# ------------------------------------------------------------------
# Servico — Criar (GET/POST /gestao/servicos/novo/)
# ------------------------------------------------------------------

@perfis("GES")
@require_http_methods(["GET", "POST"])
def gestao_servico_novo(request):
    """Cria um novo servico (pagina dedicada, sem modal)."""
    if request.method == "POST":
        form = ServicoForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO servico (nome, descricao, ativo, id_categoria, "
                    "prazo_amarelo_dias, prazo_vermelho_dias) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    [
                        d["nome"], d.get("descricao"), True,
                        d["id_categoria"].pk,
                        d["prazo_amarelo_dias"],
                        d["prazo_vermelho_dias"],
                    ],
                )
            messages.success(request, "Servico criado.")
            return redirect("portal:gestao_servicos")

    form = ServicoForm()
    categorias = db.listar_categorias_ativas()
    return render(
        request,
        "portal/gestao/servico_novo.html",
        {"form": form, "categorias": categorias},
    )


# ------------------------------------------------------------------
# Colaborador — Criar (GET/POST /gestao/colaboradores/novo/)
# ------------------------------------------------------------------

@perfis("GES")
@require_http_methods(["GET", "POST"])
def gestao_colaborador_novo(request):
    """Cria um novo colaborador (pagina dedicada, sem modal)."""
    if request.method == "POST":
        form = ColaboradorNovoForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data

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
                messages.error(request, "E-mail ou CPF ja existe.")
            else:
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
                messages.success(request, "Colaborador criado. Deve trocar a senha no 1o acesso.")
            return redirect("portal:gestao_colaboradores")

    form = ColaboradorNovoForm()
    return render(
        request,
        "portal/gestao/colaborador_novo.html",
        {"form": form},
    )


# ------------------------------------------------------------------
# Estatisticas (GET /gestao/estatisticas/)
# ------------------------------------------------------------------

@perfis("GES")
def gestao_estatisticas(request):
    """Exibe estatisticas via view SQL materializada.

    Consulta vw_estatisticas_chamados, criada no script 05_views.sql.
    Essa view usa JOIN LATERAL para buscar o ultimo status de cada
    chamado e agrupa por categoria e bairro.

    Se a view SQL ainda nao existir no banco (ProgrammingError),
    retorna lista vazia em vez de erro 500.
    """
    rows = []
    try:
        with connection.cursor() as c:
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


# ------------------------------------------------------------------
# Categorias (GET/POST /gestao/categorias/ e /gestao/categorias/<pk>/editar/)
# ------------------------------------------------------------------

@perfis("GES")
@require_http_methods(["GET", "POST"])
def gestao_categorias(request):
    """Lista categorias ativas e cria novas.

    Categorias agrupam servicos por area (ex: "Infraestrutura").
    Cada categoria pertence a uma secretaria. Como o sistema so tem
    uma secretaria (VG 24H), busca com LIMIT 1.

    O formulario usa ModelForm (CategoriaForm), mas o save() nunca
    eh chamado. Os dados sao extraidos de cleaned_data e inseridos
    via INSERT SQL puro.
    """
    if request.method == "POST":
        form = CategoriaForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            with connection.cursor() as cursor:
                cursor.execute("SELECT id_secretaria FROM secretaria LIMIT 1")
                sec_row = cursor.fetchone()
                sec_id = sec_row[0] if sec_row else None

                cursor.execute(
                    "INSERT INTO categoria_servico (nome, descricao, ativo, id_secretaria) "
                    "VALUES (%s, %s, %s, %s)",
                    [d["nome"], d.get("descricao"), True, sec_id],
                )
            messages.success(request, "Categoria criada.")
        return redirect("portal:gestao_categorias")

    form = CategoriaForm()
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
    """Edita uma categoria existente.

    No GET, busca a categoria por ID e monta um objeto CategoriaServico
    para preencher o ModelForm (precisa de instance). No POST, extrai
    os dados validados e faz UPDATE SQL puro.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_categoria, nome, descricao, ativo, id_secretaria "
            "FROM categoria_servico WHERE id_categoria = %s",
            [pk],
        )
        row = cursor.fetchone()
    if not row:
        raise Http404()

    # Monta objeto ORM para preencher o ModelForm no template.
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


# ------------------------------------------------------------------
# Servicos (GET/POST /gestao/servicos/, editar, desativar)
# ------------------------------------------------------------------

@perfis("GES")
@require_http_methods(["GET", "POST"])
def gestao_servicos(request):
    """Lista servicos ativos e cria novos.

    Servicos sao os itens que o cidadao seleciona ao abrir chamado
    (ex: "Tapa-buraco"). Cada servico pertence a uma categoria e
    tem prazos para o semaforo (amarelo/vermelho em dias).
    """
    if request.method == "POST":
        form = ServicoForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO servico (nome, descricao, ativo, id_categoria, "
                    "prazo_amarelo_dias, prazo_vermelho_dias) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    [
                        d["nome"], d.get("descricao"), True,
                        d["id_categoria"].pk,
                        d["prazo_amarelo_dias"],
                        d["prazo_vermelho_dias"],
                    ],
                )
            messages.success(request, "Servico criado.")
        return redirect("portal:gestao_servicos")

    form = ServicoForm()
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
    categorias = db.listar_categorias_ativas()
    return render(
        request,
        "portal/gestao/servicos.html",
        {"form": form, "lista": lista, "categorias": categorias},
    )


@perfis("GES")
@require_http_methods(["GET", "POST"])
def gestao_servico_edit(request, pk):
    """Edita um servico existente (incluindo prazos do semaforo)."""
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
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE servico SET nome = %s, descricao = %s, "
                    "id_categoria = %s, "
                    "prazo_amarelo_dias = %s, prazo_vermelho_dias = %s "
                    "WHERE id_servico = %s",
                    [
                        d["nome"], d.get("descricao"),
                        d["id_categoria"].pk,
                        d["prazo_amarelo_dias"], d["prazo_vermelho_dias"],
                        pk,
                    ],
                )
            messages.success(request, "Servico atualizado.")
            return redirect("portal:gestao_servicos")
    else:
        form = ServicoForm(instance=obj)

    return render(
        request,
        "portal/gestao/servico_form.html",
        {"form": form, "srv": obj, "categorias": CategoriaServico.objects.all()},
    )


# ------------------------------------------------------------------
# Bairros (GET/POST /gestao/bairros/, editar, desativar, reativar)
# ------------------------------------------------------------------

@perfis("COL", "GES")
@require_http_methods(["GET", "POST"])
def gestao_bairros(request):
    """Lista todos os bairros (ativos e inativos) e cria novos.

    Colaboradores tambem podem gerenciar bairros (alem de gestores).
    O campo regiao eh um combobox com valores predefinidos
    (Central, Norte, Sul, etc.) para evitar inconsistencias.
    """
    if request.method == "POST":
        form = BairroForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO bairro (nome_bairro, cep, regiao, ativo) "
                    "VALUES (%s, %s, %s, %s)",
                    [d["nome_bairro"], d["cep"], d.get("regiao"), True],
                )
            messages.success(request, "Bairro criado.")
            return redirect("portal:gestao_bairros")
        else:
            messages.error(request, "Corrija os erros no formulario.")
            mostrar_form = True

    form = locals().get("form", BairroForm())
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_bairro, nome_bairro, cep, regiao, ativo "
            "FROM bairro ORDER BY nome_bairro"
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
        {"form": form, "lista": lista, "mostrar_form": locals().get("mostrar_form", False)},
    )


@perfis("COL", "GES")
@require_http_methods(["GET", "POST"])
def gestao_bairro_edit(request, pk):
    """Edita um bairro existente. Permite alterar nome, CEP, regiao e ativo."""
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
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE bairro SET nome_bairro = %s, cep = %s, regiao = %s, "
                    "ativo = %s WHERE id_bairro = %s",
                    [d["nome_bairro"], d["cep"], d.get("regiao"), d.get("ativo", True), pk],
                )
            messages.success(request, "Bairro atualizado.")
            return redirect("portal:gestao_bairros")
    else:
        form = BairroForm(instance=obj)

    return render(
        request,
        "portal/gestao/bairro_form.html",
        {"form": form, "bairro": obj},
    )


# ------------------------------------------------------------------
# Colaboradores (GET/POST /gestao/colaboradores/, toggle)
# ------------------------------------------------------------------

@perfis("GES")
@require_http_methods(["GET", "POST"])
def gestao_colaboradores(request):
    """Lista colaboradores e cria novos.

    Colaboradores sao servidores com perfil="COL". Ao criar, o gestor
    define uma senha provisoria que o colaborador deve trocar no primeiro
    acesso (senha_temporaria="1").

    Antes de inserir, verifica se email ou CPF ja existem no banco.
    A verificacao no Python (em vez de deixar o banco retornar erro de
    UNIQUE constraint) permite mostrar mensagem amigavel ao usuario.

    A senha eh armazenada como hash bcrypt (via make_password) —
    a senha original nunca fica no banco.
    """
    if request.method == "POST":
        form = ColaboradorNovoForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data

            # Verifica duplicidade de email ou CPF.
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
                messages.error(request, "E-mail ou CPF ja existe.")
            else:
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
                            "1",       # Flag: senha temporaria
                            "COL",     # Perfil: colaborador
                            True,
                            timezone.now(),
                            sec_id,
                        ],
                    )
                messages.success(request, "Colaborador criado. Deve trocar a senha no 1o acesso.")
        return redirect("portal:gestao_colaboradores")

    form = ColaboradorNovoForm()
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
    """Ativa ou desativa um colaborador (toggle do campo ativo)."""
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
def gestao_colaborador_reset_senha(request, pk):
    """Redefine a senha de um colaborador com senha provisoria."""
    nova = request.POST.get("nova_senha_provisoria", "").strip()
    if len(nova) < 6:
        messages.error(request, "Senha deve ter no minimo 6 caracteres.")
        return redirect("portal:gestao_colaboradores")
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE servidor SET senha_hash = %s, senha_temporaria = '1' "
            "WHERE id_servidor = %s AND perfil = 'COL'",
            [make_password(nova), pk],
        )
        if cursor.rowcount == 0:
            raise Http404
    messages.success(request, "Senha redefinida com sucesso! Colaborador deve trocar no proximo acesso.")
    return redirect("portal:gestao_colaboradores")


# ------------------------------------------------------------------
# Acoes rapidas (desativar servico, desativar/reativar bairro)
# ------------------------------------------------------------------

@perfis("GES")
@require_http_methods(["POST"])
def gestao_servico_desativar(request, pk):
    """Desativa um servico (soft delete: ativo=FALSE).

    Servicos desativados nao aparecem no formulario de novo chamado,
    mas chamados antigos que usam este servico mantem a referencia.
    """
    with connection.cursor() as cursor:
        cursor.execute("SELECT id_servico FROM servico WHERE id_servico = %s", [pk])
        if not cursor.fetchone():
            raise Http404()
        cursor.execute("UPDATE servico SET ativo = FALSE WHERE id_servico = %s", [pk])
    messages.info(request, "Servico inativado.")
    return redirect("portal:gestao_servicos")


@perfis("COL", "GES")
@require_http_methods(["POST"])
def gestao_bairro_desativar(request, pk):
    """Desativa um bairro (soft delete: ativo=FALSE)."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT id_bairro FROM bairro WHERE id_bairro = %s", [pk])
        if not cursor.fetchone():
            raise Http404()
        cursor.execute("UPDATE bairro SET ativo = FALSE WHERE id_bairro = %s", [pk])
    messages.info(request, "Bairro inativado.")
    return redirect("portal:gestao_bairros")


@perfis("COL", "GES")
@require_http_methods(["POST"])
def gestao_bairro_ativar(request, pk):
    """Reativa um bairro previamente desativado."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT id_bairro FROM bairro WHERE id_bairro = %s", [pk])
        if not cursor.fetchone():
            raise Http404()
        cursor.execute("UPDATE bairro SET ativo = TRUE WHERE id_bairro = %s", [pk])
    messages.info(request, "Bairro reativado.")
    return redirect("portal:gestao_bairros")


# ------------------------------------------------------------------
# Banners (CRUD completo + reordenacao)
# ------------------------------------------------------------------

@perfis("GES")
def gestao_banners(request):
    """Lista todos os banners ordenados por posicao no carrossel."""
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
    """Cria um novo banner com upload de imagem.

    A ordem eh auto-incrementada (MAX + 1), colocando o banner no final
    do carrossel. A imagem pode ir para Cloudinary ou filesystem local.
    Tamanho maximo: 5MB. Resolucao recomendada: 1200x400px (3:1).
    """
    if request.method == "POST":
        titulo = request.POST.get("titulo", "").strip()
        descricao = request.POST.get("descricao", "").strip() or None
        link = request.POST.get("link", "").strip() or None
        foto = request.FILES.get("imagem")

        if not titulo:
            messages.error(request, "Titulo e obrigatorio.")
            return redirect("portal:gestao_banner_novo")
        if not foto:
            messages.error(request, "Imagem e obrigatoria.")
            return redirect("portal:gestao_banner_novo")
        if foto.size > 5 * 1024 * 1024:
            messages.error(request, "A imagem excede o tamanho maximo de 5MB.")
            return redirect("portal:gestao_banner_novo")

        url_imagem = salvar_foto_upload(foto)

        with connection.cursor() as cursor:
            # Auto-incremento: nova ordem = MAX(ordem) + 1.
            cursor.execute("SELECT COALESCE(MAX(ordem), -1) + 1 FROM banner_publicacao")
            ordem = cursor.fetchone()[0]
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
    """Edita um banner existente. Permite alterar titulo, descricao,
    link, ordem e substituir a imagem."""
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
            if foto.size > 5 * 1024 * 1024:
                messages.error(request, "A imagem excede o tamanho maximo de 5MB.")
                return redirect("portal:gestao_banner_editar", pk=pk)
            url_imagem = salvar_foto_upload(foto)

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
    """Exclui permanentemente um banner (DELETE fisico, nao soft delete)."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT id_banner FROM banner_publicacao WHERE id_banner = %s", [pk])
        if not cursor.fetchone():
            raise Http404()
        cursor.execute("DELETE FROM banner_publicacao WHERE id_banner = %s", [pk])
    messages.info(request, "Banner excluido.")
    return redirect("portal:gestao_banners")


@perfis("GES")
@require_http_methods(["POST"])
def gestao_banner_reordenar(request, pk):
    """Move um banner para cima ou para baixo no carrossel.

    A direcao vem como campo oculto no formulario (-1 para cima,
    +1 para baixo). A funcao busca o vizinho na direcao indicada
    e troca as ordens entre os dois banners (swap).
    """
    direcao = int(request.POST.get("direcao", 0))

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_banner, ordem FROM banner_publicacao WHERE id_banner = %s", [pk]
        )
        row = cursor.fetchone()
    if not row:
        raise Http404()

    ordem_atual = row[1]

    # Busca o vizinho na direcao indicada.
    with connection.cursor() as cursor:
        if direcao == -1:
            cursor.execute(
                "SELECT id_banner, ordem FROM banner_publicacao "
                "WHERE ordem < %s ORDER BY ordem DESC LIMIT 1",
                [ordem_atual],
            )
        elif direcao == 1:
            cursor.execute(
                "SELECT id_banner, ordem FROM banner_publicacao "
                "WHERE ordem > %s ORDER BY ordem ASC LIMIT 1",
                [ordem_atual],
            )
        else:
            return redirect("portal:gestao_banners")

        vizinho = cursor.fetchone()

    # Swap: troca as ordens entre o banner e o vizinho.
    if vizinho:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE banner_publicacao SET ordem = %s WHERE id_banner = %s",
                [ordem_atual, vizinho[0]],
            )
            cursor.execute(
                "UPDATE banner_publicacao SET ordem = %s WHERE id_banner = %s",
                [vizinho[1], pk],
            )

    return redirect("portal:gestao_banners")
