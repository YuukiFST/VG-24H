# Roteiro de Apresentação — Rafael Pereira

## 🎯 Responsabilidade: Banco de Dados, Modelagem e Backend Core

Rafael é responsável por toda a **camada de banco de dados** (schema, triggers, rules/triggers de integridade, views, seed) e pela **infraestrutura central do backend** (models, middleware, decorators, utils, config).

---

## 📌 O que você apresenta

### 1. Modelagem de Dados (Plano §5)

> O banco tem **11 tabelas**. O **status do chamado NÃO é um campo direto** na tabela `chamado` — ele é determinado pelo **último registro de `historico_chamado`**. Isso é uma decisão arquitetural importante: todo o histórico de status fica rastreável.

**Siglas de status:** `AB` = Aberto, `EA` = Em Análise, `EE` = Em Execução, `CO` = Concluído, `CA` = Cancelado

**As 11 entidades:**

| # | Tabela | Descrição |
|---|---|---|
| 1 | `cidadao` | Cidadãos (`perfil = 'CID'`) |
| 2 | `servidor` | Colaboradores (`COL`) e Gestores (`GES`). FK → `secretaria` |
| 3 | `secretaria` | Secretarias municipais |
| 4 | `status_chamado` | 5 status: AB, EA, EE, CO, CA |
| 5 | `categoria_servico` | Categorias de serviço. FK → `secretaria` |
| 6 | `servico` | Serviços com prazos amarelo/vermelho. FK → `categoria_servico` |
| 7 | `bairro` | Bairros de VG com CEP e região |
| 8 | `chamado` | Entidade central. **SEM `id_status`** — status vem do histórico |
| 9 | `foto_chamado` | Fotos (URL Cloudinary). FK → chamado |
| 10 | `historico_chamado` | Mudanças de status + observações. **Fonte da verdade para o status atual** |
| 11 | `notificacao` | Avisos ao cidadão (lida, arquivada) |

### 2. Scripts SQL — o que cada arquivo faz

#### `01_schema.sql` (191 linhas)

- 11 CREATE TABLE com PKs, FKs, constraints
- **`chamado` NÃO tem `id_status`** — a FK foi removida. Status = último histórico
- `CHECK (sigla IN ('AB', 'EA', 'EE', 'CO', 'CA'))` em `status_chamado`
- 6 índices de performance (não existe `ix_chamado_status` pois não há FK de status)

#### `02_seed.sql`

- 5 status: AB, EA, EE, CO, CA
- 1 secretaria, 2 categorias, 5 serviços, 20 bairros

#### `03_functions_triggers.sql` (107 linhas)

**Trigger 1** — `trg_chamado_after_insert_historico_ab`:
- `AFTER INSERT` em `chamado`
- Função `fn_chamado_after_insert_historico_ab()`: insere em `historico_chamado` com status AB
- **Garante**: todo chamado nasce com ao menos 1 histórico

**Trigger 2 — Parte A** — `trg_chamado_before_update_metadados`:
- `BEFORE UPDATE` em `chamado`
- Função `fn_chamado_before_update_metadados()`: apenas atualiza `atualizado_em = CURRENT_TIMESTAMP`

**Trigger 2 — Parte B** — `trg_historico_after_insert_status`:
- **`AFTER INSERT` em `historico_chamado`** (mudança importante — antes era AFTER UPDATE em chamado)
- Função `fn_historico_after_insert_status()`:
  1. Busca a sigla e descrição do status inserido
  2. Se CO ou CA → atualiza `dt_conclusao` no chamado
  3. Se AB, EA ou EE → limpa `dt_conclusao = NULL`
  4. Gera notificação automática com mensagem: `"Chamado XXXX: status alterado para Descrição"`

#### `04_rules.sql` (126 linhas)

> **Mudança importante**: As rules R1, R2 e R3 foram **convertidas para Triggers BEFORE** porque rules condicionais impediam o `INSERT RETURNING` do Django ORM. Agora usam `RAISE EXCEPTION` (erro explícito) em vez de `DO INSTEAD NOTHING` (falha silenciosa).

