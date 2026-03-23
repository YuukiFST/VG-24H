-- Portal VG: colar este arquivo inteiro no SQL Editor do Neon (banco neondb)

-- Portal VG 24H — PostgreSQL
-- Ordem sugerida: 01_schema.sql → 02_seed.sql → 03_functions_triggers.sql → 04_rules.sql → 05_views.sql
-- Requer PostgreSQL 12+

BEGIN;

DROP VIEW IF EXISTS vw_estatisticas_chamados CASCADE;

DROP TABLE IF EXISTS notificacao CASCADE;
DROP TABLE IF EXISTS observacao_chamado CASCADE;
DROP TABLE IF EXISTS historico_chamado CASCADE;
DROP TABLE IF EXISTS foto_chamado CASCADE;
DROP TABLE IF EXISTS chamado CASCADE;
DROP TABLE IF EXISTS usuario CASCADE;
DROP TABLE IF EXISTS servico CASCADE;
DROP TABLE IF EXISTS bairro_regiao CASCADE;
DROP TABLE IF EXISTS categoria_servico CASCADE;
DROP TABLE IF EXISTS status_chamado CASCADE;

-- Domínio de status
CREATE TABLE status_chamado (
    id_status   SERIAL PRIMARY KEY,
    tipo_status CHAR(2) NOT NULL UNIQUE,
    descricao   VARCHAR(200),
    CONSTRAINT ck_status_tipo CHECK (tipo_status IN ('AB', 'AN', 'EX', 'CO', 'CA'))
);

