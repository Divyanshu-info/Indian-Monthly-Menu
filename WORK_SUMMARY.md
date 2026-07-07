
# Work Summary: Indian Monthly Menu Web App

**Project:** Indian Monthly Menu  
**Stack:** Python 3.13 · FastAPI · SQLAlchemy · SQLite · Jinja2 · WeasyPrint · OpenAI + Gemini (LLM) · Vanilla JS · TailwindCSS · Lucide Icons  
**Server:** `http://127.0.0.1:8010`  
**Last Updated:** 2026-07-06 (v3)  

---

## 1. Objective

Build a fully functional, bilingual (English + Hindi) Indian meal planner web app with:
- A **monthly calendar** (Mon–Sun) with 4 meal slots per day (Breakfast / Lunch / Dinner / Dessert)
- **Season-aware auto-fill** for a week at a time
- A **recipe library** with full CRUD and delete-safety
- **Shopping list** scaled by household size
- **Export** to A4 PDF (WeasyPrint) and browser print
- **JSON backup** of all data
- **Dark / light mode** with an Indian spice colour palette

---

## 2. Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.13 |
| Web framework | FastAPI 0.139 |
| ORM | SQLAlchemy 2.0 |
| Database | SQLite (`menu.db`) |
| Validation | Pydantic v2 |
| Templating | Jinja2 3.1 |
| PDF export | WeasyPrint 69 (GTK required on Windows) |
| AI / LLM | OpenAI + Google Gemini (pluggable via `llm.py`, env-selected) |
| Translation | LLM-backed, DB-cached (`translations` table) |
| Frontend framework | None — vanilla JS ES2023+ |
| CSS | TailwindCSS CDN (dark-mode class strategy) |
| Icons | Lucide (CDN) |
| Fonts | Inter + Noto Sans Devanagari (Google Fonts) |
| ASGI server | Uvicorn |
| Package manager | uv |
| UI testing | Playwright MCP |
| Research | Web search + SerpAPI MCP |

---

## 3. File Structure

```
Menu/
├── main.py                   # FastAPI app entry, DB init, router wiring, static mount
├── database.py               # SQLAlchemy engine, SessionLocal, get_db dependency
├── models.py                 # ORM: Recipe, MenuEntry, AppSetting
├── schemas.py                # Pydantic request/response models
├── seed_data.py              # 200 seeded recipes (full metadata, bilingual)
├── seasonal_data.py          # Month → season + in-season vegetables + fruits
├── autofill.py               # Week auto-fill algorithm
├── llm.py                    # Pluggable OpenAI + Gemini provider (chat + translate)
├── .env.example              # Template for LLM_PROVIDER / API keys (.env is git-ignored)
├── pyproject.toml            # Project metadata + dependencies
├── menu.db                   # SQLite database (auto-created on first run)
├── routers/
│   ├── __init__.py
│   ├── recipes.py            # Recipe CRUD + delete-safety (with swap support)
│   ├── menu_entries.py       # Calendar entries CRUD + auto-fill endpoints (chicken-weekday rule)
│   ├── settings.py           # App settings (household_size) + seasonal info
│   ├── export.py             # Shopping list, PDF, browser print, JSON backup
│   ├── translate.py          # LLM translation of recipe fields + text (cached)
│   └── chat.py               # Grounded AI chat over SSE (recipes/calendar/shopping)
├── templates/
│   └── print_menu.html       # Jinja2 → WeasyPrint A4 / browser print template
└── static/
    ├── index.html            # Calendar SPA shell (Today badge, Swap chooser, language select)
    ├── app.js                # Calendar SPA logic (Swap chooser, translation, a11y, loader)
    ├── library.html          # Recipe Library shell (Veg/Non-Veg filters)
    ├── lib.js                # Recipe Library logic (debounced search, result count)
    └── chat.js               # Floating AI chat widget (SSE, EN/HI), shared by both pages
```

---

