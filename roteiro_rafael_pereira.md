# Roteiro de Apresentação — Rafael Pereira

## 🎯 Responsabilidade: Banco de Dados, Modelagem e Backend Core

Rafael é responsável por toda a **camada de banco de dados** e pela **infraestrutura central do backend** que sustenta a aplicação.

---

## 📌 O que você apresenta

### 1. Modelagem de Dados (Plano de Trabalho §5)

- Apresentar o **DER Conceitual e Lógico** (BrModelo)
- Explicar as **11 entidades** e seus relacionamentos com cardinalidades
- Justificar as decisões de modelagem: por que `cidadao` e `servidor` são tabelas separadas, por que `historico_chamado` centraliza observações, etc.

### 2. Scripts SQL — Criação e Carga

- **Schema** (`01_schema.sql`): criação de todas as tabelas, PKs, FKs, constraints (`NOT NULL`, `UNIQUE`, `CHECK`)
- **Seed** (`02_seed.sql`): carga inicial com 2 categorias, 5 serviços, 5 status e bairros de Várzea Grande
- **Install** (`00_install_all.sql`): script unificado que executa tudo em sequência

### 3. Recursos Avançados de Banco de Dados

- **Triggers** (`03_functions_triggers.sql`):
  - **Trigger 1** (AFTER INSERT em chamado): cria registro automático em `historico_chamado` com status AB
  - **Trigger 2** (AFTER UPDATE em chamado): insere histórico, gera notificação, preenche `dt_conclusao` se CO, atualiza `atualizado_em`
- **Rules** (`04_rules.sql`):
  - **Rule 1**: impede INSERT em `foto_chamado` se chamado CO ou CA
  - **Rule 2**: impede INSERT de observação em `historico_chamado` se chamado CO ou CA
  - **Rule 3**: impede UPDATE de `nota_avaliacao` e `comentario_avaliacao` se já preenchidos
  - **Rule 4**: controla alterações de status por perfil (CID, COL, GES)
  - **Rule 5**: impede UPDATE e DELETE em `historico_chamado`
  - **Rule 6**: impede fechar chamado (CO/CA) sem campo `resolucao`
- **View** (`05_views.sql`): estatísticas consolidadas por categoria, bairro e status

### 4. Models Django (ORM)

- Explicar como cada tabela SQL foi mapeada para uma classe Python no Django
- Campos, tipos, Meta class, `db_table`, `managed = False`
- O model `BannerPublicacao` (adição para painel de gestão)

### 5. Middleware e Decorators

- **Middleware** (`middleware.py`): como funciona a autenticação dual (cidadão + servidor) via sessão
- **Decorators** (`decorators.py`): como os decorators `@perfis("GES")`, `@perfis("COL","GES")` protegem as rotas

### 6. Infraestrutura

- Conexão Django ↔ PostgreSQL (Neon)
- Configuração do `settings.py` (DATABASE_URL, etc.)
- Gerenciador de ambiente `uv`

---

## 📁 Arquivos que você deve saber explicar

### SQL (Banco de Dados)

