-- View de estatísticas (painel do Administrador — controle de acesso na aplicação)

BEGIN;

DROP VIEW IF EXISTS vw_estatisticas_chamados;

CREATE VIEW vw_estatisticas_chamados AS
SELECT
    cat.nome AS categoria,
    b.nome AS bairro,
    s.tipo_status,
    s.descricao AS status_descricao,
    COUNT(*)::BIGINT AS total_chamados
FROM chamado ch
JOIN servico srv ON srv.id_servico = ch.id_servico
JOIN categoria_servico cat ON cat.id_categoria = srv.id_categoria
JOIN bairro_regiao b ON b.id_bairro = ch.id_bairro
JOIN status_chamado s ON s.id_status = ch.id_status
WHERE cat.ativo
  AND srv.ativo
  AND b.ativo
GROUP BY cat.nome, b.nome, s.tipo_status, s.descricao;

COMMIT;
