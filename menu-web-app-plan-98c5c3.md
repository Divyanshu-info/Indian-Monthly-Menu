# Indian Food Menu Web App — Calendar View

A fully responsive browser-based FastAPI + SQLite web app with a monthly calendar view (Mon–Sun, dark mode, Recipe Library page, seasonal sidebar), auto-fill week generation, clickable recipe expansion, shopping list scaled to household size, JSON backup export, server-side A4 PDF download, and block-on-delete safety — all integrated with the existing monthly Indian menu plan.

---

## All Refinements (Q&A — 36 total)

### App & UX (Q1–25)
| # | Question | Answer |
|---|---|---|
| 1 | Meal assignment | **Auto-fill entire week** — 1 click fills all meal slots by season + variety; user can edit |
| 2 | Shopping list | **Yes — simple combined list** of all ingredients from the week's recipes |
| 3 | Serving size | **Fixed serving count** per recipe (e.g. "Serves 4"), shown on recipe card |
| 4 | Print / Export | **Both** — `window.print()` browser print AND server-generated A4 PDF (WeasyPrint) |
| 5 | Seasonal display | **Collapsible sidebar panel** — in-season vegetables + fruits for the current month |
| 6 | Auth | **Single user — no login** |
| 7 | Language | ~~English only~~ → **Bilingual: English + Hindi** (updated) |
| 8 | Dark mode | **Yes — toggle in header** (light warm cream ↔ dark charcoal theme) |
| 9 | Food photos | **No — text-only recipes** |
| 10 | Time fields | **No — skip prep/cook time** |
| 11 | Week start | **Monday → Sunday** |
| 12 | Day notes | **No — no notes on calendar entries** |
| 13 | Favourites | **No** |
| 14 | Veg-only days | **No** |
| 15 | Recipe search | **Yes — full search + filters** (name + meal type + season + tags) in recipe picker |
| 16 | Auto-fill overwrite | **Warn before overwriting** — confirmation dialog before replacing existing meals |
| 17 | PDF paper size | **A4** |
| 18 | Data backup | **Yes — export as JSON** (all recipes + menu entries downloadable) |
| 19 | Nutrition | **No** |
| 20 | Shopping list scaling | **Yes — global household size setting** (quantities scale from default serving) |
| 21 | Recipe Library | **Yes — separate page** with recipe cards grid grouped by meal type |
| 22 | Delete recipe safety | **Block deletion** — show which calendar days currently use that recipe |
| 23 | Today button | **Yes** — jumps to current month and highlights today's cell |
| 24 | Copy week | **No** |
| 25 | Responsive | **Yes — fully responsive** (phone + tablet + desktop) |

### Food Menu Content (Q26–36)
| # | Question | Answer |
|---|---|---|
| 26 | Hindi names | **Yes — bilingual** — each recipe shows English name + Hindi name (e.g. Egg Paratha / अंडा पराठा) |
| 27 | Regional style | **Pan-Indian — all regions** (North, South, Bengali, Gujarati, Maharashtrian etc.) |
| 28 | Spice level | **Variable per dish** — each recipe has its authentic spice level, stored as a field |
| 29 | Accompaniment | **Yes — per meal** (e.g. Chicken Saag + Roti + Rice), shown on calendar chip + recipe card |
| 30 | Dessert slot | **Yes — optional 4th slot per day** (Kheer, Halwa, Rasgulla etc.) |
| 31 | Beverage | **Yes — suggested beverage per meal** (text field on recipe, shown in recipe modal) |
| 32 | Fasting days | **No — regular menu only** |
| 33 | Weekend meals | **Yes — weekends get elaborate/special dishes** (auto-fill priority by `is_weekend_special` flag) |
| 34 | Recipe expansion | **Add both Desserts (8) + Beverages (8)** — total ~35 seeded recipes |
| 35 | Side dish | **Yes — `suggested_sides` field per recipe** (e.g. "Boondi Raita, Mango Pickle"), shown on card |
| 36 | Recipe tags | **Yes — occasion tags** (🎉 Festive, 👨‍👩‍👧 Kids Friendly, ⚡ Quick, 💪 High Protein) — shown as badges, filterable |

