# Architecture — Maqadi (طلبات البيت)

Stack: FastAPI (Python 3.12) · SQLAlchemy 2.0 + SQLite · vanilla HTML/CSS/JS (ES modules) · pytest.
Principle: **dependencies point inward.** Domain knows nothing about FastAPI, SQL, or any LLM SDK.

## 1. Layers

```
interfaces  ──►  application  ──►  domain  ◄──  infrastructure
(HTTP, schemas)  (use cases)       (entities,    (SQLAlchemy repos,
                                    rules, ports) LLM clients, clock)
```

| Layer | Contains | May import | Must NOT import |
|---|---|---|---|
| `domain` | entities, value objects, enums, domain errors, **ports** (abstract interfaces) | stdlib only | everything else |
| `application` | use cases (one class/function per user intent), DTOs | domain | fastapi, sqlalchemy, anthropic/google SDKs |
| `infrastructure` | repository implementations, DB session, LLM adapters, rule-based extractor, settings | domain, application, libs | interfaces |
| `interfaces` | FastAPI routers, request/response schemas, dependency wiring, SSE | application, domain | infrastructure internals (wired only in `composition.py`) |

Composition root: `backend/app/composition.py` is the **only** place that knows which concrete adapter implements which port.

## 2. Repository layout

```
maqadi/
├─ AGENTS.md
├─ README.md
├─ docs/                      # 01-PLAN, 02-ARCHITECTURE, 03-STITCH-DESIGN, 04-AGENT-PROMPTS
├─ backend/
│  ├─ pyproject.toml
│  ├─ app/
│  │  ├─ main.py              # create_app(), mounts /api and static frontend
│  │  ├─ composition.py       # wiring
│  │  ├─ config.py            # pydantic-settings (.env)
│  │  ├─ domain/
│  │  │  ├─ entities.py       # Household, Member, Item
│  │  │  ├─ enums.py          # ItemStatus, Urgency, Category, ItemSource
│  │  │  ├─ errors.py
│  │  │  ├─ normalize.py      # Arabic normalization (pure functions)
│  │  │  └─ ports.py          # HouseholdRepo, MemberRepo, ItemRepo, ItemExtractor, Clock, EventBus
│  │  ├─ application/
│  │  │  ├─ households.py     # CreateHousehold, JoinHousehold, RotateInviteCode
│  │  │  ├─ items.py          # AddItem, UpdateItem, SetStatus, ListItems, ArchiveBought
│  │  │  ├─ history.py        # ListHistory
│  │  │  ├─ paste_import.py   # PreviewPaste, ConfirmPaste
│  │  │  ├─ dedupe.py         # merge logic (pure, uses domain.normalize)
│  │  │  └─ share.py          # BuildWhatsAppText
│  │  ├─ infrastructure/
│  │  │  ├─ db.py             # engine, session, migrations bootstrap
│  │  │  ├─ models.py         # SQLAlchemy ORM models (NOT domain entities)
│  │  │  ├─ repos.py          # SQL repos + mappers
│  │  │  ├─ extractors/
│  │  │  │  ├─ llm.py         # LLMItemExtractor (provider chosen by env)
│  │  │  │  ├─ rules.py       # RuleBasedExtractor (no-AI fallback)
│  │  │  │  └─ chain.py       # try LLM → on error/timeout fall back to rules
│  │  │  └─ events.py         # in-memory EventBus for SSE
│  │  └─ interfaces/
│  │     ├─ api/
│  │     │  ├─ deps.py        # auth: member token → (member, household)
│  │     │  ├─ households.py
│  │     │  ├─ items.py
│  │     │  ├─ paste.py
│  │     │  ├─ history.py
│  │     │  ├─ share.py
│  │     │  ├─ events.py      # SSE + ticket
│  │     │  └─ errors.py      # the ONE place mapping domain errors → HTTP responses
│  │     └─ schemas.py        # Pydantic request/response models
│  └─ tests/
│     ├─ unit/                # domain + application (fake repos, fake extractor)
│     ├─ integration/         # API + real SQLite (tmp file)
│     └─ fixtures/paste_samples.json   # real-ish Jordanian family messages + expected items
└─ frontend/                 # multi-page app (MPA): one HTML file per page
   ├─ index.html            # join / create household (Screen A)
   ├─ list.html             # main list + quick add + paste (Screens B, C, E, F)
   ├─ shop.html             # shop mode (Screen D)
   ├─ history.html          # history (Screen G)
   ├─ household.html        # members + invite code (Screen H)
   ├─ manifest.webmanifest, sw.js          (P2)
   ├─ css/  tokens.css · base.css · components.css · pages.css
   └─ js/
      ├─ shell.js           # renders sidebar / icon rail / bottom tab bar on every page
      ├─ guard.js           # no token in localStorage → redirect to index.html
      ├─ api.js             # fetch wrapper (only place that calls /api)
      ├─ realtime.js        # polling → SSE (used by list.js and shop.js)
      ├─ components/        # item-row.js, category-group.js, paste-dialog.js, ...
      └─ pages/             # index.js, list.js, shop.js, history.js, household.js (one entry per HTML page)
```

