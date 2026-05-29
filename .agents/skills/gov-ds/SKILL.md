---
name: gov-ds
description: Gatekeeper for Gov.br Design System compliance. Before ANY frontend change (HTML structure, CSS class, component, layout, typography, color, spacing, icon, or text), the agent MUST search GOV/ for the exact reference. No reference found → block the change and report. Also enforces UX Writing rules from GOV/padroes/writing/ for every user-facing string. Use when user types "/gov-ds", mentions "DS do gov", "design system", or any frontend modification to this project.
---

# Gov.br Design System Gatekeeper

## Purpose

Block any frontend change that lacks explicit backing from the GOV/ reference directory. This skill turns the agent into a gatekeeper — no reference, no change.

## Trigger Detection

This skill activates when the agent intends to:
- Add or modify any HTML structure in `backend/templates/`
- Change any CSS/SCSS in `backend/static/`
- Alter component markup, classes, attributes, or JS instantiation
- Write or edit any user-facing text (labels, buttons, messages, placeholders, titles, errors)
- Touch anything related to layout, spacing, color, typography, or icons

Also activates explicitly via: `/gov-ds`, "DS do gov", "padrão gov.br", "design system gov"

## Mandatory Gatekeeper Workflow

Every frontend change passes through these gates **in order**. Skip none.

### Gate 1 — Identify Domains

List every domain touched by the change:
- **Components**: Which Gov.br components? (button, input, modal, table, header, footer, menu, card, etc.)
- **Visual Foundations**: Which tokens? (colors, spacing, typography, elevation, grid, icons, motion, surface)
- **Patterns**: Which UX patterns? (form, navigation, empty states, onboarding, etc.)
- **UX Writing**: Any new or changed text? → always triggers `GOV/padroes/writing/`
- **Template**: Layout-level changes? → `GOV/templates/base/`
- **JavaScript**: Component instantiation? → `GOV/components/<name>/<name>-dev.md`

### Gate 2 — Search GOV/ References

For each domain identified, search the corresponding GOV/ path. Use `GOV-MAP.md` to locate the right file.

**Read the `-dev.md` file** (developer reference with HTML/CSS/JS code). Also read the `.md` files for conceptual overview and patterns.

If a component has: `visao-geral.html` → read it for visual reference. `.scss` files in `GOV/src/components/<name>/` → read for styling reference.

### Gate 3 — Certainty Check

After reading references, ask:

- Do I know the **exact HTML structure** required? (classes, nesting, attributes, aria roles)
- Do I know the **CSS utility classes** for colors/spacing/typography/surface?
- Do I know the **JS instantiation** pattern for interactive components?
- Do I know the **UX writing rules** for every text string?
- Do I know the **state handling** (success, danger, warning, info, disabled, loading)?

If **NO** to any question → **block the change**.

### Gate 4 — Reference Resolution

| Scenario | Action |
|---|---|
| Reference **found and clear** | Read it fully, implement exactly per reference |
| Reference **found but ambiguous** | Ask user for clarification before proceeding |
| Reference **NOT found** | **BLOCK** the change. Do NOT guess. Report: what's missing, which GOV/ paths were searched, and a recommendation based on closest Gov.br DS patterns |
| Text change, no **UX Writing** reference read | **BLOCK**. Must read `GOV/padroes/writing/` first |

### Gate 5 — Implement or Report

**If all gates pass:** Implement exactly matching the reference structure. Do not invent classes, do not use custom CSS when a GOV utility class exists.

**If blocked:** Report to user:
```
[GOV-DS GATEKEEPER] Modificação bloqueada.
Motivo: [what reference was missing]
Buscado em: [list of GOV/ paths searched]
Recomendação: [closest DS pattern + suggestion]
```

## UX Writing Rule (Always Active)

Any text change (labels, placeholders, messages, button text, titles, errors, help text, empty states) requires reading from:

- `GOV/padroes/writing/principios-writing.md` — tone, clarity, concision, accessibility principles
- `GOV/padroes/writing/microcopy.md` — per-element text rules (action labels, input labels, feedback messages, navigation, etc.)

Apply these rules:
- Labels: max 2 words (3 if unavoidable), sentence case (first letter capitalized), no truncation
- Buttons: all caps in GOV (upper case labels in Portuguese per DS convention), max 2 words
- Actions: short, objective, clear verbs
- Messages: simple, direct, no jargon
- Consistency: same term for same concept everywhere

## Key GOV/ Structure Quick Reference

| Concern | Path |
|---|---|
| Any component | `GOV/components/<name>/<name>-dev.md` |
| Component visual overview | `GOV/components/<name>/<name>.md` |
| Component SCSS | `GOV/src/components/<name>/_<name>.scss` |
| Colors | `GOV/fundamentos-visuais/cores/cores-dev.md` |
| Typography | `GOV/fundamentos-visuais/tipografia/tipografia-dev.md` |
| Spacing | `GOV/fundamentos-visuais/espacamento/espacamento-dev.md` |
| Grid | `GOV/fundamentos-visuais/grid/grid-dev.md` |
| Elevation | `GOV/fundamentos-visuais/elevacao/elevacao-dev.md` |
| Icons | `GOV/fundamentos-visuais/iconografia/iconografia-dev.md` |
| Motion | `GOV/fundamentos-visuais/movimento/movimento-dev.md` |
| Surface (borders, bg) | `GOV/fundamentos-visuais/superficie/superficie-dev.md` |
| Form pattern | `GOV/padroes/design/formulario.md` |
| Navigation pattern | `GOV/padroes/design/navegacao.md` |
| UX Writing | `GOV/padroes/writing/` |
| Template base | `GOV/templates/base/base-dev.md` |
| Error pages | `GOV/templates/erro/erro-dev.md` |
| JS coding | `GOV/codificacao-javascript/codificacao-javascript.md` |
| Component construction | `GOV/construcao-de-componentes/construcao-de-componentes.md` |

Full map: see [GOV-MAP.md](GOV-MAP.md)

## Anti-Patterns (Never Do)

- Never add `style=""` inline attributes — use GOV utility classes
- Never use custom color hex values — use `bg-*`, `text-*`, `border-*` GOV classes
- Never use arbitrary font-size/weight — use `text-*`, `text-weight-*`, `h1`-`h6` GOV classes
- Never use raw `margin`/`padding` in custom CSS — use `m-*`, `p-*` GOV spacing classes
- Never guess a component's HTML structure — always read the `-dev.md` first
- Never instantiate JS components without the documented pattern (`core.BRComponentName(...)`)
- Never write button/input/label text without checking UX Writing rules

## Idempotency

Running this gatekeeper twice on the same change produces the same result. The gates are read-only (reading GOV/ files). Implementation happens only after all gates pass.