## 4. Database Models

### `recipes`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `name` | String | English name |
| `name_hindi` | String | Devanagari name |
| `meal_type` | String indexed | breakfast / lunch / dinner / dessert / beverage |
| `description` | Text | |
| `ingredients` | Text | Newline-separated, `qty unit item` format |
| `instructions` | Text | Numbered steps, newline-separated |
| `season` | String | Winter / Summer / Monsoon / All |
| `region` | String | e.g. North, South, Pan-Indian |
| `spice_level` | String | Mild / Medium / Spicy |
| `servings` | Integer | Default 4 |
| `accompaniment` | Text | |
| `suggested_beverage` | Text | |
| `suggested_sides` | Text | |
| `tags` | Text | Comma-separated: Festive, Kids Friendly, Quick, High Protein, Vegetarian, Non-Veg |
| `is_weekend_special` | Boolean | Prioritised in auto-fill on Sat/Sun |
| `is_custom` | Boolean | True for user-created recipes |

### `menu_entries`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `year` | Integer indexed | |
| `month` | Integer indexed | |
| `day` | Integer | |
| `meal_type` | String | |
| `recipe_id` | Integer FK → recipes | |
| Unique constraint | `(year, month, day, meal_type)` | One recipe per meal slot |

### `app_settings`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `key` | String unique | e.g. `household_size` |
| `value` | String | |

### `translations` (v3)
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `recipe_id` | Integer FK → recipes | indexed |
| `lang` | String | Hindi / Tamil / Telugu / Bengali / Marathi |
| `field` | String | name / description / ingredients / instructions / accompaniment / suggested_sides |
| `text` | Text | cached translated value |
| Unique constraint | `(recipe_id, lang, field)` | one cached value per field/lang |

---

## 5. API Endpoints

### Recipes — `/api/recipes`
| Method | Path | Description |
|---|---|---|
| GET | `/api/recipes` | List with filters: `meal_type`, `season`, `region`, `spice`, `tags`, `q` (bilingual search) |
| POST | `/api/recipes` | Create custom recipe (`is_custom=True`) |
| GET | `/api/recipes/{id}` | Get single recipe |
| PUT | `/api/recipes/{id}` | Partial update (Pydantic `exclude_unset`) |
| DELETE | `/api/recipes/{id}` | Delete — blocked with HTTP 409 if in use |
| GET | `/api/recipes/{id}/used-on` | List calendar days using this recipe |
| GET | `/api/recipes/{id}/alternatives` | Same-meal-type swap candidates (optional `year/month/day`; weekday-no-chicken rule) |

### Menu Entries — `/api/menu`
| Method | Path | Description |
|---|---|---|
| GET | `/api/menu/{year}/{month}` | All entries for a month (includes adjacent month data) |
| POST | `/api/menu/entry` | Assign recipe to slot — upserts if slot occupied |
| DELETE | `/api/menu/entry/{id}` | Remove from calendar |
| GET | `/api/menu/autofill/{year}/{week}/check` | Check if week already has entries |
| POST | `/api/menu/autofill/{year}/{week}` | Run auto-fill algorithm |

### Settings & Seasonal — `/api`
| Method | Path | Description |
|---|---|---|
| GET | `/api/settings` | List all settings |
| PUT | `/api/settings/{key}` | Update a setting |
| GET | `/api/seasonal/{month}` | Season name + vegetables + fruits for month |

### Export — `/api/export`
| Method | Path | Description |
|---|---|---|
| GET | `/api/export/shopping-list/{year}/{week}` | Scaled, deduplicated ingredient list |
| GET | `/api/export/pdf/{year}/{week}` | A4 PDF (requires GTK; 501 otherwise) |
| GET | `/api/export/print/{year}/{week}` | HTML for browser print (always works) |
| GET | `/api/export/json` | Full JSON backup of recipes + entries |