## 3. Domain model

```
Household(id, name, invite_code, created_at)
Member(id, household_id, display_name, color, token_hash, created_at)
Item(id, household_id, name, name_normalized, quantity_text, note,
     category, status, urgency,
     requested_by_member_id, bought_by_member_id,
     source, created_at, updated_at, bought_at, archived_at)
```

Enums
- `ItemStatus`: `open | bought | cancelled`
- `Urgency`: `normal | urgent`
- `ItemSource`: `manual | paste`
- `Category`: `produce, dairy_eggs, meat_poultry, bakery, pantry, cleaning, pharmacy, other`
  (Arabic labels live in the frontend: خضار وفواكه · ألبان وبيض · لحوم ودجاج · مخبوزات · معلبات وجافة · منظفات · صيدلية · أخرى)

Rules (domain/application, unit-tested)
- Two **open** items in one household with equal `name_normalized` are the same item → merge, never duplicate. Enforced twice: in the use case (to return a friendly 409) **and** by a partial unique index `(household_id, name_normalized) WHERE status='open' AND archived_at IS NULL`, so races and double-clicks on confirm cannot create duplicates.
- Status transitions: `open → bought | cancelled`, `bought → open` (undo), `cancelled → open`.
- Only members of the household can read or mutate its items.
- `clear-bought` is a soft archive: it sets `archived_at`. Archived items are excluded from `GET /items` but kept for `/history` (F12). Nothing is hard-deleted in the MVP.
- Every mutation sets `updated_at` (used by the ETag and by SSE events).
- Raw pasted text is **never persisted** (privacy). Only confirmed items are stored.

### Arabic normalization (`domain/normalize.py`)
Pure function used for dedupe/search: strip tashkeel and tatweel, unify أ/إ/آ→ا, ى→ي, ة→ه (for matching only), collapse spaces, lowercase Latin, convert Arabic-Indic digits to ASCII. Display name is stored untouched.

## 4. Ports (domain/ports.py)

```python
class ItemExtractor(Protocol):
    async def extract(self, text: str, known_members: list[str]) -> ExtractionResult: ...

@dataclass
class ExtractedItem:
    name: str
    quantity_text: str | None
    category: Category
    urgency: Urgency
    requested_by: str | None      # a display name from known_members, or None
    source_snippet: str           # the fragment it came from (shown in preview only)
    confidence: float             # 0..1

@dataclass
class ExtractionResult:
    items: list[ExtractedItem]
    ignored: list[str]            # fragments judged not to be requests (chat noise)
    engine: Literal["llm", "rules"]
```

Other ports: `HouseholdRepo`, `MemberRepo`, `ItemRepo` (all async), `Clock`, `EventBus`, `RateLimiter`, `TicketSigner` (short-lived SSE tickets). Use cases receive ports by constructor injection; nothing in `application` instantiates an adapter.

## 5. Auth (no accounts)

- `POST /api/households` creates household + first member, returns `{member_token, invite_code}`.
- `POST /api/households/join` with `invite_code` + `display_name` returns a `member_token`.
- Token = random 32 bytes (urlsafe). Server stores **only a hash** (SHA-256). Client keeps it in `localStorage` and sends `Authorization: Bearer <token>`.
- Invite codes: **8 chars** from an unambiguous alphabet (no 0/O/1/I). Join attempts throttled per IP **and per code** (5 failures on one code → locked 15 minutes). `POST /households/invite/rotate` lets any member issue a new code and invalidate the old one. Anyone holding the code can join, so the UI must say so and offer rotation.
- Honest limitation: whoever has the token is that member. Fine for a family tool; document it.

## 6. HTTP API (prefix `/api/v1`)