| Rule/Trigger | Tabela | Tipo | O que faz |
|---|---|---|---|
| **R1 → Trigger** `trg_foto_chamado_encerrado` | `foto_chamado` | BEFORE INSERT | Bloqueia se último status é CO/CA. Usa subquery no último `historico_chamado`. `RAISE EXCEPTION` |
| **R2 → Trigger** `trg_historico_obs_encerrado` | `historico_chamado` | BEFORE INSERT | Bloqueia observação se último status é CO/CA. `RAISE EXCEPTION` |
| **R3 → Trigger** `trg_avaliacao_imutavel` | `chamado` | BEFORE UPDATE | Bloqueia alteração de avaliação já preenchida. `RAISE EXCEPTION` |
| **R4** | — | Removida | Controle de perfil feito na camada Django (views) |
| **R5** (Rule) | `historico_chamado` | UPDATE + DELETE | `DO INSTEAD NOTHING` — impede modificar ou excluir histórico |
| **R6** | — | Removida | Validação de resolução feita no Django (`EquipeStatusForm.clean()`) |
| **Extra** (Rule) | `chamado` | DELETE | `DO INSTEAD NOTHING` — impede excluir chamado |

#### `fix_rules_to_triggers.sql` (84 linhas — arquivo novo)

- Script de migração para converter R1, R2, R3 de rules para triggers
- DROP das rules antigas + criação dos triggers equivalentes
- Para ser executado no NeonDB SQL Editor em bancos já existentes

#### `05_views.sql` (30 linhas)

- `vw_estatisticas_chamados`: usa **`JOIN LATERAL`** para buscar o último status de cada chamado no `historico_chamado`
- Agrupa por categoria, bairro, sigla_status, status_descricao → `COUNT(*)`

### 3. Models Django (ORM) — `models.py`

> **Mudança importante**: O model `Chamado` agora tem **3 properties** em vez do campo `id_status`:

| Property | O que faz |
|---|---|
| `status_atual` | Busca o último `HistoricoChamado` e retorna o `StatusChamado` |
| `sigla_status` | Retorna a sigla do status atual (ex: `"AB"`, `"CO"`) |
| `atualizado_em` | Retorna `dt_alteracao` do último histórico |

O model `HistoricoChamado` agora tem `related_name="historicos"` para facilitar `ch.historicos.all()`.

| Model | `db_table` | Notas |
|---|---|---|
| `Chamado` | `chamado` | **Sem `id_status`**. Properties `status_atual`, `sigla_status` |
| `HistoricoChamado` | `historico_chamado` | `related_name="historicos"`. **Fonte da verdade do status** |
| `Servico` | `servico` | `related_name="servicos"` na FK `id_categoria` |
| Demais | — | Sem mudanças |

### 4. Middleware — `middleware.py`

- `_usuario_da_sessao()`: busca Cidadão ou Servidor pela sessão
- `_postgres_sessao()`: define `portal.perfil` e `portal.id_usuario_acao` na sessão PG
- `PortalUserMiddleware`: injeta `request.portal_user`

### 5. Decorators — `decorators.py`

| Decorator | O que faz |
|---|---|
| `@perfis("CID")` | Só cidadão |
| `@perfis("COL", "GES")` | Equipe |
| `@perfis("GES")` | Só gestor |

### 6. Utils — `utils.py`

| Função | O que faz |
|---|---|
| `proximo_protocolo()` | Gera protocolo `20260001` |
| `salvar_foto_upload()` | Cloudinary ou local |
| `sigla_status(chamado)` | Retorna `chamado.sigla_status` (property do model) |
| `cor_semaforo(chamado)` | verde/amarelo/vermelho |

### 7. Infraestrutura

- `config/settings.py`: PostgreSQL, WhiteNoise, timezone `America/Cuiaba`
- `backend/portal/migrations/0001_initial.py`: migration inicial do Django
- `uv` como gerenciador de pacotes

---

## 📁 Arquivos que você DEVE saber explicar

### SQL — pasta `database/`

