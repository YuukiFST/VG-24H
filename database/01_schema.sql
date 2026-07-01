-- Portal VG 24H — PostgreSQL (Plano de Trabalho v5)
-- Ordem: 01_schema.sql → 02_seed.sql → 03_functions_triggers.sql → 04_rules.sql → 05_views.sql
-- Requer PostgreSQL 12+
--
-- ============================================================================
-- SCHEMA COMPLETO — 11 tabelas com PKs, FKs, CHECKs e indices
-- ============================================================================
-- [!] DECISAO ARQUITETURAL: a tabela chamado NAO possui campo id_status.
--     O status de cada chamado e determinado pelo ULTIMO registro da tabela
--     historico_chamado. Isso garante rastreabilidade total (quem mudou, quando,
--     para qual status) e evidencia a importancia do Trigger 1, que cria o
--     primeiro historico (AB) automaticamente ao inserir um chamado.
-- ============================================================================

BEGIN;

DROP VIEW IF EXISTS vw_estatisticas_chamados CASCADE;

DROP TABLE IF EXISTS banner_publicacao CASCADE;   -- tabela extra (carrossel da home)
DROP TABLE IF EXISTS protocolo_seq CASCADE;       -- tabela auxiliar (contador de protocolo)
DROP TABLE IF EXISTS configuracao_semaforo CASCADE;
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
-- Entidade 7: status_chamado (tabela dimensional — 5 registros fixos)
-- ============================================================
-- Tabela de dominio: armazena os 5 possiveis status do chamado.
-- Nao e uma tabela de movimentacao — e um CATALOGO.
-- [!] A sigla tem CHECK constraint: apenas AB, EA, EE, CO, CA sao aceitos.
--     Nao e possivel criar um status novo sem alterar o schema.
-- ============================================================
CREATE TABLE status_chamado (
    id_status   SERIAL PRIMARY KEY,           -- PK — referencia de historico_chamado.id_status
    descricao   VARCHAR(200),                  -- Ex: "Aberto — Chamado aberto pelo cidadao"
    sigla       CHAR(2) NOT NULL UNIQUE,      -- AB, EA, EE, CO ou CA (UNIQUE + CHECK)
    CONSTRAINT ck_status_sigla CHECK (sigla IN ('AB', 'EA', 'EE', 'CO', 'CA'))
);

-- ============================================================
-- Entidade 3: secretaria (orgaos municipais — ex: Obras, Saude)
-- ============================================================
-- FK apontada por: servidor.id_secretaria, categoria_servico.id_secretaria
-- ============================================================
CREATE TABLE secretaria (
    id_secretaria       SERIAL PRIMARY KEY,
    nome                VARCHAR(100) NOT NULL,
    gestor_responsavel  VARCHAR(100) NOT NULL,  -- Nome do gestor responsavel
    cpf                 VARCHAR(11) UNIQUE NOT NULL,
    email               VARCHAR(255) UNIQUE NOT NULL,
    ativo               BOOLEAN NOT NULL DEFAULT TRUE  -- Soft delete (logico)
);

-- ============================================================
-- Entidade 4: categoria_servico (agrupa servicos por area)
-- ============================================================
-- FK → secretaria: cada categoria pertence a uma secretaria.
-- FK apontada por: servico.id_categoria
-- ============================================================
CREATE TABLE categoria_servico (
    id_categoria    SERIAL PRIMARY KEY,
    nome            VARCHAR(100) NOT NULL UNIQUE,
    descricao       VARCHAR(200),
    ativo           BOOLEAN NOT NULL DEFAULT TRUE,
    id_secretaria   INTEGER NOT NULL REFERENCES secretaria (id_secretaria)  -- FK → secretaria
);

-- ============================================================
-- Entidade 5: servico (tipos de servico com prazos de atendimento)
-- ============================================================
-- FK → categoria_servico. FK apontada por: chamado.id_servico.
-- [!] Prazos amarelo/vermelho: definem o semaforo de urgencia.
--     Usados pela property cor_semaforo em Chamado (models.py).
-- ============================================================
CREATE TABLE servico (
    id_servico           SERIAL PRIMARY KEY,
    nome                 VARCHAR(100) NOT NULL,
    descricao            VARCHAR(200),
    ativo                BOOLEAN NOT NULL DEFAULT TRUE,
    id_categoria         INTEGER NOT NULL REFERENCES categoria_servico (id_categoria),  -- FK → categoria_servico
    UNIQUE (id_categoria, nome)  -- Mesmo nome de servico nao pode repetir na mesma categoria
);