---

## Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| **Backend** | FastAPI (Python) | Existing Python project, fast API, auto-docs |
| **Database** | SQLite via SQLAlchemy | Zero config, file-based, no server needed |
| **PDF Export** | WeasyPrint | Server-side PDF from HTML template |
| **Frontend** | Single `index.html` (Vanilla JS + TailwindCSS CDN) | No build step, runs in browser immediately |
| **Styling** | TailwindCSS CDN + custom CSS tokens | Rapid UI, responsive, no build needed |
| **Icons** | Lucide (CDN) | Lightweight, clean icon set |

---

## Design System (Indian Spice Palette — 60-30-10)

### Light Mode
- **60% Dominant**: Warm cream `#FFFBF5` — page background, card backgrounds
- **30% Secondary**: Saffron-light `#FEF3C7` — nav bar, sidebar, week row headers
- **10% Accent**: Saffron orange `#F97316` — CTAs, today highlight, active states

### Dark Mode (toggle in header)
- **Background**: Deep charcoal `#1C1008` — main page background
- **Cards**: Dark brown `#2C1A0E` — calendar cells, recipe cards
- **Accent**: Muted saffron `#C2580A` — CTAs in dark (reduced saturation)
- Text in dark mode: `#E8D5B0` (warm off-white, not pure white)

### Semantic Color Coding (both modes)
- 🌅 **Breakfast**: Green `#166534` (light) / `#4ADE80` (dark)
- ☀️ **Lunch**: Amber `#D97706` (light) / `#FCD34D` (dark)
- 🌙 **Dinner**: Crimson `#DC2626` (light) / `#F87171` (dark)

### Typography
- Font: **Inter** (Google Fonts CDN) — sans-serif, clean
- Scale: 28px h1 → 20px h2 → 16px body → 12px caption
- Print font: **Georgia** serif for PDF/print output

---

## File Structure

```
c:\Users\1000305366\Documents\Personal\Menu\
├── main.py              ← FastAPI app (updated)
├── database.py          ← SQLite + SQLAlchemy engine, session
├── models.py            ← ORM: Recipe, MenuEntry, AppSetting
├── schemas.py           ← Pydantic request/response models
├── seed_data.py         ← 19 hardcoded recipes from menu plan
├── seasonal_data.py     ← Month → {season, vegetables, fruits}
├── autofill.py          ← Week auto-fill algorithm (season + variety)
├── routers/
│   ├── __init__.py
│   ├── recipes.py       ← CRUD recipes + delete-safety check
│   ├── menu_entries.py  ← CRUD entries + auto-fill + confirmation
│   ├── settings.py      ← GET/PUT household size setting
│   └── export.py        ← PDF (A4) + JSON backup + shopping list
├── templates/
│   └── print_menu.html  ← Jinja2 HTML → WeasyPrint A4 PDF
├── static/
│   ├── index.html       ← Page 1: Calendar view (SPA)
│   └── library.html     ← Page 2: Recipe Library (cards grid)
├── pyproject.toml       ← fastapi, uvicorn, sqlalchemy, weasyprint, jinja2
└── README.md            ← Run instructions + household size setup
```

---

## Database Models

### `Recipe`
| Field | Type | Notes |
|---|---|---|
| id | Integer PK | auto |
| name | String | English name, e.g. "Chicken Saag" |
| name_hindi | String | Hindi name, e.g. "चिकन साग" (shown below English name) |
| meal_type | Enum | breakfast / lunch / dinner / **dessert** |
| description | Text | one-line summary |
| ingredients | Text | newline-separated (quantities per default servings) |
| instructions | Text | numbered step-by-step |
| season | String | Winter / Summer / Monsoon / All |
| region | String | North / South / East / West / Pan-Indian |
| spice_level | String | Mild / Medium / Spicy (authentic per dish) |
| servings | Integer | default serving count, e.g. 4 |
| accompaniment | Text | e.g. "Serve with Roti or Jeera Rice" |
| suggested_beverage | Text | e.g. "Masala Chai" / "Lassi" |
| suggested_sides | Text | e.g. "Boondi Raita, Mango Pickle" |
| tags | Text | comma-separated: "Festive,High Protein,Quick" |
| is_weekend_special | Boolean | true = auto-fill prefers this for Sat/Sun |
| is_custom | Boolean | false = seeded, true = user-added |

