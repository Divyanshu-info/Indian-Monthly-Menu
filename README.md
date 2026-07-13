# 🍛 Indian Monthly Menu

A responsive FastAPI + SQLite web app for planning Indian meals on a monthly calendar. Bilingual (English + Hindi), dark mode, auto-fill weeks by season, shopping lists scaled to household size, a **481-recipe** library, an AI recipe assistant, JSON backup, and A4 PDF / browser print export.

## Features

- **Monthly calendar** (Mon–Sun) with Breakfast / Lunch / Dinner / Dessert slots per day
- **Auto-fill week** — season-aware, variety-guaranteed, weekend-special priority (chicken kept to weekends), with overwrite confirmation
- **Recipe Library** — **481 bilingual recipes**; searchable/filterable card grid; add/edit/delete custom recipes
- **Bilingual** recipes (English + Hindi names, Devanagari font) with on-demand translation to Hindi/Tamil/Telugu/Bengali/Marathi (LLM-backed, DB-cached)
- **AI Recipe Assistant** — floating chat (EN/HI auto-detect), grounded on your catalogue and week; uses **MCP tools** (sqlite-db + Spoonacular) as function-calls when an LLM key is set
- **Seasonal sidebar** — in-season vegetables & fruits for the current month
- **Shopping list drawer** — combined, deduplicated, scaled by household size
- **Swap** — pick-an-alternative panel for any planned meal (respects the weekday no-chicken rule)
- **Mobile "Today"** — tapping Today scrolls the viewport to the current date card
- **Dark / light mode** toggle (Indian spice palette)
- **Export** — JSON backup, A4 PDF (WeasyPrint), and browser print
- **Delete-safety** — recipes in use cannot be deleted until slots are cleared

## Setup

```bash
# From the project root
uv sync                      # or: uv pip install -e .
```

If `uv` is not available, use pip:

```bash
python -m venv .venv
.venv\Scripts\activate       # Windows
pip install fastapi "uvicorn[standard]" sqlalchemy jinja2 weasyprint \
            openai google-genai httpx python-dotenv mcp truststore
```

> **Note (Windows):** `weasyprint` needs the GTK runtime for PDF export. If GTK
> is not installed, the app still runs — the **PDF** button returns a helpful
> message and you can use the **Print** button (browser print) instead.

## Run

```bash
uv run uvicorn main:app --reload --port 8000
# or
python main.py
```

Open http://localhost:8000

The database (`menu.db`) is auto-created and **idempotently seeded with 481 recipes** on first launch (and any newly added recipes are merged on later startups without touching your data).

## Configuration

- **Household size** — set from the Shopping List drawer (top of the panel). Ingredient
  quantities scale from each recipe's default serving count. Stored in `AppSetting`.

### AI chat & translation (optional)

Create a `.env` file in the project root. Without keys, the chat and translation
features degrade gracefully (clear message, no crash).

```env
# Provider selection: "gemini" or "openai" (falls back to whichever key exists)
LLM_PROVIDER=gemini

# Google Gemini
GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-2.5-flash-lite

# OpenAI (alternative)
# OPENAI_API_KEY=your_openai_key
# OPENAI_MODEL=gpt-4o-mini

# Spoonacular — used by the chat backend as an MCP tool for external recipes/nutrition
SPOONACULAR_API_KEY=your_spoonacular_key
```

**How chat tools work:** the backend acts as an **MCP client** (`mcp_client.py`),
spawning the `sqlite-db` and `spoonacular` MCP servers on demand and exposing their
tools to the LLM as function-calls. If they are unavailable it falls back to
DB-grounded streaming. `truststore` is injected at startup so HTTPS works behind
corporate TLS-inspection proxies (fixes `CERTIFICATE_VERIFY_FAILED`).

## Project structure

| File | Purpose |
|---|---|
| `main.py` | FastAPI app, startup seeding, static/route wiring |
| `database.py` | SQLAlchemy engine + session |
| `models.py` | ORM: `Recipe`, `MenuEntry`, `AppSetting` |
| `schemas.py` | Pydantic request/response models |
| `seed_data.py` | Base recipes; merges `seed_data_extra.py` with name dedup |
| `seed_data_extra.py` | ~281 additional bilingual recipes (fast food, continental, chaat, regional) |
| `seasonal_data.py` | Month → season, vegetables, fruits |
| `autofill.py` | Week auto-fill algorithm |
| `llm.py` | Pluggable OpenAI + Gemini provider (chat + translate) |
| `mcp_client.py` | MCP client — spawns Spoonacular + sqlite-db servers, exposes tools to the LLM |
| `routers/` | recipes, menu_entries, settings, export, translate, chat |
| `templates/print_menu.html` | Jinja2 → WeasyPrint A4 PDF |
| `static/` | `index.html` (calendar) + `library.html` + `chat.js` + JS |
