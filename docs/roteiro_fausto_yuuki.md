# Roteiro de Apresentação — Fausto Yuuki

## 🎯 Responsabilidade: Módulo Colaborador, Módulo Gestor e Frontend (Gov.br DS)

Fausto é responsável pelos **módulos administrativos** (Colaborador e Gestor) e pela **arquitetura visual** do portal — template base, CSS, JS e conformidade com o Design System Gov.br.

---

## 📌 O que você apresenta

### 1. Frontend e Design System Gov.br (Plano §4 — Interface visual)

- **Template Base** — `base.html` (17 KB):
  - Header, sidebar dinâmico por perfil (CID/COL/GES via `nav_perfil`), footer, skip links, cookie bar
  - Bloco `{% block content %}` que todas as páginas herdam

- **CSS customizado** — `vg24h.css` (24 KB):
  - Variáveis CSS, tokens Gov.br, estilos de dashboard, semáforo, tabelas, forms

- **JavaScript** — `vg24h.js` (7 KB):
  - Carousel, interações de menu, formulários dinâmicos

- **Conformidade Gov.br**: fonte Rawline, componentes `br-button`, `br-input`, `br-table`, `br-tag`

### 2. Módulo do Colaborador — COL (Plano §3.1 — Módulo do Colaborador)

> **Mudança arquitetural importante**: O status do chamado **NÃO é um campo direto** em `chamado`. O status atual vem do **último registro de `historico_chamado`** via `ch.status_atual` / `ch.sigla_status`. Mudar status = **inserir novo registro em `historico_chamado`**.

**Siglas de status:** `AB` = Aberto, `EA` = Em Análise, `EE` = Em Execução, `CO` = Concluído, `CA` = Cancelado

- **Dashboard Semáforo + Lista** — função `equipe_chamados_lista` em `views_equipe.py`:
  - Carrega TODOS os chamados com `prefetch_related("historicos__id_status")`
  - Semáforo: verde/amarelo/vermelho via `cor_semaforo()` (compara `prazo_amarelo_dias` / `prazo_vermelho_dias`)
  - Filtro de status usa `Subquery` no último `historico_chamado`
  - Renderiza `equipe/dashboard.html`

- **Detalhe do Chamado** — função `equipe_chamado_detalhe`:
  - Status via `sigla_status(ch)` → property `ch.sigla_status`
  - Bloqueio: COL com CO/CA → `pode_status = False`; GES sempre pode
  - **3 ações POST** (campo `acao`):
    - `"status"` → **insere `HistoricoChamado` com novo status** + salva resolução e prioridade no chamado
    - `"obs"` → insere em `historico_chamado` com `id_status=ch.status_atual`
    - `"foto"` → upload via `salvar_foto_upload()` → cria `FotoChamado`
  - Renderiza `equipe/chamado_detalhe.html`

### 3. Módulo do Gestor — GES (Plano §3.1 — Módulo do Administrador)

> `@perfis("GES")` — exclusivo do Gestor. O perfil `GES` no código = "Administrador" no Plano.

- **Categorias** — `gestao_categorias`, `gestao_categoria_edit`: lista + CRUD via `CategoriaForm`
- **Serviços** — `gestao_servicos`, `gestao_servico_edit`, `gestao_servico_desativar`: CRUD via `ServicoForm` (com prazos amarelo/vermelho)
- **Bairros** — `gestao_bairros`, `gestao_bairro_edit`, `gestao_bairro_desativar`: CRUD via `BairroForm`
- **Colaboradores** — `gestao_colaboradores`, `gestao_colaborador_toggle`: cria na tabela `servidor` com `perfil='COL'`, `senha_temporaria="1"`
- **Banners** — `gestao_banners`, `gestao_banner_novo`, `gestao_banner_editar`, `gestao_banner_excluir`: CRUD de `banner_publicacao`
- **Estatísticas** — `gestao_estatisticas`: executa `SELECT * FROM vw_estatisticas_chamados` (View SQL com JOIN LATERAL no último histórico)

---

## 📁 Arquivos que você DEVE saber explicar

### Python (Backend)

| Arquivo | Caminho | Conteúdo |
|---|---|---|
| `views_equipe.py` | `backend/portal/views_equipe.py` | Dashboard semáforo, detalhe (COL + GES) |
| `views_gestao.py` | `backend/portal/views_gestao.py` | CRUD categorias, serviços, bairros, colaboradores, banners, estatísticas |
| `forms.py` | `backend/portal/forms.py` | `EquipeStatusForm`, `CategoriaForm`, `ServicoForm`, etc. |
| `urls.py` | `backend/portal/urls.py` | Rotas `equipe/*` e `gestao/*` |

### Templates — Colaborador (COL)

| Arquivo | Caminho |
|---|---|
| `dashboard.html` | `backend/templates/portal/equipe/dashboard.html` |
| `chamados_lista.html` | `backend/templates/portal/equipe/chamados_lista.html` |
| `chamado_detalhe.html` | `backend/templates/portal/equipe/chamado_detalhe.html` |

### Templates — Gestor (GES)

| Arquivo | Caminho |
|---|---|
| `categorias.html` + `categoria_form.html` | `backend/templates/portal/gestao/` |
| `servicos.html` + `servico_form.html` | `backend/templates/portal/gestao/` |
| `bairros.html` + `bairro_form.html` | `backend/templates/portal/gestao/` |
| `colaboradores.html` | `backend/templates/portal/gestao/` |
| `banners.html` + `banner_form.html` | `backend/templates/portal/gestao/` |
| `estatisticas.html` | `backend/templates/portal/gestao/` |

