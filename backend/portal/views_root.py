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

from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from portal import db
from portal.decorators import autenticado
from portal.forms import NovaSenhaForm
from portal.utils import salvar_foto_upload


def root_view(request):
    banners = db.listar_banners_ativos()
    categorias = db.listar_categorias_com_servicos()
    stats = db.buscar_stats_publicas()
    return render(request, "portal/root.html", {
        "banners": banners, "categorias": categorias, "stats": stats,
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
            from django.contrib.auth.hashers import make_password
            if hasattr(request.portal_user, "id_servidor"):
                db.atualizar_senha_usuario("servidor", request.portal_user.pk, nova)
            else:
                db.atualizar_senha_usuario("cidadao", request.portal_user.pk, nova)

            # Atualiza o cookie de sessao para refletir que a senha
            # nao eh mais temporaria (evita redirect infinito).
            request.session.modified = True

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
    notifs = db.listar_notificacoes_servidor(uid)

    nids = [n.pk for n in notifs if not n.lida]
    db.marcar_notificacoes_lidas(nids)

    # POST: exclusao de uma notificacao especifica.
    # Seguranca: subquery garante que so pode deletar notificacoes
    # dos proprios chamados atendidos (nao de outros servidores).
    if request.method == "POST":
        nid = request.POST.get("excluir")
        if nid:
            db.excluir_notificacao(nid, uid_servidor=uid)
            messages.info(request, "Notificação removida.")
        return redirect("portal:notificacoes")

    return render(request, "portal/notificacoes.html", {"lista": notifs})


# ------------------------------------------------------------------
# PAINEL DO CIDADAO (acesso rapido — perfil CID)
# ------------------------------------------------------------------

@autenticado
def painel_cidadao(request):
    cidadao = request.portal_user
    chamados = db.listar_chamados_painel(cidadao.pk)
    return render(request, "portal/cidadao/painel.html", {
        "cidadao": cidadao, "chamados": chamados,
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
    """Remove a foto de perfil do usuario (define como NULL no banco)."""
    user = request.portal_user

    from portal.models import Cidadao
    if isinstance(user, Cidadao):
        db.remover_foto_perfil("cidadao", user.pk)
    else:
        db.remover_foto_perfil("servidor", user.pk)

    messages.success(request, "Foto removida com sucesso!")
    return redirect("/")

def catalogo_servicos(request):
    """Catalogo publico de servicos."""
    blocos = [(item["categoria"], item["servicos"]) for item in db.listar_categorias_com_servicos()]
    return render(request, "portal/public/catalogo_servicos.html", {"blocos": blocos})
