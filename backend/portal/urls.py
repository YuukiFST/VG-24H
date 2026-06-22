"""
urls.py — aqui eu mapeio cada URL do meu portal pra view que responde por ela.

Eu separei as rotas por tipo de usuario pra nao virar bagunca:
- Publicas: home e catalogo, qualquer um acessa sem logar
- Autenticacao: login, logout, cadastro, recuperar senha
- Cidadao: os chamados dele e as notificacoes
- Equipe: dashboard, todos os chamados, detalhe e as acoes
- Gestao: meus CRUDs de categoria, servico, bairro, colaborador e banner
"""

# path eh o que eu uso pra registrar cada rota
from django.urls import path

# importo os modulos de view que separei por area (auth, cidadao, equipe, gestao, root)
from portal import views_auth, views_cidadao, views_equipe, views_gestao, views_root

# namespace do app, pra eu chamar as urls como "portal:login" no template
app_name = "portal"

urlpatterns = [
    # rotas abertas, sem login: a home e o catalogo de servicos
    path("", views_root.root_view, name="root"),
    path("servicos/", views_root.catalogo_servicos, name="catalogo_servicos"),

    # tudo de login/conta fica aqui embaixo
    path("accounts/login/", views_auth.login_view, name="login"),
    path("accounts/logout/", views_auth.logout_view, name="logout"),
    path("accounts/cadastro/", views_auth.cadastro_view, name="cadastro"),
    path("accounts/recuperar-senha/", views_auth.recuperar_senha_view, name="recuperar_senha"),
    # essa recebe o token na propria URL pra validar o link de redefinir
    path("accounts/redefinir-senha/<str:token>/", views_auth.redefinir_senha_view, name="redefinir_senha"),
    # quando a senha eh temporaria eu obrigo a trocar logo no login
    path("accounts/trocar-senha/", views_auth.troca_senha_obrigatoria_view, name="troca_senha_obrigatoria"),

    # area do cidadao (perfil CID): so os chamados dele e as notificacoes
    path("cidadao/chamados/", views_cidadao.cidadao_chamados_lista, name="cidadao_chamados"),
    path("cidadao/chamados/novo/", views_cidadao.cidadao_chamado_novo, name="cidadao_chamado_novo"),
    # <int:pk> eh o id do chamado que cai como parametro na view
    path("cidadao/chamados/<int:pk>/", views_cidadao.cidadao_chamado_detalhe, name="cidadao_chamado"),
    path("cidadao/chamados/<int:pk>/observar/", views_cidadao.cidadao_chamado_obs, name="cidadao_chamado_obs"),
    path("cidadao/chamados/<int:pk>/foto/", views_cidadao.cidadao_chamado_foto, name="cidadao_chamado_foto"),
    path("cidadao/chamados/<int:pk>/cancelar/", views_cidadao.cidadao_chamado_cancelar, name="cidadao_chamado_cancelar"),
    path("cidadao/chamados/<int:pk>/avaliar/", views_cidadao.cidadao_chamado_avaliar, name="cidadao_chamado_avaliar"),
    path("cidadao/notificacoes/", views_cidadao.cidadao_notificacoes, name="cidadao_notificacoes"),

    # area da equipe (perfis COL e GES): dashboard, lista e detalhe dos chamados
    path("equipe/", views_equipe.equipe_dashboard, name="equipe_dashboard"),
    path("equipe/chamados/", views_equipe.equipe_chamados_lista, name="equipe_chamados"),
    # essa tela mostra os prazos do semaforo (amarelo/vermelho)
    path("equipe/chamados/prazos/", views_equipe.gestao_prazos, name="gestao_prazos"),
    path("equipe/chamados/<int:pk>/", views_equipe.equipe_chamado_detalhe, name="equipe_chamado"),
    # aqui a equipe muda o status do chamado
    path("equipe/chamados/<int:pk>/status/", views_equipe.equipe_chamado_status, name="equipe_chamado_status"),
    path("equipe/chamados/<int:pk>/observar/", views_equipe.equipe_chamado_obs, name="equipe_chamado_obs"),
    path("equipe/chamados/<int:pk>/foto/", views_equipe.equipe_chamado_foto, name="equipe_chamado_foto"),
    # excluir eh so pro gestor, por isso aponta pra view de gestao
    path("equipe/chamados/<int:pk>/excluir/", views_equipe.gestao_chamado_excluir, name="gestao_chamado_excluir"),

    # area de gestao (perfil GES): estatisticas e os CRUDs do sistema
    path("gestao/estatisticas/", views_gestao.gestao_estatisticas, name="gestao_estatisticas"),
    # categorias
    path("gestao/categorias/", views_gestao.gestao_categorias, name="gestao_categorias"),
    path("gestao/categorias/<int:pk>/editar/", views_gestao.gestao_categoria_edit, name="gestao_categoria_editar"),
    # servicos
    path("gestao/servicos/", views_gestao.gestao_servicos, name="gestao_servicos"),
    path("gestao/servicos/novo/", views_gestao.gestao_servico_novo, name="gestao_servico_novo"),
    path("gestao/servicos/<int:pk>/editar/", views_gestao.gestao_servico_edit, name="gestao_servico_editar"),
    # nao apago servico, so desativo pra nao quebrar chamado antigo
    path("gestao/servicos/<int:pk>/desativar/", views_gestao.gestao_servico_desativar, name="gestao_servico_desativar"),
    # bairros (esses eu deixo ativar e desativar)
    path("gestao/bairros/", views_gestao.gestao_bairros, name="gestao_bairros"),
    path("gestao/bairros/<int:pk>/editar/", views_gestao.gestao_bairro_edit, name="gestao_bairro_editar"),
    path("gestao/bairros/<int:pk>/desativar/", views_gestao.gestao_bairro_desativar, name="gestao_bairro_desativar"),
    path("gestao/bairros/<int:pk>/ativar/", views_gestao.gestao_bairro_ativar, name="gestao_bairro_ativar"),
    # colaboradores (servidores da equipe)
    path("gestao/colaboradores/", views_gestao.gestao_colaboradores, name="gestao_colaboradores"),
    path("gestao/colaboradores/novo/", views_gestao.gestao_colaborador_novo, name="gestao_colaborador_novo"),
    # toggle liga/desliga o acesso do colaborador
    path("gestao/colaboradores/<int:pk>/toggle/", views_gestao.gestao_colaborador_toggle, name="gestao_colaborador_toggle"),
    # resetar senha gera uma senha temporaria pro colaborador
    path("gestao/colaboradores/<int:pk>/resetar-senha/", views_gestao.gestao_colaborador_reset_senha, name="gestao_colaborador_reset_senha"),

    # banners que aparecem na home, tudo gerenciado aqui
    path("gestao/banners/", views_gestao.gestao_banners, name="gestao_banners"),
    path("gestao/banners/novo/", views_gestao.gestao_banner_novo, name="gestao_banner_novo"),
    path("gestao/banners/<int:pk>/editar/", views_gestao.gestao_banner_editar, name="gestao_banner_editar"),
    path("gestao/banners/<int:pk>/excluir/", views_gestao.gestao_banner_excluir, name="gestao_banner_excluir"),
    # reordenar muda a ordem que os banners aparecem no carrossel
    path("gestao/banners/<int:pk>/reordenar/", views_gestao.gestao_banner_reordenar, name="gestao_banner_reordenar"),

    # foto de perfil do usuario (upload e remover)
    path("perfil/foto/", views_root.upload_foto_perfil, name="upload_foto_perfil"),
    path("perfil/foto/excluir/", views_root.excluir_foto_perfil, name="excluir_foto_perfil"),

    # trocar senha quando o cara ja ta logado e quer mudar por conta propria
    path("trocar-senha/", views_root.trocar_senha, name="trocar_senha"),
]
