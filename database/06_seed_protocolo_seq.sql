-- ============================================================
-- Seed: Sincroniza protocolo_seq com chamados existentes
-- ============================================================
-- Quando novos chamados sao inseridos manualmente (testes,
-- migracao de dados) sem passar por proximo_protocolo(), a
-- sequencia protocolo_seq fica dessincronizada e comeca a
-- gerar numeros que ja existem, causando IntegrityError.
--
-- Este script ajusta protocolo_seq para o maior sequencial
-- existente em chamado para cada ano.
--
-- Deve ser executado sempre que chamados forem inseridos
-- fora do fluxo normal (restore, migracao, seed manual).
-- ============================================================

INSERT INTO protocolo_seq (ano, ultimo_numero)
SELECT
    LEFT(num_protocolo, 4)::INT AS ano,
    MAX(RIGHT(num_protocolo, 6)::INT) AS ultimo_numero
FROM chamado
GROUP BY ano
ON CONFLICT (ano) DO UPDATE
    SET ultimo_numero = GREATEST(protocolo_seq.ultimo_numero, EXCLUDED.ultimo_numero);
