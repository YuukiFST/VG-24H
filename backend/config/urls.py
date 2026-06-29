# esse eh o urls.py raiz do projeto, ele so manda tudo pro app portal
from django.urls import include, path

urlpatterns = [
    # incluo todas as rotas do meu app portal na raiz do site
    path("", include("portal.urls")),
]
