# Agent Prompts — one feature, one branch, one pull request

How to use
1. Create one GitHub Issue per feature (copy the "Issue body" block).
2. Start a **fresh agent session per feature** (Antigravity, Claude Code, Jules, or any coding agent). Paste the **Master prompt** first, then the feature prompt.
3. The agent works on its own branch, runs the quality gates, and opens a PR. You review and merge in order. Do not run two agents that touch the same files at the same time.
4. Merge order = feature number. F0 → F1 → ... Each feature lists its dependencies.

---

## Master prompt (paste at the start of every agent session)

```
You are a senior engineer working on "Maqadi" (طلبات البيت): a web app where Arabic-speaking families share a household errands list. A family member pastes messy WhatsApp messages and the app extracts a clean categorized list with AI.

Before writing any code, read these files fully: AGENTS.md, docs/01-PLAN.md, docs/02-ARCHITECTURE.md. For UI work also read docs/03-STITCH-DESIGN.md.

Non-negotiable rules:
- Follow the clean architecture layers in docs/02-ARCHITECTURE.md. Never import infrastructure or interfaces from domain/application.
- Stack is fixed: Python 3.12 + FastAPI + SQLAlchemy 2.0 + SQLite; vanilla HTML/CSS/JS (ES modules), no frontend framework, no build step. The frontend is a multi-page app: one HTML file per page, plain links, no client-side router, no state shared between pages. Do not add dependencies unless the task says so; if you believe one is needed, stop and explain in the PR description instead of adding it.
- The UI is Arabic, right-to-left. Use CSS logical properties. Never use left/right.
- Do ONLY the scope of the feature given. Do not refactor unrelated code. Do not implement future features "while you're there".
- Write tests with the code. Run `ruff check`, `ruff format --check`, and `pytest` before opening the PR. All must pass.
- Never commit secrets. Never persist raw pasted text.
- Work on the branch named in the task. Commit in small, conventional commits (feat:, fix:, test:, docs:, refactor:, chore:).
- When finished: open a PR using the template in AGENTS.md, fill every section honestly (including what you did NOT do and anything you are unsure about).
- If requirements conflict or are ambiguous, make the smallest reasonable assumption, write it in the PR under "Assumptions", and continue. Do not stop to ask unless you are blocked.
```

---

## F0 — Project scaffold & CI
- Branch: `feat/f0-scaffold`
- Depends on: none
- Labels: `P0`, `infra`

Issue body:
```
Create the repo skeleton exactly as in docs/02-ARCHITECTURE.md section 2 (empty packages with __init__.py where needed).
Acceptance criteria:
- backend/pyproject.toml (FastAPI, uvicorn, SQLAlchemy[asyncio], aiosqlite, pydantic-settings, httpx; dev: pytest, pytest-asyncio, ruff)
- app/main.py with create_app(); GET /api/v1/healthz returns {"status":"ok"}; static frontend/ served at "/"
- app/config.py with the .env keys from section 12; .env.example committed; .env gitignored
- frontend/index.html minimal RTL page (<html lang="ar" dir="rtl">) saying "طلبات البيت"
- tests/unit/test_architecture.py enforcing the layer import rules
- GitHub Actions workflow: ruff check, ruff format --check, pytest on push and PR
- README.md with run instructions (3 commands max)
- Makefile (or justfile) with: run, test, lint, format
```
Feature prompt:
```
Implement feature F0 from docs/04-AGENT-PROMPTS.md on branch feat/f0-scaffold, following the Issue body acceptance criteria exactly. Do not implement any business logic yet.
```

---

## F1 — Domain & database
- Branch: `feat/f1-domain-db`
- Depends on: F0
- Labels: `P0`, `backend`

