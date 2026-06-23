"""
views_gestao.py — views do painel administrativo (gestao do Portal VG 24H)

Anotacao minha: aqui ficam as rotas do painel admin. Quase tudo eh so do
gestor (GES), mas BAIRROS o colaborador (COL) tambem consegue mexer.

O que tem aqui eh basicamente CRUD de cada coisa:
- Categorias de servico: listar, criar, editar
- Servicos: listar, criar, editar, desativar (soft delete, nao apaga)
- Bairros: listar, criar, editar, desativar, reativar
- Colaboradores: listar, criar, ativar/desativar (toggle)
- Banners: listar, criar, editar, excluir, reordenar
- Estatisticas: so mostra uma view SQL pronta

Importante lembrar: eu uso SQL puro (cursor.execute()) em tudo, nao o ORM
do Django. Os models so existem pros formularios (o ModelChoiceField precisa
de queryset do ORM pra validar as FKs) e uns metodos uteis. NENHUMA view aqui
chama form.save() -> eu pego os dados do cleaned_data e insiro na mao via SQL.
"""

# imports do Django + os helpers/forms/models meus do portal
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
    """Cria um servico novo (pagina propria, sem ser modal)."""
    if request.method == "POST":
        # POST: valido o form, pego os dados do cleaned_data e insiro via SQL.
        # repara que uso d["id_categoria"].pk -> o form da o objeto, eu quero o id
        form = ServicoForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            db.inserir_servico(d["nome"], d.get("descricao"), d["id_categoria"].pk)
            messages.success(request, "Serviço criado.")
            return redirect("portal:gestao_servicos")

    # GET (ou POST invalido): mostro o form vazio + as categorias pro select
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
    """Cria um colaborador novo (pagina propria, sem modal)."""
    if request.method == "POST":
        form = ColaboradorNovoForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            # antes de inserir, confiro se ja tem alguem com esse email ou cpf
            # (email em lower pra nao duplicar por causa de maiuscula)
            ja_existe = db.existe_email_ou_cpf("servidor", d["email"].lower(), d["cpf"])
            if ja_existe:
                # ja existe -> aviso e nao insiro
                messages.error(request, "E-mail ou CPF já existe.")
            else:
                # ok, insiro. ele ja nasce tendo que trocar a senha no 1o acesso
                db.inserir_colaborador(d)
                messages.success(request, "Colaborador criado. Deve trocar a senha no 1o acesso.")
            return redirect("portal:gestao_colaboradores")

    # GET: so o form vazio
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
    """Mostra estatisticas lendo uma view SQL pronta.

    Eu so faco SELECT na vw_estatisticas_chamados (que eu criei no script
    05_views.sql). Essa view usa JOIN LATERAL pra pegar o ultimo status de
    cada chamado e agrupa por categoria e bairro.

    Se a view ainda nao foi criada no banco (da ProgrammingError), eu deixo
    a lista vazia em vez de quebrar com 500.
    """
    rows = []
    # tento ler a view; se ela nao existir, o except segura e fica rows=[]
    try:
        with connection.cursor() as c:
            c.execute("SELECT * FROM vw_estatisticas_chamados ORDER BY categoria, bairro")
            # pego os nomes das colunas e monto uma lista de dicts (col->valor)
            # pra ficar facil de usar no template
            cols = [d[0] for d in c.description]
            rows = [dict(zip(cols, r, strict=True)) for r in c.fetchall()]
    except ProgrammingError:
        pass

    # cards do topo: total, concluidos e em andamento eu somo direto das rows
    # (a vw ja agrupa por categoria/bairro/status, entao e so somar total_chamados).
    # sigla CO = concluido; AB/EA/EE = em andamento (mesma divisao que uso nas triggers).
    total = sum(r["total_chamados"] for r in rows)
    concluidos = sum(r["total_chamados"] for r in rows if r["sigla_status"] == "CO")
    em_andamento = sum(r["total_chamados"] for r in rows if r["sigla_status"] in ("AB", "EA", "EE"))

    # criticos (> 10 dias em aberto) nao tem na vw, entao conto a parte: chamados cujo
    # ultimo status nao e CO/CA e que foram abertos ha mais de 10 dias. mesmo padrao de
    # subconsulta do ultimo status que uso no resto do projeto. guardo num try proprio.
    criticos = 0
    try:
        with connection.cursor() as c:
            c.execute(
                "SELECT COUNT(*) FROM chamado ch WHERE ("
                "  SELECT sc.sigla FROM historico_chamado hc "
                "  JOIN status_chamado sc ON sc.id_status = hc.id_status "
                "  WHERE hc.id_chamado = ch.id_chamado "
                "  ORDER BY hc.dt_alteracao DESC LIMIT 1"
                ") NOT IN ('CO', 'CA') "
                "AND ch.dt_abertura < NOW() - INTERVAL '10 days'"
            )
            criticos = c.fetchone()[0] or 0
    except ProgrammingError:
        pass

    stats = {
        "total": total,
        "concluidos": concluidos,
        "em_andamento": em_andamento,
        "criticos": criticos,
    }
    return render(
        request,
        "portal/gestao/estatisticas.html",
        {"rows": rows, "stats": stats},
    )


