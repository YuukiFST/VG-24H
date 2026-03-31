-- Portal VG 24H - Script completo para Neon DB (Plano de Trabalho v6)
-- Gerado automaticamente a partir dos scripts individuais
-- Execute este arquivo inteiro no console SQL do Neon

-- Portal VG 24H — PostgreSQL (Plano de Trabalho v6)
-- Ordem: 01_schema.sql → 02_seed.sql → 03_functions_triggers.sql → 04_rules.sql → 05_views.sql
-- Requer PostgreSQL 12+

BEGIN;

DROP VIEW IF EXISTS vw_estatisticas_chamados CASCADE;

DROP TABLE IF EXISTS notificacao CASCADE;
DROP TABLE IF EXISTS historico_chamado CASCADE;
DROP TABLE IF EXISTS foto_chamado CASCADE;
DROP TABLE IF EXISTS chamado CASCADE;
DROP TABLE IF EXISTS servidor CASCADE;
DROP TABLE IF EXISTS cidadao CASCADE;
DROP TABLE IF EXISTS servico CASCADE;
DROP TABLE IF EXISTS bairro CASCADE;
DROP TABLE IF EXISTS categoria_servico CASCADE;
DROP TABLE IF EXISTS secretaria CASCADE;
DROP TABLE IF EXISTS status_chamado CASCADE;

-- ============================================================
-- Entidade 7: status
-- ============================================================
CREATE TABLE status_chamado (
    id_status   SERIAL PRIMARY KEY,
    descricao   VARCHAR(200),
    sigla       CHAR(2) NOT NULL UNIQUE,
    CONSTRAINT ck_status_sigla CHECK (sigla IN ('AB', 'AN', 'EX', 'CO', 'CA'))
);

-- ============================================================
-- Entidade 3: secretaria
-- ============================================================
CREATE TABLE secretaria (
    id_secretaria       SERIAL PRIMARY KEY,
    nome                VARCHAR(100) NOT NULL,
    gestor_responsavel  VARCHAR(100) NOT NULL,
    cpf                 VARCHAR(11) UNIQUE NOT NULL,
    email               VARCHAR(255) UNIQUE NOT NULL,
    ativo               BOOLEAN NOT NULL DEFAULT TRUE
);

-- ============================================================
-- Entidade 4: categoria_servico (FK → secretaria)
-- ============================================================
CREATE TABLE categoria_servico (
    id_categoria    SERIAL PRIMARY KEY,
    nome            VARCHAR(100) NOT NULL UNIQUE,
    descricao       VARCHAR(200),
    ativo           BOOLEAN NOT NULL DEFAULT TRUE,
    id_secretaria   INTEGER NOT NULL REFERENCES secretaria (id_secretaria)
);

-- ============================================================
-- Entidade 5: servico (FK → categoria_servico)
-- ============================================================
CREATE TABLE servico (
    id_servico           SERIAL PRIMARY KEY,
    nome                 VARCHAR(100) NOT NULL,
    descricao            VARCHAR(200),
    prazo_amarelo_dias   INTEGER NOT NULL DEFAULT 15 CHECK (prazo_amarelo_dias >= 0),
    prazo_vermelho_dias  INTEGER NOT NULL DEFAULT 30 CHECK (prazo_vermelho_dias >= 0),
    ativo                BOOLEAN NOT NULL DEFAULT TRUE,
    id_categoria         INTEGER NOT NULL REFERENCES categoria_servico (id_categoria),
    UNIQUE (id_categoria, nome)
);

-- ============================================================
-- Entidade 6: bairro
-- ============================================================
CREATE TABLE bairro (
    id_bairro          SERIAL PRIMARY KEY,
    nome_bairro        VARCHAR(100) NOT NULL,
    cep                CHAR(8) NOT NULL,
    regiao             VARCHAR(200),
    num_casa           VARCHAR(5),
    ponto_referencia   VARCHAR(100),
    ativo              BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (nome_bairro)
);

-- ============================================================
-- Entidade 1: cidadao
-- ============================================================
CREATE TABLE cidadao (
    id_cidadao           SERIAL PRIMARY KEY,
    nome_completo        VARCHAR(200) NOT NULL,
    cpf                  VARCHAR(11) NOT NULL UNIQUE,
    dt_nascimento        DATE NOT NULL,
    telefone             VARCHAR(20) NOT NULL,
    email                VARCHAR(255) NOT NULL UNIQUE,
    senha_hash           VARCHAR(255) NOT NULL,
    senha_temporaria     VARCHAR(200),
    perfil               CHAR(3) NOT NULL DEFAULT 'CID' CHECK (perfil IN ('CID', 'VER')),
    rua                  VARCHAR(100),
    num_endereco         VARCHAR(10),
    complemento_endereco VARCHAR(200),
    bairro_endereco      VARCHAR(200),
    cep_endereco         CHAR(8),
    dt_cadastro          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ativo                BOOLEAN NOT NULL DEFAULT TRUE
);