Issue body:
```
Implement domain entities, enums, errors, normalize.py and ports per docs/02-ARCHITECTURE.md sections 3 and 4. Implement infrastructure/db.py, models.py, repos.py (SQLite, WAL mode, foreign keys on) and schema creation at startup (use simple create_all; no Alembic yet).
Acceptance criteria:
- Entities are plain dataclasses (no ORM objects leaking out of repos)
- normalize_ar() handles: tashkeel, tatweel, alef variants, ya/alef-maqsura, ta-marbuta, Arabic-Indic digits, extra whitespace
- Unit tests for normalize_ar with at least 12 cases
- Repo integration tests using a temp SQLite file (create/read/update, uniqueness of invite_code)
- Status transition rules implemented in domain and unit-tested (including illegal transitions)
- Partial unique index on items (household_id, name_normalized) WHERE status='open' AND archived_at IS NULL (sqlite_where), with a test that a duplicate insert is rejected at DB level
```
Feature prompt:
```
Implement feature F1 on branch feat/f1-domain-db per the Issue body. Keep domain free of any third-party imports. Provide fake in-memory repos in tests/unit/fakes.py for later features to reuse.
```

---

## F2 — Households & members (no-account join)
- Branch: `feat/f2-households-auth`
- Depends on: F1
- Labels: `P0`, `backend`

Issue body:
```
Implement use cases CreateHousehold and JoinHousehold, token auth, and the endpoints POST /households, POST /households/join, GET /me (docs/02-ARCHITECTURE.md sections 5 and 6).
Acceptance criteria:
- Invite code: 8 chars, unambiguous alphabet, unique; POST /households/invite/rotate invalidates the old code
- Join throttling per IP and per code (5 failures → 15 min lock), with tests
- Member token: secrets.token_urlsafe(32); only SHA-256 hash stored
- deps.py resolves Authorization: Bearer token to (member, household); 401 with the standard error shape otherwise
- Member color must be one of the 6 allowed values; display_name 1..30 chars, trimmed
- Tests: unit for use cases (fake repos), integration for all endpoints including 401/404/422 paths
```
Feature prompt:
```
Implement feature F2 on branch feat/f2-households-auth per the Issue body. Do not build any frontend.
```

---

## F3 — Items API
- Branch: `feat/f3-items-api`
- Depends on: F2
- Labels: `P0`, `backend`

Issue body:
```
Implement items use cases and endpoints: GET /items?status=, POST /items, PATCH /items/{id}, POST /items/{id}/status, POST /items/clear-bought.
Acceptance criteria:
- All routes scoped to the authenticated member's household; accessing another household's item returns 404 (not 403)
- Adding an item whose name_normalized equals an existing OPEN item in the same household returns 409 with the existing item id (the client decides to merge)
- requested_by = current member; bought_by set when status becomes bought; bought_at set/cleared correctly; updated_at set on every mutation
- clear-bought sets archived_at (soft archive), never deletes; GET /items excludes archived
- Invalid status transitions return 422 with a clear error code
- Items list sorted: urgent first, then created_at ascending; bought at the end
- ETag support on GET /items (ETag from count + max(updated_at)); If-None-Match returns 304
- Tests: unit (use cases) and integration (all routes, cross-household isolation test is mandatory)
```
Feature prompt:
```
Implement feature F3 on branch feat/f3-items-api per the Issue body.
```

---

## F4 — Frontend shell & design tokens
- Branch: `feat/f4-frontend-shell`
- Depends on: F2 (and Stitch screenshots in docs/design/ if available)
- Labels: `P0`, `frontend`

Issue body:
```
Build the frontend foundation per docs/02-ARCHITECTURE.md section 10 and docs/03-STITCH-DESIGN.md section 1.
Acceptance criteria:
- css/tokens.css with all color, type, spacing, radius tokens from the design system (CSS custom properties)
- Font: IBM Plex Sans Arabic (single family) via Google Fonts with a system-ui fallback stack
- Responsive shell per docs/03-STITCH-DESIGN.md "Responsive layout system": desktop >= 1200px (right sidebar + main + side panel), tablet 768-1199px (icon rail), phone < 768px (bottom tab bar). same shell on every page, CSS media queries only
- base.css (reset, RTL defaults, focus ring, reduced-motion), components.css (button, input, sheet, toast, chip)
- Multi-page structure per docs/02-ARCHITECTURE.md section 2: index.html, list.html, shop.html, history.html, household.html (the last four may be placeholders in F4), each with its entry module in js/pages/
- js/api.js (only fetch wrapper; attaches token; maps error shape to thrown ApiError), js/guard.js, js/shell.js (renders sidebar / icon rail / bottom tab bar identically on every page, marks the active page)
- `@view-transition { navigation: auto; }` in base.css as an enhancement
- Join/Create page (Screen A, index.html) fully working against the real API from F2; token saved in localStorage; redirects to list.html when authenticated
- Works at 360px, 820px and 1440px widths without horizontal scroll; keyboard focus visible everywhere; no hover-only actions
- Manual test checklist added to the PR description (steps + screenshots at 360px and 1280px)
```
Feature prompt:
```
Implement feature F4 on branch feat/f4-frontend-shell. Use only textContent for user data. Do not implement the list page yet (only a placeholder list.html that loads the shell).
```