| Arquivo | Conteúdo |
|---|---|
| `00_install_all.sql` | Script master |
| `01_schema.sql` | 11 tabelas + constraints (chamado SEM id_status) |
| `02_seed.sql` | Status AB/EA/EE/CO/CA, secretaria, categorias, serviços, bairros |
| `03_functions_triggers.sql` | 3 funções + 3 triggers (T1 + T2A + T2B) |
| `04_rules.sql` | R1→Trigger, R2→Trigger, R3→Trigger, R5 Rule, Extra Rule |
| `05_views.sql` | View com JOIN LATERAL |
| `fix_rules_to_triggers.sql` | Migração rules → triggers |
| `aplicar_no_neon.sql` | Script consolidado para Neon |

### Python — pasta `backend/portal/`

| Arquivo | Conteúdo |
|---|---|
| `models.py` | 12 classes ORM. `Chamado` com properties `status_atual`, `sigla_status` |
| `middleware.py` | Autenticação dual + `set_config` PG |
| `decorators.py` | `@perfis()` |
| `utils.py` | Protocolo, upload, semáforo |
| `context_processors.py` | `nav_user`, `nav_perfil`, `notif_count` |
| `migrations/0001_initial.py` | Migration inicial |

---

## 🗣️ Pontos-chave para a apresentação

1. **Explique a decisão arquitetural**: status no `historico_chamado`, não campo direto. Mostra `ch.status_atual` → property
2. **Mostre no pgAdmin**: INSERT chamado → Trigger 1 cria histórico AB
3. **INSERT em historico_chamado** com novo status → Trigger 2B atualiza `dt_conclusao` e gera notificação
4. **Demonstre cada trigger de integridade**:
   - `trg_foto_chamado_encerrado`: INSERT foto em chamado CO → `RAISE EXCEPTION`
   - `trg_historico_obs_encerrado`: INSERT observação em CA → `RAISE EXCEPTION`
   - `trg_avaliacao_imutavel`: UPDATE avaliação já preenchida → `RAISE EXCEPTION`
5. **Mostre as Rules restantes**: R5 (historico imutável), Extra (chamado sem delete)
6. **Mostre a View** com `JOIN LATERAL` no último histórico
7. **Explique o middleware**: `set_config` → sessão PG
8. **Explique porque rules foram convertidas**: `INSERT RETURNING` do Django ORM é incompatível com rules condicionais

---

## 📚 Mapeamento por Etapa da Disciplina

| Etapa | O que Rafael apresenta |
|---|---|
| **Etapa 1** | Seção 5 — Modelo de Dados: 11 entidades |
| **Etapa 2** | DER + `01_schema.sql` + pgAdmin |
| **Etapa 3** | Apoio com estrutura de dados |
| **Etapa 4** | `settings.py`, conexão Neon, `middleware.py` |
| **Etapa 5** | CRUD de Bairros + Triggers + Triggers de integridade |
| **Etapa 6** | `models.py`, `decorators.py`, `middleware.py`, `utils.py` |

### ⚠️ Ponto Crítico — Conversão Rules → Triggers

Explique que as rules R1, R2 e R3 precisaram ser convertidas para triggers porque:
- O Django ORM usa `INSERT ... RETURNING id` para obter o ID do registro inserido
- Rules condicionais (`DO INSTEAD NOTHING`) interceptam o INSERT, fazendo o RETURNING falhar
- Triggers BEFORE com `RAISE EXCEPTION` são compatíveis: retornam erro explícito que o Django captura

### 📄 Checklist

- [ ] Print do DER (11 entidades, chamado SEM id_status)
- [ ] Print das tabelas no pgAdmin
- [ ] SQL do Trigger 1 (`fn_chamado_after_insert_historico_ab`) — linha a linha
- [ ] SQL do Trigger 2A (`fn_chamado_before_update_metadados`) — linha a linha
- [ ] SQL do Trigger 2B (`fn_historico_after_insert_status`) — linha a linha
- [ ] SQL dos Triggers de integridade (R1→T, R2→T, R3→T) — linha a linha
- [ ] SQL da View com JOIN LATERAL
- [ ] Print do `models.py` — properties `status_atual`, `sigla_status`
- [ ] Print do `middleware.py` — `set_config`
- [ ] Demonstração: INSERT chamado → Trigger 1
- [ ] Demonstração: INSERT historico → Trigger 2B (notificação + dt_conclusao)
- [ ] Demonstração: violação de cada trigger de integridade → RAISE EXCEPTION
