# 🍛 Indian Monthly Menu

A responsive FastAPI + SQLite web app for planning Indian meals on a monthly calendar. Bilingual (English + Hindi), dark mode, auto-fill weeks by season, shopping lists scaled to household size, a recipe library, JSON backup, and A4 PDF / browser print export.

## Features

- **Monthly calendar** (Mon–Sun) with Breakfast / Lunch / Dinner / Dessert slots per day
- **Auto-fill week** — season-aware, variety-guaranteed, weekend-special priority (with overwrite confirmation)
- **Recipe Library** — searchable/filterable card grid; add/edit/delete custom recipes
- **Bilingual** recipes (English + Hindi names, Devanagari font)
- **Seasonal sidebar** — in-season vegetables & fruits for the current month
- **Shopping list drawer** — combined, deduplicated, scaled by household size
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
pip install fastapi "uvicorn[standard]" sqlalchemy jinja2 weasyprint
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

The database (`menu.db`) is created and seeded with ~35 recipes on first launch.

## Configuration

- **Household size** — set from the Shopping List drawer (top of the panel). Ingredient
  quantities scale from each recipe's default serving count. Stored in `AppSetting`.

## Project structure

| File | Purpose |
|---|---|
| `main.py` | FastAPI app, startup seeding, static/route wiring |
| `database.py` | SQLAlchemy engine + session |
| `models.py` | ORM: `Recipe`, `MenuEntry`, `AppSetting` |
| `schemas.py` | Pydantic request/response models |
| `seed_data.py` | ~35 seeded recipes |
| `seasonal_data.py` | Month → season, vegetables, fruits |
| `autofill.py` | Week auto-fill algorithm |
| `routers/` | recipes, menu_entries, settings, export |
| `templates/print_menu.html` | Jinja2 → WeasyPrint A4 PDF |
| `static/` | `index.html` (calendar) + `library.html` + JS |
