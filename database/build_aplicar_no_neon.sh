#!/usr/bin/env bash
# ============================================================================
# build_aplicar_no_neon.sh — regenera o consolidado a partir das fontes 01..05
# ============================================================================
# POR QUE EXISTE: o SQL Editor do Neon nao suporta o comando \i (include) do
# psql, entao 00_install_all.sql (que usa \i) nao roda la. Para instalar no
# Neon precisamos de UM arquivo unico. Este script concatena os scripts
# canonicos na ordem correta e gera database/aplicar_no_neon.sql.
#
# Assim o consolidado NUNCA diverge das fontes (a divergencia manual ja tinha
# causado bug: rules antigas em vez de triggers, tabela protocolo_seq ausente,
# descricoes de status prefixadas). Sempre rode este script apos editar 01..05.
#
# USO:  bash database/build_aplicar_no_neon.sh
# ============================================================================
set -euo pipefail
cd "$(dirname "$0")"

OUT=aplicar_no_neon.sql
FONTES=(01_schema 02_seed 03_functions_triggers 04_rules 05_views)

{
    echo "-- ============================================================================"
    echo "-- aplicar_no_neon.sql — ARQUIVO GERADO AUTOMATICAMENTE. NAO EDITE A MAO."
    echo "-- ============================================================================"
    echo "-- Fonte: ${FONTES[*]}"
    echo "-- Regenere com:  bash database/build_aplicar_no_neon.sh"
    echo "-- Cole o conteudo inteiro no SQL Editor do Neon (que nao suporta \\i)."
    echo "-- Para instalar via psql local, prefira: psql ... -f 00_install_all.sql"
    echo "-- ============================================================================"
    echo
    for f in "${FONTES[@]}"; do
        echo "-- >>>>>>>>>>>>>>>>>>>>>>>>  ${f}.sql  >>>>>>>>>>>>>>>>>>>>>>>>"
        cat "${f}.sql"
        echo
    done
} > "$OUT"

echo "Gerado ${OUT} ($(wc -l < "$OUT") linhas) a partir de: ${FONTES[*]}"