CREATE TABLE categoria_servico (
    id_categoria SERIAL PRIMARY KEY,
    nome         VARCHAR(200) NOT NULL UNIQUE,
    descricao    VARCHAR(200),
    ativo        BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE servico (
    id_servico           SERIAL PRIMARY KEY,
    id_categoria         INTEGER NOT NULL REFERENCES categoria_servico (id_categoria),
    nome                 VARCHAR(200) NOT NULL,
    descricao            VARCHAR(200),
    prazo_amarelo_dias   INTEGER NOT NULL DEFAULT 15 CHECK (prazo_amarelo_dias >= 0),
    prazo_vermelho_dias  INTEGER NOT NULL DEFAULT 30 CHECK (prazo_vermelho_dias >= 0),
    ativo                BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (id_categoria, nome)
);

CREATE TABLE bairro_regiao (
    id_bairro             SERIAL PRIMARY KEY,
    nome                  VARCHAR(200) NOT NULL,
    cep                   CHAR(8) NOT NULL,
    regiao_administrativa VARCHAR(200),
    ativo                 BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (nome)
);

CREATE TABLE usuario (
    id_usuario           SERIAL PRIMARY KEY,
    nome_completo        VARCHAR(200) NOT NULL,
    cpf                  VARCHAR(14) NOT NULL UNIQUE,
    dt_nascimento        DATE NOT NULL,
    telefone             VARCHAR(20) NOT NULL,
    email                VARCHAR(255) NOT NULL UNIQUE,
    senha_hash           VARCHAR(255) NOT NULL,
    senha_temporaria     VARCHAR(255),
    perfil               CHAR(3) NOT NULL CHECK (perfil IN ('CID', 'COL', 'ADM')),
    rua                  VARCHAR(200),
    numero_endereco      VARCHAR(10),
    complemento_endereco VARCHAR(200),
    bairro_endereco      VARCHAR(200),
    cep_endereco         CHAR(8),
    ativo                BOOLEAN NOT NULL DEFAULT TRUE,
    dt_cadastro          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE chamado (
    id_chamado             SERIAL PRIMARY KEY,
    protocolo              VARCHAR(20) NOT NULL UNIQUE,
    prioridade             SMALLINT NOT NULL DEFAULT 0 CHECK (prioridade >= 0 AND prioridade <= 5),
    rua                    VARCHAR(200) NOT NULL,
    numero                 VARCHAR(10) NOT NULL DEFAULT '0',
    complemento            VARCHAR(200),
    ponto_referencia       VARCHAR(200),
    descricao              VARCHAR(500) NOT NULL CHECK (char_length(descricao) <= 500),
    resolucao              VARCHAR(500) CHECK (resolucao IS NULL OR char_length(resolucao) <= 500),
    nota_avaliacao         SMALLINT CHECK (
        nota_avaliacao IS NULL OR (nota_avaliacao >= 1 AND nota_avaliacao <= 5)
    ),
    comentario_avaliacao   VARCHAR(500) CHECK (
        comentario_avaliacao IS NULL OR char_length(comentario_avaliacao) <= 500
    ),
    dt_abertura            TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    dt_conclusao           TIMESTAMPTZ,
    dt_avaliacao           TIMESTAMPTZ,
    atualizado_em          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    id_usuario             INTEGER NOT NULL REFERENCES usuario (id_usuario),
    id_servico             INTEGER NOT NULL REFERENCES servico (id_servico),
    id_status              INTEGER NOT NULL REFERENCES status_chamado (id_status),
    id_bairro              INTEGER NOT NULL REFERENCES bairro_regiao (id_bairro)
);

CREATE TABLE foto_chamado (
    id_foto    SERIAL PRIMARY KEY,
    id_chamado INTEGER NOT NULL REFERENCES chamado (id_chamado),
    url_foto   VARCHAR(500) NOT NULL,
    dt_upload  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE historico_chamado (
    id_historico          SERIAL PRIMARY KEY,
    id_chamado            INTEGER NOT NULL REFERENCES chamado (id_chamado),
    id_usuario_responsavel INTEGER REFERENCES usuario (id_usuario),
    tipo_status           CHAR(2) NOT NULL CHECK (tipo_status IN ('AB', 'AN', 'EX', 'CO', 'CA')),
    dt_alteracao          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    observacao            VARCHAR(500) CHECK (observacao IS NULL OR char_length(observacao) <= 500)
);

CREATE TABLE observacao_chamado (
    id_observacao     SERIAL PRIMARY KEY,
    id_chamado        INTEGER NOT NULL REFERENCES chamado (id_chamado),
    id_usuario_autor  INTEGER NOT NULL REFERENCES usuario (id_usuario),
    texto_observacao  VARCHAR(500) NOT NULL CHECK (char_length(texto_observacao) <= 500),
    criado_em         TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE notificacao (
    id_notificacao SERIAL PRIMARY KEY,
    id_usuario     INTEGER NOT NULL REFERENCES usuario (id_usuario),
    id_chamado     INTEGER REFERENCES chamado (id_chamado),
    mensagem       VARCHAR(200) NOT NULL,
    lida           BOOLEAN NOT NULL DEFAULT FALSE,
    arquivada      BOOLEAN NOT NULL DEFAULT FALSE,
    dt_envio       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_chamado_usuario ON chamado (id_usuario);
CREATE INDEX ix_chamado_status ON chamado (id_status);
CREATE INDEX ix_chamado_bairro ON chamado (id_bairro);
CREATE INDEX ix_chamado_servico ON chamado (id_servico);
CREATE INDEX ix_foto_chamado ON foto_chamado (id_chamado);
CREATE INDEX ix_historico_chamado ON historico_chamado (id_chamado);
CREATE INDEX ix_observacao_chamado ON observacao_chamado (id_chamado);
CREATE INDEX ix_notificacao_usuario ON notificacao (id_usuario);

COMMIT;


-- Carga inicial: 5 status, 2 categorias, 5 serviços, bairros de Várzea Grande (MT)

BEGIN;

INSERT INTO status_chamado (tipo_status, descricao) VALUES
    ('AB', 'Chamado aberto pelo cidadão'),
    ('AN', 'Em análise pela equipe responsável'),
    ('EX', 'Em execução no campo'),
    ('CO', 'Serviço concluído'),
    ('CA', 'Chamado cancelado');

INSERT INTO categoria_servico (nome, descricao) VALUES
    ('Infraestrutura e Via Pública', 'Problemas que afetam a locomoção e segurança imediata.'),
    ('Mobilidade e Cidadania', 'Serviços de organização, saúde e segurança.');

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
INSERT INTO bairro_regiao (nome, cep, regiao_administrativa) VALUES
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


-- Rules do plano (PostgreSQL). A aplicação deve definir o perfil na sessão ao alterar chamados:
--   SELECT set_config('portal.perfil', 'CID', true);  -- ou 'COL' / 'ADM'

BEGIN;

-- Rule 1 — foto_chamado: impede INSERT se o chamado estiver CO ou CA
DROP RULE IF EXISTS r01_foto_chamado_encerrado ON foto_chamado;
CREATE RULE r01_foto_chamado_encerrado AS ON INSERT TO foto_chamado
WHERE EXISTS (
    SELECT 1
    FROM chamado c
    JOIN status_chamado s ON s.id_status = c.id_status
    WHERE c.id_chamado = NEW.id_chamado
      AND s.tipo_status IN ('CO', 'CA')
)
DO INSTEAD NOTHING;

-- Rule 2 — observacao_chamado: impede INSERT se o chamado estiver CO ou CA
DROP RULE IF EXISTS r02_observacao_chamado_encerrado ON observacao_chamado;
CREATE RULE r02_observacao_chamado_encerrado AS ON INSERT TO observacao_chamado
WHERE EXISTS (
    SELECT 1
    FROM chamado c
    JOIN status_chamado s ON s.id_status = c.id_status
    WHERE c.id_chamado = NEW.id_chamado
      AND s.tipo_status IN ('CO', 'CA')
)
DO INSTEAD NOTHING;

-- Rule 3 — chamado: impede alterar nota_avaliacao / comentario_avaliacao se já preenchidos
DROP RULE IF EXISTS r03_chamado_avaliacao_imutavel ON chamado;
CREATE RULE r03_chamado_avaliacao_imutavel AS ON UPDATE TO chamado
WHERE OLD.nota_avaliacao IS NOT NULL
  AND (
    NEW.nota_avaliacao IS DISTINCT FROM OLD.nota_avaliacao
    OR NEW.comentario_avaliacao IS DISTINCT FROM OLD.comentario_avaliacao
  )
DO INSTEAD NOTHING;

-- Rule 4 — chamado: restrições de mudança de status por perfil (ADM sem restrição quando portal.perfil <> CID/COL)
DROP RULE IF EXISTS r04_chamado_perfil_status ON chamado;
CREATE RULE r04_chamado_perfil_status AS ON UPDATE TO chamado
WHERE NEW.id_status IS DISTINCT FROM OLD.id_status
  AND (
    (
      current_setting('portal.perfil', true) = 'COL'
      AND EXISTS (
          SELECT 1 FROM status_chamado sc
          WHERE sc.id_status = OLD.id_status AND sc.tipo_status IN ('CO', 'CA')
      )
    )
    OR (
      current_setting('portal.perfil', true) = 'CID'
      AND EXISTS (
          SELECT 1 FROM status_chamado sc
          WHERE sc.id_status = OLD.id_status AND sc.tipo_status IN ('CO', 'CA')
      )
    )
    OR (
      current_setting('portal.perfil', true) = 'CID'
      AND EXISTS (
          SELECT 1 FROM status_chamado scn
          WHERE scn.id_status = NEW.id_status AND scn.tipo_status = 'CA'
      )
      AND EXISTS (
          SELECT 1 FROM status_chamado sco
          WHERE sco.id_status = OLD.id_status AND sco.tipo_status = 'EX'
      )
    )
  )
DO INSTEAD NOTHING;

-- Rule 5 — chamado: impede DELETE (integridade / chamados nunca removidos)
DROP RULE IF EXISTS r05_chamado_sem_delete ON chamado;
CREATE RULE r05_chamado_sem_delete AS ON DELETE TO chamado DO INSTEAD NOTHING;

-- Rule 6 — chamado: CO ou CA exige resolução preenchida
DROP RULE IF EXISTS r06_chamado_resolucao_encerramento ON chamado;
CREATE RULE r06_chamado_resolucao_encerramento AS ON UPDATE TO chamado
WHERE NEW.id_status IS DISTINCT FROM OLD.id_status
  AND EXISTS (
    SELECT 1 FROM status_chamado s
    WHERE s.id_status = NEW.id_status
      AND s.tipo_status IN ('CO', 'CA')
  )
  AND (
    NEW.resolucao IS NULL
    OR btrim(NEW.resolucao) = ''
  )
DO INSTEAD NOTHING;

COMMIT;


-- View de estatísticas (painel do Administrador — controle de acesso na aplicação)

BEGIN;

DROP VIEW IF EXISTS vw_estatisticas_chamados;

CREATE VIEW vw_estatisticas_chamados AS
SELECT
    cat.nome AS categoria,
    b.nome AS bairro,
    s.tipo_status,
    s.descricao AS status_descricao,
    COUNT(*)::BIGINT AS total_chamados
FROM chamado ch
JOIN servico srv ON srv.id_servico = ch.id_servico
JOIN categoria_servico cat ON cat.id_categoria = srv.id_categoria
JOIN bairro_regiao b ON b.id_bairro = ch.id_bairro
JOIN status_chamado s ON s.id_status = ch.id_status
WHERE cat.ativo
  AND srv.ativo
  AND b.ativo
GROUP BY cat.nome, b.nome, s.tipo_status, s.descricao;

COMMIT;


