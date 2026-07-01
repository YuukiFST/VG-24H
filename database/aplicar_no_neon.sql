-- ============================================================================
-- aplicar_no_neon.sql — ARQUIVO GERADO AUTOMATICAMENTE. NAO EDITE A MAO.
-- ============================================================================
-- Fonte: 01_schema 02_seed 03_functions_triggers 04_rules 05_views
-- Regenere com:  bash database/build_aplicar_no_neon.sh
-- Cole o conteudo inteiro no SQL Editor do Neon (que nao suporta \i).
-- Para instalar via psql local, prefira: psql ... -f 00_install_all.sql
-- ============================================================================

-- >>>>>>>>>>>>>>>>>>>>>>>>  01_schema.sql  >>>>>>>>>>>>>>>>>>>>>>>>
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

-- >>>>>>>>>>>>>>>>>>>>>>>>  02_seed.sql  >>>>>>>>>>>>>>>>>>>>>>>>
-- Carga inicial: 5 status, 1 secretaria, 2 categorias, 5 servicos, 20 bairros de Varzea Grande (MT)
-- Dados minimos para o sistema funcionar (ambiente de desenvolvimento/testes)

BEGIN;

-- ============================================================================
-- 5 status do chamado (dominio fixo, corresponde ao CHECK constraint)
-- ============================================================================
-- [!] A descricao vai SEM o prefixo da sigla (nao "AB — Aberto", so "Aberto").
--     A sigla ja fica na coluna propria; a descricao aparece pura para o
--     usuario e entra na mensagem de notificacao gerada pelo Trigger 2B
--     ("status alterado para Concluido"). Isso torna o patch pontual
--     fix_status_descricoes.sql desnecessario em instalacoes novas.
INSERT INTO status_chamado (sigla, descricao) VALUES
    ('AB', 'Aberto'),
    ('EA', 'Em Atendimento'),
    ('EE', 'Em Execução'),
    ('CO', 'Concluído'),
    ('CA', 'Cancelado');

-- ============================================================================
-- 1 secretaria padrao (secretaria de obras)
-- ============================================================================
INSERT INTO secretaria (nome, gestor_responsavel, cpf, email) VALUES
    ('Secretaria de Obras e Servicos Urbanos', 'Gestor Padrao', '00000000000', 'obras@varzeagrande.mt.gov.br');

-- ============================================================================
-- 2 categorias de servico (ambas vinculadas a secretaria padrao)
-- ============================================================================
INSERT INTO categoria_servico (nome, descricao, id_secretaria) VALUES
    ('Infraestrutura e Via Publica', 'Problemas que afetam a locomocao e seguranca imediata.', 1),
    ('Mobilidade e Cidadania', 'Servicos de organizacao, saude e seguranca.', 1);

-- ============================================================================
-- 5 servicos (vinculados as categorias via JOIN com VALUES)
-- Prazos removidos para o semaforo global (configuracao_semaforo)
-- ============================================================================
INSERT INTO servico (id_categoria, nome, descricao)
SELECT c.id_categoria, v.nome, v.descricao
FROM categoria_servico c
JOIN (VALUES
    ('Infraestrutura e Via Publica', 'Iluminacao Publica', 'Postes, lampadas e pontos escuros.'),
    ('Infraestrutura e Via Publica', 'Pavimentacao e Vias', 'Buracos, calcadas e pavimentacao.'),
    ('Infraestrutura e Via Publica', 'Saneamento e Drenagem', 'Bueiros, alagamentos e esgoto.'),
    ('Mobilidade e Cidadania', 'Transito e Sinalizacao', 'Semaforos, placas e fiscalizacao.'),
    ('Mobilidade e Cidadania', 'Saude e Bem-estar', 'Demandas de saude publica e bem-estar urbano.')
) AS v(cat, nome, descricao) ON c.nome = v.cat;

-- ============================================================================
-- Configuracao do semaforo global (singleton, id=1)
-- prazo_amarelo = 15 dias, prazo_vermelho = 30 dias
-- ============================================================================
INSERT INTO configuracao_semaforo (id, prazo_amarelo_dias, prazo_vermelho_dias)
VALUES (1, 15, 30);

