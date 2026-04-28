# Guia de Frontend e Interface — Portal VG 24H

Este guia explica **onde está cada parte visual** do projeto e **qual arquivo editar** para alterar qualquer elemento da interface. Use como referência rápida para localizar e modificar qualquer tela ou componente.

---

## 📂 Estrutura de Pastas do Frontend

```
backend/
├── templates/portal/           ← Todos os HTMLs
│   ├── base.html               ← Template master (header, sidebar, footer)
│   ├── root.html               ← Homepage pública
│   ├── auth/                   ← Telas de autenticação (5 arquivos)
│   ├── cidadao/                ← Telas do cidadão (7 arquivos)
│   ├── equipe/                 ← Telas da equipe COL/GES (3 arquivos)
│   ├── gestao/                 ← Telas do gestor GES (10 arquivos)
│   └── public/                 ← Telas públicas (2 arquivos)
│
├── static/
│   ├── img/
│   │   └── logo.png            ← Logo do sistema
│   └── portal/
│       ├── css/
│       │   └── vg24h.css       ← CSS principal (todos os estilos customizados)
│       ├── js/
│       │   └── vg24h.js        ← JavaScript principal (carousel, menus, forms)
│       ├── govbr-layout.css    ← Ajustes layout Gov.br
│       └── govbr-message-close.js  ← Fechar mensagens Gov.br
```

---

## 🧩 Template Base — `base.html` (afeta TODAS as páginas)

> **Localização:** `backend/templates/portal/base.html` (21 KB)
>
> Todas as páginas do sistema usam `{% extends "portal/base.html" %}`. Então qualquer mudança aqui **afeta o sistema inteiro**.

### O que está dentro do `base.html`:

| Elemento | O que faz | Como encontrar |
|---|---|---|
| **Header / Barra superior** | Logo, nome do portal, barra de busca, avatar do usuário | Procure por `<header` ou classe `header` |
| **Menu / Sidebar** | Navegação lateral com links dinâmicos por perfil (CID, COL, GES) | Procure por `nav_perfil` — o menu muda conforme o perfil logado |
| **Footer** | Endereço da prefeitura, redes sociais, links institucionais, ouvidoria | Procure por `<footer` |
| **Cookie bar (LGPD)** | Barra de cookies no rodapé | Procure por `cookie` |
| **Skip links** | Links de acessibilidade | Procure por `skip` |
| **Bloco de conteúdo** | Área que cada página preenche | `{% block content %}{% endblock %}` |
| **Bloco de CSS extra** | Permite páginas adicionarem CSS próprio | `{% block extra_css %}` |
| **Bloco de JS extra** | Permite páginas adicionarem JS próprio | `{% block extra_js %}` |
| **Mensagens Django** | Alertas de sucesso/erro (ex: "Chamado aberto") | Procure por `messages` |

### Perguntas frequentes sobre o `base.html`:

- **"Quero mudar o footer"** → Edite dentro de `<footer>` no `base.html`. Afeta TODAS as páginas.
- **"Quero mudar o header/logo"** → Edite dentro de `<header>` no `base.html`. A imagem está em `static/img/logo.png`.
- **"Quero adicionar um link no menu"** → Dentro do bloco de navegação (sidebar) no `base.html`, procure por `nav_perfil` e adicione `<a>` conforme o perfil.
- **"Quero mudar a cor do header"** → Edite no `vg24h.css` (procure pelas classes do header).

---

## 🏠 Homepage (Página Pública) — `root.html`

> **Localização:** `backend/templates/portal/root.html` (14 KB)
>
> **URL:** `http://localhost:8000/`

### Seções da homepage (de cima para baixo):

| Seção | O que faz | Onde alterar |
|---|---|---|
| **Carousel de Banners** | Imagens rotativas no topo. São dinâmicas (vêm do banco). | HTML: `root.html` (procure por `carousel` ou `banner`). **Para trocar as imagens**: use o painel do Gestor → Banners. |
| **Quick Actions** | Botões de ação rápida (ex: "Abrir Chamado", "Acompanhar") | `root.html` (procure por "quick" ou "acao") |
| **Cards de Serviços** | Mostra os top 5 serviços ativos | `root.html` (procure por `servicos`) |
| **Seção de Estatísticas** | "X Chamados resolvidos", "Y Bairros atendidos", etc. | `root.html` (procure por `stats` ou `estatisticas`). Para alinhar/posicionar → edite no `vg24h.css` as classes `.stats-section` / `.stats-grid` |
| **CTA (Call to Action)** | Faixa de destaque convidando o cidadão a usar o sistema | `root.html` |