-- ============================================================
-- Entidade 2: servidor (FK → secretaria)
-- ============================================================
CREATE TABLE servidor (
    id_servidor          SERIAL PRIMARY KEY,
    nome_completo        VARCHAR(200) NOT NULL,
    cpf                  VARCHAR(11) NOT NULL UNIQUE,
    dt_nascimento        DATE NOT NULL,
    telefone             VARCHAR(20) NOT NULL,
    email                VARCHAR(255) NOT NULL UNIQUE,
    senha_hash           VARCHAR(255) NOT NULL,
    senha_temporaria     VARCHAR(200),
    perfil               CHAR(3) NOT NULL CHECK (perfil IN ('GES', 'COL')),
    dt_cadastro          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ativo                BOOLEAN NOT NULL DEFAULT TRUE,
    id_secretaria        INTEGER NOT NULL REFERENCES secretaria (id_secretaria)
);

-- ============================================================
-- Entidade 8: chamado (FK → cidadao, servico, status_chamado, bairro)
-- ============================================================
CREATE TABLE chamado (
    id_chamado             SERIAL PRIMARY KEY,
    num_protocolo          VARCHAR(20) NOT NULL UNIQUE,
    prioridade             INTEGER NOT NULL DEFAULT 0 CHECK (prioridade >= 0 AND prioridade <= 5),
    descricao              VARCHAR(500) NOT NULL CHECK (char_length(descricao) <= 500),
    resolucao              VARCHAR(500) CHECK (resolucao IS NULL OR char_length(resolucao) <= 500),
    nota_avaliacao         INTEGER CHECK (
        nota_avaliacao IS NULL OR (nota_avaliacao >= 1 AND nota_avaliacao <= 5)
    ),
    comentario_avaliacao   VARCHAR(500) CHECK (
        comentario_avaliacao IS NULL OR char_length(comentario_avaliacao) <= 500
    ),
    dt_abertura            TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    dt_conclusao           TIMESTAMPTZ,
    dt_avaliacao           TIMESTAMPTZ,
    atualizado_em          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    id_servico             INTEGER NOT NULL REFERENCES servico (id_servico),
    id_bairro              INTEGER NOT NULL REFERENCES bairro (id_bairro),
    id_cidadao             INTEGER NOT NULL REFERENCES cidadao (id_cidadao),
    id_status              INTEGER NOT NULL REFERENCES status_chamado (id_status)
);

-- ============================================================
-- Entidade 9: foto_chamado (FK → chamado)
-- ============================================================
CREATE TABLE foto_chamado (
    id_foto    SERIAL PRIMARY KEY,
    url_foto   VARCHAR(200) NOT NULL,
    dt_upload  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    id_chamado INTEGER NOT NULL REFERENCES chamado (id_chamado)
);

-- ============================================================
-- Entidade 10: historico_chamado (FK → chamado, servidor, status_chamado)
-- Observações centralizadas nesta tabela (sem entidade observacao_chamado separada)
-- ============================================================
CREATE TABLE historico_chamado (
    id_historico_chamado   SERIAL PRIMARY KEY,
    dt_alteracao           TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    observacao             VARCHAR(500) CHECK (observacao IS NULL OR char_length(observacao) <= 500),
    id_chamado             INTEGER NOT NULL REFERENCES chamado (id_chamado),
    id_servidor            INTEGER REFERENCES servidor (id_servidor),
    id_status              INTEGER NOT NULL REFERENCES status_chamado (id_status)
);

-- ============================================================
-- Entidade 11: notificacao (FK → chamado)
-- ============================================================
CREATE TABLE notificacao (
    id_notificacao SERIAL PRIMARY KEY,
    mensagem       VARCHAR(200) NOT NULL,
    lida           BOOLEAN NOT NULL DEFAULT FALSE,
    arquivada      BOOLEAN NOT NULL DEFAULT FALSE,
    dt_envio       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    id_chamado     INTEGER REFERENCES chamado (id_chamado)
);

-- ============================================================
-- Índices
-- ============================================================
CREATE INDEX ix_chamado_cidadao   ON chamado (id_cidadao);
CREATE INDEX ix_chamado_status    ON chamado (id_status);
CREATE INDEX ix_chamado_bairro    ON chamado (id_bairro);
CREATE INDEX ix_chamado_servico   ON chamado (id_servico);
CREATE INDEX ix_foto_chamado      ON foto_chamado (id_chamado);
CREATE INDEX ix_historico_chamado  ON historico_chamado (id_chamado);
CREATE INDEX ix_notificacao_chamado ON notificacao (id_chamado);

