# Guia de Frontend e Interface — Portal VG 24H

Este guia tem como objetivo explicar a estrutura da interface do usuário (HTML, CSS, JS) e responder às perguntas mais comuns sobre onde alterar partes específicas da página.

## 📂 Onde estão os arquivos de Frontend?

O Django usa uma arquitetura de templates e arquivos estáticos mantidos em diretórios específicos dentro da pasta `backend`:

- **HTML (Templates)**: Todos os arquivos `.html` estão dentro de `backend/templates/portal/`.
- **CSS (Estilos)**: `backend/static/portal/css/vg24h.css`
- **JS (Lógica do cliente)**: `backend/static/portal/js/vg24h.js`
- **Imagens (Imagens fixas/Logo)**: `backend/static/img/`

> **Nota importante sobre herança**:
> Quase todas as páginas do site herdam do arquivo `backend/templates/portal/base.html`. Nele estão definidos o **cabeçalho (Header)** e o **rodapé (Footer)** globais, para que você não precise alterá-los em toda página.

---

## 🛠️ Onde eu vou para alterar...

### 1. A Logo do Sistema

- **Como alterar a imagem:** Substitua a imagem física localizada em `backend/static/img/logo.png`.
- **Como alterar o comportamento:** Para alterar onde e como a logo aparece no cabeçalho ou no painel de login, edite o código HTML dela diretamente em `backend/templates/portal/base.html` (para o sistema todo) ou `backend/templates/portal/auth/login.html` (para a página de login).

### 2. O Banner Principal (Página Inicial)

Existem dois elementos de destaque que chamamos de banner:

- **A faixa azul no topo com os botões**: Se quiser alterar botões como "Entrar" ou links rápidos, o código fica dentro do `backend/templates/portal/base.html`.
- **O grande Carrossel (Imagens Rotativas)**: Ele é **dinâmico** e pode ser alterado direto no painel administrativo "Gestão", logando com um usuário gestor e indo na guia **Banners**.
- Se você quiser alterar a área de estrutura dele no código, o carrossel fica desenhado no arquivo `backend/templates/portal/root.html`.

### 3. O Footer da Página Inicial

- Como a página inicial (`root.html`) herda dados globais, o **Rodapé Geral do Sistema**, onde estão descritos endereço, redes sociais e links de ouvidoria, fica todo contido e gerenciado em **`backend/templates/portal/base.html`**. O que você alterar lá, afetará a página inicial.

### 4. O Footer da Página de Login

- A página de login (`auth/login.html`) também usa as tags `{% extends "portal/base.html" %}`.
- Logo, se você altera o footer no arquivo **`backend/templates/portal/base.html`**, isso altera e padroniza para o sistema **inteiro**, tanto para a página inicial, quanto para a do Cidadão e para a do Login.

### 5. Alterar a Área de Estatísticas (Chamados Resolvidos / Bairros Atendidos)

> _"Se eu quiser colocar mais para a direita essa seção, para onde eu vou?"_

- **Onde fica essa seção no HTML**: Todas as tags que constroem os números ("0 Chamados resolvidos", etc) estão localizadas em **`backend/templates/portal/root.html`** perto da linha _220_ usando a classe `.stats-section` ou `.stats-grid`.
- **Como colocar mais para a direita**: Você pode alterar de duas maneiras:
  1. No próprio **`backend/templates/portal/root.html`**, procurar pela classe container das estatísticas e adicionar uma classe de alinhamento Bootstrap como `justify-content-end` ou um estilo online ex: `style="display: flex; justify-content: flex-end;"`.
  2. No arquivo **`backend/static/portal/css/vg24h.css`**, criar regras para as classes da estatística, utilizando por exemplo `margin-left: auto;` ou mudando paddings e layouts de grid.

---

## 📌 Resumo Prático de Arquivos Essenciais

| Parte Visual              | Arquivo para Editar                                       |
| ------------------------- | --------------------------------------------------------- |
| Cabeçalho / Footer Global | `templates/portal/base.html`                              |
| Estrutura Página Inicial  | `templates/portal/root.html`                              |
| Tela de Cadastro/Login    | `templates/portal/auth/login.html`                        |
| Tela Pós-Login do Perfil  | `templates/portal/cidadao/` ou `templates/portal/equipe/` |
| Tema Azul/GovBr de Cores  | `static/portal/css/vg24h.css`                             |