### Perguntas frequentes sobre a homepage:

- **"Quero mudar o banner"** → Logue como Gestor → Gestão → Banners → Criar/Editar banner.
- **"Quero mudar a estrutura do carousel"** → Edite em `root.html`.
- **"Quero mover as estatísticas"** → Altere a classe no `root.html` ou crie regra CSS em `vg24h.css`.
- **"Quero mudar a cor de fundo"** → Edite em `vg24h.css`.

---

## 🔐 Telas de Autenticação — pasta `auth/`

> **Localização:** `backend/templates/portal/auth/`

| Arquivo | URL | O que faz |
|---|---|---|
| `login.html` | `/accounts/login/` | Formulário de e-mail + senha. Links para cadastro e recuperação. |
| `cadastro.html` (8 KB) | `/accounts/cadastro/` | **Wizard de 3 etapas**: Dados Pessoais → Endereço → Segurança. Contém sidebar com dicas, validação JS inline. |
| `recuperar_senha.html` | `/accounts/recuperar-senha/` | Campo de e-mail para enviar link de recuperação. |
| `redefinir_senha.html` | `/accounts/redefinir-senha/<token>/` | Campos nova senha + confirmação. |
| `troca_senha_obrigatoria.html` | `/accounts/trocar-senha/` | Troca de senha no 1º acesso de colaboradores. |

### Perguntas frequentes:

- **"Quero mudar a tela de login"** → Edite `auth/login.html`. A logo da tela de login pode estar usando `static/img/logo.png`.
- **"Quero mudar o cadastro"** → Edite `auth/cadastro.html`. É um wizard com 3 passos controlados por JS (procure por `step` ou `etapa`).
- **"Quero mudar as mensagens de validação"** → Edite tanto no template (mensagens visuais) quanto em `backend/portal/forms.py` (validações Python).

---

## 👤 Telas do Cidadão — pasta `cidadao/`

> **Localização:** `backend/templates/portal/cidadao/`
>
> Acessível apenas com perfil CID.

| Arquivo | URL | O que faz |
|---|---|---|
| `dashboard.html` (8 KB) | `/cidadao/chamados/` | **Tela principal pós-login**. Cards de semáforo (verde/amarelo/vermelho) + lista de chamados com filtros. |
| `chamados_lista.html` | — | Lista simples de chamados (pode ser include). |
| `novo_chamado.html` (13 KB) | `/cidadao/chamados/novo/` | Formulário de abertura: seleção de categoria → serviço → bairro → descrição → foto obrigatória. |
| `chamado_detalhe.html` (11 KB) | `/cidadao/chamados/<id>/` | Detalhe: timeline do histórico, fotos, formulário de observação, botão cancelar, formulário de avaliação (nota + comentário). |
| `notificacoes.html` | `/cidadao/notificacoes/` | Lista de notificações com opção de excluir individualmente. |
| `inicio.html` | — | Tela de início/boas-vindas do cidadão. |
| `chamado_form.html` | — | Template auxiliar para formulários de chamado. |

### Perguntas frequentes:

- **"Quero mudar o semáforo do dashboard"** → Edite `cidadao/dashboard.html`. Procure pelas classes de cor (verde/amarelo/vermelho). As cores ficam em `vg24h.css`.
- **"Quero mudar o formulário de abertura"** → Edite `cidadao/novo_chamado.html`. A seleção de categoria→serviço é dinâmica via JS.
- **"Quero mudar o layout do detalhe"** → Edite `cidadao/chamado_detalhe.html`. A timeline, fotos e avaliação estão tudo nesse arquivo.
- **"Quero adicionar campos ao chamado"** → Além do template, precisa alterar `backend/portal/forms.py` (formulário) e `backend/portal/views_cidadao.py` (view).

---

## 👷 Telas da Equipe (COL/GES) — pasta `equipe/`

> **Localização:** `backend/templates/portal/equipe/`
>
> Acessível com perfil COL ou GES.

