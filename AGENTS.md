## 6. Gov.br Design System Gatekeeper (Always Active)

Block any frontend change that lacks explicit backing from the GOV/ reference directory. No reference, no change.

**Applies to:** HTML in `backend/templates/`, CSS/SCSS in `backend/static/`, component markup/classes/JS, user-facing text, layout/spacing/color/typography/icons.

### Mandatory Gatekeeper Workflow

Every frontend change passes through these gates **in order**.

**Gate 1 — Identify Domains:**
- Components: button, input, modal, table, header, footer, menu, card, etc.
- Visual Foundations: colors, spacing, typography, elevation, grid, icons, motion, surface
- Patterns: form, navigation, empty states, onboarding, etc.
- UX Writing: any text change → always triggers `GOV/padroes/writing/`
- Template: layout changes → `GOV/templates/base/`
- JavaScript: component instantiation → `GOV/components/<name>/<name>-dev.md`

**Gate 2 — Search GOV/ References:**
For each domain, search the corresponding GOV/ path. Use `GOV-MAP.md` (project root) to locate files. Read the `-dev.md` file for developer reference. Read `.md` files for conceptual overview. Read `visao-geral.html` for visual reference. Read `.scss` files for styling reference.

**Gate 3 — Certainty Check:**
- Exact HTML structure? (classes, nesting, attributes, aria roles)
- CSS utility classes for colors/spacing/typography/surface?
- JS instantiation pattern? (`core.BRComponentName(...)`)
- UX writing rules for every text string?
- State handling? (success, danger, warning, info, disabled, loading)

If **NO** to any → **block the change**.

**Gate 4 — Reference Resolution:**

| Scenario | Action |
|---|---|
| Reference found and clear | Implement exactly per reference |
| Reference found but ambiguous | Ask user before proceeding |
| Reference NOT found | **BLOCK**. Report: what's missing, paths searched, recommendation |
| Text change, no UX Writing reference read | **BLOCK**. Must read `GOV/padroes/writing/` first |

**Gate 5 — Implement or Report:**
If all gates pass: implement exactly matching reference structure. No invented classes, no custom CSS when GOV utility exists.
If blocked:
```
[GOV-DS GATEKEEPER] Modification blocked.
Reason: [what reference was missing]
Searched in: [GOV/ paths searched]
Recommendation: [closest DS pattern + suggestion]
```

### UX Writing Rule (Always Active)

Any text change requires reading:
- `GOV/padroes/writing/principios-writing.md` — tone, clarity, concision, accessibility
- `GOV/padroes/writing/microcopy.md` — per-element text rules

Rules: labels max 2 words (3 if unavoidable), sentence case. Buttons: all caps, max 2 words. Actions: short, objective verbs. Messages: simple, direct, no jargon. Consistency: same term for same concept everywhere.

### Key GOV/ Structure

**Components (34 total — see GOV-MAP.md for full list)** — generic reference:

| Concern | Path |
|---|---|
| Component dev reference | `GOV/components/<name>/<name>-dev.md` |
| Component overview | `GOV/components/<name>/<name>.md` |
| Component SCSS | `GOV/src/components/<name>/_<name>.scss` |
| Component visual overview | `GOV/components/visao-geral/visao-geral.html` |

**Visual Foundations (Fundamentos Visuais):**

| Foundation | Dev Reference |
|---|---|
| Colors | `GOV/fundamentos-visuais/cores/cores-dev.md` |
| Typography | `GOV/fundamentos-visuais/tipografia/tipografia-dev.md` |
| Spacing | `GOV/fundamentos-visuais/espacamento/espacamento-dev.md` |
| Grid | `GOV/fundamentos-visuais/grid/grid-dev.md` |
| Elevation | `GOV/fundamentos-visuais/elevacao/elevacao-dev.md` |
| Icons | `GOV/fundamentos-visuais/iconografia/iconografia-dev.md` |
| Motion | `GOV/fundamentos-visuais/movimento/movimento-dev.md` |
| Surface | `GOV/fundamentos-visuais/superficie/superficie-dev.md` |

**Design Patterns (Padrões de Design):**

| Pattern | Path |
|---|---|
| Form | `GOV/padroes/design/formulario.md` |
| Navigation | `GOV/padroes/design/navegacao.md` |
| Help & Communication | `GOV/padroes/design/ajuda-comunicacao.md` |
| Density | `GOV/padroes/design/densidade.md` |
| Content Overflow | `GOV/padroes/design/contentoverflow.md` |
| Dropdown | `GOV/padroes/design/dropdown.md` |
| Empty States | `GOV/padroes/design/emptystates.md` |
| Graphs | `GOV/padroes/design/grafico.md` |
| Onboarding | `GOV/padroes/design/onboarding.md` |
| Collapse | `GOV/padroes/design/collapse.md` |

**UX Writing:**

| Resource | Path |
|---|---|
| Principles | `GOV/padroes/writing/principios-writing.md` |
| Microcopy Rules | `GOV/padroes/writing/microcopy.md` |

**Templates:**

| Template | Dev Reference |
|---|---|
| Base layout | `GOV/templates/base/base-dev.md` |
| Error pages | `GOV/templates/erro/erro-dev.md` |

**Engineering Guides:**

| Guide | Path |
|---|---|
| Component Construction | `GOV/construcao-de-componentes/construcao-de-componentes.md` |
| JavaScript Coding | `GOV/codificacao-javascript/codificacao-javascript.md` |
| Sass Coding | `GOV/codificacao-sass/codificacao-sass.md` |
| Using Sass | `GOV/utilizando-sass/utilizando-sass.md` |
| Installation | `GOV/instalacao/instalacao.md` |
| Lite Version | `GOV/versao-lite/versao-lite.md` |
| Vendors | `GOV/vendors/vendors.md` |
| PurgeCSS | `GOV/purgecss/purgecss.md` |

