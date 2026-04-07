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
-- Atualiza atualizado_em a cada UPDATE
-- ============================================================
CREATE OR REPLACE FUNCTION fn_chamado_before_update_metadados()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.atualizado_em := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_chamado_before_update_metadados ON chamado;
CREATE TRIGGER trg_chamado_before_update_metadados
    BEFORE UPDATE ON chamado
    FOR EACH ROW
    EXECUTE PROCEDURE fn_chamado_before_update_metadados();

-- ============================================================
-- Trigger 2 part B — AFTER INSERT em historico_chamado:
-- Quando um novo registro de histórico é inserido:
--   1. Atualiza dt_conclusao no chamado se status for CO/CA
--   2. Insere aviso em notificacao para o cidadão dono do chamado
-- ============================================================
CREATE OR REPLACE FUNCTION fn_historico_after_insert_status()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    nova_sigla  CHAR(2);
    desc_nova   VARCHAR(200);
    v_protocolo VARCHAR(20);
    msg         VARCHAR(200);
BEGIN
    SELECT sigla, descricao INTO nova_sigla, desc_nova
    FROM status_chamado WHERE id_status = NEW.id_status;

    SELECT num_protocolo INTO v_protocolo
    FROM chamado WHERE id_chamado = NEW.id_chamado;

    -- Atualiza dt_conclusao conforme status
    IF nova_sigla IN ('CO', 'CA') THEN
        UPDATE chamado SET dt_conclusao = COALESCE(dt_conclusao, CURRENT_TIMESTAMP)
        WHERE id_chamado = NEW.id_chamado;
    ELSIF nova_sigla IN ('AB', 'EA', 'EE') THEN
        UPDATE chamado SET dt_conclusao = NULL
        WHERE id_chamado = NEW.id_chamado;
    END IF;

    -- Notificação
    msg := left(
        'Chamado ' || v_protocolo || ': status alterado para ' || COALESCE(desc_nova, nova_sigla),
        200
    );

    INSERT INTO notificacao (id_chamado, mensagem)
    VALUES (NEW.id_chamado, msg);

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_historico_after_insert_status ON historico_chamado;
CREATE TRIGGER trg_historico_after_insert_status
    AFTER INSERT ON historico_chamado
    FOR EACH ROW
    EXECUTE PROCEDURE fn_historico_after_insert_status();

COMMIT;