| Arquivo | URL | O que faz |
|---|---|---|
| `dashboard.html` (7 KB) | `/equipe/chamados/` | **Dashboard Semáforo**: cards verde/amarelo/vermelho + tabela de chamados com filtros (bairro, status, data). |
| `chamados_lista.html` (3 KB) | — | Lista de chamados tabular (pode ser include). |
| `chamado_detalhe.html` (11 KB) | `/equipe/chamados/<id>/` | Detalhe para equipe: alterar status (dropdown), definir prioridade (0-5), adicionar observação, upload de foto de comprovação. |

### Perguntas frequentes:

- **"Quero mudar os filtros do dashboard"** → Edite `equipe/dashboard.html`. Os dropdowns de bairro e status ficam no topo.
- **"Quero mudar como o status é alterado"** → Edite `equipe/chamado_detalhe.html`. Procure pelo formulário com `acao = "status"`.
- **"Quero alterar as opções de prioridade"** → As opções estão definidas em `backend/portal/views_equipe.py` (variável `PRIORIDADES`), o template apenas renderiza.

---

## ⚙️ Telas de Gestão (GES) — pasta `gestao/`

> **Localização:** `backend/templates/portal/gestao/`
>
> Acessível apenas com perfil GES (Gestor/Administrador).

| Arquivo | URL | O que faz |
|---|---|---|
| `categorias.html` (4 KB) | `/gestao/categorias/` | Lista de categorias + formulário inline para criar nova. |
| `categoria_form.html` (2 KB) | `/gestao/categorias/<id>/editar/` | Edição de uma categoria existente. |
| `servicos.html` (5 KB) | `/gestao/servicos/` | Lista de serviços + formulário inline. Mostra prazos amarelo/vermelho. |
| `servico_form.html` (3 KB) | `/gestao/servicos/<id>/editar/` | Edição de um serviço (inclui campos de prazo). |
| `bairros.html` (4 KB) | `/gestao/bairros/` | Lista de bairros + formulário inline. |
| `bairro_form.html` (2 KB) | `/gestao/bairros/<id>/editar/` | Edição de um bairro. |
| `colaboradores.html` (6 KB) | `/gestao/colaboradores/` | Lista de colaboradores + formulário para criar novo (com senha provisória). Botão toggle ativo/inativo. |
| `banners.html` (2 KB) | `/gestao/banners/` | Lista de banners do carousel da homepage. |
| `banner_form.html` (2 KB) | `/gestao/banners/novo/` ou `<id>/editar/` | Criar/editar banner (título, descrição, imagem, link, ordem). |
| `estatisticas.html` (5 KB) | `/gestao/estatisticas/` | Painel de estatísticas consolidadas (vem da View SQL). |

### Perguntas frequentes:

- **"Quero adicionar um campo ao CRUD de serviço"** → Edite `gestao/servico_form.html` (template) + `backend/portal/forms.py` (`ServicoForm`) + `backend/portal/views_gestao.py`.
- **"Quero mudar os banners da homepage"** → Acesse `/gestao/banners/` logado como GES.
- **"Quero mudar as estatísticas"** → O template é `gestao/estatisticas.html`, mas os dados vêm da View SQL `vw_estatisticas_chamados` (em `database/05_views.sql`).

---

## 🌐 Telas Públicas — pasta `public/`

> **Localização:** `backend/templates/portal/public/`

| Arquivo | URL | O que faz |
|---|---|---|
| `catalogo_servicos.html` (2 KB) | `/servicos/` | Catálogo público de todos os serviços por categoria, com campo de busca. |
| `landing.html` | — | Landing page alternativa. |

---

## 🎨 CSS — Onde alterar cores, fontes, layout

> **Arquivo principal:** `backend/static/portal/css/vg24h.css` (24 KB)
>
> Este é o **único arquivo CSS customizado** que você precisa mexer. Todos os estilos do portal estão aqui.

### O que tem dentro do `vg24h.css`:

