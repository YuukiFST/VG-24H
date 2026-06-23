"""
views_root.py — aqui ficam minhas views publicas e de raiz (Portal VG 24H)

Joguei aqui as views que NAO precisam de login mais as rotas de raiz:
pagina inicial, troca forcada de senha e o upload/remocao de foto de perfil.

A troca de senha aqui eh obrigatoria pra servidor que ta com
senha_temporaria='1' (colaborador que o gestor acabou de criar). O
decorator @exige_troca_senha segura QUALQUER requisicao e manda o cara
pra tela de troca ate ele botar uma senha nova.
"""

# imports do django + meus modulos (db = minhas funcoes de SQL puro, decorators, forms, utils)
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from portal import db
from portal.decorators import autenticado
from portal.forms import NovaSenhaForm
from portal.utils import salvar_foto_upload


def root_view(request):
    # home publica: pego os banners ativos, as categorias com seus servicos
    banners = db.listar_banners_ativos()
    categorias = db.listar_categorias_com_servicos()
    # stats publicas (numeros que aparecem na home, tipo total de chamados)
    stats = db.buscar_stats_publicas()
    # mando tudo pro template da raiz
    return render(request, "portal/root.html", {
        "banners": banners, "categorias": categorias, "stats": stats,
    })

# ------------------------------------------------------------------
# TROCA DE SENHA (obrigatoria para servidores com senha_temporaria='1')
# ------------------------------------------------------------------

@autenticado
@require_http_methods(["GET", "POST"])
def trocar_senha(request):
    """Minha tela de troca de senha obrigatoria.

    Serve pra qualquer um logado (COL, GES, CID). Quando troca certo eu
    limpo a flag senha_temporaria no banco e atualizo o cookie da sessao.

    Esse senha_temporaria='1' fica ligado quando o gestor cria um
    colaborador novo. O middleware enxerga isso pelo cookie e joga todas
    as requisicoes pra ca ate o cara trocar.
    """
    if request.method == "POST":
        # so processa a troca no POST; valido pelo meu form de senha nova
        form = NovaSenhaForm(request.POST)
        if form.is_valid():
            nova = form.cleaned_data["nova_senha"]

            # aqui decido em qual tabela mexer: se o user tem id_servidor eh
            # servidor, senao eh cidadao. A funcao do db ja faz o hash bcrypt.
            if hasattr(request.portal_user, "id_servidor"):
                db.atualizar_senha_usuario("servidor", request.portal_user.pk, nova)
            else:
                db.atualizar_senha_usuario("cidadao", request.portal_user.pk, nova)

            # o db ja zerou senha_temporaria; marco a sessao como modificada
            # pra renovar o cookie e o middleware reler o user atualizado
            request.session.modified = True

            messages.success(request, "Senha alterada com sucesso!")
            return redirect("/")  # deu certo, mando pra home
    else:
        # GET: so mostro o form vazio
        form = NovaSenhaForm()

    return render(request, "portal/senha/trocar_senha.html", {"form": form})


# ------------------------------------------------------------------
# UPLOAD DE FOTO DO PERFIL (cidadao e servidor)
# ------------------------------------------------------------------

@autenticado
@require_http_methods(["POST"])
def upload_foto_perfil(request):
    """Salva ou troca a foto de perfil de quem ta logado.

    Sozinho eu descubro se eh cidadao ou servidor e atualizo a tabela
    certa. O upload vai pro Cloudinary (se tiver configurado) ou pro
    filesystem local.
    """
    foto = request.FILES.get("foto")
    if not foto:
        # nao mandaram arquivo nenhum, aviso e volto pra home
        messages.error(request, "Nenhuma foto selecionada.")
        return redirect("/")

    try:
        # essa funcao do utils salva a foto e me devolve a url
        url = salvar_foto_upload(foto, request=request)
    except ValueError as e:
        # se a foto for invalida (tipo/tamanho) ela estoura ValueError
        messages.error(request, str(e))
        return redirect("/")

    user = request.portal_user

    # uso isinstance pra saber se eh Cidadao e gravar a url na tabela certa
    from portal.models import Cidadao
    if isinstance(user, Cidadao):
        db.atualizar_foto_perfil("cidadao", user.pk, url)
    else:
        db.atualizar_foto_perfil("servidor", user.pk, url)

    messages.success(request, "Foto atualizada com sucesso!")
    return redirect("/")


# ------------------------------------------------------------------
# EXCLUIR FOTO DO PERFIL
# ------------------------------------------------------------------

@autenticado
@require_http_methods(["POST"])
def excluir_foto_perfil(request):
    """Tira a foto de perfil (deixa NULL no banco)."""
    user = request.portal_user

    # mesma logica do upload: descubro o tipo e removo na tabela certa
    from portal.models import Cidadao
    if isinstance(user, Cidadao):
        db.remover_foto_perfil("cidadao", user.pk)
    else:
        db.remover_foto_perfil("servidor", user.pk)

    messages.success(request, "Foto removida com sucesso!")
    return redirect("/")

def catalogo_servicos(request):
    """Catalogo publico de servicos."""
    # monto uma lista de tuplas (categoria, servicos) pra ficar facil de
    # iterar no template, em vez de mandar os dicts crus
    blocos = [(item["categoria"], item["servicos"]) for item in db.listar_categorias_com_servicos()]
    return render(request, "portal/public/catalogo_servicos.html", {"blocos": blocos})