# ------------------------------------------------------------------
# Categorias (GET/POST /gestao/categorias/ e /gestao/categorias/<pk>/editar/)
# ------------------------------------------------------------------

@perfis("GES")
@require_http_methods(["GET", "POST"])
def gestao_categorias(request):
    """Lista as categorias e cria novas (tudo na mesma pagina).

    Categoria agrupa servicos por area (ex: "Infraestrutura"). Cada uma
    pertence a uma secretaria, mas como so tem uma (VG 24H) eu busco com
    LIMIT 1 la no db.

    Uso o CategoriaForm (ModelForm) so pra validar; nunca chamo save().
    Pego do cleaned_data e faco o INSERT na mao.
    """
    if request.method == "POST":
        # POST = criar. valido, insiro e mando a mensagem. repara que o redirect
        # ta fora do if, entao mesmo form invalido recarrega a pagina (PRG)
        form = CategoriaForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            db.inserir_categoria(d["nome"], d.get("descricao"))
            messages.success(request, "Categoria criada.")
        return redirect("portal:gestao_categorias")

    # GET: form vazio + a lista de todas as categorias pra tabela
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
    """Edita uma categoria que ja existe.

    Truque aqui: como nao uso ORM pra buscar, eu leio a linha via SQL e
    monto na mao um objeto CategoriaServico so pra dar de instance pro
    ModelForm (o form precisa de uma instance pra editar). No POST faco
    o UPDATE via SQL puro.
    """
    # busco a categoria pelo id; se nao existe -> 404
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_categoria, nome, descricao, ativo, id_secretaria "
            "FROM categoria_servico WHERE id_categoria = %s",
            [pk],
        )
        row = cursor.fetchone()
    if not row:
        raise Http404()

    # monto o objeto ORM na mao com os dados da linha. o _state.adding = False
    # eh pra ele se comportar como "ja existe" e nao como objeto novo
    obj = CategoriaServico()
    obj.id_categoria = row[0]
    obj.nome = row[1]
    obj.descricao = row[2]
    obj.ativo = row[3]
    obj.id_secretaria_id = row[4]
    obj._state.adding = False

    if request.method == "POST":
        # valido o form ja amarrado na instance e faco o UPDATE
        form = CategoriaForm(request.POST, instance=obj)
        if form.is_valid():
            d = form.cleaned_data
            db.atualizar_categoria(pk, d["nome"], d.get("descricao"))
            messages.success(request, "Categoria atualizada.")
            return redirect("portal:gestao_categorias")
    else:
        # GET: form ja preenchido com os dados atuais
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
    """Lista os servicos e cria novos (mesma pagina).

    Servico eh o que o cidadao escolhe quando abre chamado (ex: "Tapa-buraco").
    Cada um fica numa categoria e tem prazos pro semaforo (amarelo/vermelho
    em dias).
    """
    if request.method == "POST":
        # mesma logica do servico_novo, so que aqui a lista ja vem junto
        form = ServicoForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            db.inserir_servico(d["nome"], d.get("descricao"), d["id_categoria"].pk)
            messages.success(request, "Serviço criado.")
        return redirect("portal:gestao_servicos")

    # GET: form vazio + lista de servicos (com a categoria) + categorias pro select
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
    """Edita um servico que ja existe (mesmo esquema da categoria_edit)."""
    # busco o servico pelo id; nao achou -> 404
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_servico, nome, descricao, ativo, id_categoria "
            "FROM servico WHERE id_servico = %s",
            [pk],
        )
        row = cursor.fetchone()
    if not row:
        raise Http404()

    # monto o objeto Servico na mao pra dar de instance pro form
    obj = Servico()
    obj.id_servico = row[0]
    obj.nome = row[1]
    obj.descricao = row[2]
    obj.ativo = row[3]
    obj.id_categoria_id = row[4]
    obj._state.adding = False

    if request.method == "POST":
        # valido e faco o UPDATE via SQL (de novo o .pk pra pegar o id da categoria)
        form = ServicoForm(request.POST, instance=obj)
        if form.is_valid():
            d = form.cleaned_data
            db.atualizar_servico(pk, d["nome"], d.get("descricao"), d["id_categoria"].pk)
            messages.success(request, "Serviço atualizado.")
            return redirect("portal:gestao_servicos")
    else:
        # GET: form preenchido
        form = ServicoForm(instance=obj)

    # aqui eu mando as categorias via ORM mesmo (CategoriaServico.objects.all())
    # porque o template precisa montar o select
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
    """Lista os bairros (ativos e inativos) e cria novos.

    Aqui o COL tambem pode mexer, nao so o GES. O campo regiao eh um combobox
    com valores fixos (Central, Norte, Sul...) pra ninguem escrever errado.
    """
    # comeco com form vazio e a flag pra reabrir o form fechada
    form = BairroForm()
    mostrar_form = False
    if request.method == "POST":
        form = BairroForm(request.POST)
        if form.is_valid():
            # valido OK: insiro e volto pra lista
            d = form.cleaned_data
            db.inserir_bairro(d["nome_bairro"], d["cep"], d.get("regiao"))
            messages.success(request, "Bairro criado.")
            return redirect("portal:gestao_bairros")
        # invalido: aviso e ligo a flag pra reabrir o form com os erros
        messages.error(request, "Corrija os erros no formulário.")
        mostrar_form = True

    # busco todos os bairros pra tabela e renderizo
    lista = db.listar_bairros_todos()
    return render(
        request,
        "portal/gestao/bairros.html",
        {"form": form, "lista": lista, "mostrar_form": mostrar_form},
    )