| Seção | O que controla | Como encontrar |
|---|---|---|
| **Variáveis CSS** | Cores primárias, secundárias, fontes | Procure por `:root {` no topo do arquivo |
| **Header** | Barra superior, logo, avatar | Procure por `header` ou `.br-header` |
| **Sidebar / Menu** | Navegação lateral | Procure por `sidebar` ou `nav` |
| **Hero** | Seção de destaque na homepage | Procure por `.hero` |
| **Cards** | Cards de serviço, chamados, etc. | Procure por `.card` |
| **Semáforo** | Cores verde/amarelo/vermelho do dashboard | Procure por `semaforo`, `verde`, `amarelo`, `vermelho` |
| **Steps / Wizard** | Passos do cadastro | Procure por `.step` |
| **Stats** | Estatísticas na homepage | Procure por `.stats` |
| **CTA** | Call to action | Procure por `.cta` |
| **Tabelas** | Estilo das tabelas de listagem | Procure por `table` ou `.br-table` |
| **Forms** | Estilos de formulários | Procure por `form` ou `.br-input` |
| **Footer** | Rodapé | Procure por `footer` |

### Perguntas frequentes sobre CSS:

- **"Quero mudar a cor azul principal"** → No `:root {` do `vg24h.css`, procure a variável de cor primária e altere.
- **"Quero mudar a fonte"** → Procure por `font-family` no `vg24h.css`. O projeto usa a fonte **Rawline** do Gov.br.
- **"Quero mudar o semáforo"** → Procure no CSS por `verde`, `amarelo`, `vermelho` e altere as cores.
- **"Quero adicionar um estilo novo"** → Adicione ao final do `vg24h.css`.

### Outros arquivos de estilo:

| Arquivo | O que faz |
|---|---|
| `govbr-layout.css` | Pequenos ajustes de layout para componentes Gov.br |

---

## ⚡ JavaScript — Onde alterar interações

> **Arquivo principal:** `backend/static/portal/js/vg24h.js` (7 KB)

### O que tem dentro do `vg24h.js`:

| Funcionalidade | O que faz |
|---|---|
| **Carousel** | Rotação automática dos banners na homepage |
| **Menu toggle** | Abrir/fechar sidebar em mobile |
| **Form dinâmico** | Ex: selecionar categoria → filtrar serviços no formulário de novo chamado |
| **Validações visuais** | Feedback visual em campos de formulário |

### Outro JS:

| Arquivo | O que faz |
|---|---|
| `govbr-message-close.js` | Fechar alertas/mensagens do Gov.br ao clicar no X |

---

## 🖼️ Imagens

> **Localização:** `backend/static/img/`

| Arquivo | Onde aparece |
|---|---|
| `logo.png` | Header (todas as páginas), tela de login |

Para trocar a logo, substitua o arquivo `logo.png` por outra imagem com o mesmo nome, ou edite o `src` da tag `<img>` no `base.html`.

---

## 📌 Resumo Rápido — "Quero alterar X, vou onde?"

| O que quero alterar | Arquivo para editar |
|---|---|
| **Header (topo)** | `templates/portal/base.html` |
| **Footer (rodapé)** | `templates/portal/base.html` |
| **Menu lateral / Sidebar** | `templates/portal/base.html` |
| **Logo** | `static/img/logo.png` (imagem) + `base.html` (HTML) |
| **Carousel de banners** | Conteúdo: painel GES → Banners. Estrutura: `root.html` |
| **Estatísticas na homepage** | `root.html` (HTML) + `vg24h.css` (posição/cor) |
| **Cores do sistema** | `static/portal/css/vg24h.css` (variáveis `:root`) |
| **Fonte do sistema** | `vg24h.css` (`font-family`) |
| **Cores do semáforo** | `vg24h.css` (classes verde/amarelo/vermelho) |
| **Tela de login** | `templates/portal/auth/login.html` |
| **Tela de cadastro** | `templates/portal/auth/cadastro.html` |
| **Dashboard do cidadão** | `templates/portal/cidadao/dashboard.html` |
| **Abertura de chamado** | `templates/portal/cidadao/novo_chamado.html` |
| **Detalhe do chamado (cidadão)** | `templates/portal/cidadao/chamado_detalhe.html` |
| **Dashboard da equipe** | `templates/portal/equipe/dashboard.html` |
| **Detalhe do chamado (equipe)** | `templates/portal/equipe/chamado_detalhe.html` |
| **CRUD de categorias** | `templates/portal/gestao/categorias.html` + `categoria_form.html` |
| **CRUD de serviços** | `templates/portal/gestao/servicos.html` + `servico_form.html` |
| **CRUD de bairros** | `templates/portal/gestao/bairros.html` + `bairro_form.html` |
| **CRUD de colaboradores** | `templates/portal/gestao/colaboradores.html` |
| **CRUD de banners** | `templates/portal/gestao/banners.html` + `banner_form.html` |
| **Estatísticas do gestor** | `templates/portal/gestao/estatisticas.html` |
| **Catálogo público** | `templates/portal/public/catalogo_servicos.html` |
| **JS do carousel/menus** | `static/portal/js/vg24h.js` |
| **Validações de formulário** | Template (visual) + `backend/portal/forms.py` (regras) |
| **Adicionar campo a uma tela** | Template + `forms.py` + `views_*.py` correspondente |

