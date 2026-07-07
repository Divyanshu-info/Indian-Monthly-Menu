"""Shopping list (scaled), A4 PDF (WeasyPrint), and JSON backup."""

import re
from collections import OrderedDict
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, Response
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.orm import Session

from autofill import week_dates
from database import get_db
from models import AppSetting, MenuEntry, Recipe

router = APIRouter(prefix="/api/export", tags=["export"])

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)

_QTY_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*([a-zA-Z]*)\s+(.*)$")


def _household_size(db: Session) -> int:
    s = db.query(AppSetting).filter(AppSetting.key == "household_size").first()
    try:
        return int(s.value) if s else 4
    except (TypeError, ValueError):
        return 4


def _week_entries(db: Session, year: int, week: int) -> list[MenuEntry]:
    dates = week_dates(year, week)
    entries: list[MenuEntry] = []
    for d in dates:
        entries.extend(
            db.query(MenuEntry)
            .filter(
                MenuEntry.year == d.year,
                MenuEntry.month == d.month,
                MenuEntry.day == d.day,
            )
            .all()
        )
    return entries


def _build_shopping_list(db: Session, year: int, week: int) -> list[str]:
    household = _household_size(db)
    entries = _week_entries(db, year, week)

    # key: (name_lower, unit) -> [qty_or_None, display_name]
    combined: "OrderedDict[tuple[str, str], list]" = OrderedDict()
    plain: list[str] = []

    for e in entries:
        recipe: Recipe = e.recipe
        if not recipe or not recipe.ingredients:
            continue
        factor = household / (recipe.servings or 4)
        for line in recipe.ingredients.splitlines():
            line = line.strip()
            if not line:
                continue
            m = _QTY_RE.match(line)
            if m:
                qty = float(m.group(1)) * factor
                unit = m.group(2).lower()
                name = m.group(3).strip().lower()
                key = (name, unit)
                if key in combined:
                    combined[key][0] += qty
                else:
                    combined[key] = [qty, m.group(3).strip(), unit]
            else:
                if line not in plain:
                    plain.append(line)

    result: list[str] = []
    for (name, unit), (qty, disp, u) in combined.items():
        qty_str = f"{qty:.0f}" if abs(qty - round(qty)) < 0.05 else f"{qty:.1f}"
        unit_str = f"{u} " if u else ""
        result.append(f"{qty_str} {unit_str}{disp}".strip())
    result.extend(plain)
    result.sort(key=str.lower)
    return result


@router.get("/shopping-list/{year}/{week}")
def shopping_list(year: int, week: int, db: Session = Depends(get_db)):
    return {
        "year": year,
        "week": week,
        "household_size": _household_size(db),
        "items": _build_shopping_list(db, year, week),
    }


def _render_week_html(db: Session, year: int, week: int) -> str:
    dates = week_dates(year, week)
    days = []
    for d in dates:
        entries = (
            db.query(MenuEntry)
            .filter(
                MenuEntry.year == d.year,
                MenuEntry.month == d.month,
                MenuEntry.day == d.day,
            )
            .all()
        )
        by_meal = {}
        for e in entries:
            by_meal[e.meal_type] = e.recipe
        days.append(
            {
                "label": d.strftime("%A, %d %b %Y"),
                "meals": [
                    (m, by_meal.get(m))
                    for m in ["breakfast", "lunch", "dinner", "dessert"]
                ],
            }
        )
    template = _env.get_template("print_menu.html")
    return template.render(
        year=year,
        week=week,
        days=days,
        shopping=_build_shopping_list(db, year, week),
        household=_household_size(db),
    )


@router.get("/pdf/{year}/{week}")
def export_pdf(year: int, week: int, db: Session = Depends(get_db)):
    html = _render_week_html(db, year, week)
    try:
        from weasyprint import HTML  # lazy import (WeasyPrint needs GTK libs)
    except (ImportError, OSError) as exc:
        raise HTTPException(
            status_code=501,
            detail=(
                "PDF export requires WeasyPrint + GTK runtime. "
                f"Use browser Print instead. ({exc})"
            ),
        )
    pdf_bytes = HTML(string=html).write_pdf()
    filename = f"menu-{year}-W{week}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/print/{year}/{week}", response_class=Response)
def print_html(year: int, week: int, db: Session = Depends(get_db)):
    """HTML version of the week for browser printing (fallback for PDF)."""
    return Response(content=_render_week_html(db, year, week), media_type="text/html")


@router.get("/json")
def export_json(db: Session = Depends(get_db)):
    recipes = db.query(Recipe).all()
    entries = db.query(MenuEntry).all()

    def recipe_dict(r: Recipe) -> dict:
        return {c.name: getattr(r, c.name) for c in r.__table__.columns}

    def entry_dict(e: MenuEntry) -> dict:
        return {c.name: getattr(e, c.name) for c in e.__table__.columns}

    data = {
        "exported_at": date.today().isoformat(),
        "recipes": [recipe_dict(r) for r in recipes],
        "menu_entries": [entry_dict(e) for e in entries],
    }
    return JSONResponse(
        content=data,
        headers={"Content-Disposition": 'attachment; filename="menu-backup.json"'},
    )
