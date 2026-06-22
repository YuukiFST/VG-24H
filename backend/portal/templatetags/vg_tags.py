from django import template

register = template.Library()


STATUS_CORES = {
    "AB": "info",
    "EA": "warning",
    "EE": "orange-vivid-30",
    "CO": "success",
    "CA": "danger",
}


@register.simple_tag
def status_tag(sigla):
    """Renderiza badge de status com cor do GOV.br.

    Uso: {% status_tag chamado.sigla_status %}
    """
    cor = STATUS_CORES.get(sigla, "info")
    descricoes = {"AB": "Aberto", "EA": "Em Atendimento", "EE": "Em Execução",
                  "CO": "Concluído", "CA": "Cancelado"}
    descricao = descricoes.get(sigla, sigla)
    return f'<span class="br-tag br-tag-{cor}">{descricao}</span>'


@register.simple_tag
def prioridade_tag(valor):
    """Renderiza badge de prioridade.

    Uso: {% prioridade_tag chamado.prioridade %}
    """
    cores = {5: "danger", 4: "warning", 3: "info", 2: "secondary", 1: "secondary", 0: "secondary"}
    cor = cores.get(valor, "secondary")
    return f'<span class="br-tag br-tag-{cor}">{valor}</span>'


@register.simple_tag(takes_context=True)
def breadcrumb(context, *crumbs):
    """Renderiza breadcrumb do GOV.br.

    Uso: {% breadcrumb "Home" "portal:root" "Seção" "portal:secao" "Página atual" %}
    Pares: (nome, url_name) ou apenas nome para o item atual.
    """
    from django.urls import reverse
    pages = []
    parts = list(crumbs)
    while parts:
        name = parts.pop(0)
        if parts and parts[0].startswith("portal:"):
            url_name = parts.pop(0)
            pages.append((name, url_name))
        else:
            pages.append((name, None))
            break
    items_html = ""
    for name, url_name in pages:
        if url_name is None:
            items_html += f'<li><a href="#" aria-current="page">{name}</a></li>'
        else:
            url = reverse(url_name)
            items_html += f'<li><a href="{url}">{name}</a></li>'
    return f'''
<nav class="br-breadcrumb" aria-label="Breadcrumb">
  <ol class="crumb-list">
    <li><a href="/">Home</a></li>
    {items_html}
  </ol>
</nav>'''
