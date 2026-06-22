# esse eh o urls.py raiz do projeto, ele so manda tudo pro app portal
from django.conf import settings
from django.conf.urls.static import static  # helper pra servir media no dev
from django.urls import include, path

urlpatterns = [
    # incluo todas as rotas do meu app portal na raiz do site
    path("", include("portal.urls")),
]

# so no modo dev (DEBUG) eu deixo o Django servir as fotos da pasta media;
# em producao quem cuida disso eh o servidor/whitenoise, nao o Django
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
