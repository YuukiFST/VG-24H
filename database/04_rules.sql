-- Regras de integridade (plano de trabalho v6)
-- A aplicacao deve definir o perfil na sessao ao alterar chamados:
--   SELECT set_config('portal.perfil', 'CID', true);  -- ou 'COL' / 'GES'
-- [!] As variaveis de sessao sao setadas pelo PortalUserMiddleware (middleware.py).

BEGIN;

-- ============================================================================
-- R1 → Trigger: trg_foto_chamado_encerrado (CONVERTIDO de Rule para Trigger)
-- ============================================================================
-- [!] ANTES era uma Rule condicional (DO INSTEAD NOTHING). Foi convertida para
--     Trigger BEFORE com RAISE EXCEPTION porque Rules condicionais impedem o
--     INSERT RETURNING usado pelo Django ORM para obter o ID recem-criado.
--
-- FINALIDADE: Bloqueia INSERT em foto_chamado se o ultimo status do chamado
--     for CO (Concluido) ou CA (Cancelado). O trigger verifica no historico.
-- ============================================================================
DROP RULE IF EXISTS r01_foto_chamado_encerrado ON foto_chamado;

CREATE OR REPLACE FUNCTION fn_rule_foto_chamado_encerrado()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    -- [!] Subconsulta: verifica se existe algum historico onde o ultimo status
    --     do chamado seja CO ou CA. Usa MAX(dt_alteracao) para pegar o ultimo.
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
        -- [!] RAISE EXCEPTION (em vez de DO INSTEAD NOTHING): retorna erro explicito
        --     que o backend Python captura e exibe ao usuario.
        RAISE EXCEPTION 'Chamado encerrado (CO/CA): nao e permitido adicionar fotos.';
    END IF;
    RETURN NEW;  -- Libera o INSERT se a verificacao passou
END;
$$;

DROP TRIGGER IF EXISTS trg_foto_chamado_encerrado ON foto_chamado;
CREATE TRIGGER trg_foto_chamado_encerrado
    BEFORE INSERT ON foto_chamado          -- BEFORE: executa ANTES da gravacao
    FOR EACH ROW EXECUTE FUNCTION fn_rule_foto_chamado_encerrado();

-- ============================================================================
-- R2 → Trigger: trg_historico_obs_encerrado (CONVERTIDO de Rule para Trigger)
-- ============================================================================
-- FINALIDADE: Bloqueia INSERT de observacao em historico_chamado se o chamado
--     ja estiver encerrado (CO/CA). Permite mudanca de status mesmo em encerrado
--     (ex: reabrir), mas nao permite acrescentar observacao.
-- ============================================================================
DROP RULE IF EXISTS r02_historico_observacao_encerrado ON historico_chamado;

CREATE OR REPLACE FUNCTION fn_rule_historico_obs_encerrado()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    -- Verifica se: (1) ha observacao sendo inserida E (2) o ultimo status do chamado e CO/CA
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
-- R3 → Trigger: trg_avaliacao_imutavel (CONVERTIDO de Rule para Trigger)
-- ============================================================================
-- FINALIDADE: Uma vez que o cidadao avalia o chamado (nota_avaliacao),
--     nao e possivel alterar nem a nota nem o comentario.
--     [!] Usa IS DISTINCT FROM (compara tratando NULL como valor valido).
-- ============================================================================
DROP RULE IF EXISTS r03_chamado_avaliacao_imutavel ON chamado;

CREATE OR REPLACE FUNCTION fn_rule_avaliacao_imutavel()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    -- Se a avaliacao ja foi preenchida (OLD.nota_avaliacao IS NOT NULL)
    -- e houve alteracao na nota OU no comentario, bloqueia.
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

-- ============================================================================
-- R4 — REMOVIDA: restricoes de mudanca de status por perfil
-- ============================================================================
-- Justificativa: sem id_status direto em chamado, controle de perfil
-- passa a ser feito na camada de aplicacao (Django views usando os decorators
-- @perfis("CID"), @perfis("COL"), @perfis("GES") em decorators.py).