---

## 🎯 FAQ de Apresentação (Perguntas Frequentes sobre Interface)

Se a professora fizer perguntas específicas sobre a localização de elementos visuais na hora da apresentação, use este guia rápido de respostas:

### 1. Onde eu coloco a imagem do "Banner" do carrossel?
- **Pelo sistema (dinâmico):** Um usuário logado com perfil de Gestor (GES) deve ir no menu **Gestão > Banners** e fazer o upload da imagem por lá. As imagens não ficam "chumbadas" no código.
- **Estrutura no código:** Se ela perguntar onde fica o código HTML que exibe esse carrossel, a resposta é no arquivo `backend/templates/portal/root.html`. O arquivo de JavaScript responsável por fazer as imagens girarem é o `backend/static/portal/js/vg24h.js`.

### 2. O projeto tem cookies? Onde eles estão e como altero a mensagem?
- **Localização:** `backend/templates/portal/base.html`
- **Resposta:** Sim, o projeto possui um aviso de consentimento de Cookies (regra da LGPD). Como essa barra precisa aparecer em **todas** as telas do portal, ela foi colocada no arquivo mestre `base.html`, geralmente próximo ao código do rodapé (`<footer>`). Para alterar o texto da mensagem, basta buscar por `cookie` dentro do `base.html`.

### 3. Se eu quiser mudar a logo do sistema, onde fica?
- **Imagem:** O arquivo físico da imagem fica em `backend/static/img/logo.png`. Para trocar a logo de fato, basta substituir essa imagem por outra de mesmo nome.
- **Código:** O HTML que puxa essa logo para aparecer no topo do site está no `<header>` dentro de `backend/templates/portal/base.html`. Alterando no `base.html`, a logo muda no site inteiro. A tela de login tem um layout próprio, mas puxa essa mesma imagem em `auth/login.html`.

### 4. Se eu quiser alterar o "Breadcrumb" (ex: Início > Meus Chamados) dentro do chamado, onde devo ir?
- **Resposta:** O breadcrumb (rastro de navegação) não é global; ele é construído especificamente para cada página. Para alterar o breadcrumb de dentro de um chamado, você deve editar o HTML da própria tela do chamado:
  - Visão do Cidadão: `backend/templates/portal/cidadao/chamado_detalhe.html`
  - Visão da Equipe/Gestão: `backend/templates/portal/equipe/chamado_detalhe.html`
- Procure pelas tags com a classe `.br-breadcrumb` logo no topo do código desses arquivos.

### 5. Onde ficam os "Modais" (popups) do projeto? (Ex: Modal de excluir, de cancelar chamado)
- **Resposta:** Os modais (que usam a classe `.br-modal` do padrão Gov.br) não ficam em arquivos separados. Eles ficam embutidos no próprio arquivo HTML da página onde são chamados, geralmente no final do código, e ficam ocultos até o usuário clicar no botão de ação.
- **Exemplo:** O popup para o Gestor excluir uma categoria fica dentro de `backend/templates/portal/gestao/categorias.html`. O modal para o Cidadão cancelar um chamado fica no fim de `backend/templates/portal/cidadao/chamado_detalhe.html`.

---

## 🧠 Dicas Importantes (Aprofundado com Exemplos para Apresentação)

