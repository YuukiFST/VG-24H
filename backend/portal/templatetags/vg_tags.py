# template e a forma do Django de eu criar minhas proprias tags/filtros pro html
from django import template

# esse register e o que liga minhas funcoes pro template enxergar
register = template.Library()


# de cada sigla de status pra cor do design system do GOV.br
STATUS_CORES = {
    "AB": "info",
    "EA": "warning",
    "EE": "orange-vivid-30",
    "CO": "success",
    "CA": "danger",
}


@register.simple_tag
def status_tag(sigla):
    """Monto o badge de status ja com a cor do GOV.br.

    Eu chamo assim no template: {% status_tag chamado.sigla_status %}
    """
    # pego a cor pela sigla; se for sigla que eu nao conheco caio no "info"
    cor = STATUS_CORES.get(sigla, "info")
    # de sigla pro texto que aparece pro usuario
    descricoes = {"AB": "Aberto", "EA": "Em Atendimento", "EE": "Em Execução",
                  "CO": "Concluído", "CA": "Cancelado"}
    # se nao achar a descricao eu mostro a propria sigla mesmo
    descricao = descricoes.get(sigla, sigla)
    # devolvo o html prontinho do badge
    return f'<span class="br-tag br-tag-{cor}">{descricao}</span>'


@register.simple_tag
def prioridade_tag(valor):
    """Monto o badge de prioridade.

    Eu chamo assim: {% prioridade_tag chamado.prioridade %}
    """
    # quanto maior a prioridade, cor mais "quente"; o resto fica cinza (secondary)
    cores = {5: "danger", 4: "warning", 3: "info", 2: "secondary", 1: "secondary", 0: "secondary"}
    # valor que eu nao mapeei cai em secondary
    cor = cores.get(valor, "secondary")
    # devolvo o badge mostrando o proprio numero da prioridade
    return f'<span class="br-tag br-tag-{cor}">{valor}</span>'


@register.simple_tag(takes_context=True)
def breadcrumb(context, *crumbs):
    """Monto o breadcrumb (aquela trilha de navegacao) do GOV.br.

    Eu chamo assim:
    {% breadcrumb "Home" "portal:root" "Seção" "portal:secao" "Página atual" %}
    A ideia e ir em pares: (nome, url_name), e o ultimo item pode ser so o
    nome (a pagina atual, que nao vira link).
    """
    # importo aqui dentro so quando vou usar pra gerar a url pelo nome da rota
    from django.urls import reverse
    pages = []
    # transformo os argumentos numa lista que eu vou consumindo do inicio
    parts = list(crumbs)
    while parts:
        # tiro o nome do item
        name = parts.pop(0)
        # se o proximo parece um nome de rota ("portal:..."), entao esse item vira link
        if parts and parts[0].startswith("portal:"):
            url_name = parts.pop(0)
            pages.append((name, url_name))
        else:
            # senao e o item atual (sem link) e eu paro o loop aqui
            pages.append((name, None))
            break
    items_html = ""
    for name, url_name in pages:
        if url_name is None:
            # item atual: marco com aria-current e href "#" porque nao e pra clicar
            items_html += f'<li><a href="#" aria-current="page">{name}</a></li>'
        else:
            # item com link: converto o nome da rota na url de verdade
            url = reverse(url_name)
            items_html += f'<li><a href="{url}">{name}</a></li>'
    # devolvo o nav inteiro, sempre comecando pelo "Home" fixo
    return f'''
<nav class="br-breadcrumb" aria-label="Breadcrumb">
  <ol class="crumb-list">
    <li><a href="/">Home</a></li>
    {items_html}
  </ol>
</nav>'''