| Method | Path | Purpose |
|---|---|---|
| POST | `/households` | create household + first member |
| POST | `/households/join` | join by invite code |
| POST | `/households/invite/rotate` | issue a new invite code, invalidate the old one |
| GET | `/me` | current member + household + members list |
| GET | `/items?status=open` | list items (grouped client-side) |
| POST | `/items` | add one item |
| PATCH | `/items/{id}` | edit name/quantity/note/category/urgency |
| POST | `/items/{id}/status` | `{status}` → open/bought/cancelled |
| POST | `/items/clear-bought` | archive bought items older than N hours |
| POST | `/paste/preview` | `{text}` → `ExtractionResult` + merge suggestions (nothing saved) |
| POST | `/paste/confirm` | `{items:[...]}` → saves chosen items (applies dedupe) |
| GET | `/share/whatsapp` | ready-to-send Arabic text of open items |
| GET | `/history?limit=` | recently bought items (includes archived) with who bought and when |
| POST | `/events/ticket` | short-lived (60 s), single-use ticket for opening the SSE stream |
| GET | `/events?ticket=` | SSE stream: `item.created/updated`, `member.joined` |
| GET | `/healthz` | liveness |

Conventions: JSON only, snake_case, ISO-8601 UTC timestamps, errors as `{ "error": {"code": "...", "message": "..."} }`, UTF-8 everywhere.

## 7. AI extraction contract (the heart of the product)

Goal: turn messy Jordanian/Levantine Arabic family messages into structured items.

Pipeline: `text → (size limit 6,000 chars) → ChainExtractor → LLM (timeout 12s, 1 retry) → validate JSON against schema → on failure → RuleBasedExtractor`.

**System prompt for the LLM adapter** (keep in `infrastructure/extractors/prompts.py`):

```
You extract household shopping requests from pasted family chat messages.
The messages are in Arabic (mostly Jordanian/Levantine dialect), sometimes mixed with English, emojis, and chat noise.

Return ONLY valid JSON matching the schema. No prose, no markdown fences.

Rules:
1. Extract only things someone asks to BUY or BRING (groceries, household items, pharmacy). Ignore greetings, jokes, questions about timing, and messages that cancel nothing.
2. One item per product. Split "جيب لبن وخبز وبيض" into three items.
3. Keep the item name in Arabic exactly as people would say it at the shop; normalize obvious spelling variants. Do not translate.
4. quantity_text: copy the quantity phrase as written ("2 كيلو", "خبزتين", "علبتين"). Use null if none.
5. If the same product is requested more than once, return ONE item and keep the largest/most specific quantity.
6. If a later message cancels an earlier request ("خلص جبناه", "مش لازم بيض"), do not include the item.
7. category must be one of: produce, dairy_eggs, meat_poultry, bakery, pantry, cleaning, pharmacy, other.
8. urgency = "urgent" only if the text says so ("ضروري", "اليوم", "هلأ", "مستعجل").
9. requested_by: use a name from KNOWN_MEMBERS only if the message is clearly attributed to that person (chat export format "Name: message"). Otherwise null.
10. Never invent items. If unsure, lower confidence (0.0-1.0) instead of guessing.
11. Put fragments that were not requests in "ignored".

Schema:
{"items":[{"name":str,"quantity_text":str|null,"category":str,"urgency":"normal"|"urgent",
"requested_by":str|null,"source_snippet":str,"confidence":number}],"ignored":[str]}
```

**Few-shot examples** (also used as regression tests in `tests/fixtures/paste_samples.json`):

Input:
```
ماما: يا يونس لا تنسى تجيب خبزتين ولبن
أبو أحمد: وجيب بيض كمان، ضروري اليوم
ماما: صح وكيلو بندورة
سارة: انا بدي شامبو وكاسات للضيوف
أبو أحمد: لا خلص ما بدنا بيض، لقيت بالبيت
😂😂 مين أكل الشوكولاتة؟
```
Expected items:
- خبز — خبزتين — bakery — requested_by ماما
- لبن — null — dairy_eggs — ماما
- بندورة — كيلو — produce — ماما
- شامبو — null — other — سارة
- كاسات — للضيوف — other — سارة
- (بيض is NOT returned: cancelled by later message)
- ignored: ["😂😂 مين أكل الشوكولاتة؟"]

Note: the example shows a cancelled item. Rule 6 is the hardest for LLMs: it needs its own regression test.

**RuleBasedExtractor (fallback, no AI):** split by newline / "،" / "و" / ","; strip leading verbs (جيب, اشتري, بدي, لا تنسى, بدنا); detect quantity via regex (digits, كيلو, علبة, حبة, ربطة, خبزتين...); category via keyword dictionary (`infrastructure/extractors/keywords_ar.py`); `confidence` capped at 0.6. It must pass a reduced subset of the fixtures (>= 70%).

## 8. Dedupe & merge (`application/dedupe.py`)

- Key = `name_normalized` + singular/plural folding for a small list (خبز/خبزة/خبزتين → خبز).
- On preview: each extracted item is annotated `merge_with_item_id` if an open item matches. UI shows "موجود أصلاً: ضم؟".
- Quantities are **not** summed automatically (text like "كيلو" + "نص كيلو" is ambiguous): show both in the note, user decides.

