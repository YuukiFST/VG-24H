# CLAUDE.md

Behavioral guidelines to reduce LLM coding mistakes. Merge with project instructions.

**Tradeoff:** Bias caution over speed. Trivial tasks → use judgment.

## 0. Output Style

- Thorough reasoning, concise output.
- No sycophantic openers or closing fluff. No emojis. No em-dashes.
- Read existing files before writing. Don't re-read unless changed.
- Skip files >100KB unless required.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

- State assumptions explicitly. Uncertain → ask.
- Multiple interpretations → present them, don't pick silently.
- Simpler approach exists → say so. Push back when warranted.
- Unclear → stop, name what's confusing, ask.
- Never guess APIs, versions, flags, commit SHAs, package names. Verify via code/docs before asserting.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility"/"configurability" unrequested.
- No error handling for impossible scenarios.
- 200 lines that could be 50 → rewrite.

Test: "Would a senior engineer say this is overcomplicated?" Yes → simplify.

## 3. Surgical Changes

**Touch only what you must. Clean only your own mess.**

Editing existing code:
- Don't "improve" adjacent code, comments, formatting.
- Don't refactor what isn't broken.
- Match existing style.
- Unrelated dead code → mention, don't delete.

Orphans from your changes:
- Remove imports/vars/fns YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

Test: every changed line traces directly to user request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Convert tasks → verifiable goals:
- "Add validation" → "Write tests for invalid inputs, make them pass"
- "Fix the bug" → "Write test that reproduces it, make it pass"
- "Refactor X" → "Ensure tests pass before and after"

Multi-step → brief plan:

```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
```

Strong criteria → loop independently. Weak ("make it work") → constant clarification.

---

**Working if:** fewer unnecessary diff lines, fewer overcomplication rewrites, clarifying questions before mistakes.

## 5. Project Doc Structure (Token-Efficient)

Source: nadimtuhin/claude-token-optimizer. Target: ≤800 tokens loaded at startup, rest lazy.

**Layout per project:**
```
CLAUDE.md / AGENTS.md       # entry point only — ≤800 tokens
.claudeignore               # excludes archive/legacy docs
.claude/
  COMMON_MISTAKES.md        # top 5 critical bugs only
  QUICK_START.md            # daily commands
  ARCHITECTURE_MAP.md       # system layout
  completions/              # done tasks (0 tokens until read)
  sessions/                 # historical work (0 tokens)
docs/
  INDEX.md
  learnings/                # topic files, loaded on request
  archive/                  # deprecated (ignored)
```

**Rules:**
- Entry file references topic files by path; agent loads on demand.
- `.claudeignore` MUST exclude `archive/`, old wikis, generated docs.
- `COMMON_MISTAKES.md` — only log bugs that took >1h to debug. Keep ≤5 entries; prune oldest.
- Never inline content from topic files into entry. Link instead.
- Initial context budget: ~1300 tokens total across entry + 3 essentials.

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
[GOV-DS GATEKEEPER] Modificação bloqueada.
Motivo: [what reference was missing]
Buscado em: [GOV/ paths searched]
Recomendação: [closest DS pattern + suggestion]
```

### UX Writing Rule (Always Active)

Any text change requires reading:
- `GOV/padroes/writing/principios-writing.md` — tone, clarity, concision, accessibility
- `GOV/padroes/writing/microcopy.md` — per-element text rules

Rules: labels max 2 words (3 if unavoidable), sentence case. Buttons: all caps, max 2 words. Actions: short, objective verbs. Messages: simple, direct, no jargon. Consistency: same term for same concept everywhere.

### Key GOV/ Structure

| Concern | Path |
|---|---|
| Any component | `GOV/components/<name>/<name>-dev.md` |
| Component overview | `GOV/components/<name>/<name>.md` |
| Component SCSS | `GOV/src/components/<name>/_<name>.scss` |
| Colors | `GOV/fundamentos-visuais/cores/cores-dev.md` |
| Typography | `GOV/fundamentos-visuais/tipografia/tipografia-dev.md` |
| Spacing | `GOV/fundamentos-visuais/espacamento/espacamento-dev.md` |
| Grid | `GOV/fundamentos-visuais/grid/grid-dev.md` |
| Elevation | `GOV/fundamentos-visuais/elevacao/elevacao-dev.md` |
| Icons | `GOV/fundamentos-visuais/iconografia/iconografia-dev.md` |
| Motion | `GOV/fundamentos-visuais/movimento/movimento-dev.md` |
| Surface | `GOV/fundamentos-visuais/superficie/superficie-dev.md` |
| Form pattern | `GOV/padroes/design/formulario.md` |
| Navigation pattern | `GOV/padroes/design/navegacao.md` |
| UX Writing | `GOV/padroes/writing/` |
| Template base | `GOV/templates/base/base-dev.md` |
| Error pages | `GOV/templates/erro/erro-dev.md` |
| JS coding | `GOV/codificacao-javascript/codificacao-javascript.md` |
| Component construction | `GOV/construcao-de-componentes/construcao-de-componentes.md` |

Full map: `GOV-MAP.md` (project root)

### Anti-Patterns (Never Do)

- Never add `style=""` inline — use GOV utility classes
- Never use custom color hex — use `bg-*`, `text-*`, `border-*` GOV classes
- Never use arbitrary font-size/weight — use `text-*`, `text-weight-*`, `h1`-`h6` GOV classes
- Never use raw `margin`/`padding` in custom CSS — use `m-*`, `p-*` GOV spacing classes
- Never guess a component's HTML structure — always read the `-dev.md` first
- Never instantiate JS components without documented pattern (`core.BRComponentName(...)`)
- Never write button/input/label text without checking UX Writing rules