-- ============================================================================
-- R5 — Trigger: historico_chamado IMUTAVEL (UPDATE proibido)
-- ============================================================================
-- [!] Apenas UPDATE é bloqueado (auditoria). DELETE é permitido pois
--     a exclusão de chamado (gestao_chamado_excluir) registra log de
--     auditoria no histórico e depois remove os registros associados.
-- FINALIDADE: Preservar a auditoria. NENHUM registro de historico
--     pode ser alterado depois de criado.
-- ============================================================================
DROP RULE IF EXISTS r05_historico_sem_update ON historico_chamado;
DROP RULE IF EXISTS r05_historico_sem_delete ON historico_chamado;

DROP TRIGGER IF EXISTS trg_historico_sem_update ON historico_chamado;
CREATE OR REPLACE FUNCTION fn_historico_sem_update()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Histórico de chamado é imutável: UPDATE não permitido.';
END;
$$;
CREATE TRIGGER trg_historico_sem_update
    BEFORE UPDATE ON historico_chamado
    FOR EACH ROW EXECUTE FUNCTION fn_historico_sem_update();

-- ============================================================================
-- R6 — REMOVIDA: validacao de resolucao obrigatoria
-- ============================================================================
-- Justificativa: sem id_status direto em chamado, a validacao de resolucao
-- obrigatoria ao concluir e feita na camada de aplicacao (Django forms).

-- ============================================================================
-- EXTRA — Trigger: chamado DELETE protegido por log de auditoria
-- ============================================================================
-- ============================================================================
-- R5b — Trigger: historico_chamado DELETE protegido (auditoria)
-- ============================================================================
-- [!] DELETE em historico_chamado so e permitido quando a view
--     gestao_chamado_excluir seta portal.excluindo = 'true' na sessao.
--     Protege o audit trail contra DELETEs via SQL direto (psql, injection).
-- FINALIDADE: Preservar trilha de auditoria. Apenas a exclusao completa
--     de um chamado (com log) pode remover registros do historico.
-- ============================================================================
CREATE OR REPLACE FUNCTION fn_historico_sem_delete()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF current_setting('portal.excluindo', true) IS DISTINCT FROM 'true' THEN
        RAISE EXCEPTION 'Historico de chamado e imutavel: DELETE nao permitido diretamente.';
    END IF;
    RETURN OLD;
END;
$$;

DROP TRIGGER IF EXISTS trg_historico_sem_delete ON historico_chamado;
CREATE TRIGGER trg_historico_sem_delete
    BEFORE DELETE ON historico_chamado
    FOR EACH ROW EXECUTE FUNCTION fn_historico_sem_delete();

-- ============================================================================
-- EXTRA — Trigger: chamado DELETE protegido por sessao
-- ============================================================================
-- [!] DELETE em chamado so e permitido quando a view
--     gestao_chamado_excluir seta portal.excluindo = 'true' na sessao.
--     A view insere log de auditoria e exclui registros filhos primeiro.
--     Protegido por @perfis('GES') na camada de aplicacao.
-- FINALIDADE: Rastreabilidade — toda exclusao deixa registro e passa
--     exclusivamente pelo fluxo controlado da aplicacao.
-- ============================================================================
CREATE OR REPLACE FUNCTION fn_chamado_sem_delete()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF current_setting('portal.excluindo', true) IS DISTINCT FROM 'true' THEN
        RAISE EXCEPTION 'Chamado nao pode ser excluido diretamente. Use a interface de exclusao no portal.';
    END IF;
    RETURN OLD;
END;
$$;

DROP TRIGGER IF EXISTS trg_chamado_sem_delete ON chamado;
CREATE TRIGGER trg_chamado_sem_delete
    BEFORE DELETE ON chamado
    FOR EACH ROW EXECUTE FUNCTION fn_chamado_sem_delete();

COMMIT;