@perfis("COL", "GES")
@require_http_methods(["GET", "POST"])
def gestao_bairro_edit(request, pk):
    """Edita um bairro. Da pra mudar nome, CEP, regiao e o ativo."""
    # busco o bairro; nao achou -> 404
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id_bairro, nome_bairro, cep, regiao, ativo "
            "FROM bairro WHERE id_bairro = %s",
            [pk],
        )
        row = cursor.fetchone()
    if not row:
        raise Http404()

    # mesmo truque: monto o objeto na mao pra usar de instance no form
    obj = Bairro()
    obj.id_bairro = row[0]
    obj.nome_bairro = row[1]
    obj.cep = row[2]
    obj.regiao = row[3]
    obj.ativo = row[4]
    obj._state.adding = False

    if request.method == "POST":
        # valido e dou UPDATE. o ativo eu pego com default True caso nao venha
        form = BairroForm(request.POST, instance=obj)
        if form.is_valid():
            d = form.cleaned_data
            db.atualizar_bairro(pk, d["nome_bairro"], d["cep"], d.get("regiao"), d.get("ativo", True))
            messages.success(request, "Bairro atualizado.")
            return redirect("portal:gestao_bairros")
    else:
        # GET: form preenchido
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
    """Lista os colaboradores e cria novos (mesma pagina).

    Colaborador eh servidor com perfil="COL". Quando crio, eu defino uma
    senha provisoria que ele eh obrigado a trocar no 1o acesso (a flag
    senha_temporaria="1").

    Antes de inserir eu confiro no Python se email ou CPF ja existem. Faco
    no Python (em vez de deixar o banco estourar o UNIQUE) so pra conseguir
    mostrar uma mensagem bonitinha pro usuario.

    A senha vai pro banco como hash bcrypt (make_password) -> a senha
    original nunca fica salva.
    """
    if request.method == "POST":
        form = ColaboradorNovoForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data

            # confiro se ja tem esse email/cpf antes de inserir
            ja_existe = db.existe_email_ou_cpf("servidor", d["email"].lower(), d["cpf"])

            if ja_existe:
                # ja existe -> so aviso
                messages.error(request, "E-mail ou CPF já existe.")
            else:
                # insiro o colaborador novo
                db.inserir_colaborador(d)
                messages.success(request, "Colaborador criado. Deve trocar a senha no 1o acesso.")
        return redirect("portal:gestao_colaboradores")

    # GET: form vazio + lista de colaboradores pra tabela
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
    # liga/desliga o colaborador (ativo <-> inativo). o db ja faz a virada
    # e me devolve (nome, status) pra montar a mensagem
    result = db.alternar_colaborador_ativo(pk)
    if result is None:
        # nao achou o colaborador -> 404
        raise Http404()
    nome, status = result
    messages.success(request, f"Colaborador {nome} {status}.")
    return redirect("portal:gestao_colaboradores")