-- ============================================================
-- ConfiguracaoSemaforo — prazos globais do semaforo (singleton)
-- ============================================================
-- Contem EXATAMENTE 1 registro, enforced via CHECK (id = 1).
-- Usada por cor_semaforo() em models.py e db.py.
-- Criada no seed (02_seed.sql) com defaults 15/30.
-- ============================================================
CREATE TABLE configuracao_semaforo (
    id                  INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1),  -- enforce singleton
    prazo_amarelo_dias  INTEGER NOT NULL DEFAULT 15 CHECK (prazo_amarelo_dias >= 0),
    prazo_vermelho_dias INTEGER NOT NULL DEFAULT 30 CHECK (prazo_vermelho_dias >= 0)
);

-- ============================================================
-- Entidade 6: bairro (bairros de Varzea Grande/MT)
-- ============================================================
-- FK apontada por: chamado.id_bairro (bairro onde o chamado foi aberto)
-- ============================================================
CREATE TABLE bairro (
    id_bairro          SERIAL PRIMARY KEY,
    nome_bairro        VARCHAR(100) NOT NULL,
    cep                CHAR(8) NOT NULL,              -- CEP representativo sem mascara (8 digitos)
    regiao             VARCHAR(200),                   -- Ex: "Central", "Norte", "Sul"
    ativo              BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (nome_bairro)
);

-- ============================================================
-- Entidade 1: cidadao (usuarios cidadaos que abrem chamados)
-- ============================================================
-- Autenticacao propria (NAO usa django.contrib.auth).
-- Perfis: 'CID' = Cidadao padrao, 'VER' = Verificador (possivel extensao futura).
-- FK apontada por: chamado.id_cidadao.
-- ============================================================
CREATE TABLE cidadao (
    id_cidadao           SERIAL PRIMARY KEY,
    nome_completo        VARCHAR(200) NOT NULL,
    cpf                  VARCHAR(11) NOT NULL UNIQUE,          -- CPF sem mascara (11 digitos)
    dt_nascimento        DATE NOT NULL,
    telefone             VARCHAR(20) NOT NULL,
    email                VARCHAR(255) NOT NULL UNIQUE,
    senha_hash           VARCHAR(255) NOT NULL,                -- Hash bcrypt (NUNCA senha em texto puro)
    senha_temporaria     VARCHAR(200),                         -- Senha temporaria para primeiro acesso
    perfil               CHAR(3) NOT NULL DEFAULT 'CID' CHECK (perfil IN ('CID', 'VER')),  -- 'CID' padrao
    rua                  VARCHAR(100),
    num_endereco         VARCHAR(10),
    complemento_endereco VARCHAR(200),
    bairro_endereco      VARCHAR(200),
    cep_endereco         CHAR(8),
    dt_cadastro          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ativo                BOOLEAN NOT NULL DEFAULT TRUE          -- Soft delete: false = conta desativada
);

-- ============================================================
-- Entidade 2: servidor (colaboradores e gestores da prefeitura)
-- ============================================================
-- FK → secretaria: cada servidor pertence a uma secretaria.
-- Perfis: 'COL' = Colaborador (acesso parcial), 'GES' = Gestor (acesso total).
-- FK apontada por: historico_chamado.id_servidor (quem alterou o status).
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
    perfil               CHAR(3) NOT NULL CHECK (perfil IN ('GES', 'COL')),  -- 'GES' ou 'COL'
    dt_cadastro          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ativo                BOOLEAN NOT NULL DEFAULT TRUE,
    id_secretaria        INTEGER NOT NULL REFERENCES secretaria (id_secretaria)  -- FK → secretaria
);