## 9. Realtime

- v1: client polls `GET /items` every 5 s with `If-None-Match` (ETag of max(updated_at, count)).
- On every page that shows live data (`list`, `shop`), the entry module opens the SSE connection on load and closes it on navigation (pages are separate documents).
- v2: SSE `/events`; single-process in-memory `EventBus` (fine for hackathon). Client falls back to polling if SSE drops.
- Document that scaling past one process needs Redis pub/sub.

## 10. Frontend rules

- Multi-page app. No framework, no build step. Each HTML page loads its own entry module from `js/pages/` plus the shared `shell.js` and `guard.js`. Navigation is plain links (`<a href="list.html">`), never JS routing.
- Smooth page changes are a progressive enhancement: `@view-transition { navigation: auto; }` in `base.css`. Browsers without support just navigate normally.
- `api.js` is the only module that calls `fetch`. Page and component modules never touch the network directly.
- State lives inside each page module (the list page holds its items array). Render functions are pure: `(state) → DOM`. Nothing is shared between pages except the token in `localStorage`; every page loads its data from the API on arrival.
- `guard.js` is a UX redirect only. Real protection is the API's token check.
- `dir="rtl"` and `lang="ar"` on `<html>`; use CSS logical properties (`margin-inline-start`, `padding-inline`), never `left/right`.
- Design tokens only from `css/tokens.css` (no hard-coded colors).
- Accessibility floor: visible focus, 44×44px tap targets, `prefers-reduced-motion`, contrast ≥ 4.5:1.
- Escape all user text (use `textContent`, never `innerHTML` with user data).
- Pages restored from the back/forward cache must not show stale data: in `list.js`/`shop.js`/`history.js`, listen to `pageshow` and refetch when `event.persisted` is true; also refetch on `visibilitychange` to visible.
- Unsent input (pasted text, half-typed item) is kept as a draft in `sessionStorage` and cleared on success, so a reload or navigation does not lose it.
- `localStorage` holds only the member token and small UI preferences (shop mode toggle). Mitigate token theft by strict CSP (no inline scripts, self + Google Fonts only) and by never injecting user data as HTML.

## 11. Quality gates (every PR)

- `ruff check` + `ruff format --check`
- `pytest` green; new logic has tests; paste fixtures pass thresholds
- No secrets in repo; `.env.example` updated if config changes
- No layer violations (a simple import-linter test in `tests/unit/test_architecture.py` checks: domain imports nothing outside stdlib; application doesn't import infrastructure/interfaces)

## 12. Config (.env)

```
APP_ENV=dev
DATABASE_URL=sqlite+aiosqlite:///./maqadi.db
LLM_PROVIDER=none            # none | anthropic | gemini
LLM_API_KEY=
LLM_MODEL=
LLM_TIMEOUT_SECONDS=12
MAX_PASTE_CHARS=6000
CORS_ORIGINS=http://localhost:8000
```
`LLM_PROVIDER=none` must always work (rules extractor only).

## 13. Serving, operations and known limits

**Serving:** FastAPI serves `frontend/` with `StaticFiles` at `/` and the API under `/api/v1`, same origin (no CORS needed in production). Pages are plain files: `/index.html`, `/list.html`, `/shop.html`, `/history.html`, `/household.html`. Set long cache headers on `css/` and `js/` with content-hash query strings (`?v=<git-sha>`) so deploys do not serve stale assets.

**Logging:** structured JSON logs (`request_id`, method, path, status, duration). **Never log** request bodies for `/paste/*`, tokens, invite codes or item names. Each response carries `X-Request-ID`.

**Errors:** domain errors (`NotFound`, `InvalidTransition`, `DuplicateItem`, `Forbidden`, `RateLimited`) are mapped to HTTP only in `interfaces/api/errors.py`. Unexpected errors return a generic 500 with the request id.

**Backups:** SQLite file lives on a persistent volume; a scheduled copy (`sqlite3 .backup`) to a second location. Document restore steps in `DEPLOY.md`.

**Known limits (state them honestly in the README):**
- Single process only (in-memory rate limiter, EventBus). Scaling out needs Redis (limiter, pub/sub) and Postgres.
- `create_all` instead of migrations. Introduce Alembic before the first real user keeps data.
- Whoever holds a member token is that member; whoever holds the invite code can join. Mitigations: 8-char code, throttling, code rotation.
- AI extraction quality is measured on `tests/fixtures/paste_samples.json` only; real-world accuracy must be re-measured with family messages.