@perfis("GES")
@require_http_methods(["POST"])
def gestao_colaborador_reset_senha(request, pk):
    """Reseta a senha do colaborador, botando uma provisoria nova."""
    # pego a senha nova do POST e limpo os espacos
    nova = request.POST.get("nova_senha_provisoria", "").strip()
    # regra simples: minimo 6 caracteres
    if len(nova) < 6:
        messages.error(request, "Senha deve ter no mínimo 6 caracteres.")
        return redirect("portal:gestao_colaboradores")
    # se o db nao achar o colaborador (retorna falsy) -> 404
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
    # soft delete do servico (so marca inativo). se nao achar -> 404
    if not db.desativar_servico(pk):
        raise Http404()
    messages.info(request, "Serviço inativado.")
    return redirect("portal:gestao_servicos")


@perfis("COL", "GES")
@require_http_methods(["POST"])
def gestao_bairro_desativar(request, pk):
    # desativa o bairro (soft delete). nao achou -> 404
    if not db.desativar_bairro(pk):
        raise Http404()
    messages.info(request, "Bairro inativado.")
    return redirect("portal:gestao_bairros")


@perfis("COL", "GES")
@require_http_methods(["POST"])
def gestao_bairro_ativar(request, pk):
    # o contrario do de cima: reativa o bairro. nao achou -> 404
    if not db.ativar_bairro(pk):
        raise Http404()
    messages.info(request, "Bairro reativado.")
    return redirect("portal:gestao_bairros")


# ------------------------------------------------------------------
# Banners (CRUD completo + reordenacao)
# ------------------------------------------------------------------

@perfis("GES")
def gestao_banners(request):
    # so lista todos os banners pra tela de gerenciamento do carrossel
    banners = db.listar_banners_todos()
    return render(request, "portal/gestao/banners.html", {"banners": banners})