-- ============================================================
-- Entidade 8: chamado (TABELA CENTRAL — solicitacoes dos cidadaos)
-- ============================================================
-- [!] DECISAO ARQUITETURAL: chamado NAO possui campo id_status.
--     O status e determinado pelo ULTIMO registro de historico_chamado.
--     Isso garante rastreabilidade: toda mudanca de status fica registrada.
--     A property status_atual em models.py faz essa consulta.
--
-- FKs: id_servico → servico, id_bairro → bairro, id_cidadao → cidadao
-- Trigger 1 (AFTER INSERT): cria automaticamente o primeiro historico (status AB)
-- Trigger 2A (BEFORE UPDATE): atualiza atualizado_em automaticamente
-- ============================================================
CREATE TABLE chamado (
    id_chamado             SERIAL PRIMARY KEY,
    num_protocolo          VARCHAR(20) NOT NULL UNIQUE,        -- Ex: "2026000001" (gerado por utils.proximo_protocolo)
    prioridade             INTEGER NOT NULL DEFAULT 0 CHECK (prioridade >= 0 AND prioridade <= 5),
    ponto_de_referencia    VARCHAR(100),                        -- Ponto de referencia do local
    descricao              VARCHAR(500) NOT NULL CHECK (char_length(descricao) <= 500),
    resolucao              VARCHAR(600) CHECK (resolucao IS NULL OR char_length(resolucao) <= 600),  -- Preenchido ao concluir
    nota_avaliacao         INTEGER CHECK (                      -- Avaliacao do cidadao (1-5)
        nota_avaliacao IS NULL OR (nota_avaliacao >= 1 AND nota_avaliacao <= 5)
    ),
    comentario_avaliacao   VARCHAR(500) CHECK (
        comentario_avaliacao IS NULL OR char_length(comentario_avaliacao) <= 500
    ),
    dt_abertura            TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    dt_conclusao           TIMESTAMPTZ,                         -- Atualizado pelo Trigger 2B
    dt_avaliacao           TIMESTAMPTZ,
    atualizado_em          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,  -- Atualizado pelo Trigger 2A
    id_servico             INTEGER NOT NULL REFERENCES servico (id_servico),
    id_bairro              INTEGER NOT NULL REFERENCES bairro (id_bairro),
    id_cidadao             INTEGER NOT NULL REFERENCES cidadao (id_cidadao)  -- FK → cidadao (quem abriu)
);

-- ============================================================
-- Entidade 9: foto_chamado (fotos anexadas ao chamado)
-- ============================================================
-- FK → chamado. As URLs sao armazenadas (Cloudinary).
-- Trigger de integridade (R1→T em 04_rules.sql): bloqueia INSERT se chamado estiver CO/CA.
-- ============================================================
CREATE TABLE foto_chamado (
    id_foto    SERIAL PRIMARY KEY,
    url_foto   VARCHAR(200) NOT NULL,             -- URL da foto (Cloudinary)
    dt_upload  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    id_chamado INTEGER NOT NULL REFERENCES chamado (id_chamado)  -- FK → chamado
);

-- ============================================================
-- Entidade 10: historico_chamado (FONTE DA VERDADE para o status)
-- ============================================================
-- [!] FONTE DA VERDADE: o status ATUAL de cada chamado e o ULTIMO
--     registro desta tabela (maior dt_alteracao para aquele id_chamado).
--
-- FKs: id_chamado → chamado, id_servidor → servidor (quem alterou, pode ser NULL),
--      id_status → status_chamado.
-- Observacoes sao centralizadas aqui (NAO ha tabela separada de observacoes).
-- Rule 5 (04_rules.sql): impede UPDATE e DELETE em historicos já inseridos.
-- ============================================================
CREATE TABLE historico_chamado (
    id_historico_chamado   SERIAL PRIMARY KEY,
    dt_alteracao           TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,  -- Quando a mudanca ocorreu
    observacao             VARCHAR(500) CHECK (observacao IS NULL OR char_length(observacao) <= 500),
    id_chamado             INTEGER NOT NULL REFERENCES chamado (id_chamado),    -- FK → chamado
    id_servidor            INTEGER REFERENCES servidor (id_servidor),           -- FK → servidor (quem alterou, NULL se automatico)
    id_status              INTEGER NOT NULL REFERENCES status_chamado (id_status)  -- FK → status_chamado
);

