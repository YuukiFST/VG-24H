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