---

## F5 — List page & check-off
- Branch: `feat/f5-list-page`
- Depends on: F3, F4
- Labels: `P0`, `frontend`

Issue body:
```
Implement the main list page, list.html (Screen B) with grouped categories, check-off, undo toast, and polling.
Acceptance criteria:
- Items grouped by category with sticky headers and counts; bought items at the bottom of each group, struck through
- Check-off is optimistic with rollback on error; toast with Undo for 5 seconds
- Member dot + name on each row; urgent marker with text (not color only)
- Empty state that invites action (no sad illustration): explains the two buttons
- Polling every 5s using ETag/304, paused when the tab is hidden; refetch on `pageshow` when `event.persisted` (back/forward cache) and on `visibilitychange` to visible
- Pure render functions in js/components/, no framework
- Basic JS tests are optional; PR must include a manual test checklist
```
Feature prompt:
```
Implement feature F5 on branch feat/f5-list-page per the Issue body. Follow docs/03-STITCH-DESIGN.md Screen B.
```

---

## F6 — Quick add & edit
- Branch: `feat/f6-quick-add`
- Depends on: F5
- Labels: `P0`, `frontend`

Issue body:
```
Implement the add-item bottom sheet (Screen E) and item edit/delete.
Acceptance criteria:
- Desktop: always-visible quick-add bar at the top of the list (Enter adds; expands with category chip, quantity, urgency); phone: floating "+" opens a bottom sheet with the name input autofocused; "أضف وكمّل" keeps it open
- Category auto-suggest from a small client-side keyword map (same keywords as backend rules extractor; export once to a shared JSON file in docs/ or backend static if needed, no duplication of logic beyond data)
- Handles 409 duplicate: shows "موجود أصلاً" with options to edit the existing item or cancel
- Edit via tap-and-hold or an edit icon; delete = status cancelled with Undo
- Validation messages in Arabic; no layout shift
```
Feature prompt:
```
Implement feature F6 on branch feat/f6-quick-add per the Issue body.
```

---

## F7 — AI paste → items (core feature)
- Branch: `feat/f7-ai-paste`
- Depends on: F3, F5
- Labels: `P0`, `ai`, `backend`, `frontend`

Issue body:
```
Implement the paste flow end to end: ChainExtractor (LLM → rules fallback), POST /paste/preview, POST /paste/confirm, and the paste/preview UI (Screen C).
Acceptance criteria (backend):
- infrastructure/extractors/llm.py supports provider selection by env (none | anthropic | gemini); uses the system prompt and JSON schema in docs/02-ARCHITECTURE.md section 7; temperature low; timeout 12s; one retry; strict JSON validation (Pydantic); invalid output → fallback
- rules.py RuleBasedExtractor with keywords_ar.py dictionary
- LLM_PROVIDER=none works fully
- Preview returns items, ignored, engine, and merge suggestions (annotate items matching OPEN items); persists NOTHING
- Confirm saves only the posted items, applies dedupe rules, sets source=paste, requested_by from posted value (must be a household member) or current member
- Input limit MAX_PASTE_CHARS enforced (413/422 with clear message)
- tests/fixtures/paste_samples.json with at least 20 realistic Jordanian family chat samples and expected items (include: cancellations, repeated items, quantities like "خبزتين", chat noise, emojis, English words, a "Name: message" export format)
- Test the rules extractor against the fixtures (>= 70% item recall, 0 hallucinated items on noise-only samples); LLM adapter tested with a mocked client (valid, invalid JSON, timeout)
Acceptance criteria (frontend):
- Desktop: two-column dialog (source text | extracted items) plus the persistent paste card in the side panel; phone: bottom sheet with 3 steps. States exactly as Screen C: paste, loading, preview, error; the pasted text is never lost on error
- Each preview row editable (name, quantity, category, requester), uncheckable; "ignored" section collapsible
- "موجود أصلاً — ضم؟" handling per row
- Loading state under 15s feels responsive (skeleton rows, no spinner-only)
- Unsent pasted text is kept as a draft in sessionStorage (cleared on confirm) so a reload or page change does not lose it
```
Feature prompt:
```
Implement feature F7 on branch feat/f7-ai-paste. This is the most important feature: prioritize correctness and graceful failure over polish. Never auto-add AI results without user confirmation. Never log raw pasted text. Include a small script scripts/eval_extraction.py that runs the fixtures through the active extractor and prints recall/precision so I can measure accuracy.
```

