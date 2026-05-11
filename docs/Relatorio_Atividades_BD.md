# Relatório de Atividades do Projeto - Portal VG 24H

**Membros da Equipe:** 
- Fausto Yuuki
- Bruno Dias
- Rafael Pereira

---

## Divisão de Tarefas e Contribuições no Código (Commits)

Este documento detalha o papel de cada membro do grupo e suas respectivas responsabilidades no desenvolvimento do sistema e banco de dados, com base nos commits realizados no repositório do projeto. A divisão do trabalho foi estruturada para garantir que todos os alunos tivessem participação ativa na codificação, estruturação e integração do projeto.

### 1. Fausto Yuuki
**Papel Principal:** Frontend, Design System GOV.BR e Interface com o Usuário

O Fausto ficou inteiramente responsável pela camada de apresentação visual do portal, garantindo a integração correta do Design System do GOV.BR com os dados dinâmicos vindos do banco de dados.

**Principais Feitos e Commits no Código:**
*   **Templates e Telas (`backend/templates/portal/`):** Desenvolvimento de todas as interfaces HTML (Cidadão, Equipe, Gestão, Login), estruturando como as informações consultadas no banco de dados são exibidas para o usuário.
*   **Design System GOV.BR (`backend/static/portal/`):** Implementação e customização do CSS e JavaScript do padrão GOV.BR (`govbr-layout.css`, `govbr-carousel-custom.css`, `vg24h.css`, `vg24h.js`), garantindo a acessibilidade e responsividade da aplicação.
*   **Visualização de Dados Dinâmicos:** Conexão do front-end com os objetos de contexto passados pelas views, mapeando os dados relacionais (como listas de chamados, dashboards e catálogos de serviços) diretamente nas interfaces.

### 2. Rafael Pereira
**Papel Principal:** Engenharia de Banco de Dados e Modelagem

O Rafael focou na arquitetura do banco de dados, garantindo a integridade relacional, a modelagem física e o comportamento do SGBD utilizado no projeto.

**Principais Feitos e Commits no Código:**
*   **Esquema e Tabelas (`database/01_schema.sql`):** Criação de todo o modelo DDL do banco (PostgreSQL), englobando as tabelas principais (`auth_user`, `portal_chamado`, `portal_bairro`, `portal_categoria`).
*   **Regras de Negócio no SGBD (`database/03_functions_triggers.sql` e `database/05_views.sql`):** Desenvolvimento de triggers, functions (PL/pgSQL) e views consolidadas para automatizar lógicas diretamente no banco (ex: histórico de chamados e métricas).
*   **Mapeamento ORM e Seeds (`backend/portal/models.py` e `database/02_seed.sql`):** Tradução do banco físico para o ORM do Django, além da criação da carga de dados iniciais (inserts) para testes e popularização do ambiente.

### 3. Bruno Dias
**Papel Principal:** Backend, Segurança e Regras de Negócio (CRUD)

O Bruno liderou a integração entre a interface (criada pelo Fausto) e o banco de dados (estruturado pelo Rafael), construindo a lógica de servidor, autenticação e controle de acessos.

**Principais Feitos e Commits no Código:**
*   **Autenticação e Permissões (`backend/portal/views_auth.py` e `backend/portal/decorators.py`):** Lógica de login, recuperação de senhas e a criação de decoradores de rotas para garantir que as consultas ao banco só fossem feitas por usuários com os devidos níveis de acesso (Cidadão, Equipe, Gestão).
*   **Controladores e Operações DML (`backend/portal/views_gestao.py` e `backend/portal/forms.py`):** Desenvolvimento das operações de inserção, leitura, atualização e exclusão (CRUD) das áreas gerenciais, processando formulários e validando as requisições antes de enviá-las ao banco de dados.
*   **Automações de Backend (`backend/portal/management/commands/`):** Criação de scripts via CLI do Django (comandos de gerenciamento) para interagir programaticamente com o banco (ex: criação de contas administrativas e arquivamento de notificações).

---