### 1. Herança de Templates (O que está no `base.html` vs. O que está nas páginas)
Toda página do sistema começa com a linha `{% extends "portal/base.html" %}`. Isso significa que a tela inteira é estruturada pelo `base.html`, e a página atual só "preenche" o miolo.
- **Exemplos do que APARECE em TODAS as páginas (e que, portanto, fica no `base.html`)**:
  - O **Header escuro no topo** (Logo VG 24H, link "Entrar", menu de acessibilidade alto contraste e avatar do usuário).
  - O **Menu Lateral (Sidebar)** (onde os usuários clicam em "Meus Chamados", "Gestão", "Sair").
  - O **Rodapé (Footer)** (endereço da prefeitura, telefones, ouvidoria, redes sociais, barra de Cookies e selo do Governo).
- **Exemplos do que NÃO aparece em todas as páginas (e que fica no arquivo específico da página)**:
  - O "miolo" central em si (tabelas, gráficos, listas, formulários).
  - O **Breadcrumb** (ex: *Início > Meus Chamados*). Como o caminho e os links mudam de página para página, ele é colocado no topo do código de cada página específica (como `dashboard.html` ou `chamado_detalhe.html`), e nunca no `base.html`.
  - O Carrossel e Banners rotativos (existem apenas no `root.html`).

### 2. O conceito de Blocos (Blocks)
Cada página específica "injeta" seu conteúdo no `base.html` através de blocos definidos.
- **`{% block content %}`**: É o bloco principal. É aqui que o HTML da tabela de chamados ou de um formulário daquela tela entra.
- **Exemplo de JS e CSS isolado (`{% block extra_js %}`)**: Se a professora perguntar como o sistema gerencia performance, você pode explicar que o JavaScript do carrossel ou gráficos não é carregado no sistema inteiro. Em vez de deixar todas as páginas pesadas colocando tudo no `base.html`, a página inicial (`root.html`) usa o `{% block extra_js %}` para carregar aquele script *apenas e somente nela*.

### 3. Contexto Dinâmico (Como a tela sabe quem é o usuário?)
Se a professora perguntar *"Como você exibe o nome do usuário ali no canto ou esconde o botão de Gestão para quem não é gestor?"*:
- O backend Python injeta variáveis silenciosamente em **todas** as telas do sistema simultaneamente (via `backend/portal/context_processors.py`).
- **Exemplos práticos no HTML:**
  - **Para exibir o nome:** Qualquer template do projeto só precisa chamar a tag `{{ nav_user.nome_completo }}`.
  - **Para esconder menus restritos:** No `base.html` usamos um IF: `{% if nav_perfil == "GES" %}` mostra o botão "Gestão" `{% endif %}`. Se for "CID", o HTML desse botão sequer é renderizado para o cidadão.
  - **Notificações:** O sininho vermelho no menu do cidadão usa a variável global `{{ notif_count }}` para mostrar quantas mensagens não lidas existem, sem que as Views do projeto precisem ficar recalculando isso o tempo todo.

### 4. Mensagens do Sistema (Toasts/Alerts)
Se a professora perguntar *"De onde saem essas barrinhas verdes e vermelhas de alerta no topo?"*:
- **A Lógica:** Quando uma ação dá certo (ex: criar serviço) ou errado, o backend diz via Python: `messages.success(request, "Serviço criado!")` e redireciona o usuário.
- **O Visual:** Como é o `base.html` que desenha o topo de *todas* as telas, ele tem um pedaço de código programado para ler se existe alguma mensagem pendente e desenhá-la. Assim a mensagem exibe lindamente, independente de para qual tela o usuário acabou sendo redirecionado.

### 5. Estilização e Componentes Gov.br
Se a professora quiser saber *"Vocês fizeram esse CSS todo do zero?"*:
- **A Resposta:** O projeto adota a biblioteca oficial de design do governo (https://www.gov.br/ds/). A maior parte da beleza e interações já vem pronta através de classes CSS oficiais.
- **Exemplo Prático:** Para criar um botão azul, não escrevemos CSS novo. Simplesmente escrevemos no HTML `<button class="br-button primary">`. Para inputs textuais, usamos `<div class="br-input">`. 
- O arquivo que nós criamos (`vg24h.css`) existe apenas para customizar a **cor principal** para azul escuro (através de variáveis `:root` e de tema), alinhar componentes (margins/paddings) e aplicar cores semânticas como o verde/amarelo/vermelho do semáforo, que não são nativas do Gov.br.
