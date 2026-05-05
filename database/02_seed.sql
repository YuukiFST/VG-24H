-- Carga inicial: 5 status, 1 secretaria, 2 categorias, 5 servicos, 20 bairros de Varzea Grande (MT)
-- Dados minimos para o sistema funcionar (ambiente de desenvolvimento/testes)

BEGIN;

-- ============================================================================
-- 5 status do chamado (dominio fixo, corresponde ao CHECK constraint)
-- ============================================================================
INSERT INTO status_chamado (sigla, descricao) VALUES
    ('AB', 'Aberto — Chamado aberto pelo cidadao'),
    ('EA', 'Em Atendimento — Em atendimento pela equipe responsavel'),
    ('EE', 'Em Execucao — Em execucao no campo'),
    ('CO', 'Concluido — Servico concluido'),
    ('CA', 'Cancelado — Chamado cancelado');

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
-- prazo_amarelo = 15 dias, prazo_vermelho = 30 dias para todos
-- ============================================================================
INSERT INTO servico (id_categoria, nome, descricao, prazo_amarelo_dias, prazo_vermelho_dias)
SELECT c.id_categoria, v.nome, v.descricao, 15, 30
FROM categoria_servico c
JOIN (VALUES
    ('Infraestrutura e Via Publica', 'Iluminacao Publica', 'Postes, lampadas e pontos escuros.'),
    ('Infraestrutura e Via Publica', 'Pavimentacao e Vias', 'Buracos, calcadas e pavimentacao.'),
    ('Infraestrutura e Via Publica', 'Saneamento e Drenagem', 'Bueiros, alagamentos e esgoto.'),
    ('Mobilidade e Cidadania', 'Transito e Sinalizacao', 'Semaforos, placas e fiscalizacao.'),
    ('Mobilidade e Cidadania', 'Saude e Bem-estar', 'Demandas de saude publica e bem-estar urbano.')
) AS v(cat, nome, descricao) ON c.nome = v.cat;

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
