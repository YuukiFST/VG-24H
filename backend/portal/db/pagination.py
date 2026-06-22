"""portal.db.pagination — minha paginacao na mao (saiu do db.py).
A fachada publica fica em portal/db/__init__.py."""


# SimpleNamespace eu uso aqui pra fingir um objeto "paginator" pro template.
from types import SimpleNamespace


class _PageObj:
    """Objeto de pagina que imita o que o template do Django espera.

    Anotacao importante que eu descobri quebrando a cara: NAO da pra usar
    SimpleNamespace aqui porque o Python so reconhece os metodos dunder
    (__len__, __iter__) quando eles estao DEFINIDOS NA CLASSE, e nao quando
    sao colados na instancia. Por isso virou uma classe de verdade.
    """

    # guardo tudo que o template de paginacao do Django costuma acessar:
    # a lista da pagina, o numero da pagina atual, o "paginator", e as flags
    # de tem proxima / tem anterior com os numeros de cada uma.
    def __init__(self, object_list, number, paginator,
                 has_previous, has_next,
                 previous_page_number, next_page_number):
        self.object_list = object_list
        self.number = number
        self.paginator = paginator
        self.has_previous = has_previous
        self.has_next = has_next
        self.previous_page_number = previous_page_number
        self.next_page_number = next_page_number

    # __len__ e __iter__ pra eu poder fazer len(page) e for x in page no template,
    # delegando tudo pra lista object_list de dentro.
    def __len__(self):
        return len(self.object_list)

    def __iter__(self):
        return iter(self.object_list)

def paginar(itens, pagina, por_pagina=15, total_count=None):
    """Minha paginacao manual pra listas.

    Funciona de dois jeitos:
    1) Se eu NAO passar total_count, ele assume que `itens` eh a lista inteira
       e fatia ela aqui em Python (start:end).
    2) Se eu passar total_count (o COUNT(*) que eu ja fiz no SQL), ele entende
       que `itens` ja eh so a pagina atual (porque eu fiz LIMIT/OFFSET na query)
       e nao fatia de novo. Esse jeito eh melhor pra performance porque eu nao
       trago a tabela toda pra memoria.
    """
    # se ninguem me deu o total, eu conto o tamanho da lista mesmo.
    if total_count is None:
        total_count = len(itens)
    # calculo quantas paginas no total. Aquela conta com +por_pagina-1 eh o
    # truque de arredondar pra cima na divisao inteira. max(1,...) pra nunca dar 0.
    total_pages = max(1, (total_count + por_pagina - 1) // por_pagina)

    # a pagina vem da URL (string), entao tento converter pra int. Se vier lixo
    # (texto, None) eu caio no except e assumo pagina 1 em vez de quebrar.
    try:
        page_number = int(pagina)
    except (ValueError, TypeError):
        page_number = 1
    # prendo o numero da pagina entre 1 e o total, pra ninguem pedir pagina -5
    # ou pagina 9999 que nao existe.
    page_number = max(1, min(page_number, total_pages))

    # aqui eu decido se preciso fatiar ou nao:
    # se o total nao bate com o tamanho da lista, eh porque o SQL ja paginou
    # (caso 2 la de cima), entao uso os itens como vieram.
    if total_count is not None and total_count != len(itens):
        page_items = itens
    else:
        # senao eh o caso 1: eu mesmo recorto a fatia da pagina atual.
        start = (page_number - 1) * por_pagina
        end = start + por_pagina
        page_items = itens[start:end]

    # monto o objeto de pagina com tudo que o template precisa. O "paginator"
    # eu finjo com SimpleNamespace, so com num_pages e o range pra montar os
    # botoes de pagina (1..total).
    page_obj = _PageObj(
        object_list=page_items,
        number=page_number,
        paginator=SimpleNamespace(
            num_pages=total_pages,
            page_range=range(1, total_pages + 1),
        ),
        # so tem "anterior" se nao for a pagina 1, e "proxima" se nao for a ultima.
        has_previous=page_number > 1,
        has_next=page_number < total_pages,
        # os numeros das paginas vizinhas, ou None nas pontas.
        previous_page_number=page_number - 1 if page_number > 1 else None,
        next_page_number=page_number + 1 if page_number < total_pages else None,
    )

    # devolvo a pagina pronta e o total (o total eh util pra view mostrar "X resultados").
    return page_obj, total_count
