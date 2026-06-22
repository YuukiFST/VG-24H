"""portal.db.pagination — extraido de db.py (camada SQL pura).
Veja portal/db/__init__.py para a fachada publica."""


from types import SimpleNamespace


class _PageObj:
    """Wrapper de paginacao compativel com templates Django.

    Nao pode ser SimpleNamespace porque o Python so enxerga metodos
    dunder (__len__, __iter__) definidos na classe, nao em instancias.
    """

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

    def __len__(self):
        return len(self.object_list)

    def __iter__(self):
        return iter(self.object_list)

def paginar(itens, pagina, por_pagina=15, total_count=None):
    """Paginacao manual para listas de objetos.

    Recebe uma lista de itens (ja filtrados ou pagina atual) e retorna
    um _PageObj compativel com os templates Django. O total_count permite
    que o chamador passe o COUNT(*) do SQL para evitar contar em Python.

    Se total_count for informado, assume que 'itens' ja contem apenas
    os registros da pagina atual (LIMIT/OFFSET feito no SQL).
    """
    if total_count is None:
        total_count = len(itens)
    total_pages = max(1, (total_count + por_pagina - 1) // por_pagina)

    try:
        page_number = int(pagina)
    except (ValueError, TypeError):
        page_number = 1
    page_number = max(1, min(page_number, total_pages))

    if total_count is not None and total_count != len(itens):
        page_items = itens
    else:
        start = (page_number - 1) * por_pagina
        end = start + por_pagina
        page_items = itens[start:end]

    page_obj = _PageObj(
        object_list=page_items,
        number=page_number,
        paginator=SimpleNamespace(
            num_pages=total_pages,
            page_range=range(1, total_pages + 1),
        ),
        has_previous=page_number > 1,
        has_next=page_number < total_pages,
        previous_page_number=page_number - 1 if page_number > 1 else None,
        next_page_number=page_number + 1 if page_number < total_pages else None,
    )

    return page_obj, total_count
