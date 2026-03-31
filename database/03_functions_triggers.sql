-- Funções e triggers (Trigger 1 e 2 do plano de trabalho v6)
-- Variáveis de sessão usadas pela aplicação Django:
--   SELECT set_config('portal.perfil', 'COL', true);
--   SELECT set_config('portal.id_usuario_acao', '1', true);

BEGIN;

-- ============================================================
-- Trigger 1 — AFTER INSERT em chamado:
-- Insere automaticamente o primeiro registro em historico_chamado
-- com status AB, garantindo que todo chamado nasça com ao menos um histórico.
-- ============================================================
CREATE OR REPLACE FUNCTION fn_chamado_after_insert_historico_ab()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_id_status INTEGER;
BEGIN
    SELECT id_status INTO v_id_status
    FROM status_chamado WHERE sigla = 'AB';

    INSERT INTO historico_chamado (id_chamado, id_servidor, id_status, observacao)
    VALUES (NEW.id_chamado, NULL, v_id_status, NULL);

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_chamado_after_insert_historico_ab ON chamado;
CREATE TRIGGER trg_chamado_after_insert_historico_ab
    AFTER INSERT ON chamado
    FOR EACH ROW
    EXECUTE PROCEDURE fn_chamado_after_insert_historico_ab();

-- ============================================================
-- Trigger 2 part A — BEFORE UPDATE em chamado:
-- Quando id_status é alterado, atualiza metadados:
--   1. Preenche dt_conclusao se novo status é CO
--   2. Atualiza atualizado_em
-- ============================================================
CREATE OR REPLACE FUNCTION fn_chamado_before_update_metadados()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    nova_sigla CHAR(2);
BEGIN
    NEW.atualizado_em := CURRENT_TIMESTAMP;

    IF NEW.id_status IS DISTINCT FROM OLD.id_status THEN
        SELECT sigla INTO nova_sigla FROM status_chamado WHERE id_status = NEW.id_status;
        IF nova_sigla IN ('CO', 'CA') THEN
            NEW.dt_conclusao := COALESCE(NEW.dt_conclusao, CURRENT_TIMESTAMP);
        ELSIF nova_sigla IN ('AB', 'AN', 'EX') THEN
            NEW.dt_conclusao := NULL;
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_chamado_before_update_metadados ON chamado;
CREATE TRIGGER trg_chamado_before_update_metadados
    BEFORE UPDATE ON chamado
    FOR EACH ROW
    EXECUTE PROCEDURE fn_chamado_before_update_metadados();

-- ============================================================
-- Trigger 2 part B — AFTER UPDATE em chamado:
-- Quando id_status é alterado, executa:
--   1. Insere registro em historico_chamado
--   2. Insere aviso em notificacao para o cidadão dono do chamado
-- ============================================================
CREATE OR REPLACE FUNCTION fn_chamado_after_update_status()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    nova_sigla  CHAR(2);
    desc_nova   VARCHAR(200);
    uid_acao    INTEGER;
    msg         VARCHAR(200);
BEGIN
    IF NEW.id_status IS NOT DISTINCT FROM OLD.id_status THEN
        RETURN NEW;
    END IF;

    SELECT sigla INTO nova_sigla FROM status_chamado WHERE id_status = NEW.id_status;
    SELECT descricao INTO desc_nova FROM status_chamado WHERE id_status = NEW.id_status;

    -- Recuperar id do servidor que fez a ação (sessão Django)
    BEGIN
        uid_acao := NULLIF(current_setting('portal.id_usuario_acao', true), '')::INTEGER;
    EXCEPTION
        WHEN invalid_text_representation THEN
            uid_acao := NULL;
    END;

    -- 1. Histórico
    INSERT INTO historico_chamado (id_chamado, id_servidor, id_status, observacao)
    VALUES (NEW.id_chamado, uid_acao, NEW.id_status, NULL);

    -- 2. Notificação
    msg := left(
        'Chamado ' || NEW.num_protocolo || ': status alterado para ' || COALESCE(desc_nova, nova_sigla),
        200
    );

    INSERT INTO notificacao (id_chamado, mensagem)
    VALUES (NEW.id_chamado, msg);

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_chamado_after_update_status ON chamado;
CREATE TRIGGER trg_chamado_after_update_status
    AFTER UPDATE ON chamado
    FOR EACH ROW
    EXECUTE PROCEDURE fn_chamado_after_update_status();

COMMIT;