### `MenuEntry`
| Field | Type | Notes |
|---|---|---|
| id | Integer PK | auto |
| year | Integer | e.g. 2026 |
| month | Integer | 1–12 |
| day | Integer | 1–31 |
| meal_type | Enum | breakfast / lunch / dinner / **dessert** |
| recipe_id | Integer FK → Recipe | |

### `AppSetting`
| Field | Type | Notes |
|---|---|---|
| id | Integer PK | auto |
| key | String unique | e.g. "household_size" |
| value | String | stored as string, cast on read |

---

## API Endpoints

```
# Recipes
GET    /api/recipes                            → list all (filter: ?meal_type=&season=&q=&tags=&region=&spice=)
POST   /api/recipes                            → create recipe
PUT    /api/recipes/{id}                       → update recipe
DELETE /api/recipes/{id}                       → delete — returns 409 + day list if in use
GET    /api/recipes/{id}/used-on              → days where recipe is assigned

# Menu Calendar
GET    /api/menu/{year}/{month}                → full month entries (array)
POST   /api/menu/entry                         → assign recipe to a day/meal
DELETE /api/menu/entry/{id}                   → remove a single assignment
GET    /api/menu/autofill/{year}/{week}/check → returns True if week has existing meals
POST   /api/menu/autofill/{year}/{week}       → auto-fill 28 slots (21 meals + up to 7 dessert slots)

# Shopping List
GET    /api/shopping-list/{year}/{week}       → scaled ingredient list (uses household_size)

# Export
GET    /api/export/pdf/{year}/{week}          → A4 PDF download (WeasyPrint)
GET    /api/export/json                        → full JSON backup (recipes + all menu entries)

# Seasonal & Settings
GET    /api/seasonal/{month}                   → {season, vegetables, fruits}
GET    /api/settings                           → all settings (incl. household_size)
PUT    /api/settings/{key}                     → update a setting value
```

---

## Frontend UI — Pages & Screens

### Page 1: Calendar (`index.html`)

#### Header Bar
- 🍛 Logo + **"Indian Monthly Menu"** title (left)
- `← Prev` | **Month Year** | `Next →` month navigation (centre)
- `📅 Today` button — jumps to current month, highlights today
- `🌙 / ☀️` dark-mode toggle (right)
- `� Recipe Library` link → navigates to `library.html`

#### Two-Column Layout (Desktop)
- **Left**: Collapsible seasonal sidebar (~260px), `☰` toggle
- **Right**: Calendar grid (fills remaining width)
- On mobile: sidebar hidden by default; calendar collapses to vertical day-list

#### Monthly Calendar Grid
- 7-column grid (Mon → Sun), 4–5 week rows
- **Week row header**: small row above each week showing week dates + `🪄 Auto-Fill` + `🛒 Shopping List` buttons per row
- Each day cell:
  - Date number + day name (top-left, bold if today)
  - 🌅 **Breakfast** chip (green pill) — English name + Hindi name (small, muted)
  - ☀️ **Lunch** chip (amber pill) — English + Hindi name
  - 🌙 **Dinner** chip (crimson pill) — English + Hindi name
  - 🍮 **Dessert** chip (purple pill) — optional 4th slot
  - Empty slots show `＋` icon on hover → opens recipe picker
  - **Weekend cells** (Sat/Sun) have subtle gold border — indicate special dishes
- Today's cell: saffron ring border
- **Mobile**: Collapses to accordion-style vertical day cards (Mon first)