### Translation — `/api/translate` (v3)
| Method | Path | Description |
|---|---|---|
| GET | `/api/translate/languages` | Supported languages + active provider |
| POST | `/api/translate/recipe/{id}?lang=` | Translate recipe fields (cache-first); 501 if no key |
| POST | `/api/translate/text` | Translate a list of free-text lines (e.g. shopping items) |

### AI Chat — `/api/chat` (v3)
| Method | Path | Description |
|---|---|---|
| GET | `/api/chat/status` | Whether an LLM key is configured + which provider |
| POST | `/api/chat` | SSE stream; grounded on recipe catalogue + week menu/shopping; EN/HI auto-reply |

---

## 6. Key Algorithms

### Auto-fill (`autofill.py → autofill_week`)
```
1. Resolve ISO week → 7 dates (Mon–Sun)
2. Determine season from mid-week month
3. Clear all existing entries for those 7 days
4. For each meal type:
   a. Query all recipes of that type
   b. Filter to season-compatible pool (season == current OR "All")
   c. Split pools:
      - weekday_pool: excludes is_weekend_special AND excludes chicken (is_chicken check)
      - weekend_pool: includes is_weekend_special OR is_chicken
   d. For each day:
      - Weekends → pick from weekend_pool
      - Weekdays → pick from weekday_pool (no chicken ever on weekdays)
      - Dessert on weekdays is randomly skipped 50% of the time
      - Variety enforced: track used_ids, pick fresh recipe first
5. Bulk-insert and commit; return count created
```

`is_chicken(recipe)` — returns True if "chicken" appears in recipe name or tags (case-insensitive).


### Shopping List Scaling (`export.py → _build_shopping_list`)
```
1. Load household_size from AppSetting
2. Fetch all MenuEntry rows for the week with eager-loaded Recipe
3. For each ingredient line per recipe:
   - Parse with regex: r"^(\d+(?:\.\d+)?)\s*([a-zA-Z]*)\s+(.*)$"
   - Scale qty by (household_size / recipe.servings)
   - Aggregate by (ingredient_name_lower, unit) key
4. Append unstructured lines (e.g. "Salt to taste") deduped
5. Sort alphabetically, return list of strings
```

### Delete Safety (`recipes.py → delete_recipe`)
```
1. Query MenuEntry WHERE recipe_id = target
2. If any entries found → raise HTTP 409 with list of "Day (meal)" strings
3. Frontend shows "Cannot Delete" modal with the blocking days
4. Only proceeds with DELETE if no entries reference the recipe
```

---

## 7. Seed Data

**200 recipes** seeded idempotently on startup (`init_db` adds any missing names without touching existing data or calendar entries):

| Meal Type | Count (v3) | Notable dishes |
|---|---|---|
| Breakfast | 40 | Idli, Dosa, Uttapam, Medu Vada, Upma, Poha, Thepla, Khaman Dhokla, Misal Pav, Vada Pav, Sattu/Gobi/Mooli Paratha, Appam, Idiyappam, Sabudana Khichdi |
| Lunch | 55 | Sambar, Rasam, Bisi Bele Bath, regional rice (Lemon/Curd/Tamarind/Vangi/Tomato/Coconut), Veg Biryani, Shahi/Kadai Paneer, Malai Kofta, dals, Sarson ka Saag, Undhiyu, Mutton Rogan Josh ⭐, Chicken Chettinad ⭐, Goan Fish Curry ⭐ |
| Dinner | 50 | Dal Bukhara, Paneer Lababdar/Do Pyaza/Tikka Masala, Chilli Paneer, Bharwa Baingan, Navratan Korma, Veg/Gobi Manchurian, Hakka Noodles, Fried Rice, Chicken Korma ⭐, Chilli Chicken ⭐, Prawn Masala ⭐ |
| Dessert | 30 | Rasmalai ⭐, ladoos (Coconut/Boondi/Motichoor), Malpua, Gujiya, Modak, Sandesh, Mysore Pak, Kalakand, Rabri, Kulfi, Doodh Peda |
| Beverage | 25 | Mango/Rose Lassi, Thandai, Badam Milk, Sattu/Bel/Kokum Sharbat, Sol Kadhi, Sugarcane Juice, Kashmiri Kahwa, Cold Coffee, Ragi Malt, Piyush |
| **Total** | **200** | Verified via sqlite-db MCP — 0 missing Hindi names, 0 duplicate names |

