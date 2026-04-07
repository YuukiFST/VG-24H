# Roteiro de Apresentação — Fausto Yuuki

## 🎯 Responsabilidade: Módulo Colaborador, Módulo Gestor e Frontend (Gov.br DS)

Fausto é responsável pelos **módulos administrativos** (Colaborador e Gestor) e pela **arquitetura visual** do portal, incluindo o template base e a conformidade com o Design System Gov.br.

---

## 📌 O que você apresenta

### 1. Frontend e Design System Gov.br (Plano §4 — Interface visual)

- **Template Base** (`base.html`): estrutura master que todas as páginas herdam
  - Header com logo da Prefeitura, barra de busca, menu de acesso rápido, avatar do usuário
  - Sidebar/menu de navegação dinâmico por perfil (CID, COL, GES)
  - Footer com logo e links institucionais
  - Skip links para acessibilidade
  - Cookie bar (LGPD)
- **CSS customizado** (`vg24h.css`): variáveis CSS, tokens de design, estilos das seções (hero, cards, steps, stats, CTA, dashboard, etc.)
- **Conformidade Gov.br**: uso da fonte Rawline, componentes `br-button`, `br-input`, `br-table`, `br-tag`, etc.
- **Responsividade**: como o layout se adapta em telas menores

### 2. Módulo do Colaborador — COL (Plano §3.1 — Módulo do Colaborador)

- **Dashboard Semáforo** (`views_equipe.py` → `equipe_dashboard`): cards coloridos (verde/amarelo/vermelho) contando chamados por faixa de prazo
- **Lista de Chamados** (`views_equipe.py` → `equipe_chamados`): tabela com filtros por bairro, status e data
- **Detalhe do Chamado** (`views_equipe.py` → `equipe_chamado_detalhe`):
  - Alteração de status (livre, exceto reabrir CO/CA)
  - Preenchimento obrigatório do campo resolução para fechar (CO/CA)
  - Adição de observação no histórico (visível ao cidadão)
  - Upload de fotos como comprovação

### 3. Módulo do Gestor — GES (Plano §3.1 — Módulo do Gestor)

- **Todas as funcionalidades do Colaborador** + as exclusivas:
- **Gerenciamento de Colaboradores** (`views_gestao.py` → `gestao_colaboradores`): criação de contas com senha temporária
- **Gerenciamento de Categorias** (`views_gestao.py` → `gestao_categorias`, `gestao_categoria_nova`, `gestao_categoria_editar`): CRUD completo
- **Gerenciamento de Serviços** (`views_gestao.py` → `gestao_servicos`, `gestao_servico_novo`, `gestao_servico_editar`): CRUD com definição de prazos (semáforo amarelo/vermelho)
- **Gerenciamento de Bairros** (`views_gestao.py` → `gestao_bairros`, `gestao_bairro_novo`, `gestao_bairro_editar`): CRUD
- **Gerenciamento de Banners** (`views_gestao.py` → `gestao_banners`, `gestao_banner_novo`, `gestao_banner_editar`, `gestao_banner_excluir`): CRUD para o carousel da homepage
- **Painel de Estatísticas** (`views_gestao.py` → `gestao_estatisticas`): dados consolidados por categoria, bairro e status (utiliza a View SQL)
- **Poder total** sobre status: pode alterar qualquer chamado, incluindo reabrir CO e CA

### 4. Sistema de Banners

- Model `BannerPublicacao` (criado em `models.py`)
- CRUD de banners no painel de gestão
- Carousel dinâmico na homepage (`root.html`) — auto-advance, dots, prev/next

### 5. Rotas Administrativas

- Explicar as rotas em `urls.py` referentes às funcionalidades do Colaborador e Gestor

---

## 📁 Arquivos que você deve saber explicar

### Python (Backend)

