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