**CSS Utilities (Utilitários):**

| Category | Path |
|---|---|
| Colors | `GOV/utilitarios/css/cores/` |
| Typography | `GOV/utilitarios/css/tipografia/` |
| Spacing | `GOV/utilitarios/css/espacamento/` |
| Grid | `GOV/utilitarios/css/grid/` |
| Flexbox | `GOV/utilitarios/css/flexbox/` |
| Display | `GOV/utilitarios/css/display/` |
| Elevation | `GOV/utilitarios/css/elevacao/` |
| Borders | `GOV/utilitarios/css/bordas/` |
| Rounding | `GOV/utilitarios/css/arredondamento/` |
| Overflow | `GOV/utilitarios/css/overflow/` |
| Motion | `GOV/utilitarios/css/movimento/` |
| Text | `GOV/utilitarios/css/textos/` |

**Core SCSS Architecture:**

| File | Purpose |
|---|---|
| `GOV/src/core.scss` | Main entry point |
| `GOV/src/partial/scss/_configs.scss` | All design tokens |
| `GOV/src/partial/scss/_base.scss` | Reset & base styles |
| `GOV/src/partial/scss/_components.scss` | All component styles |
| `GOV/src/partial/scss/_templates.scss` | Template styles |
| `GOV/src/partial/scss/_utilities.scss` | Utility classes |
| `GOV/src/partial/scss/_mixins.scss` | Sass mixins |
| `GOV/src/partial/scss/_functions.scss` | Sass functions |

Full map: `GOV-MAP.md` (project root)

### Anti-Patterns (Never Do)

- Never add `style=""` inline — use GOV utility classes
- Never use custom color hex — use `bg-*`, `text-*`, `border-*` GOV classes
- Never use arbitrary font-size/weight — use `text-*`, `text-weight-*`, `h1`-`h6` GOV classes
- Never use raw `margin`/`padding` in custom CSS — use `m-*`, `p-*` GOV spacing classes
- Never guess a component's HTML structure — always read the `-dev.md` first
- Never instantiate JS components without documented pattern (`core.BRComponentName(...)`)
- Never write button/input/label text without checking UX Writing rules

## 7. Database: Mandatory Advanced Features

The project MUST have advanced PostgreSQL features in the database. Minimum required:

- **1 trigger** (e.g.: audit, automatic timestamp updates, validation)
- **1 view** (e.g.: report, consolidation, query abstraction layer)
- **1 stored procedure / function** (e.g.: business rule in DB, calculation, atomic insert)

Do not remove or disable these features without replacing them with equivalent code that provides the same consistency guarantees.

## 8. Database Portability

The project currently uses **Neon** (managed cloud PostgreSQL) as the database, but MUST be compatible with future migration to the city hall's database (on-premise or other provider).

### Rules

- Do not use Neon-exclusive features (extensions, functions, proprietary APIs). Check before adopting any extension.
- All SQL queries must be standard PostgreSQL (portable across versions 13+).
- If a specific extension is necessary (e.g.: pgcrypto, pg_trgm), document it in-code and in `docs/learnings/dependencias-banco.md`.
- Keep connection config separate from code (via environment variables). The `DATABASE_URL` schema must be standard PostgreSQL (`postgresql://user:pass@host:port/db`).
- Avoid functions/extension-only features in migration SQL when a standard alternative is available.

## 9. Commit and Authorship Rules

Commits MUST be separated by domain. Each commit uses the author matching the change type.

| Domain | Author | Email |
|---|---|---|
| Frontend (HTML templates, CSS, JS, SCSS, ui) | YuukiFST | faustoyuuki@gmail.com |
| Backend (Python, Django, views, services, models) | bruno-d | brunoodfonteles@gmail.com |
| Database (SQL, migrations, DB models, schema) | RafaelPMarquesP | rafpereiramar@gmail.com |

### Rules

- Never mix frontend + backend + DB in the same commit. Atomic commits per domain.
- Before each commit, configure the author locally:
  ```
  git -c user.name="Name" -c user.email="email" commit -m "tipo(escopo): mensagem"
  ```
  Or via `git config user.name` / `user.email` in the repository before committing.
- The commit message must reflect only the commit's domain.
- Commit messages must be in PT-BR following conventional commits format.
- If the work involves multiple domains, create separate commits for each, starting with dependencies (DB → Backend → Frontend).

## 10. Code Documentation for Academic Purposes

All new code (Python, HTML, CSS, JS, SQL) MUST contain explanatory comments line by line or block by block, so that any team member can understand and explain the code during the project presentation.

### General Rules

- Document every function/method: purpose, parameters, return value, step-by-step logic.
- Document HTML templates: purpose of each block/section, data flow, conditionals.
- Document SQL: what each query/trigger/view/procedure does, tables involved, business rules.
- Comments in PT-BR, didactic style (classroom language).
- Detail level: enough for a teammate to read and explain without doubts.
- Avoid obvious comments that merely repeat the code — focus on the "why" and context.

### Frontend-Specific Rule (GOV/DS)

- Comment CSS/SCSS: which component/element each rule styles and why.
- **Whenever the GOV Design System justifies the decision, include it in the comment.**
  Example: if a GOV class exists for accessibility reasons, mention it.
  If GOV recommends a pattern for usability, performance, or visual consistency,
  make that explicit in the comment.
- This ensures that during the presentation the team member can say: "we used X because
  the Padrao Digital de Governo defines Y, and that guarantees Z."