### Frontend

| Arquivo | Caminho |
|---|---|
| `base.html` | `backend/templates/portal/base.html` |
| `vg24h.css` | `backend/static/portal/css/vg24h.css` |
| `vg24h.js` | `backend/static/portal/js/vg24h.js` |

### Suas rotas em `urls.py`

| Rota | View | Name |
|---|---|---|
| `equipe/chamados/` | `equipe_chamados_lista` | `equipe_chamados` |
| `equipe/chamados/<pk>/` | `equipe_chamado_detalhe` | `equipe_chamado` |
| `gestao/estatisticas/` | `gestao_estatisticas` | `gestao_estatisticas` |
| `gestao/categorias/` | `gestao_categorias` | `gestao_categorias` |
| `gestao/categorias/<pk>/editar/` | `gestao_categoria_edit` | `gestao_categoria_editar` |
| `gestao/servicos/` | `gestao_servicos` | `gestao_servicos` |
| `gestao/servicos/<pk>/editar/` | `gestao_servico_edit` | `gestao_servico_editar` |
| `gestao/servicos/<pk>/desativar/` | `gestao_servico_desativar` | `gestao_servico_desativar` |
| `gestao/bairros/` | `gestao_bairros` | `gestao_bairros` |
| `gestao/bairros/<pk>/editar/` | `gestao_bairro_edit` | `gestao_bairro_editar` |
| `gestao/bairros/<pk>/desativar/` | `gestao_bairro_desativar` | `gestao_bairro_desativar` |
| `gestao/colaboradores/` | `gestao_colaboradores` | `gestao_colaboradores` |
| `gestao/colaboradores/<pk>/toggle/` | `gestao_colaborador_toggle` | `gestao_colaborador_toggle` |
| `gestao/banners/` | `gestao_banners` | `gestao_banners` |
| `gestao/banners/novo/` | `gestao_banner_novo` | `gestao_banner_novo` |
| `gestao/banners/<pk>/editar/` | `gestao_banner_editar` | `gestao_banner_editar` |
| `gestao/banners/<pk>/excluir/` | `gestao_banner_excluir` | `gestao_banner_excluir` |

---

## 🗣️ Pontos-chave para a apresentação

1. **Mostre `base.html`** — herança de templates, menu dinâmico por perfil
2. **Explique a mudança arquitetural**: status não é campo direto, vem do último `historico_chamado`. Mudar status = INSERT em `historico_chamado`
3. **Painel do Gestor ao vivo**: crie colaborador, serviço com prazos, banner
4. **Dashboard Semáforo**: explique verde/amarelo/vermelho e `cor_semaforo()`
5. **Altere status de um chamado**: insere em historico → Trigger 2B gera notificação + `dt_conclusao`
6. **Tente fechar sem resolução**: `EquipeStatusForm.clean()` impede
7. **COL vs GES**: COL bloqueado em CO/CA, GES livre
8. **Controle de acesso**: COL acessando `/gestao/` → "Sem permissão"
9. **Responsividade** e **CSS** (`vg24h.css`)

---

## 📚 Mapeamento por Etapa da Disciplina

| Etapa | O que Fausto apresenta |
|---|---|
| **Etapa 1** (Plano de Trabalho) | Seções 3.1 (Módulo COL e GES), 4 (Restrições), 7 (Ferramentas) |
| **Etapa 2** (Modelagem + Criação BD) | Entidades `secretaria`, `servidor`, `categoria_servico`, `servico`, `bairro`, `historico_chamado` |
| **Etapa 3** (Layout das telas) | Print de todas as telas de equipe e gestão |
| **Etapa 4** (Conexão + Login) | `base.html` como template master + Gov.br DS |
| **Etapa 5** (Cadastro piloto) | CRUD de Categorias: INSERT, SELECT, UPDATE, DELETE lógico |
| **Etapa 6** (Demais telas) | Todas as telas listadas |

### ⚠️ Ponto Crítico — Etapa 6

> **Telas desenvolvidas por Fausto Yuuki:**
>
> 1. Template Base (`base.html`) + CSS (`vg24h.css`) + JS (`vg24h.js`)
> 2. Dashboard Semáforo (`equipe/dashboard.html`)
> 3. Lista Chamados Equipe (`equipe/chamados_lista.html`)
> 4. Detalhe Chamado Equipe (`equipe/chamado_detalhe.html`)
> 5. Gestão de Colaboradores (`gestao/colaboradores.html`)
> 6. Gestão de Categorias (`gestao/categorias.html` + `categoria_form.html`)
> 7. Gestão de Serviços (`gestao/servicos.html` + `servico_form.html`)
> 8. Gestão de Bairros (`gestao/bairros.html` + `bairro_form.html`)
> 9. Gestão de Banners (`gestao/banners.html` + `banner_form.html`)
> 10. Painel de Estatísticas (`gestao/estatisticas.html`)

### 📄 Checklist para o Seminário Final

- [ ] Print do `views_equipe.py` — dashboard e detalhe
- [ ] Print do `views_gestao.py` — CRUDs
- [ ] Print do `base.html` e `vg24h.css`
- [ ] Print do Dashboard Semáforo (cards verde/amarelo/vermelho)
- [ ] Print do CRUD de Categorias completo
- [ ] Print do CRUD de Serviços com prazos
- [ ] Print da criação de Colaborador
- [ ] Print do Painel de Estatísticas
- [ ] Print dos Banners + carousel
- [ ] Demonstração ao vivo: login GES → CRUD → alterar status → dashboard