| Arquivo                                                                                         | Conteúdo                                                                           |
| ----------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| [views_equipe.py](file:///e:/Projects/PersonalProjects/VG_Smart/backend/portal/views_equipe.py) | Dashboard semáforo, lista e detalhe de chamados (COL)                              |
| [views_gestao.py](file:///e:/Projects/PersonalProjects/VG_Smart/backend/portal/views_gestao.py) | CRUD de colaboradores, categorias, serviços, bairros, banners e estatísticas (GES) |
| [urls.py](file:///e:/Projects/PersonalProjects/VG_Smart/backend/portal/urls.py)                 | Rotas de equipe e gestão (sua metade)                                              |

### Templates — Colaborador (COL)

| Arquivo                                                                                                                           | Conteúdo                                                |
| --------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| [equipe/dashboard.html](file:///e:/Projects/PersonalProjects/VG_Smart/backend/templates/portal/equipe/dashboard.html)             | Dashboard semáforo com cards verde/amarelo/vermelho     |
| [equipe/chamados_lista.html](file:///e:/Projects/PersonalProjects/VG_Smart/backend/templates/portal/equipe/chamados_lista.html)   | Tabela de chamados filtráveis                           |
| [equipe/chamado_detalhe.html](file:///e:/Projects/PersonalProjects/VG_Smart/backend/templates/portal/equipe/chamado_detalhe.html) | Detalhe do chamado com ações (status, observação, foto) |

### Templates — Gestor (GES)

| Arquivo                                                                                                                         | Conteúdo                             |
| ------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------ |
| [gestao/colaboradores.html](file:///e:/Projects/PersonalProjects/VG_Smart/backend/templates/portal/gestao/colaboradores.html)   | Lista e criação de colaboradores     |
| [gestao/categorias.html](file:///e:/Projects/PersonalProjects/VG_Smart/backend/templates/portal/gestao/categorias.html)         | Lista de categorias                  |
| [gestao/categoria_form.html](file:///e:/Projects/PersonalProjects/VG_Smart/backend/templates/portal/gestao/categoria_form.html) | Formulário de criar/editar categoria |
| [gestao/servicos.html](file:///e:/Projects/PersonalProjects/VG_Smart/backend/templates/portal/gestao/servicos.html)             | Lista de serviços                    |
| [gestao/servico_form.html](file:///e:/Projects/PersonalProjects/VG_Smart/backend/templates/portal/gestao/servico_form.html)     | Formulário de criar/editar serviço   |
| [gestao/bairros.html](file:///e:/Projects/PersonalProjects/VG_Smart/backend/templates/portal/gestao/bairros.html)               | Lista de bairros                     |
| [gestao/bairro_form.html](file:///e:/Projects/PersonalProjects/VG_Smart/backend/templates/portal/gestao/bairro_form.html)       | Formulário de criar/editar bairro    |
| [gestao/banners.html](file:///e:/Projects/PersonalProjects/VG_Smart/backend/templates/portal/gestao/banners.html)               | Lista de banners                     |
| [gestao/banner_form.html](file:///e:/Projects/PersonalProjects/VG_Smart/backend/templates/portal/gestao/banner_form.html)       | Formulário de criar/editar banner    |
| [gestao/estatisticas.html](file:///e:/Projects/PersonalProjects/VG_Smart/backend/templates/portal/gestao/estatisticas.html)     | Painel de estatísticas consolidadas  |

### Frontend — Template Base e CSS

| Arquivo                                                                                        | Conteúdo                                                         |
| ---------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| [base.html](file:///e:/Projects/PersonalProjects/VG_Smart/backend/templates/portal/base.html)  | Template master: header, sidebar, footer, skip links, cookie bar |
| [vg24h.css](file:///e:/Projects/PersonalProjects/VG_Smart/backend/static/portal/css/vg24h.css) | CSS customizado: variáveis, tokens, todos os estilos do portal   |

---

## 🗣️ Pontos-chave para a apresentação

1. **Mostre o `base.html`** e explique como todas as páginas herdam a estrutura (header + sidebar + footer)
2. **Abra o painel do Gestor** e faça operações ao vivo:
   - Crie um novo colaborador e mostre a senha temporária gerada
   - Crie um novo serviço com prazos de semáforo customizados
   - Adicione/edite um banner e mostre ele aparecendo no carousel da homepage
3. **Mostre o Dashboard Semáforo** do Colaborador e explique as cores (verde = dentro do prazo, amarelo = atenção, vermelho = atrasado)
4. **Altere o status de um chamado** no painel do Colaborador:
   - Mude para AN (Em análise) → mostre a notificação gerada ao cidadão
   - Tente fechar (CO) sem preencher resolução → mostre o erro
   - Feche o chamado com resolução preenchida → sucesso
5. **Demonstre o controle de acesso**: mostre que um COL não consegue acessar a rota `/gestao/` (retorna erro 403/redirect)
6. **Mostre a responsividade**: redimensione a tela e mostre o layout adaptando (sidebar colapsando, cards empilhando)
7. **Destaque o CSS** (`vg24h.css`): mostre as variáveis CSS customizadas, o sistema de tokens de cor do Gov.br, e como os componentes `br-*` são estilizados

---

## 📚 Mapeamento por Etapa da Disciplina

A professora avalia o projeto por etapas. Abaixo está o que você é responsável em cada uma:

| Etapa                                            | O que Fausto apresenta                                                                                                                                                                                            |
| ------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Etapa 1** (Plano de Trabalho)                  | Seções 3.1 (Módulo COL e GES), 4 (Restrições) e 7 (Ferramentas)                                                                                                                                                   |
| **Etapa 2** (Modelagem + Criação BD)             | Entidades `servidor`, `secretaria`, `categoria_servico`, `servico`, `bairro`, `historico_chamado` — explicar campos e constraints                                                                                 |
| **Etapa 3** (Layout das telas)                   | Print do layout das telas: Dashboard Semáforo (COL), Lista de Chamados da Equipe, Detalhe do Chamado (COL/GES), Painel de Gestão (categorias, serviços, bairros, colaboradores, banners), Estatísticas            |
| **Etapa 4** (Conexão + Login)                    | Mostrar o `base.html` como template master e a integração com o Design System Gov.br (CDN)                                                                                                                        |
| **Etapa 5** (Cadastro piloto + Recurso avançado) | CRUD de Categorias de Serviço como tela piloto — demonstrar INSERT (nova categoria), SELECT (listar), UPDATE (editar), DELETE (inativar)                                                                          |
| **Etapa 6** (Demais telas)                       | **Telas que Fausto desenvolveu:** Dashboard Semáforo, Lista de Chamados (equipe), Detalhe do Chamado (equipe), Gestão de Colaboradores, Categorias, Serviços, Bairros, Banners, Estatísticas, Template Base e CSS |

### ⚠️ Ponto Crítico — Etapa 5

A professora quer ver **uma tela de cadastro piloto** com as **4 operações (SELECT, INSERT, UPDATE, DELETE)**. Fausto deve:

1. Mostrar a lista de Categorias (SELECT) na tela `categorias.html`
2. Criar uma nova Categoria (INSERT) via `categoria_form.html`
3. Editar a categoria criada (UPDATE)
4. Inativar a categoria (DELETE lógico — campo `ativo = FALSE`)

### ⚠️ Ponto Crítico — Etapa 6

A professora exige que **cada aluno relate quais telas foram eleitas para desenvolvimento**. Fausto deve listar:

> **Telas desenvolvidas por Fausto Yuuki:**
>
> 1. Template Base (`base.html`) — header, sidebar, footer, cookie bar
> 2. CSS Global (`vg24h.css`) — design system, variáveis, responsividade
> 3. Dashboard Semáforo do Colaborador (`equipe/dashboard.html`)
> 4. Lista de Chamados da Equipe (`equipe/chamados_lista.html`)
> 5. Detalhe do Chamado — visão Equipe (`equipe/chamado_detalhe.html`)
> 6. Gestão de Colaboradores (`gestao/colaboradores.html`)
> 7. Gestão de Categorias (`gestao/categorias.html` + `gestao/categoria_form.html`)
> 8. Gestão de Serviços (`gestao/servicos.html` + `gestao/servico_form.html`)
> 9. Gestão de Bairros (`gestao/bairros.html` + `gestao/bairro_form.html`)
> 10. Gestão de Banners (`gestao/banners.html` + `gestao/banner_form.html`)
> 11. Painel de Estatísticas (`gestao/estatisticas.html`)

### 📄 Checklist para o Seminário Final

- [ ] Print do código `views_equipe.py` — dashboard e detalhe de chamado
- [ ] Print do código `views_gestao.py` — CRUD de categorias, serviços, bairros, colaboradores
- [ ] Print do `base.html` — explicar a estrutura master herdada por todas as páginas
- [ ] Print do `vg24h.css` — variáveis CSS e tokens do Gov.br
- [ ] Print do Dashboard Semáforo em execução (cards verde/amarelo/vermelho)
- [ ] Print da lista de chamados com filtros em execução
- [ ] Print do CRUD completo de Categorias (listar → criar → editar → inativar)
- [ ] Print do CRUD de Serviços com prazos de semáforo (amarelo/vermelho)
- [ ] Print da criação de Colaborador com senha temporária
- [ ] Print do Painel de Estatísticas consolidadas
- [ ] Print da gestão de Banners + carousel na homepage
- [ ] Demonstração ao vivo: login como GES → CRUD → alterar status de chamado → ver impacto no dashboard
