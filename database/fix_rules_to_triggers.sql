-- ============================================================================
-- FIX: Converte Rules condicionais para Triggers BEFORE
-- ============================================================================
-- [!] MOTIVO DA CONVERSÃO (PONTO CRITICO PARA A APRESENTACAO):
--     Rules condicionais com DO INSTEAD NOTHING impedem o INSERT RETURNING
--     usado pelo Django ORM para obter o ID recem-criado (ex: ao inserir
--     uma foto, o Python precisa do id_foto retornado).
--
--     Triggers BEFORE com RAISE EXCEPTION:
--       - Funcionam: retornam erro EXPLICITO que o Python captura
--       - Nao bloqueiam INSERT RETURNING (o trigger executa antes)
--
-- Execute este script no NeonDB SQL Editor em bancos ja existentes.
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1) DROP das rules antigas (necessario antes de criar os triggers
--    com o mesmo nome de funcao — CREATE OR REPLACE FUNCTION precisa
--    que a funcao exista ou nao, mas as rules precisam ser removidas)
-- ============================================================================
DROP RULE IF EXISTS r01_foto_chamado_encerrado ON foto_chamado;
DROP RULE IF EXISTS r02_historico_observacao_encerrado ON historico_chamado;
DROP RULE IF EXISTS r03_chamado_avaliacao_imutavel ON chamado;

-- ============================================================================
-- 2) Trigger: foto_chamado — impede INSERT se chamado estiver CO/CA
-- ============================================================================
CREATE OR REPLACE FUNCTION fn_rule_foto_chamado_encerrado()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF EXISTS (
        -- Verifica se o ultimo status do chamado e CO ou CA
        SELECT 1
        FROM historico_chamado hc
        JOIN status_chamado s ON s.id_status = hc.id_status
        WHERE hc.id_chamado = NEW.id_chamado
          AND s.sigla IN ('CO', 'CA')
          AND hc.dt_alteracao = (
              SELECT MAX(dt_alteracao) FROM historico_chamado WHERE id_chamado = NEW.id_chamado
          )
    ) THEN
        RAISE EXCEPTION 'Chamado encerrado (CO/CA): nao e permitido adicionar fotos.';
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_foto_chamado_encerrado ON foto_chamado;
CREATE TRIGGER trg_foto_chamado_encerrado
    BEFORE INSERT ON foto_chamado
    FOR EACH ROW EXECUTE FUNCTION fn_rule_foto_chamado_encerrado();

-- ============================================================================
-- 3) Trigger: historico_chamado — impede INSERT de observacao se CO/CA
-- ============================================================================
CREATE OR REPLACE FUNCTION fn_rule_historico_obs_encerrado()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.observacao IS NOT NULL AND EXISTS (
        SELECT 1
        FROM historico_chamado hc
        JOIN status_chamado s ON s.id_status = hc.id_status
        WHERE hc.id_chamado = NEW.id_chamado
          AND s.sigla IN ('CO', 'CA')
          AND hc.dt_alteracao = (
              SELECT MAX(dt_alteracao) FROM historico_chamado WHERE id_chamado = NEW.id_chamado
          )
    ) THEN
        RAISE EXCEPTION 'Chamado encerrado (CO/CA): nao e permitido adicionar observacoes.';
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_historico_obs_encerrado ON historico_chamado;
CREATE TRIGGER trg_historico_obs_encerrado
    BEFORE INSERT ON historico_chamado
    FOR EACH ROW EXECUTE FUNCTION fn_rule_historico_obs_encerrado();

-- ============================================================================
-- 4) Trigger: chamado — impede alterar avaliacao ja preenchida
-- ============================================================================
CREATE OR REPLACE FUNCTION fn_rule_avaliacao_imutavel()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    -- Se ja existe nota_avaliacao preenchida E o novo valor e diferente → bloqueia
    IF OLD.nota_avaliacao IS NOT NULL
       AND (
           NEW.nota_avaliacao IS DISTINCT FROM OLD.nota_avaliacao
           OR NEW.comentario_avaliacao IS DISTINCT FROM OLD.comentario_avaliacao
       )
    THEN
        RAISE EXCEPTION 'A avaliacao ja foi registrada e nao pode ser alterada.';
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_avaliacao_imutavel ON chamado;
CREATE TRIGGER trg_avaliacao_imutavel
    BEFORE UPDATE ON chamado
    FOR EACH ROW EXECUTE FUNCTION fn_rule_avaliacao_imutavel();

COMMIT;
