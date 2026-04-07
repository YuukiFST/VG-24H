-- Carga inicial: 5 status, 1 secretaria, 2 categorias, 5 serviços, bairros de Várzea Grande (MT)

BEGIN;

INSERT INTO status_chamado (sigla, descricao) VALUES
    ('AB', 'Aberto — Chamado aberto pelo cidadão'),
    ('EA', 'Em Atendimento — Em atendimento pela equipe responsável'),
    ('EE', 'Em Execução — Em execução no campo'),
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
