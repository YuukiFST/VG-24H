-- ============================================================================
-- 00_install_all.sql — Script MASTER para instalacao completa do banco
-- ============================================================================
-- Executar a partir da pasta database/:
--   psql -U usuario -d portal_vg -v ON_ERROR_STOP=1 -f 00_install_all.sql
--
-- [!] Este arquivo apenas ORQUESTRA a execucao dos scripts individuais.
--     Veja os comentarios detalhados em cada arquivo-fonte:
--       01_schema.sql           → estrutura das 11 tabelas
--       02_seed.sql             → carga inicial
--       03_functions_triggers.sql → T1, T2A, T2B
--       04_rules.sql            → triggers de integridade + R5 + Extra
--       05_views.sql            → view com JOIN LATERAL
-- ============================================================================

\i 01_schema.sql
\i 02_seed.sql
\i 03_functions_triggers.sql
\i 04_rules.sql
\i 05_views.sql