COMMIT;

-- Carga inicial: 5 status, 1 secretaria, 2 categorias, 5 serviços, bairros de Várzea Grande (MT)

BEGIN;

INSERT INTO status_chamado (sigla, descricao) VALUES
    ('AB', 'Aberto — Chamado aberto pelo cidadão'),
    ('AN', 'Em Análise — Em análise pela equipe responsável'),
    ('EX', 'Em Execução — Em execução no campo'),
    ('CO', 'Concluído — Serviço concluído'),
    ('CA', 'Cancelado — Chamado cancelado');

-- Secretaria padrão
INSERT INTO secretaria (nome, gestor_responsavel, cpf, email) VALUES
    ('Secretaria de Obras e Serviços Urbanos', 'Gestor Padrão', '00000000000', 'obras@varzeagrande.mt.gov.br');

INSERT INTO categoria_servico (nome, descricao, id_secretaria) VALUES
    ('Infraestrutura e Via Pública', 'Problemas que afetam a locomoção e segurança imediata.', 1),
    ('Mobilidade e Cidadania', 'Serviços de organização, saúde e segurança.', 1);

INSERT INTO servico (id_categoria, nome, descricao, prazo_amarelo_dias, prazo_vermelho_dias)
SELECT c.id_categoria, v.nome, v.descricao, 15, 30
FROM categoria_servico c
JOIN (VALUES
    ('Infraestrutura e Via Pública', 'Iluminação Pública', 'Postes, lâmpadas e pontos escuros.'),
    ('Infraestrutura e Via Pública', 'Pavimentação e Vias', 'Buracos, calçadas e pavimentação.'),
    ('Infraestrutura e Via Pública', 'Saneamento e Drenagem', 'Bueiros, alagamentos e esgoto.'),
    ('Mobilidade e Cidadania', 'Trânsito e Sinalização', 'Semáforos, placas e fiscalização.'),
    ('Mobilidade e Cidadania', 'Saúde e Bem-estar', 'Demandas de saúde pública e bem-estar urbano.')
) AS v(cat, nome, descricao) ON c.nome = v.cat;

-- Bairros (nomes públicos; CEPs representativos na faixa de Várzea Grande/MT)
INSERT INTO bairro (nome_bairro, cep, regiao) VALUES
    ('Centro-Norte', '78110100', 'Central'),
    ('Centro-Sul', '78110150', 'Central'),
    ('Jardim Eldorado', '78128500', 'Norte'),
    ('São Matheus', '78145600', 'Leste'),
    ('Ponte Nova', '78152300', 'Oeste'),
    ('Costa Verde', '78118000', 'Norte'),
    ('Mapim', '78142800', 'Sul'),
    ('Ikaray', '78138000', 'Sul'),
    ('23 de Setembro', '78115000', 'Central'),
    ('Petrópolis', '78144000', 'Leste'),
    ('Santa Isabel', '78148700', 'Leste'),
    ('Guarita', '78155000', 'Oeste'),
    ('Capão Grande', '78160000', 'Rural'),
    ('Água Vermelha', '78125000', 'Norte'),
    ('Panamericano', '78135000', 'Sul'),
    ('Christ Rei', '78117000', 'Central'),
    ('Parque do Lago', '78120000', 'Norte'),
    ('Jardim dos Estados', '78130000', 'Sul'),
    ('Marajoara', '78148000', 'Leste'),
    ('Bom Sucesso', '78152700', 'Oeste');

COMMIT;

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

-- Rules do plano de trabalho v6
-- A aplicação deve definir o perfil na sessão ao alterar chamados:
--   SELECT set_config('portal.perfil', 'CID', true);  -- ou 'COL' / 'GES'

BEGIN;

-- ============================================================
-- Rule 1 — foto_chamado: impede INSERT se o chamado estiver CO ou CA
-- ============================================================
DROP RULE IF EXISTS r01_foto_chamado_encerrado ON foto_chamado;
CREATE RULE r01_foto_chamado_encerrado AS ON INSERT TO foto_chamado
WHERE EXISTS (
    SELECT 1
    FROM chamado c
    JOIN status_chamado s ON s.id_status = c.id_status
    WHERE c.id_chamado = NEW.id_chamado
      AND s.sigla IN ('CO', 'CA')
)
DO INSTEAD NOTHING;