⭐ = Weekend Special. Chicken dishes marked weekend-only so autofill never places them on weekdays.

Each recipe includes: English name, Hindi name, meal type, season, region, spice level, servings, description, ingredients (with quantities for scaling), step-by-step instructions, accompaniment, suggested beverage, suggested sides, and comma-separated tags.

---

## 8. Seasonal Data

Sourced via web research + SerpAPI on Indian Rabi/Kharif/Zaid agricultural cycles:

| Month(s) | Season | Key Vegetables | Key Fruits |
|---|---|---|---|
| Nov–Feb | Winter (Rabi) | Spinach, Methi, Cauliflower, Peas, Carrot, Radish | Orange, Guava, Grapes, Strawberry |
| Mar–Jun | Summer (Zaid) | Lauki, Karela, Bhindi, Tinda, Turai | Mango, Watermelon, Litchi, Papaya |
| Jul–Oct | Monsoon (Kharif) | Bhindi, Arbi, Corn, Ginger, Palak | Jamun, Pomegranate, Pear, Banana |

---

## 9. Frontend Architecture

### Calendar SPA (`index.html` + `app.js`)
- **State object:** `{ year, month, recipes, entries, pick, household }`
- **Render cycle:** `loadEntries()` → `loadSeasonal()` → `render()` (full re-render on each navigation)
- **Calendar grid:** 5–6 week rows, Mon–Sun columns; cells show bilingual meal chips
- **Chip colours:** Breakfast=green, Lunch=amber, Dinner=red, Dessert=purple
- **Weekend cells:** Gold border ring; **Today cell:** 3px accent ring + accent-tinted background + "Today" pill badge
- **Modals:** Recipe Picker (with live search + filters), Recipe View (badges + tabs + Swap button), Confirm dialog, Shopping Drawer
- **Swap feature:** In Recipe View modal, the **Swap** button picks a random alternative recipe of the same meal type, respects the weekday no-chicken rule, upserts the slot, and re-opens the modal showing the new recipe
- **Per-week actions:** Auto-Fill, Shopping, PDF, Print

### Recipe Library (`library.html` + `lib.js`)
- **Meal tabs:** all / breakfast / lunch / dinner / dessert / beverage
- **Filters:** Region, Season, Spice Level, Tags (all combinable; includes Vegetarian 🥬 and Non-Veg 🍗)
- **Search:** real-time, matches English and Hindi name
- **Cards:** show name, Hindi name, edit/delete buttons, all metadata badges, tags, description
- **Add/Edit modal:** 2-column grid form; tag checkboxes (incl. Vegetarian, Non-Veg); full Pydantic-validated POST/PUT
- **Delete:** browser confirm → API DELETE → 409 shows "Cannot Delete" modal with blocking days

### Dark Mode
- CSS custom properties on `:root` / `html.dark`; toggled via `document.documentElement.classList`
- Persisted to `localStorage` key `menu-theme`
- Indian spice palette: warm amber/orange accents, brown tones

---

## 10. Export Features

| Feature | How | Notes |
|---|---|---|
| Shopping List | GET `/api/export/shopping-list/{y}/{w}` | Scaled to household size, alphabetically sorted, checkbox UI |
| A4 PDF | GET `/api/export/pdf/{y}/{w}` | WeasyPrint + GTK; graceful HTTP 501 on Windows without GTK |
| Browser Print | GET `/api/export/print/{y}/{w}` | Jinja2 HTML with `@page` A4 CSS; always works |
| JSON Backup | GET `/api/export/json` | All recipes + all entries, `exported_at` timestamp |