-- ============================================================
-- Entidade 11: notificacao (avisos automaticos ao cidadao)
-- ============================================================
-- FK → chamado. As notificacoes sao geradas AUTOMATICAMENTE pelo Trigger 2B
-- sempre que um novo status e inserido em historico_chamado.
-- Campos: lida (visualizada), arquivada (removida da view).
-- ============================================================
CREATE TABLE notificacao (
    id_notificacao SERIAL PRIMARY KEY,
    mensagem       VARCHAR(200) NOT NULL,           -- Ex: "Chamado 20260001: status alterado para Concluido"
    lida           BOOLEAN NOT NULL DEFAULT FALSE,
    arquivada      BOOLEAN NOT NULL DEFAULT FALSE,
    dt_envio       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    id_chamado     INTEGER REFERENCES chamado (id_chamado)  -- FK → chamado (pode ser NULL se chamado for removido)
);

-- ============================================================
-- Tabela extra: banner_publicacao (carrossel de destaques da home)
-- ============================================================
-- [!] NAO faz parte das 11 entidades do DER — e um recurso extra do portal.
--     Alimenta o carrossel da home (root_view) e o CRUD de banners do gestor
--     (db/catalogo.py: listar_banners_ativos/inserir/atualizar/reordenar_banner).
--     Sem esta tabela a home retorna 500 ("relation banner_publicacao does not exist").
--     Espelhada pelo model managed=False BannerPublicacao (models.py).
-- ============================================================
CREATE TABLE banner_publicacao (
    id_banner    SERIAL PRIMARY KEY,
    titulo       VARCHAR(100) NOT NULL,                          -- titulo exibido no banner
    descricao    VARCHAR(300),                                   -- texto opcional de apoio
    url_imagem   VARCHAR(500) NOT NULL,                          -- URL da imagem (Cloudinary)
    link         VARCHAR(500),                                   -- link opcional ao clicar no banner
    ordem        INTEGER NOT NULL DEFAULT 0,                     -- posicao no carrossel (menor primeiro)
    ativo        BOOLEAN NOT NULL DEFAULT TRUE,                  -- soft toggle: so os ativos aparecem na home
    dt_criacao   TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP  -- data de criacao (desempate do carrossel)
);

-- ============================================================
-- Indices de performance
-- ============================================================
-- [!] NAO existe ix_chamado_status porque chamado nao tem id_status.
--     A consulta por status usa historico_chamado (ultimo registro).
-- Indices nas FKs mais consultadas para acelerar JOINs e filtros.
-- ============================================================
CREATE INDEX ix_chamado_cidadao   ON chamado (id_cidadao);        -- Filtro: "Meus chamados" (cidadao)
CREATE INDEX ix_chamado_bairro    ON chamado (id_bairro);         -- Filtro: chamados por bairro
CREATE INDEX ix_chamado_servico   ON chamado (id_servico);        -- JOIN com servico
CREATE INDEX ix_foto_chamado      ON foto_chamado (id_chamado);   -- JOIN para listar fotos de um chamado
CREATE INDEX ix_historico_chamado  ON historico_chamado (id_chamado);  -- JOIN para buscar historico de um chamado
CREATE INDEX ix_historico_chamado_status ON historico_chamado (id_chamado, dt_alteracao);  -- "ultimo status" queries (LATERAL/Subquery)
CREATE INDEX ix_notificacao_chamado ON notificacao (id_chamado);  -- JOIN para notificacoes de um chamado
CREATE INDEX ix_banner_ordem       ON banner_publicacao (ordem);  -- ordenacao do carrossel da home

-- ============================================================
-- Tabela auxiliar: sequencia de protocolo por ano
-- ============================================================
-- Usada por proximo_protocolo() com INSERT ... ON CONFLICT DO UPDATE
-- RETURNING para gerar numeros sequenciais atomicos (sem race condition).
CREATE TABLE protocolo_seq (
    ano            INTEGER PRIMARY KEY,
    ultimo_numero  INTEGER NOT NULL DEFAULT 0
);

COMMIT;
