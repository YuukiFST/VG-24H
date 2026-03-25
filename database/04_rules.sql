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
