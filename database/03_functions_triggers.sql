-- Funções e triggers (Trigger 1 e 2 do plano de trabalho)
-- Variáveis de sessão usadas pela aplicação Django (SET LOCAL opcional):
--   SELECT set_config('portal.perfil', 'COL', true);
--   SELECT set_config('portal.id_usuario_acao', '1', true);

BEGIN;

CREATE OR REPLACE FUNCTION fn_chamado_after_insert_historico_ab()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO historico_chamado (id_chamado, id_usuario_responsavel, tipo_status, observacao)
    VALUES (NEW.id_chamado, NEW.id_usuario, 'AB', NULL);
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_chamado_after_insert_historico_ab ON chamado;
CREATE TRIGGER trg_chamado_after_insert_historico_ab
    AFTER INSERT ON chamado
    FOR EACH ROW
    EXECUTE PROCEDURE fn_chamado_after_insert_historico_ab();

CREATE OR REPLACE FUNCTION fn_chamado_before_update_metadados()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    novo_tipo CHAR(2);
BEGIN
    NEW.atualizado_em := CURRENT_TIMESTAMP;

    IF NEW.id_status IS DISTINCT FROM OLD.id_status THEN
        SELECT tipo_status INTO novo_tipo FROM status_chamado WHERE id_status = NEW.id_status;
        IF novo_tipo IN ('CO', 'CA') THEN
            NEW.dt_conclusao := COALESCE(NEW.dt_conclusao, CURRENT_TIMESTAMP);
        ELSIF novo_tipo IN ('AB', 'AN', 'EX') THEN
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

CREATE OR REPLACE FUNCTION fn_chamado_after_update_status()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    tipo_novo CHAR(2);
    desc_nova VARCHAR(200);
    uid_acao  INTEGER;
    msg       VARCHAR(200);
BEGIN
    IF NEW.id_status IS NOT DISTINCT FROM OLD.id_status THEN
        RETURN NEW;
    END IF;

    SELECT tipo_status INTO tipo_novo FROM status_chamado WHERE id_status = NEW.id_status;
    SELECT descricao INTO desc_nova FROM status_chamado WHERE id_status = NEW.id_status;

    BEGIN
        uid_acao := NULLIF(current_setting('portal.id_usuario_acao', true), '')::INTEGER;
    EXCEPTION
        WHEN invalid_text_representation THEN
            uid_acao := NULL;
    END;

    INSERT INTO historico_chamado (id_chamado, id_usuario_responsavel, tipo_status, observacao)
    VALUES (NEW.id_chamado, uid_acao, tipo_novo, NULL);

    msg := left(
        'Chamado ' || NEW.protocolo || ': status alterado para ' || COALESCE(desc_nova, tipo_novo),
        200
    );

    INSERT INTO notificacao (id_usuario, id_chamado, mensagem)
    VALUES (NEW.id_usuario, NEW.id_chamado, msg);

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_chamado_after_update_status ON chamado;
CREATE TRIGGER trg_chamado_after_update_status
    AFTER UPDATE ON chamado
    FOR EACH ROW
    EXECUTE PROCEDURE fn_chamado_after_update_status();

COMMIT;
