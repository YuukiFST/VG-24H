-- View de estatisticas (painel do Gestor — controle de acesso na aplicacao)
--
-- ============================================================================
-- vw_estatisticas_chamados
-- ============================================================================
-- [!] DESTAQUE: Usa JOIN LATERAL para buscar o ULTIMO status de cada chamado
--     na tabela historico_chamado. Diferenca pratica:
--       - Sem LATERAL: precisaria de uma subconsulta complexa com GROUP BY
--       - Com LATERAL: executa a subconsulta para CADA linha de chamado,
--         pegando apenas 1 registro (LIMIT 1) — o mais recente.
--
--     A view retorna: total de chamados agrupados por (categoria, bairro,
--     status), considerando apenas registros ativos.
--
--     Uso: Dashboard do Gestor — exibe graficos de chamados por regiao e status.
-- ============================================================================

BEGIN;

DROP VIEW IF EXISTS vw_estatisticas_chamados;

CREATE VIEW vw_estatisticas_chamados AS
SELECT
    cat.nome        AS categoria,          -- Nome da categoria de servico
    b.nome_bairro   AS bairro,             -- Nome do bairro
    s.sigla         AS sigla_status,       -- Sigla do status (AB, EA, EE, CO, CA)
    s.descricao     AS status_descricao,   -- Descricao do status
    COUNT(*)::BIGINT AS total_chamados     -- Quantidade de chamados (cast para BIGINT)
FROM chamado ch
-- JOIN 1: chamado → servico → categoria_servico (cadeia de FKs)
JOIN servico srv     ON srv.id_servico  = ch.id_servico
JOIN categoria_servico cat ON cat.id_categoria = srv.id_categoria
-- JOIN 2: chamado → bairro (localizacao)
JOIN bairro b        ON b.id_bairro     = ch.id_bairro
-- [!] JOIN 3: LATERAL — busca o ultimo status de cada chamado no historico
--     A subconsulta roda para CADA chamado (como um foreach), ordena por
--     dt_alteracao DESC e pega apenas 1 registro (o mais recente).
JOIN LATERAL (
    SELECT id_status FROM historico_chamado
    WHERE id_chamado = ch.id_chamado
    ORDER BY dt_alteracao DESC LIMIT 1
) ultimo_h ON TRUE
-- JOIN 4: status_chamado — pega a sigla e descricao do status atual
JOIN status_chamado s ON s.id_status = ultimo_h.id_status
-- Filtra apenas registros ativos (soft delete)
WHERE cat.ativo
  AND srv.ativo
  AND b.ativo
-- Agrupamento: um registro por (categoria, bairro, status)
GROUP BY cat.nome, b.nome_bairro, s.sigla, s.descricao;

COMMIT;
