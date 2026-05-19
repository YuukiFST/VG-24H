-- Fix: Remove siglas prefixadas das descricoes de status_chamado
-- Executar em bancos existentes onde as descricoes ainda contem "AB —", "CO —", etc.

UPDATE status_chamado SET descricao = 'Aberto'      WHERE sigla = 'AB';
UPDATE status_chamado SET descricao = 'Em Atendimento' WHERE sigla = 'EA';
UPDATE status_chamado SET descricao = 'Em Execução'    WHERE sigla = 'EE';
UPDATE status_chamado SET descricao = 'Concluído'      WHERE sigla = 'CO';
UPDATE status_chamado SET descricao = 'Cancelado'      WHERE sigla = 'CA';