#### Seasonal Sidebar (collapsible)
- Season badge at top: 🌞 Summer / 🌧 Monsoon / ❄️ Winter
- **In-Season Vegetables** — bulleted list
- **In-Season Fruits** — bulleted list
- Auto-updates when month changes
- Collapses to narrow icon rail on toggle

#### Recipe Picker Modal (click empty `+` slot)
- Search input (name search, live filter by English or Hindi name)
- Filter row: **Season** dropdown + **Region** dropdown + **Tags** dropdown
- Meal type is pre-selected from the slot clicked (Breakfast / Lunch / Dinner / Dessert)
- Each list row shows: English name | Hindi name (muted) | season badge | region badge | spice chillies
- Click a row to assign; modal closes and chip appears on calendar

#### Recipe View Modal (click filled chip)
- English dish name (large) + **Hindi name** below in Devanagari (muted)
- Badges row: season tag | region tag | spice level (🌶️ / 🌶️🌶️ / 🌶️🌶️🌶️) | **Serves N** | occasion tags
- **Accompaniment**: shown as a highlighted note below dish name (e.g. "Serve with Roti or Rice")
- **Suggested Beverage**: ☕ icon + beverage name (e.g. "Masala Chai")
- **Suggested Sides**: shown as a small grey row (e.g. "Boondi Raita • Mango Pickle")
- Two tabs: **Ingredients** | **Instructions**
- `✏️ Edit` opens Edit form; `🗑 Remove` clears this slot; `✕ Close`
- Escape key closes; focus-trapped

#### Auto-Fill Confirmation Dialog
- Triggered when week already has ≥1 existing meal
- Message: *"This will replace all existing meals for this week. Continue?"*
- `Confirm` / `Cancel` buttons

#### Shopping List Drawer (slide in from right)
- Triggered by `🛒 Shopping List` button on week row header
- Shows scaled combined ingredient list (household size applied)
- Checkbox per line (client-side tick-off)
- **Household size** input at top of drawer (reads/writes `/api/settings/household_size`)
- `🖨 Print List` button

#### Print View (`@media print`)
- Hides all nav, sidebar, buttons
- Renders full-week table (Mon–Sun): each day shows 3 meals with complete ingredients + steps
- Georgia serif, saffron header

#### PDF Download (`⬇ PDF` button on week header)
- Calls `GET /api/export/pdf/{year}/{week}` → triggers file download
- WeasyPrint A4 PDF from Jinja2 template — same layout as print view

---

### Page 2: Recipe Library (`library.html`)

#### Header
- Same top bar as calendar page (dark mode toggle + `← Back to Calendar`)
- `＋ Add New Recipe` button (saffron, top-right)
- Search bar (searches English + Hindi name)
- Meal Type filter tabs: **All** / **Breakfast** / **Lunch** / **Dinner** / **Dessert** / **Beverage**
- Secondary filter row: **Region** dropdown + **Season** dropdown + **Spice** dropdown + **Tag** chips

#### Recipe Cards Grid
- 3-column grid (desktop), 2-column (tablet), 1-column (mobile)
- Each card shows:
  - Dish name (English, bold) + Hindi name below (Devanagari, muted)
  - Meal type badge + Season badge + Region badge
  - Spice level chillies (🌶️ / 🌶️🌶️ / 🌶️🌶️🌶️) + **Serves N**
  - Occasion tag badges (🎉 Festive / ⚡ Quick / 💪 High Protein / 👨‍👩‍👧 Kids Friendly)
  - Gold star ⭐ if `is_weekend_special`
  - 1-line description
- `✏️ Edit` icon (top-right) → opens full Edit modal
- `🗑 Delete` icon → calls delete API; if in use: blocking modal lists days (cannot delete until slots cleared)