@perfis("GES")
@require_http_methods(["GET", "POST"])
def gestao_banner_novo(request):
    """Cria um banner novo com upload de imagem.

    A ordem eu deixo o db calcular (MAX + 1), entao o banner novo cai no fim
    do carrossel. A imagem pode ir pro Cloudinary ou pro disco local. Limite
    de 5MB. Resolucao recomendada 1200x400 (3:1).
    """
    if request.method == "POST":
        # leio os campos do POST. nos opcionais, se ficar vazio eu viro None
        titulo = request.POST.get("titulo", "").strip()
        descricao = request.POST.get("descricao", "").strip() or None
        link = request.POST.get("link", "").strip() or None
        foto = request.FILES.get("imagem")

        # validacoes na mao (aqui nao uso form): titulo obrigatorio...
        if not titulo:
            messages.error(request, "Título é obrigatório.")
            return redirect("portal:gestao_banner_novo")
        # ...imagem obrigatoria...
        if not foto:
            messages.error(request, "Imagem é obrigatória.")
            return redirect("portal:gestao_banner_novo")
        # ...e nao pode passar de 5MB
        if foto.size > 5 * 1024 * 1024:
            messages.error(request, "A imagem excede o tamanho máximo de 5MB.")
            return redirect("portal:gestao_banner_novo")

        # passou em tudo: salvo o arquivo e pego a URL final
        url_imagem = salvar_foto_upload(foto)

        # insiro o banner com a URL da imagem e volto pra lista
        db.inserir_banner(titulo, descricao, url_imagem, link)
        messages.success(request, "Banner criado com sucesso!")
        return redirect("portal:gestao_banners")

    # GET: form de banner vazio (banner=None pro template saber que eh criacao)
    return render(request, "portal/gestao/banner_form.html", {"banner": None})


@perfis("GES")
@require_http_methods(["GET", "POST"])
def gestao_banner_editar(request, pk):
    # busco o banner; nao existe -> 404
    banner = db.buscar_banner(pk)
    if not banner:
        raise Http404()

    if request.method == "POST":
        # titulo: se vier vazio eu mantenho o que ja era (banner.titulo).
        # descricao e link viram None se ficarem vazios. ordem como int
        titulo = request.POST.get("titulo", "").strip() or banner.titulo
        descricao = request.POST.get("descricao", "").strip() or None
        link = request.POST.get("link", "").strip() or None
        ordem = int(request.POST.get("ordem", 0) or 0)

        # por padrao mantenho a imagem atual. so troco se mandaram um arquivo novo
        url_imagem = banner.url_imagem
        foto = request.FILES.get("imagem")
        if foto:
            # mesma regra de 5MB; se passar, nem salvo e volto
            if foto.size > 5 * 1024 * 1024:
                messages.error(request, "A imagem excede o tamanho máximo de 5MB.")
                return redirect("portal:gestao_banner_editar", pk=pk)
            url_imagem = salvar_foto_upload(foto)

        # dou o UPDATE com tudo e volto pra lista
        db.atualizar_banner(pk, titulo, descricao, url_imagem, link, ordem)
        messages.success(request, "Banner atualizado!")
        return redirect("portal:gestao_banners")

    # GET: mostro o form ja com o banner carregado
    return render(request, "portal/gestao/banner_form.html", {"banner": banner})


@perfis("GES")
@require_http_methods(["POST"])
def gestao_banner_excluir(request, pk):
    # apaga o banner de vez (esse aqui eh delete mesmo, nao soft). nao achou -> 404
    if not db.excluir_banner(pk):
        raise Http404()
    messages.info(request, "Banner excluído.")
    return redirect("portal:gestao_banners")


@perfis("GES")
@require_http_methods(["POST"])
def gestao_banner_reordenar(request, pk):
    # sobe/desce o banner no carrossel. direcao vem do POST (tipo -1/+1) e o
    # db troca a ordem com o vizinho. sem mensagem, so volto pra lista
    direcao = int(request.POST.get("direcao", 0))
    db.reordenar_banner(pk, direcao)
    return redirect("portal:gestao_banners")