---

## 11. New Features (v3)

### Swap → Pick-an-Alternative
- The **Swap** button in the Recipe View modal now opens an **inline panel** listing same-meal-type alternatives (respecting the weekday-no-chicken rule) instead of swapping randomly.
- Each row shows name, Hindi name, region and spice; clicking one performs the swap.
- A **Random** shortcut inside the panel keeps the old one-click behaviour.
- Backend: `GET /api/recipes/{id}/alternatives`.

### Recipe Translation
- Language dropdown in the Recipe View modal: **English, Hindi, Tamil, Telugu, Bengali, Marathi**.
- Translates name, description, ingredients, instructions, accompaniment and sides via the LLM, **cached** in the `translations` table for reuse.
- Backend: `routers/translate.py`; degrades to HTTP 501 with a clear message when no key is set.

### AI Chat (EN + HI)
- Floating **Recipe Assistant** widget (`static/chat.js`) on both the Calendar and Library pages.
- **SSE streaming** responses; **auto-detects** the user's language (English/Hindi) and replies in kind.
- **Grounded** on the app's own recipe catalogue plus the current ISO week's menu and shopping list.
- Dual provider via `llm.py` — set `LLM_PROVIDER` and `OPENAI_API_KEY` / `GEMINI_API_KEY` in `.env`.

### 200+ Recipe Library
- Expanded from 70 → **200 recipes**, all bilingual (English + Hindi), authored from web + Spoonacular research.
- Distribution: **breakfast 40, lunch 55, dinner 50, dessert 30, beverage 25** (verified with the sqlite-db MCP; 0 missing Hindi names, 0 duplicates).
- Broad regional coverage (North/South/East/West/Pan-Indian) plus Indo-Chinese; chicken/mutton/fish kept as weekend specials.

### Accessibility & Usability polish
- ARIA roles/labels on modals and icon buttons, focus management, skip links, `prefers-reduced-motion`, larger touch targets, loading spinner, debounced search, and result counts.

## 12. Changelog

### v3 — 2026-07-06

| Area | Change |
|---|---|
| **Recipes** | Library expanded 70 → **200** bilingual dishes (idli/dosa/thepla/dhokla, regional rice, dals, paneer, Indo-Chinese, chaats, mithai, sharbats) |
| **Swap** | Swap button now shows a **pick-an-alternative** panel (with a Random shortcut); new `/alternatives` endpoint |
| **Translation** | New `translations` table + `/api/translate/*`; recipe view language dropdown (Hindi + 4 regional) with DB caching |
| **AI Chat** | New floating assistant (`chat.js`) + `/api/chat` SSE; grounded on recipes/week/shopping; EN/HI auto-detect |
| **LLM layer** | New `llm.py` supporting **both OpenAI and Gemini**, env-selected with fallback; `.env.example` added, `.env` git-ignored |
| **Deps** | Added `openai`, `google-genai`, `httpx`, `python-dotenv` |
| **A11y/UX** | ARIA dialogs, focus management, skip links, reduced-motion, loading spinner, debounced search, result counts |
| **Tools used** | web search + Spoonacular MCP (dish research), sqlite-db MCP (count/verification) |

### v2 — 2026-07-06

