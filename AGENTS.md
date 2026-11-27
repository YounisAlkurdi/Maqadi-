# AGENTS.md — Rules for any AI agent working on Maqadi

Read first: `docs/01-PLAN.md` (what and why), `docs/02-ARCHITECTURE.md` (how), `docs/03-STITCH-DESIGN.md` (UI), `docs/04-AGENT-PROMPTS.md` (your task).

## Project in one paragraph
Maqadi (طلبات البيت) is a website where an Arabic-speaking family shares one errands/shopping list. The signature feature: paste messy WhatsApp messages → AI extracts a clean, categorized list that the user confirms. UI is Arabic RTL, designed laptop-first (1440px) and fully responsive down to 360px phones, with a conventional shopping-list app look (see docs/03-STITCH-DESIGN.md).

## Hard rules
1. **Clean architecture.** `domain` ← `application` ← `interfaces`; `infrastructure` implements ports. Domain imports only stdlib. Wiring only in `composition.py`.
2. **Fixed stack.** Python 3.12, FastAPI, SQLAlchemy 2.0, SQLite; vanilla HTML/CSS/JS ES modules. The frontend is a multi-page app (one HTML file per page, plain links, no client-side router). No new dependency without explicit approval in the task.
3. **Scope discipline.** Implement only the assigned feature. No drive-by refactors, no extra features.
4. **Tests ship with code.** Unit tests for logic, integration tests for endpoints. Household isolation tests are mandatory for any new data route.
5. **Privacy.** Never persist or log raw pasted text. Never log tokens. Store only token hashes.
6. **AI is advisory.** AI output is always previewed and confirmed by the user. The app must work with `LLM_PROVIDER=none`.
7. **RTL always.** `dir="rtl"`, CSS logical properties, no `left/right`. Arabic copy is plain and consistent (same word for the same action everywhere).
8. **Safe DOM.** User data goes in via `textContent`. No `innerHTML` with user input.
9. **Secrets.** Nothing secret in the repo. Update `.env.example` when adding config.
10. **Honesty in PRs.** State what you didn't do, what you assumed, and what you're unsure about.

## Commands
```
make run      # uvicorn app.main:app --reload (from backend/)
make test     # pytest
make lint     # ruff check
make format   # ruff format
```

## Git workflow
- `main` is always deployable. Never push to `main`. Never force-push shared branches.
- One feature = one issue = one branch = one PR.
- Branch names: `feat/fN-short-name`, `fix/short-name`, `docs/short-name`, `chore/short-name`.
- Conventional commits: `feat:`, `fix:`, `test:`, `docs:`, `refactor:`, `chore:`. Small commits, imperative mood.
- Rebase on latest `main` before opening the PR. PRs should be reviewable in under 20 minutes (aim for < 500 changed lines excluding tests/fixtures).
- Merge strategy: squash merge, title = conventional commit.
- Definition of done: acceptance criteria met, lint + tests green in CI, PR template complete, reviewer-agent report attached or summarized.

## Pull request template (copy into `.github/pull_request_template.md`)
```markdown
## What
<!-- One or two sentences. Link the issue: Closes #N -->

## Why
<!-- The user problem this feature solves -->

## How
<!-- Key design decisions, which layers were touched -->

## Acceptance criteria
- [ ] (copy from the issue, tick honestly)

## Tests
<!-- What you added, how to run them, results -->

## Manual test steps (UI changes)
<!-- Steps + screenshots at 360px and 1280px, RTL checked -->

## Assumptions
<!-- Anything you decided without confirmation -->

## Not done / follow-ups
<!-- Be explicit -->

## Risk & rollback
<!-- What could break, how to revert -->

## Checklist
- [ ] Layers respected (domain has no third-party imports)
- [ ] No raw pasted text stored or logged
- [ ] Household isolation tested (if data routes were added)
- [ ] RTL + keyboard focus verified (if UI)
- [ ] `ruff check`, `ruff format --check`, `pytest` pass
- [ ] `.env.example` and docs updated if needed
```

## Issue template (copy into `.github/ISSUE_TEMPLATE/feature.md`)
```markdown
---
name: Feature
about: One feature = one PR
labels: feature
---
**Feature ID:** FN
**Branch:** feat/fN-name
**Depends on:** F?
**Priority:** P0 | P1 | P2

## Problem
## Scope (in)
## Out of scope
## Acceptance criteria
- [ ]
## Notes
```

## Definition of "clean"
- Functions do one thing; use cases are small; routers contain no business logic.
- Names are domain words (`Household`, `Item`, `PreviewPaste`), not technical ones (`Manager`, `Helper`).
- Errors are domain errors mapped to HTTP in one place.
- No commented-out code, no TODOs without an issue number.

## When blocked
Make the smallest reasonable assumption, note it under "Assumptions" in the PR, and continue. Stop only for a real blocker (missing credentials, contradictory requirements).
