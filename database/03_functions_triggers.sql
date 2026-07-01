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

-- ============================================================================
-- STORED FUNCTION — fn_proximo_protocolo(ano)
-- ============================================================================
-- [!] FINALIDADE: gerar o proximo numero de protocolo de forma ATOMICA dentro
--     do proprio banco. E a stored function/procedure exigida pelo projeto
--     (regra de negocio + insert atomico no banco). Formato: ANO(4) + seq(6).
--     Ex.: 2026000001.
--
--     Chamada pela aplicacao em utils.proximo_protocolo():
--         SELECT fn_proximo_protocolo(2026);
--
--     ATOMICIDADE: o INSERT ... ON CONFLICT DO UPDATE ... RETURNING faz o
--     Postgres serializar o UPDATE da linha do ano, entao dois pedidos
--     simultaneos NUNCA recebem o mesmo numero (sem race condition). Se por
--     alguma dessincronizacao o numero ja existir em chamado, o LOOP avanca
--     ate encontrar um livre (pode deixar buracos na sequencia, e aceitavel).
--
--     PORTABILIDADE: usa apenas PL/pgSQL padrao (ON CONFLICT, lpad) — sem
--     recursos exclusivos do Neon; compativel com PostgreSQL 13+.
-- ============================================================================
CREATE OR REPLACE FUNCTION fn_proximo_protocolo(p_ano INTEGER)
RETURNS VARCHAR
LANGUAGE plpgsql
AS $$
DECLARE
    v_numero    INTEGER;       -- sequencial devolvido pelo contador do ano
    v_protocolo VARCHAR(20);   -- protocolo final montado (ano + sequencial)
BEGIN
    LOOP
        -- passo atomico: cria a linha do ano com 1, ou incrementa +1 se ja existe
        INSERT INTO protocolo_seq (ano, ultimo_numero)
        VALUES (p_ano, 1)
        ON CONFLICT (ano)
            DO UPDATE SET ultimo_numero = protocolo_seq.ultimo_numero + 1
        RETURNING ultimo_numero INTO v_numero;

        -- monta ANO + sequencial de 6 digitos com zeros a esquerda (lpad)
        v_protocolo := p_ano::TEXT || lpad(v_numero::TEXT, 6, '0');

        -- se esse protocolo ainda nao existe em chamado, esta livre -> devolve
        EXIT WHEN NOT EXISTS (
            SELECT 1 FROM chamado WHERE num_protocolo = v_protocolo
        );
        -- senao, o LOOP tenta o proximo numero automaticamente
    END LOOP;

    RETURN v_protocolo;
END;
$$;

COMMIT;