---

## F8 — Dedupe & merge improvements
- Branch: `feat/f8-dedupe`
- Depends on: F7
- Labels: `P1`, `backend`

Issue body:
```
Improve duplicate detection: singular/plural/dual folding (خبز/خبزة/خبزتين), common spelling variants (بندورة/بنادورة/طماطم as alias group), and a small alias table in data (not code).
Acceptance criteria:
- alias data in backend/app/domain/aliases_ar.py (data only), covered by tests
- merge suggestions show both quantities, never auto-sum
- No false merges between clearly different items (test: "لبن" vs "لبنة" must NOT merge)
```
Feature prompt:
```
Implement feature F8 on branch feat/f8-dedupe per the Issue body. Pure functions, heavily unit-tested.
```

---

## F9 — Categories & shop mode
- Branch: `feat/f9-shop-mode`
- Depends on: F5
- Labels: `P1`, `frontend`

Issue body:
```
Implement Screen D (shop mode): larger rows, only open items, category order = typical supermarket walk, progress "باقي X من Y", completion button that calls clear-bought.
Acceptance criteria:
- Toggle from main list; remembered per device
- Wake Lock API requested while shop mode is open (feature-detected, fails silently)
- High contrast, 72px rows, 32px checkboxes
- Works offline-tolerant: if a request fails, keep optimistic state and retry; show a subtle "غير متصل" indicator
```
Feature prompt:
```
Implement feature F9 on branch feat/f9-shop-mode per the Issue body.
```

---

## F10 — Share to WhatsApp
- Branch: `feat/f10-share-whatsapp`
- Depends on: F5
- Labels: `P1`, `backend`, `frontend`

Issue body:
```
Implement GET /share/whatsapp (plain Arabic text grouped by category, open items only, capped at 3500 chars) and Screen F (preview sheet with "افتح الواتساب" using https://wa.me/?text=<urlencoded> and "انسخ النص" using the Clipboard API with fallback).
Acceptance criteria:
- Text format exactly as in the Screen F prompt example; urgent items marked "(مستعجل)"
- URL-encoding tested with Arabic + emoji
- Unit tests for the text builder
```
Feature prompt:
```
Implement feature F10 on branch feat/f10-share-whatsapp per the Issue body.
```

---

## F11 — Realtime (SSE)
- Branch: `feat/f11-realtime-sse`
- Depends on: F5
- Labels: `P1`, `backend`, `frontend`

Issue body:
```
Add GET /events (Server-Sent Events) with an in-memory EventBus (infrastructure/events.py implementing the EventBus port). Publish item.created / item.updated / member.joined from use cases via the port (not from routers).
Acceptance criteria:
- Authenticated via token (EventSource can't send headers: accept a short-lived signed ticket from POST /events/ticket, valid 60s, single use)
- Per-household isolation test: events never leak across households
- Heartbeat every 20s; client reconnects with backoff; falls back to 5s polling if SSE fails 3 times
- Document the single-process limitation in docs/02-ARCHITECTURE.md
- SSE is opened only by list.js and shop.js on load and closed on navigation (pages are separate documents)
```
Feature prompt:
```
Implement feature F11 on branch feat/f11-realtime-sse per the Issue body.
```

---

## F12 — History & household pages
- Branch: `feat/f12-history`
- Depends on: F5
- Labels: `P2`

