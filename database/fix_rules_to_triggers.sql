-- FIX: Converte Rules condicionais para Triggers BEFORE
-- (Rules condicionais impedem INSERT RETURNING do Django ORM)
-- Execute este script no NeonDB SQL Editor

BEGIN;

-- 1) DROP das rules antigas
DROP RULE IF EXISTS r01_foto_chamado_encerrado ON foto_chamado;
DROP RULE IF EXISTS r02_historico_observacao_encerrado ON historico_chamado;
DROP RULE IF EXISTS r03_chamado_avaliacao_imutavel ON chamado;

-- 2) Trigger: foto_chamado — impede INSERT se chamado CO/CA
CREATE OR REPLACE FUNCTION fn_rule_foto_chamado_encerrado()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM historico_chamado hc
        JOIN status_chamado s ON s.id_status = hc.id_status
        WHERE hc.id_chamado = NEW.id_chamado
          AND s.sigla IN ('CO', 'CA')
          AND hc.dt_alteracao = (
              SELECT MAX(dt_alteracao) FROM historico_chamado WHERE id_chamado = NEW.id_chamado
          )
    ) THEN
        RAISE EXCEPTION 'Chamado encerrado (CO/CA): não é permitido adicionar fotos.';
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_foto_chamado_encerrado ON foto_chamado;
CREATE TRIGGER trg_foto_chamado_encerrado
    BEFORE INSERT ON foto_chamado
    FOR EACH ROW EXECUTE FUNCTION fn_rule_foto_chamado_encerrado();

-- 3) Trigger: historico_chamado — impede INSERT de observação se CO/CA
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
        RAISE EXCEPTION 'Chamado encerrado (CO/CA): não é permitido adicionar observações.';
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_historico_obs_encerrado ON historico_chamado;
CREATE TRIGGER trg_historico_obs_encerrado
    BEFORE INSERT ON historico_chamado
    FOR EACH ROW EXECUTE FUNCTION fn_rule_historico_obs_encerrado();

-- 4) Trigger: chamado — impede alterar avaliação já preenchida
CREATE OR REPLACE FUNCTION fn_rule_avaliacao_imutavel()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF OLD.nota_avaliacao IS NOT NULL
       AND (
           NEW.nota_avaliacao IS DISTINCT FROM OLD.nota_avaliacao
           OR NEW.comentario_avaliacao IS DISTINCT FROM OLD.comentario_avaliacao
       )
    THEN
        RAISE EXCEPTION 'A avaliação já foi registrada e não pode ser alterada.';
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_avaliacao_imutavel ON chamado;
CREATE TRIGGER trg_avaliacao_imutavel
    BEFORE UPDATE ON chamado
    FOR EACH ROW EXECUTE FUNCTION fn_rule_avaliacao_imutavel();

COMMIT;
