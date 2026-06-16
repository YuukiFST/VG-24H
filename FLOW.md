# TASK: Full System Flow Documentation — VG-24h

## Project context

Django urban infrastructure management system for the city of Várzea Grande, MT, Brazil.
Citizens report incidents (street lighting, paving, sanitation); municipal staff monitor and respond.
Stack: Django + PostgreSQL (NeonDB) + GOV.br Design System. Django root: `backend/`.

No code will be written. Read the existing project and document the flows.

---

## Step 0 — Required reading before any output

Read in this order. Produce nothing until done.

1. `backend/settings.py` — focus on: INSTALLED_APPS, MIDDLEWARE (exact order),
   AUTH_USER_MODEL, LOGIN_URL, LOGIN_REDIRECT_URL, AUTHENTICATION_BACKENDS
2. `backend/urls.py` (root)
3. All `urls.py` files inside `/portal` and other apps
4. All Python files in `/portal`: models.py, views.py, forms.py,
   decorators.py, signals.py, managers.py, admin.py (whatever exists)
5. Templates in `/templates` or `backend/templates/`:
   focus on login, registration, home/dashboard, ticket list and ticket detail
6. If `.claude/ARCHITECTURE_MAP.md` exists, read it too

---

## What to document

### Flow A — Authentication: from registration to access

Describe each step in real execution order. Always cite the file and function/class
responsible (e.g. `portal/views.py → class RegisterView`).

1. **Registration**
   - URL, view, form and template involved
   - Form fields and validations applied
   - What is saved to the database (model, fields, default values)
   - Is there manual admin approval or email confirmation?
   - What is the user state right after registration (active/inactive)?

2. **Login**
   - URL, view and template
   - Authentication backend used (default Django or custom?)
   - What happens on invalid credentials

3. **Middlewares**
   - List all middlewares in the exact order from settings
   - For each one relevant to access control or session:
     describe what it checks and what happens on failure

4. **Post-login redirect**
   - Where is the user sent after successful authentication?
   - Does the destination vary by user type (citizen vs. manager/admin)?
   - Is the `next` parameter respected?

5. **Home/dashboard access**
   - What checks happen before rendering (decorator, mixin, manual check)?
   - What does an unauthenticated user see when accessing directly?

---

### Flow B — Ticket lifecycle

1. **Opening**
   - URL and creation view
   - Who can access (user type, group, decorator/mixin applied)
   - Form fields, validations, image upload (if any)
   - What is saved to the database; initial ticket status

2. **Listing**
   - URL and listing view
   - Does the citizen see only their own tickets or all?
   - Does the manager/admin see a different listing?

3. **Detail and update**
   - URL and detail view
   - Who can update a ticket's status?
   - What status transitions exist (e.g. Open → In progress → Resolved)?
   - Is the citizen notified on any status change?

4. **Closure**
   - Is there a closure/archiving flow?

---

### Flow C — Permissions map

Build a table covering all identified URLs/views:

| URL | View / Template | Who can access | Restriction applied (decorator/mixin/check) |
|---|---|---|---|

---

## Response format

- Use Markdown with headings and subheadings
- Cite file and function for each step (e.g. `portal/views.py → def my_view`)
- If anything is ambiguous or incomplete in the code, flag it with **⚠️** and explain
- End with a **"Watch out"** section listing any unexpected behavior,
  potential security gaps, or confusing logic found

Prioritize completeness over speed.

Respond in Brazilian Portuguese (pt-BR).