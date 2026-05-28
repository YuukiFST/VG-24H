"""
urls.py — Rotas do Portal VG 24H

Rotas organizadas por perfil de acesso:
- Publicas: pagina inicial, catalogo de servicos
- Autenticacao: login, logout, cadastro, recuperacao de senha
- Cidadao: chamados proprios, notificacoes
- Equipe: dashboard, todos os chamados, detalhe + acoes
- Gestao: CRUD de categorias, servicos, bairros, colaboradores, banners
"""

from django.urls import path

from portal import views_auth, views_cidadao, views_equipe, views_gestao, views_root

app_name = "portal"

urlpatterns = [
    # Rotas publicas (nao exigem login).
    path("", views_root.root_view, name="root"),
    path("servicos/", views_root.catalogo_servicos, name="catalogo_servicos"),

    # Autenticacao (login, cadastro, recuperacao de senha).
    path("accounts/login/", views_auth.login_view, name="login"),
    path("accounts/logout/", views_auth.logout_view, name="logout"),
    path("accounts/cadastro/", views_auth.cadastro_view, name="cadastro"),
    path("accounts/recuperar-senha/", views_auth.recuperar_senha_view, name="recuperar_senha"),
    path("accounts/redefinir-senha/<str:token>/", views_auth.redefinir_senha_view, name="redefinir_senha"),
    path("accounts/trocar-senha/", views_auth.troca_senha_obrigatoria_view, name="troca_senha_obrigatoria"),

    # Cidadao (perfil CID): chamados proprios e notificacoes.
    path("cidadao/chamados/", views_cidadao.cidadao_chamados_lista, name="cidadao_chamados"),
    path("cidadao/chamados/novo/", views_cidadao.cidadao_chamado_novo, name="cidadao_chamado_novo"),
    path("cidadao/chamados/<int:pk>/", views_cidadao.cidadao_chamado_detalhe, name="cidadao_chamado"),
    path("cidadao/notificacoes/", views_cidadao.cidadao_notificacoes, name="cidadao_notificacoes"),

    # Equipe (perfis COL e GES): dashboard, chamados, detalhe.
    path("equipe/", views_equipe.equipe_dashboard, name="equipe_dashboard"),
    path("equipe/chamados/", views_equipe.equipe_chamados_lista, name="equipe_chamados"),
    path("equipe/chamados/<int:pk>/", views_equipe.equipe_chamado_detalhe, name="equipe_chamado"),
    path("equipe/chamados/<int:pk>/excluir/", views_equipe.gestao_chamado_excluir, name="gestao_chamado_excluir"),

    # Gestao (perfil GES): estatisticas, categorias, servicos, bairros, colaboradores, banners.
    path("gestao/estatisticas/", views_gestao.gestao_estatisticas, name="gestao_estatisticas"),
    path("gestao/categorias/", views_gestao.gestao_categorias, name="gestao_categorias"),
    path("gestao/categorias/<int:pk>/editar/", views_gestao.gestao_categoria_edit, name="gestao_categoria_editar"),
    path("gestao/servicos/", views_gestao.gestao_servicos, name="gestao_servicos"),
    path("gestao/servicos/<int:pk>/editar/", views_gestao.gestao_servico_edit, name="gestao_servico_editar"),
    path("gestao/servicos/<int:pk>/desativar/", views_gestao.gestao_servico_desativar, name="gestao_servico_desativar"),
    path("gestao/bairros/", views_gestao.gestao_bairros, name="gestao_bairros"),
    path("gestao/bairros/<int:pk>/editar/", views_gestao.gestao_bairro_edit, name="gestao_bairro_editar"),
    path("gestao/bairros/<int:pk>/desativar/", views_gestao.gestao_bairro_desativar, name="gestao_bairro_desativar"),
    path("gestao/bairros/<int:pk>/ativar/", views_gestao.gestao_bairro_ativar, name="gestao_bairro_ativar"),
    path("gestao/colaboradores/", views_gestao.gestao_colaboradores, name="gestao_colaboradores"),
    path("gestao/colaboradores/<int:pk>/toggle/", views_gestao.gestao_colaborador_toggle, name="gestao_colaborador_toggle"),

    # Banners (painel de gestao).
    path("gestao/banners/", views_gestao.gestao_banners, name="gestao_banners"),
    path("gestao/banners/novo/", views_gestao.gestao_banner_novo, name="gestao_banner_novo"),
    path("gestao/banners/<int:pk>/editar/", views_gestao.gestao_banner_editar, name="gestao_banner_editar"),
    path("gestao/banners/<int:pk>/excluir/", views_gestao.gestao_banner_excluir, name="gestao_banner_excluir"),
    path("gestao/banners/<int:pk>/reordenar/", views_gestao.gestao_banner_reordenar, name="gestao_banner_reordenar"),

    # Perfil do usuario (foto).
    path("perfil/foto/", views_root.upload_foto_perfil, name="upload_foto_perfil"),
    path("perfil/foto/excluir/", views_root.excluir_foto_perfil, name="excluir_foto_perfil"),

    # Troca de senha (qualquer usuario logado).
    path("trocar-senha/", views_root.trocar_senha, name="trocar_senha"),
]
