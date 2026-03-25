-- Executar a partir da pasta database/:
--   psql -U usuario -d portal_vg -v ON_ERROR_STOP=1 -f 00_install_all.sql

\i 01_schema.sql
\i 02_seed.sql
\i 03_functions_triggers.sql
\i 04_rules.sql
\i 05_views.sql
