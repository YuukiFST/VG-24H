-- Funcoes e triggers (Trigger 1 e 2 do plano de trabalho v6)
-- Variaveis de sessao usadas pela aplicacao Django (setadas pelo middleware):
--   SELECT set_config('portal.perfil', 'COL', true);
--   SELECT set_config('portal.id_usuario_acao', '1', true);
-- [!] Essas variaveis sao injetadas pelo PortalUserMiddleware em middleware.py
--     e permitem que as triggers do banco saibam quem esta executando a acao.

BEGIN;

-- ============================================================================
-- TRIGGER 1 — AFTER INSERT em chamado
-- ============================================================================
-- [!] FINALIDADE: Todo chamado, ao ser criado, recebe AUTOMATICAMENTE um
--     registro em historico_chamado com status 'AB' (Aberto).
--     A aplicacao da APENAS 1 INSERT (em chamado). O trigger cuida do resto.
-- ============================================================================
CREATE OR REPLACE FUNCTION fn_chamado_after_insert_historico_ab()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_id_status INTEGER;                                  -- Variavel para armazenar o ID do status 'AB'
BEGIN
    -- Busca o ID do status 'AB' na tabela status_chamado
    SELECT id_status INTO v_id_status
    FROM status_chamado WHERE sigla = 'AB';

    -- Insere o primeiro historico: id_chamado = ID recem-criado, id_servidor = NULL (sistema),
    -- id_status = 'AB', observacao = NULL (ainda sem observacao)
    INSERT INTO historico_chamado (id_chamado, id_servidor, id_status, observacao)
    VALUES (NEW.id_chamado, NULL, v_id_status, NULL);

    RETURN NEW;  -- Obrigatorio em AFTER INSERT (retorna a nova linha)
END;
$$;

DROP TRIGGER IF EXISTS trg_chamado_after_insert_historico_ab ON chamado;
CREATE TRIGGER trg_chamado_after_insert_historico_ab
    AFTER INSERT ON chamado
    FOR EACH ROW          -- Dispara para CADA linha inserida
    EXECUTE PROCEDURE fn_chamado_after_insert_historico_ab();

-- ============================================================================
-- TRIGGER 2A — BEFORE UPDATE em chamado
-- ============================================================================
-- FINALIDADE: Atualiza automaticamente o campo atualizado_em sempre que
--     qualquer UPDATE ocorrer na tabela chamado.
-- ============================================================================
CREATE OR REPLACE FUNCTION fn_chamado_before_update_metadados()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    -- [!] BEFORE UPDATE: modifica NEW antes da gravacao.
    --     Nao precisa de UPDATE extra — apenas sobrescreve o valor de atualizado_em.
    NEW.atualizado_em := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_chamado_before_update_metadados ON chamado;
CREATE TRIGGER trg_chamado_before_update_metadados
    BEFORE UPDATE ON chamado
    FOR EACH ROW
    EXECUTE PROCEDURE fn_chamado_before_update_metadados();

-- ============================================================================
-- TRIGGER 2B — AFTER INSERT em historico_chamado (ANTES era AFTER UPDATE em chamado)
-- ============================================================================
-- [!] MOTIVO DA MUDANCA: Antes este trigger escutava AFTER UPDATE em chamado.
--     Com a remocao do id_status de chamado, agora escuta AFTER INSERT em
--     historico_chamado — que e a FONTE DA VERDADE do status atual.
--
-- EFEITOS:
--   1. Se novo status for CO ou CA → atualiza dt_conclusao no chamado
--   2. Se novo status for AB, EA ou EE → limpa dt_conclusao (=NULL)
--   3. Gera notificacao automatica: "Chamado XXXX: status alterado para ..."
-- ============================================================================
CREATE OR REPLACE FUNCTION fn_historico_after_insert_status()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    nova_sigla  CHAR(2);          -- Sigla do novo status (ex: 'CO', 'EA')
    desc_nova   VARCHAR(200);     -- Descricao do novo status (ex: 'Concluido')
    v_protocolo VARCHAR(20);      -- Numero de protocolo do chamado
    msg         VARCHAR(200);     -- Mensagem da notificacao
BEGIN
    -- Passo 1: Busca a sigla e descricao do status inserido
    SELECT sigla, descricao INTO nova_sigla, desc_nova
    FROM status_chamado WHERE id_status = NEW.id_status;

    -- Passo 2: Busca o numero de protocolo do chamado (para a notificacao)
    SELECT num_protocolo INTO v_protocolo
    FROM chamado WHERE id_chamado = NEW.id_chamado;

    -- Passo 3: Atualiza dt_conclusao conforme o tipo de status
    -- [!] CO (Concluido) ou CA (Cancelado) → marca data de conclusao
    --     Usa COALESCE para nao sobrescrever uma data ja existente
    IF nova_sigla IN ('CO', 'CA') THEN
        UPDATE chamado SET dt_conclusao = COALESCE(dt_conclusao, CURRENT_TIMESTAMP)
        WHERE id_chamado = NEW.id_chamado;
    -- Passo 4: AB, EA ou EE → limpa dt_conclusao (chamado reaberto ou em andamento)
    ELSIF nova_sigla IN ('AB', 'EA', 'EE') THEN
        UPDATE chamado SET dt_conclusao = NULL
        WHERE id_chamado = NEW.id_chamado;
    END IF;

    -- Passo 5: Gera notificacao automatica (limitada a 200 chars com a funcao left())
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