#### Add / Edit Recipe Modal (Library)
- Fields: **Name (English)**, **Name (Hindi)**, **Meal Type** (Breakfast/Lunch/Dinner/Dessert), **Season**, **Region**, **Spice Level** (select), **Servings**, **Description**, **Accompaniment**, **Suggested Beverage**, **Suggested Sides**, **Tags** (checkbox group: Festive / Kids Friendly / Quick / High Protein), **Ingredients** (textarea), **Instructions** (textarea)
- `☑ Weekend Special` checkbox
- `Save` / `Cancel`; validation: name + meal type + season + ingredients required

---

## Seeded Recipes (~35 total)

### Breakfast — नाश्ता (6 dishes)
| English | Hindi | Season | Region | Weekend? |
|---|---|---|---|---|
| Egg Paratha | अंडा पराठा | All | North | No |
| Egg Dosa (Mutta Dosa) | अंडा डोसा | All | South | No |
| Egg Pesarettu | अंडा पेसरेट्टू | All | South | No |
| Masala Omelette | मसाला आमलेट | All | Pan-Indian | No |
| Lentil & Egg Chila | दाल अंडा चीला | All | North | No |
| Egg Bhurji Paratha | अंडा भुरजी पराठा | All | Pan-Indian | No |

### Lunch — दोपहर का खाना (7 dishes)
| English | Hindi | Season | Region | Weekend? |
|---|---|---|---|---|
| Chicken Saag / Palak Chicken | पालक चिकन | Winter | North | No |
| Chicken and Fenugreek Curry | मेथी चिकन | Winter | North | Yes |
| Lentil Chicken Curry | दाल चिकन करी | All | Pan-Indian | No |
| Rajma Masala | राजमा मसाला | All | North | No |
| Chole Rajma Curry | छोले राजमा करी | All | North | No |
| Chicken with Seasonal Gourds | लौकी चिकन | Summer/Monsoon | Pan-Indian | No |
| Dal Tadka with Chicken | दाल तड़का चिकन | All | North | No |

### Dinner — रात का खाना (6 dishes)
| English | Hindi | Season | Region | Weekend? |
|---|---|---|---|---|
| Egg Tadka Dal (Dimer Torka) | अंडा तड़का दाल | All | East (Bengali) | No |
| Egg and Lentil Curry | अंडा दाल सालन | All | Pan-Indian | No |
| Chicken Curry with Seasonal Greens | हरे साग चिकन | Winter/Monsoon | North | Yes |
| Egg Curry with Seasonal Vegetables | अंडा सालन | All | Pan-Indian | No |
| Dal with Greens | साग दाल | Winter | North | No |
| One-Pot Chicken and Lentil Stew | दाल चिकन हांडी | All | Pan-Indian | Yes |

### Dessert — मिठाई (8 dishes — new)
| English | Hindi | Season | Region | Weekend? |
|---|---|---|---|---|
| Rice Kheer | चावल खीर | All | Pan-Indian | Yes |
| Gajar Halwa | गाजर का हलवा | Winter | North | Yes |
| Gulab Jamun | गुलाब जामुन | All | North | Yes |
| Rasgulla | रसगुल्ला | All | East (Bengali) | Yes |
| Payasam | पायसम् | All | South | No |
| Shrikhand | श्रीखंड | Summer | West (Gujarati) | Yes |
| Sooji Halwa | सूजी का हलवा | All | North | No |
| Phirni | फिरनी | All | North | Yes |

### Beverages — पेय पदार्थ (8 dishes — new, in Recipe Library for reference)
| English | Hindi | Season | Pairs With |
|---|---|---|---|
| Masala Chai | मसाला चाय | All | Breakfast |
| Lassi (Sweet) | मीठी लس्सी | Summer | Lunch |
| Chaas / Buttermilk | छाछ / मठ्ठा | Summer/Monsoon | Lunch |
| Haldi Doodh | हल्दी दूध | Winter | Dinner |
| Nimbu Pani | निंबू पानी | Summer | Lunch |
| Aam Panna | आम पना | Summer | Lunch |
| Filter Coffee | फिल्टर कॉफी | All | Breakfast |
| Jal Jeera | जल जीरा | Summer/Monsoon | Lunch |

---

