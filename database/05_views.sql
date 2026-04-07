-- View de estatísticas (painel do Gestor — controle de acesso na aplicação)

BEGIN;

DROP VIEW IF EXISTS vw_estatisticas_chamados;

CREATE VIEW vw_estatisticas_chamados AS
SELECT
    cat.nome        AS categoria,
    b.nome_bairro   AS bairro,
    s.sigla         AS sigla_status,
    s.descricao     AS status_descricao,
    COUNT(*)::BIGINT AS total_chamados
FROM chamado ch
JOIN servico srv     ON srv.id_servico  = ch.id_servico
JOIN categoria_servico cat ON cat.id_categoria = srv.id_categoria
JOIN bairro b        ON b.id_bairro     = ch.id_bairro
JOIN LATERAL (
    SELECT id_status FROM historico_chamado
    WHERE id_chamado = ch.id_chamado
    ORDER BY dt_alteracao DESC LIMIT 1
) ultimo_h ON TRUE
JOIN status_chamado s ON s.id_status = ultimo_h.id_status
WHERE cat.ativo
  AND srv.ativo
  AND b.ativo
GROUP BY cat.nome, b.nome_bairro, s.sigla, s.descricao;

COMMIT;