-- ============================================================================
-- 20 bairros de Varzea Grande/MT (CEPs representativos)
-- Distribuidos nas regioes: Central, Norte, Sul, Leste, Oeste, Rural
-- ============================================================================
INSERT INTO bairro (nome_bairro, cep, regiao) VALUES
    ('Centro-Norte', '78110100', 'Central'),
    ('Centro-Sul', '78110150', 'Central'),
    ('Jardim Eldorado', '78128500', 'Norte'),
    ('Sao Matheus', '78145600', 'Leste'),
    ('Ponte Nova', '78152300', 'Oeste'),
    ('Costa Verde', '78118000', 'Norte'),
    ('Mapim', '78142800', 'Sul'),
    ('Ikaray', '78138000', 'Sul'),
    ('23 de Setembro', '78115000', 'Central'),
    ('Petropolis', '78144000', 'Leste'),
    ('Santa Isabel', '78148700', 'Leste'),
    ('Guarita', '78155000', 'Oeste'),
    ('Capao Grande', '78160000', 'Rural'),
    ('Agua Vermelha', '78125000', 'Norte'),
    ('Panamericano', '78135000', 'Sul'),
    ('Christ Rei', '78117000', 'Central'),
    ('Parque do Lago', '78120000', 'Norte'),
    ('Jardim dos Estados', '78130000', 'Sul'),
    ('Marajoara', '78148000', 'Leste'),
    ('Bom Sucesso', '78152700', 'Oeste');

COMMIT;

-- >>>>>>>>>>>>>>>>>>>>>>>>  03_functions_triggers.sql  >>>>>>>>>>>>>>>>>>>>>>>>
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

-- >>>>>>>>>>>>>>>>>>>>>>>>  04_rules.sql  >>>>>>>>>>>>>>>>>>>>>>>>
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

-- >>>>>>>>>>>>>>>>>>>>>>>>  05_views.sql  >>>>>>>>>>>>>>>>>>>>>>>>
-- View de estatisticas (painel do Gestor — controle de acesso na aplicacao)
--
-- ============================================================================
-- vw_estatisticas_chamados
-- ============================================================================
-- [!] DESTAQUE: Usa JOIN LATERAL para buscar o ULTIMO status de cada chamado
--     na tabela historico_chamado. Diferenca pratica:
--       - Sem LATERAL: precisaria de uma subconsulta complexa com GROUP BY
--       - Com LATERAL: executa a subconsulta para CADA linha de chamado,
--         pegando apenas 1 registro (LIMIT 1) — o mais recente.
--
--     A view retorna: total de chamados agrupados por (categoria, bairro,
--     status), considerando apenas registros ativos.
--
--     Uso: Dashboard do Gestor — exibe graficos de chamados por regiao e status.
-- ============================================================================

BEGIN;

DROP VIEW IF EXISTS vw_estatisticas_chamados;

CREATE VIEW vw_estatisticas_chamados AS
SELECT
    cat.nome        AS categoria,          -- Nome da categoria de servico
    b.nome_bairro   AS bairro,             -- Nome do bairro
    s.sigla         AS sigla_status,       -- Sigla do status (AB, EA, EE, CO, CA)
    s.descricao     AS status_descricao,   -- Descricao do status
    COUNT(*)::BIGINT AS total_chamados     -- Quantidade de chamados (cast para BIGINT)
FROM chamado ch
-- JOIN 1: chamado → servico → categoria_servico (cadeia de FKs)
JOIN servico srv     ON srv.id_servico  = ch.id_servico
JOIN categoria_servico cat ON cat.id_categoria = srv.id_categoria
-- JOIN 2: chamado → bairro (localizacao)
JOIN bairro b        ON b.id_bairro     = ch.id_bairro
-- [!] JOIN 3: LATERAL — busca o ultimo status de cada chamado no historico
--     A subconsulta roda para CADA chamado (como um foreach), ordena por
--     dt_alteracao DESC e pega apenas 1 registro (o mais recente).
JOIN LATERAL (
    SELECT id_status FROM historico_chamado
    WHERE id_chamado = ch.id_chamado
    ORDER BY dt_alteracao DESC LIMIT 1
) ultimo_h ON TRUE
-- JOIN 4: status_chamado — pega a sigla e descricao do status atual
JOIN status_chamado s ON s.id_status = ultimo_h.id_status
-- Filtra apenas registros ativos (soft delete)
WHERE cat.ativo
  AND srv.ativo
  AND b.ativo
-- Agrupamento: um registro por (categoria, bairro, status)
GROUP BY cat.nome, b.nome_bairro, s.sigla, s.descricao;

COMMIT;