## Implementation Steps (in order)

### Backend
1. **Update `pyproject.toml`** — add `fastapi`, `uvicorn[standard]`, `sqlalchemy`, `weasyprint`, `jinja2`
2. **Create `database.py`** — SQLAlchemy engine + `SessionLocal` (SQLite: `menu.db`)
3. **Create `models.py`** — `Recipe` (all new fields), `MenuEntry`, `AppSetting` ORM models
4. **Create `schemas.py`** — Pydantic models (Recipe now includes `name_hindi`, `region`, `spice_level`, `accompaniment`, `suggested_beverage`, `suggested_sides`, `tags`, `is_weekend_special`)
5. **Create `seasonal_data.py`** — `SEASONAL: dict[int, dict]` (month 1–12 → season, veg list, fruit list)
6. **Create `seed_data.py`** — All ~35 recipes (19 original + 8 desserts + 8 beverages) with Hindi names, full ingredients, instructions, all metadata
7. **Create `autofill.py`** — Season-aware, variety-guaranteed filler; weekday = quick/standard, Sat/Sun = `is_weekend_special` priority; fills up to 28 slots (21 meals + optional desserts)
8. **Create `routers/recipes.py`** — Full CRUD + `GET /{id}/used-on`; extended filters (`?tags=&region=&spice=`)
9. **Create `routers/menu_entries.py`** — Entry CRUD + autofill check + autofill commit (dessert slot included)
10. **Create `routers/settings.py`** — GET all + PUT `household_size`
11. **Create `routers/export.py`** — Shopping list (scaled) + A4 PDF + JSON backup
12. **Create `templates/print_menu.html`** — Jinja2 → WeasyPrint A4 PDF (includes Hindi name, accompaniment, sides, beverage)
13. **Update `main.py`** — App wiring: routers, static files mount, DB init + seed on startup

### Frontend
14. **Create `static/index.html`** — Calendar page: bilingual header, 4-slot day cells (Breakfast/Lunch/Dinner/Dessert), weekend gold border, all modals with full recipe fields, print styles
15. **Create `static/library.html`** — Recipe Library: card grid with Hindi name + tags badges + region + spice icons; search/filter by tags + region + spice
16. **Update `README.md`** — Install + run instructions, household size config note

---

## Run Command

```bash
# Install dependencies
uv pip install fastapi "uvicorn[standard]" sqlalchemy weasyprint jinja2

# Start the server
uvicorn main:app --reload --port 8000
# Open: http://localhost:8000
```

## Auto-Fill Algorithm (Updated)

1. Receive `year` + `week` (ISO week number)
2. Derive month → season from `seasonal_data.py`
3. For each meal type (breakfast, lunch, dinner, dessert):
   - Build base pool: `season == current_season OR season == "All"`
   - **Weekday pool** (Mon–Fri): prefer `is_weekend_special == False`
   - **Weekend pool** (Sat–Sun): prefer `is_weekend_special == True`, fallback to full pool
4. Shuffle each pool; assign to 7 days without repeating any dish in the same week
5. Dessert slots: filled only if pool is non-empty (optional slot — can remain empty)
6. Delete existing entries for the week, bulk-insert up to 28 new `MenuEntry` rows

## Shopping List Scaling Logic

1. Fetch `household_size` from `AppSetting` (default: 4)
2. For each recipe in the week's 21 entries, parse ingredient lines
3. Detect numeric quantity at start of each line (e.g. `"500g chicken"` → `500`)
4. Scale: `scaled_qty = original_qty × (household_size / recipe.servings)`
5. Deduplicate same ingredient across recipes (sum quantities where detectable)
6. Return as flat list of strings

## Delete-Safety Check

- `DELETE /api/recipes/{id}` first queries `MenuEntry` for any row with `recipe_id == id`
- If found: return **HTTP 409** with `{"error": "Recipe in use", "days": ["Mon Jul 7", "Wed Jul 9", ...]}`
- Frontend shows blocking modal listing the days — user must clear those slots first
