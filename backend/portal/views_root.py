"""
views_root.py — Views publicas e pagina inicial do Portal VG 24H

[!] NAO tem @perfis() — sao rotas PUBLICAS (qualquer um pode acessar).
[!] total_resolvidos usa Subquery para contar chamados com ultimo status = 'CO'.
    Mesma logica arquitetural: status vem do historico_chamado, nao de um campo direto.

Contem:
- Catalogo de servicos (publico)
- Pagina inicial com estatisticas e banners
"""

import logging

from types import SimpleNamespace

from django.db import connection
from django.shortcuts import redirect, render

from portal.decorators import perfil_codigo
from portal.utils import escape_like

logger = logging.getLogger(__name__)


def catalogo_servicos(request):
    q_raw = (request.GET.get("q") or "").strip()
    blocos = []
    try:
        with connection.cursor() as cursor:
            # SQL puro: busca todas as categorias ativas
            cursor.execute(
                "SELECT id_categoria, nome, descricao, ativo "
                "FROM categoria_servico "
                "WHERE ativo = TRUE "
                "ORDER BY nome"
            )
            categorias = cursor.fetchall()

            for cat_row in categorias:
                cat = SimpleNamespace(
                    id_categoria=cat_row[0], nome=cat_row[1],
                    descricao=cat_row[2], ativo=cat_row[3], pk=cat_row[0],
                )
                if not q_raw:
                    # SQL puro: busca serviços da categoria
                    cursor.execute(
                        "SELECT id_servico, nome, descricao, ativo "
                        "FROM servico "
                        "WHERE id_categoria = %s AND ativo = TRUE "
                        "ORDER BY nome",
                        [cat.pk],
                    )
                    servicos = [
                        SimpleNamespace(id_servico=r[0], nome=r[1], descricao=r[2], ativo=r[3], pk=r[0])
                        for r in cursor.fetchall()
                    ]
                else:
                    q_lower = q_raw.lower()
                    cat_match = q_lower in cat.nome.lower()
                    if cat.descricao:
                        cat_match = cat_match or q_lower in cat.descricao.lower()
                    if cat_match:
                        # Categoria combina → mostra todos os serviços
                        cursor.execute(
                            "SELECT id_servico, nome, descricao, ativo "
                            "FROM servico "
                            "WHERE id_categoria = %s AND ativo = TRUE "
                            "ORDER BY nome",
                            [cat.pk],
                        )
                        servicos = [
                            SimpleNamespace(id_servico=r[0], nome=r[1], descricao=r[2], ativo=r[3], pk=r[0])
                            for r in cursor.fetchall()
                        ]
                    else:
                        # Filtra serviços pelo termo de busca
                        q_like = f"%{escape_like(q_lower)}%"
                        cursor.execute(
                            "SELECT id_servico, nome, descricao, ativo "
                            "FROM servico "
                            "WHERE id_categoria = %s AND ativo = TRUE "
                            "AND (LOWER(nome) LIKE %s ESCAPE '\\\\' OR LOWER(descricao) LIKE %s ESCAPE '\\\\') "
                            "ORDER BY nome",
                            [cat.pk, q_like, q_like],
                        )
                        servicos = [
                            SimpleNamespace(id_servico=r[0], nome=r[1], descricao=r[2], ativo=r[3], pk=r[0])
                            for r in cursor.fetchall()
                        ]
                        if not servicos:
                            continue
                blocos.append((cat, servicos))
    except Exception:
        logger.exception("Erro ao carregar catalogo de servicos")
        blocos = []
    return render(
        request,
        "portal/public/catalogo_servicos.html",
        {"blocos": blocos, "q": q_raw},
    )


def root_view(request):
    try:
        categorias = []
        with connection.cursor() as cursor:
            # SQL puro: SELECT categorias ativas com seus serviços
            cursor.execute(
                "SELECT id_categoria, nome, descricao "
                "FROM categoria_servico "
                "WHERE ativo = TRUE ORDER BY nome"
            )
            cats = cursor.fetchall()

            for cat_row in cats:
                cat = SimpleNamespace(
                    id_categoria=cat_row[0], nome=cat_row[1],
                    descricao=cat_row[2], pk=cat_row[0],
                )
                # SQL puro: SELECT serviços de cada categoria
                cursor.execute(
                    "SELECT id_servico, nome, descricao "
                    "FROM servico "
                    "WHERE id_categoria = %s AND ativo = TRUE "
                    "ORDER BY nome",
                    [cat.pk],
                )
                svcs = [
                    SimpleNamespace(id_servico=r[0], nome=r[1], descricao=r[2], pk=r[0])
                    for r in cursor.fetchall()
                ]
                categorias.append({"categoria": cat, "servicos": svcs})

            # SQL puro: conta total de chamados resolvidos (status 'CO')
            # Subconsulta: último status de cada chamado
            cursor.execute(
                "SELECT COUNT(*) FROM chamado c "
                "WHERE ("
                "  SELECT sc.sigla FROM historico_chamado hc "
                "  JOIN status_chamado sc ON hc.id_status = sc.id_status "
                "  WHERE hc.id_chamado = c.id_chamado "
                "  ORDER BY hc.dt_alteracao DESC LIMIT 1"
                ") = 'CO'"
            )
            total_resolvidos = cursor.fetchone()[0]

            # SQL puro: conta bairros e serviços ativos
            cursor.execute("SELECT COUNT(*) FROM bairro WHERE ativo = TRUE")
            total_bairros = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM servico WHERE ativo = TRUE")
            total_servicos = cursor.fetchone()[0]

        stats = {
            "total_resolvidos": total_resolvidos,
            "total_bairros": total_bairros,
            "total_servicos": total_servicos,
        }
    except Exception:
        logger.exception("Erro ao carregar pagina inicial")
        categorias = []
        stats = {
            "total_resolvidos": 0,
            "total_bairros": 0,
            "total_servicos": 0,
        }

    try:
        with connection.cursor() as cursor:
            # SQL puro: SELECT banners ativos ordenados
            cursor.execute(
                "SELECT id_banner, titulo, descricao, url_imagem, link, ordem, ativo, dt_criacao "
                "FROM banner_publicacao "
                "WHERE ativo = TRUE "
                "ORDER BY ordem, dt_criacao DESC"
            )
            banners = [
                SimpleNamespace(
                    id_banner=r[0], titulo=r[1], descricao=r[2],
                    url_imagem=r[3], link=r[4], ordem=r[5],
                    ativo=r[6], dt_criacao=r[7], pk=r[0],
                )
                for r in cursor.fetchall()
            ]
    except Exception:
        logger.exception("Erro ao carregar banners")
        banners = []

    return render(
        request,
        "portal/root.html",
        {"categorias": categorias, "stats": stats, "banners": banners},
    )