| Arquivo                                                                                                       | Conteúdo                                            |
| ------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| [00_install_all.sql](file:///e:/Projects/PersonalProjects/VG_Smart/database/00_install_all.sql)               | Script master que executa todos os SQLs em ordem    |
| [01_schema.sql](file:///e:/Projects/PersonalProjects/VG_Smart/database/01_schema.sql)                         | CREATE TABLE de todas as 11 entidades + constraints |
| [02_seed.sql](file:///e:/Projects/PersonalProjects/VG_Smart/database/02_seed.sql)                             | INSERT de categorias, serviços, status e bairros    |
| [03_functions_triggers.sql](file:///e:/Projects/PersonalProjects/VG_Smart/database/03_functions_triggers.sql) | Funções PL/pgSQL + 2 Triggers                       |
| [04_rules.sql](file:///e:/Projects/PersonalProjects/VG_Smart/database/04_rules.sql)                           | 6 Rules de integridade                              |
| [05_views.sql](file:///e:/Projects/PersonalProjects/VG_Smart/database/05_views.sql)                           | View de estatísticas consolidadas                   |

### Python (Backend Core)

| Arquivo                                                                                                     | Conteúdo                                         |
| ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| [models.py](file:///e:/Projects/PersonalProjects/VG_Smart/backend/portal/models.py)                         | ORM: todas as classes que mapeiam as tabelas     |
| [middleware.py](file:///e:/Projects/PersonalProjects/VG_Smart/backend/portal/middleware.py)                 | Autenticação dual (cidadão/servidor) via sessão  |
| [decorators.py](file:///e:/Projects/PersonalProjects/VG_Smart/backend/portal/decorators.py)                 | Controle de acesso por perfil (@perfis)          |
| [utils.py](file:///e:/Projects/PersonalProjects/VG_Smart/backend/portal/utils.py)                           | Funções utilitárias (geração de protocolo, etc.) |
| [context_processors.py](file:///e:/Projects/PersonalProjects/VG_Smart/backend/portal/context_processors.py) | Variáveis globais injetadas nos templates        |

---

## 🗣️ Pontos-chave para a apresentação

1. **Abra o pgAdmin** e mostre as tabelas criadas, os dados de seed, os triggers e rules
2. **Execute um INSERT de chamado** e mostre o Trigger 1 criando o histórico automaticamente
3. **Altere o status de um chamado** e mostre o Trigger 2 gerando notificação + histórico
4. **Tente violar uma Rule** (ex: inserir foto em chamado CO) e mostre o erro do banco impedindo
5. **Mostre a View** de estatísticas no pgAdmin com os dados consolidados
6. **Explique no código** como `models.py` mapeia cada tabela e como `middleware.py` identifica se é cidadão ou servidor

---

## 📚 Mapeamento por Etapa da Disciplina

A professora avalia o projeto por etapas. Abaixo está o que você é responsável em cada uma:

| Etapa                                            | O que Rafael apresenta                                                                                                             |
| ------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------- |
| **Etapa 1** (Plano de Trabalho)                  | Seção 5 — Modelo de Dados: entidades, atributos, tipos, restrições                                                                 |
| **Etapa 2** (Modelagem + Criação BD)             | DER conceitual e lógico (BrModelo), esquema físico (`01_schema.sql`), print das tabelas criadas no PostgreSQL (pgAdmin)            |
| **Etapa 3** (Layout das telas)                   | _Não se aplica diretamente_ — apoiar com a estrutura de dados que as telas consomem                                                |
| **Etapa 4** (Conexão + Login)                    | Teste de conexão Django ↔ PostgreSQL (Neon), `settings.py` com `DATABASE_URL`, `middleware.py`                                     |
| **Etapa 5** (Cadastro piloto + Recurso avançado) | Demonstrar as **4 operações CRUD** em uma entidade (ex: Bairro ou Serviço) + demonstrar **Triggers e Rules** como recurso avançado |
| **Etapa 6** (Demais telas)                       | Código dos `models.py`, `decorators.py`, `middleware.py`, `utils.py`, `context_processors.py`                                      |

### ⚠️ Ponto Crítico — Etapa 5

A professora quer ver **uma tela de cadastro piloto** com as **4 operações básicas (SELECT, INSERT, UPDATE, DELETE)** + **recurso avançado de BD**. Você deve:

1. Mostrar o CRUD de Bairros (ou Serviços) funcionando — INSERT, listagem (SELECT), edição (UPDATE), e inativação (DELETE lógico)
2. Logo em seguida, mostrar um **Trigger** sendo disparado ao vivo (ex: inserir chamado → Trigger 1 cria histórico automático)
3. Mostrar uma **Rule** impedindo uma operação inválida (ex: tentar inserir foto em chamado CO → Rule 1 bloqueia)

### 📄 Checklist para o Seminário Final

- [ ] Print do DER conceitual e lógico (BrModelo)
- [ ] Print das tabelas criadas no pgAdmin
- [ ] Código SQL dos Triggers (com explicação linha a linha)
- [ ] Código SQL das Rules (com explicação linha a linha)
- [ ] Código SQL da View de estatísticas
- [ ] Print do `models.py` mostrando o mapeamento ORM
- [ ] Print do `middleware.py` mostrando a autenticação dual
- [ ] Demonstração ao vivo: INSERT chamado → Trigger cria histórico
- [ ] Demonstração ao vivo: tentativa de violação de Rule → erro