Issue body:
```
Add GET /history?limit= (recently bought items with who bought and when) and the history page (Screen G) plus the household page (Screen H: members list, invite code with copy button, "غيّر الكود" confirmation dialog calling POST /households/invite/rotate).
Acceptance criteria:
- Relative times in Arabic ("قبل ساعتين"), using Intl.RelativeTimeFormat('ar')
- Tap on a history item → "أضفه مرة ثانية" re-adds it as open
- Tests for query ordering and household isolation
```
Feature prompt:
```
Implement feature F12 on branch feat/f12-history per the Issue body.
```

---

## F13 — PWA & offline shell
- Branch: `feat/f13-pwa`
- Depends on: F5
- Labels: `P2`, `frontend`

Issue body:
```
Add manifest.webmanifest (name, icons, theme color #1F8A5B, dir rtl, lang ar), a service worker caching the app shell (the five HTML pages plus css/js; cache-first for static assets, network-first for /api GET with cached fallback), and an install hint shown once.
Acceptance criteria:
- Lighthouse PWA/installability passes on desktop Chrome
- Offline: app shell loads and shows the last known list with the "غير متصل" indicator; writes are disabled with a clear message (no silent queueing in this feature)
- Cache versioning so updates don't get stuck
```
Feature prompt:
```
Implement feature F13 on branch feat/f13-pwa per the Issue body.
```

---

## F14 — Deployment & demo data
- Branch: `feat/f14-deploy-demo`
- Depends on: F7 (minimum)
- Labels: `P0-for-demo`, `infra`

Issue body:
```
Containerize and make deployable to a free/cheap host (Render/Railway/Fly: choose one and document it).
Acceptance criteria:
- Dockerfile (multi-stage, non-root), .dockerignore, healthcheck on /api/v1/healthz
- Persistent volume path for SQLite documented
- scripts/seed_demo.py creates a demo household "بيت أبو أحمد" with 4 members and 12 items, plus a ready sample paste text in docs/demo-paste.txt
- DEPLOY.md with exact steps and required env vars
- CORS and security headers (CSP allowing Google Fonts only), HTTPS-only cookie/headers notes
```
Feature prompt:
```
Implement feature F14 on branch feat/f14-deploy-demo per the Issue body.
```

---

## F15 — Polish & accessibility pass
- Branch: `feat/f15-polish-a11y`
- Depends on: all P0/P1
- Labels: `P2`

Issue body:
```
Final pass with no new features.
Acceptance criteria:
- Axe/Lighthouse accessibility score >= 95 on main list and paste flows
- All touch targets >= 44px; focus order correct in RTL; screen reader labels in Arabic
- Contrast >= 4.5:1 for all text on all backgrounds
- Consistent empty/error/loading states; Arabic copy reviewed for consistency (same word for the same action everywhere)
- Remove dead code and unused CSS; update README with screenshots
```
Feature prompt:
```
Implement feature F15 on branch feat/f15-polish-a11y per the Issue body. Make no behavior changes except bug fixes you list explicitly in the PR.
```

---

## Reviewer agent prompt (run on every PR before you merge)

```
You are a strict code reviewer for the Maqadi repo. Review the diff of this PR against: AGENTS.md, docs/02-ARCHITECTURE.md, and the Issue's acceptance criteria.
Output:
1. Acceptance criteria checklist (met / not met / partially, with file references)
2. Architecture violations (layer imports, logic in routers, fetch outside api.js, client-side routing, business logic inside HTML files)
3. Security & privacy issues (raw pasted text stored or logged, missing household scoping, unescaped user HTML, secrets)
4. RTL/accessibility issues in UI changes
5. Missing or weak tests
6. Out-of-scope changes that should be removed
Be blunt. List blocking issues first. Do not rewrite the code; only review.
```

## Orchestrator prompt (optional: to run several agents)

```
You are coordinating coding agents for the Maqadi repo. Read docs/04-AGENT-PROMPTS.md. For the next unmerged feature in dependency order, create the GitHub issue from its "Issue body", create the branch, and hand the Master prompt + feature prompt to a coding agent. Never start a feature whose dependencies are not merged. After the PR is opened, run the Reviewer prompt on it and summarize the verdict in one paragraph. Never merge yourself.
```
