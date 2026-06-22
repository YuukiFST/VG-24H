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

from django.contrib import messages
from django.db import connection
from django.db.utils import ProgrammingError
from django.http import Http404
from django.shortcuts import redirect, render
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
    CategoriaServico,
    Servico,
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
            db.inserir_servico(d["nome"], d.get("descricao"), d["id_categoria"].pk)
            messages.success(request, "Serviço criado.")
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
            ja_existe = db.existe_email_ou_cpf("servidor", d["email"].lower(), d["cpf"])
            if ja_existe:
                messages.error(request, "E-mail ou CPF já existe.")
            else:
                db.inserir_colaborador(d)
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
            db.inserir_categoria(d["nome"], d.get("descricao"))
            messages.success(request, "Categoria criada.")
        return redirect("portal:gestao_categorias")

    form = CategoriaForm()
    lista = db.listar_categorias_todas()
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
            db.atualizar_categoria(pk, d["nome"], d.get("descricao"))
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
            db.inserir_servico(d["nome"], d.get("descricao"), d["id_categoria"].pk)
            messages.success(request, "Serviço criado.")
        return redirect("portal:gestao_servicos")

    form = ServicoForm()
    lista = db.listar_servicos_com_categoria()
    categorias = db.listar_categorias_ativas()
    return render(
        request,
        "portal/gestao/servicos.html",
        {"form": form, "lista": lista, "categorias": categorias},
    )


@perfis("GES")
@require_http_methods(["GET", "POST"])
def gestao_servico_edit(request, pk):
    """Edita um servico existente."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_servico, nome, descricao, ativo, id_categoria "
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
    obj._state.adding = False

    if request.method == "POST":
        form = ServicoForm(request.POST, instance=obj)
        if form.is_valid():
            d = form.cleaned_data
            db.atualizar_servico(pk, d["nome"], d.get("descricao"), d["id_categoria"].pk)
            messages.success(request, "Serviço atualizado.")
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
            db.inserir_bairro(d["nome_bairro"], d["cep"], d.get("regiao"))
            messages.success(request, "Bairro criado.")
            return redirect("portal:gestao_bairros")
        else:
            messages.error(request, "Corrija os erros no formulário.")
            mostrar_form = True

    form = locals().get("form", BairroForm())
    lista = db.listar_bairros_todos()
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
            db.atualizar_bairro(pk, d["nome_bairro"], d["cep"], d.get("regiao"), d.get("ativo", True))
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
            ja_existe = db.existe_email_ou_cpf("servidor", d["email"].lower(), d["cpf"])

            if ja_existe:
                messages.error(request, "E-mail ou CPF já existe.")
            else:
                db.inserir_colaborador(d)
                messages.success(request, "Colaborador criado. Deve trocar a senha no 1o acesso.")
        return redirect("portal:gestao_colaboradores")

    form = ColaboradorNovoForm()
    lista = db.listar_colaboradores()
    return render(
        request,
        "portal/gestao/colaboradores.html",
        {"form": form, "lista": lista},
    )


@perfis("GES")
@require_http_methods(["POST"])
def gestao_colaborador_toggle(request, pk):
    result = db.alternar_colaborador_ativo(pk)
    if result is None:
        raise Http404()
    nome, status = result
    messages.success(request, f"Colaborador {nome} {status}.")
    return redirect("portal:gestao_colaboradores")


@perfis("GES")
@require_http_methods(["POST"])
def gestao_colaborador_reset_senha(request, pk):
    """Redefine a senha de um colaborador com senha provisoria."""
    nova = request.POST.get("nova_senha_provisoria", "").strip()
    if len(nova) < 6:
        messages.error(request, "Senha deve ter no mínimo 6 caracteres.")
        return redirect("portal:gestao_colaboradores")
    if not db.resetar_senha_colaborador(pk, nova):
        raise Http404()
    messages.success(request, "Senha redefinida com sucesso! Colaborador deve trocar no proximo acesso.")
    return redirect("portal:gestao_colaboradores")


# ------------------------------------------------------------------
# Acoes rapidas (desativar servico, desativar/reativar bairro)
# ------------------------------------------------------------------

@perfis("GES")
@require_http_methods(["POST"])
def gestao_servico_desativar(request, pk):
    if not db.desativar_servico(pk):
        raise Http404()
    messages.info(request, "Serviço inativado.")
    return redirect("portal:gestao_servicos")


@perfis("COL", "GES")
@require_http_methods(["POST"])
def gestao_bairro_desativar(request, pk):
    if not db.desativar_bairro(pk):
        raise Http404()
    messages.info(request, "Bairro inativado.")
    return redirect("portal:gestao_bairros")


@perfis("COL", "GES")
@require_http_methods(["POST"])
def gestao_bairro_ativar(request, pk):
    if not db.ativar_bairro(pk):
        raise Http404()
    messages.info(request, "Bairro reativado.")
    return redirect("portal:gestao_bairros")


# ------------------------------------------------------------------
# Banners (CRUD completo + reordenacao)
# ------------------------------------------------------------------

@perfis("GES")
def gestao_banners(request):
    banners = db.listar_banners_todos()
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
            messages.error(request, "Título é obrigatório.")
            return redirect("portal:gestao_banner_novo")
        if not foto:
            messages.error(request, "Imagem é obrigatória.")
            return redirect("portal:gestao_banner_novo")
        if foto.size > 5 * 1024 * 1024:
            messages.error(request, "A imagem excede o tamanho máximo de 5MB.")
            return redirect("portal:gestao_banner_novo")

        url_imagem = salvar_foto_upload(foto)

        db.inserir_banner(titulo, descricao, url_imagem, link)
        messages.success(request, "Banner criado com sucesso!")
        return redirect("portal:gestao_banners")

    return render(request, "portal/gestao/banner_form.html", {"banner": None})


@perfis("GES")
@require_http_methods(["GET", "POST"])
def gestao_banner_editar(request, pk):
    banner = db.buscar_banner(pk)
    if not banner:
        raise Http404()

    if request.method == "POST":
        titulo = request.POST.get("titulo", "").strip() or banner.titulo
        descricao = request.POST.get("descricao", "").strip() or None
        link = request.POST.get("link", "").strip() or None
        ordem = int(request.POST.get("ordem", 0) or 0)

        url_imagem = banner.url_imagem
        foto = request.FILES.get("imagem")
        if foto:
            if foto.size > 5 * 1024 * 1024:
                messages.error(request, "A imagem excede o tamanho máximo de 5MB.")
                return redirect("portal:gestao_banner_editar", pk=pk)
            url_imagem = salvar_foto_upload(foto)

        db.atualizar_banner(pk, titulo, descricao, url_imagem, link, ordem)
        messages.success(request, "Banner atualizado!")
        return redirect("portal:gestao_banners")

    return render(request, "portal/gestao/banner_form.html", {"banner": banner})


@perfis("GES")
@require_http_methods(["POST"])
def gestao_banner_excluir(request, pk):
    if not db.excluir_banner(pk):
        raise Http404()
    messages.info(request, "Banner excluído.")
    return redirect("portal:gestao_banners")


@perfis("GES")
@require_http_methods(["POST"])
def gestao_banner_reordenar(request, pk):
    direcao = int(request.POST.get("direcao", 0))
    db.reordenar_banner(pk, direcao)
    return redirect("portal:gestao_banners")
