"""Menu calendar entries + auto-fill."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from autofill import autofill_week, week_has_entries
from database import get_db
from models import MenuEntry, Recipe
from schemas import MenuEntryCreate, MenuEntryOut

router = APIRouter(prefix="/api/menu", tags=["menu"])


@router.get("/{year}/{month}", response_model=list[MenuEntryOut])
def month_entries(year: int, month: int, db: Session = Depends(get_db)):
    return (
        db.query(MenuEntry)
        .filter(MenuEntry.year == year, MenuEntry.month == month)
        .all()
    )


@router.post("/entry", response_model=MenuEntryOut, status_code=201)
def create_entry(payload: MenuEntryCreate, db: Session = Depends(get_db)):
    if not db.get(Recipe, payload.recipe_id):
        raise HTTPException(404, "Recipe not found")
    # Replace existing assignment in the same slot.
    existing = (
        db.query(MenuEntry)
        .filter(
            MenuEntry.year == payload.year,
            MenuEntry.month == payload.month,
            MenuEntry.day == payload.day,
            MenuEntry.meal_type == payload.meal_type,
        )
        .first()
    )
    if existing:
        existing.recipe_id = payload.recipe_id
        db.commit()
        db.refresh(existing)
        return existing
    entry = MenuEntry(**payload.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/entry/{entry_id}")
def delete_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = db.get(MenuEntry, entry_id)
    if not entry:
        raise HTTPException(404, "Entry not found")
    db.delete(entry)
    db.commit()
    return {"deleted": entry_id}


@router.get("/autofill/{year}/{week}/check")
def autofill_check(year: int, week: int, db: Session = Depends(get_db)):
    return {"has_existing": week_has_entries(db, year, week)}


@router.post("/autofill/{year}/{week}")
def autofill(year: int, week: int, db: Session = Depends(get_db)):
    count = autofill_week(db, year, week)
    return {"created": count}
