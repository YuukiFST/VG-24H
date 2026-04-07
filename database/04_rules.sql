-- Rules do plano de trabalho v6
-- A aplicação deve definir o perfil na sessão ao alterar chamados:
--   SELECT set_config('portal.perfil', 'CID', true);  -- ou 'COL' / 'GES'

BEGIN;

-- ============================================================
-- Rule 1 → Trigger: foto_chamado: impede INSERT se chamado CO/CA
-- (Convertido de Rule para Trigger para compatibilidade com
--  INSERT RETURNING usado pelo Django ORM)
-- ============================================================
DROP RULE IF EXISTS r01_foto_chamado_encerrado ON foto_chamado;

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

-- ============================================================
-- Rule 2 → Trigger: historico_chamado: impede INSERT de observação
-- se o chamado estiver com status CO ou CA
-- ============================================================
DROP RULE IF EXISTS r02_historico_observacao_encerrado ON historico_chamado;

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

-- ============================================================
-- Rule 3 → Trigger: chamado: impede alterar avaliação já preenchida
-- ============================================================
DROP RULE IF EXISTS r03_chamado_avaliacao_imutavel ON chamado;

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

-- ============================================================
-- Rule 4 — chamado: restrições de mudança de status por perfil
-- CID: não pode alterar status se CO ou CA; não pode cancelar se EX
-- COL: não pode alterar status se CO ou CA
-- GES: sem restrição (isento)
-- ============================================================
-- Rule 4 removida: sem id_status direto em chamado, controle de
-- perfil será feito na camada de aplicação (Django views).

-- ============================================================
-- Rule 5 — historico_chamado: impede UPDATE e DELETE em registros
-- já inseridos, para todos os perfis, preservando o histórico
-- ============================================================
DROP RULE IF EXISTS r05_historico_sem_update ON historico_chamado;
CREATE RULE r05_historico_sem_update AS ON UPDATE TO historico_chamado
DO INSTEAD NOTHING;

DROP RULE IF EXISTS r05_historico_sem_delete ON historico_chamado;
CREATE RULE r05_historico_sem_delete AS ON DELETE TO historico_chamado
DO INSTEAD NOTHING;

-- ============================================================
-- Rule 6 — chamado: impede UPDATE do status para CO ou CA
-- se o campo resolução estiver NULL ou vazio
-- ============================================================
-- Rule 6 removida: sem id_status direto em chamado, validação de
-- resolução obrigatória será feita na camada de aplicação (Django views).

-- Extra: impede DELETE em chamado (integridade)
DROP RULE IF EXISTS rx_chamado_sem_delete ON chamado;
CREATE RULE rx_chamado_sem_delete AS ON DELETE TO chamado DO INSTEAD NOTHING;

COMMIT;