-- ============================================================
-- Rule 2 — historico_chamado: impede INSERT de observação
-- se o chamado estiver com status CO ou CA
-- ============================================================
DROP RULE IF EXISTS r02_historico_observacao_encerrado ON historico_chamado;
CREATE RULE r02_historico_observacao_encerrado AS ON INSERT TO historico_chamado
WHERE NEW.observacao IS NOT NULL
  AND EXISTS (
    SELECT 1
    FROM chamado c
    JOIN status_chamado s ON s.id_status = c.id_status
    WHERE c.id_chamado = NEW.id_chamado
      AND s.sigla IN ('CO', 'CA')
)
DO INSTEAD NOTHING;

-- ============================================================
-- Rule 3 — chamado: impede alterar nota_avaliacao / comentario_avaliacao
-- se já estiverem preenchidos (avaliação uma única vez, não alterável)
-- ============================================================
DROP RULE IF EXISTS r03_chamado_avaliacao_imutavel ON chamado;
CREATE RULE r03_chamado_avaliacao_imutavel AS ON UPDATE TO chamado
WHERE OLD.nota_avaliacao IS NOT NULL
  AND (
    NEW.nota_avaliacao IS DISTINCT FROM OLD.nota_avaliacao
    OR NEW.comentario_avaliacao IS DISTINCT FROM OLD.comentario_avaliacao
  )
DO INSTEAD NOTHING;

-- ============================================================
-- Rule 4 — chamado: restrições de mudança de status por perfil
-- CID: não pode alterar status se CO ou CA; não pode cancelar se EX
-- COL: não pode alterar status se CO ou CA
-- GES: sem restrição (isento)
-- ============================================================
DROP RULE IF EXISTS r04_chamado_perfil_status ON chamado;
CREATE RULE r04_chamado_perfil_status AS ON UPDATE TO chamado
WHERE NEW.id_status IS DISTINCT FROM OLD.id_status
  AND (
    (
      current_setting('portal.perfil', true) = 'COL'
      AND EXISTS (
          SELECT 1 FROM status_chamado sc
          WHERE sc.id_status = OLD.id_status AND sc.sigla IN ('CO', 'CA')
      )
    )
    OR (
      current_setting('portal.perfil', true) = 'CID'
      AND EXISTS (
          SELECT 1 FROM status_chamado sc
          WHERE sc.id_status = OLD.id_status AND sc.sigla IN ('CO', 'CA')
      )
    )
    OR (
      current_setting('portal.perfil', true) = 'CID'
      AND EXISTS (
          SELECT 1 FROM status_chamado scn
          WHERE scn.id_status = NEW.id_status AND scn.sigla = 'CA'
      )
      AND EXISTS (
          SELECT 1 FROM status_chamado sco
          WHERE sco.id_status = OLD.id_status AND sco.sigla = 'EX'
      )
    )
  )
DO INSTEAD NOTHING;

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
DROP RULE IF EXISTS r06_chamado_resolucao_encerramento ON chamado;
CREATE RULE r06_chamado_resolucao_encerramento AS ON UPDATE TO chamado
WHERE NEW.id_status IS DISTINCT FROM OLD.id_status
  AND EXISTS (
    SELECT 1 FROM status_chamado s
    WHERE s.id_status = NEW.id_status
      AND s.sigla IN ('CO', 'CA')
  )
  AND (
    NEW.resolucao IS NULL
    OR btrim(NEW.resolucao) = ''
  )
DO INSTEAD NOTHING;

-- Extra: impede DELETE em chamado (integridade)
DROP RULE IF EXISTS rx_chamado_sem_delete ON chamado;
CREATE RULE rx_chamado_sem_delete AS ON DELETE TO chamado DO INSTEAD NOTHING;

COMMIT;

-- View de estatísticas (painel do Gestor — controle de acesso na aplicação)

BEGIN;

DROP VIEW IF EXISTS vw_estatisticas_chamados;

CREATE VIEW vw_estatisticas_chamados AS
SELECT
    cat.nome        AS categoria,
    b.nome_bairro   AS bairro,
    s.sigla         AS sigla_status,
    s.descricao     AS status_descricao,
    COUNT(*)::BIGINT AS total_chamados
FROM chamado ch
JOIN servico srv     ON srv.id_servico  = ch.id_servico
JOIN categoria_servico cat ON cat.id_categoria = srv.id_categoria
JOIN bairro b        ON b.id_bairro     = ch.id_bairro
JOIN status_chamado s ON s.id_status    = ch.id_status
WHERE cat.ativo
  AND srv.ativo
  AND b.ativo
GROUP BY cat.nome, b.nome_bairro, s.sigla, s.descricao;

COMMIT;
