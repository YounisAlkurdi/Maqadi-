[English](README.md) | [العربية](README.ar.md)

# Maqadi — Shared Household Errands List (طلبات البيت)

Built for **Nmkkn AI Hackathon 2026** (November 22–30, 2026).

An Arabic-first (RTL) web application where families share one household shopping and errands list without accounts or passwords. Its signature feature lets you paste messy WhatsApp messages and uses AI (with a rule-based fallback) to extract a clean, categorized list ready for confirmation.

## Local Setup

```bash
cd backend && uv sync --extra dev
cp ../.env.example ../.env
cd backend && uv run uvicorn app.main:app --reload
```

Open `http://localhost:8000` in your browser, and `http://localhost:8000/api/v1/healthz` to verify the API health check.