| Area | Change |
|---|---|
| **Recipes** | Library expanded 35 → **70 recipes** (North Indian veg, pasta, macaroni, sweet potato, chicken variety, desserts) |
| **Chicken rule** | Autofill now **excludes chicken on weekdays**; chicken dishes only appear Sat/Sun. `is_chicken()` uses name + tag detection |
| **Chicken variety** | Added 6 chicken weekend specials: Butter Chicken, Chicken Changezi, Tikka Masala, Kadai Chicken, Biryani, Tandoori |
| **Today highlight** | Today cell upgraded: 3px accent ring + accent-tint background + **"Today" pill badge** (replaces weekday abbrev) |
| **Swap feature** | New **Swap button** in Recipe View modal — one-click swap to a random same-meal-type alternative, respects chicken rule |
| **Veg/Non-Veg tags** | Added `Vegetarian` 🥬 and `Non-Veg` 🍗 tags; exposed in picker, library filter, add-recipe form, and view badges |
| **Idempotent seed** | `init_db()` now adds missing recipes on every startup without wiping existing data or calendar entries |
| **Tools used** | Spoonacular MCP (recipe research), sqlite-db MCP (verification), SerpAPI/web search (Chicken Changezi research) |

---

## 12. Testing (Playwright MCP)

All tests performed against `http://127.0.0.1:8010`:

| Test | Result |
|---|---|
| Page load + seasonal sidebar (July = Monsoon) | ✅ Correct vegetables and fruits displayed |
| Auto-fill Week 27 | ✅ 20+ meals created; weekends got weekend-special dishes |
| Bilingual chips (English + Devanagari) | ✅ Both names rendered correctly |
| Recipe View modal — Ingredients tab | ✅ All 9 ingredients listed for Egg Paratha |
| Recipe View modal — Instructions tab | ✅ 5 steps displayed correctly |
| Shopping list drawer | ✅ Aggregated, household-scaled list opened |
| Add custom recipe via Library | ✅ Persisted as `is_custom=True` in SQLite |
| Delete safety (recipe in use) | ✅ HTTP 409 → "Cannot Delete" modal with "Mon Jun 29 (breakfast)" |
| JSON backup | ✅ HTTP 200, file download triggered |
| PDF export (no GTK) | ✅ HTTP 501 with descriptive fallback message |
| Dark mode toggle | ✅ `html.dark` class toggled; `localStorage` updated |
| **v2** Recipe library shows 70 recipes | ✅ Verified via Playwright evaluate |
| **v2** Butter Chicken, Pasta, Shakarkandi in library | ✅ All found by name |
| **v2** Today cell: badge + tinted background | ✅ 1 `today-cell`, `today-badge` renders "Today" |
| **v2** Swap feature | ✅ Breakfast swapped Lentil & Egg Chila → Paneer Paratha |
| **v2** Weekday autofill pool: zero chicken | ✅ 7 non-chicken lunch options confirmed in Python |

Only error observed: `favicon.ico` 404 (cosmetic, no impact).

---

## 13. Known Limitations / Future Improvements

- **PDF on Windows:** WeasyPrint requires the GTK3 runtime (`libgobject-2.0-0`). Until installed, use the **Print** button (browser `@media print`).
- **No authentication:** Single-user local app; no login/session required.
- **Recipe import:** No bulk CSV/JSON import UI yet — can be done via the JSON restore endpoint if implemented.
- **Beverage slot:** Beverages exist in the library but do not have a dedicated calendar slot (could be added as a 5th meal type).
- **Month boundary weeks:** Adjacent month data is fetched to handle weeks that span two months, but the calendar only renders the current month's days prominently.

---

## 14. How to Run

```bash
# Install dependencies
uv sync

# (Optional) enable AI chat + translation: copy .env.example to .env and add a key
#   LLM_PROVIDER=openai            # or: gemini
#   OPENAI_API_KEY=...  and/or  GEMINI_API_KEY=...
# Without a key, chat/translation degrade gracefully (clear message, no crash).

# Start server
uv run uvicorn main:app --reload --port 8010

# Open browser
http://127.0.0.1:8010          # Calendar
http://127.0.0.1:8010/library  # Recipe Library
http://127.0.0.1:8010/docs     # FastAPI Swagger UI
```

The database (`menu.db`) is **auto-created** on first launch and **idempotently seeded** — new recipes from `seed_data.py` are added on every startup without touching existing data. Currently **200 recipes** are seeded. The `translations` table is created automatically. No migrations needed.
