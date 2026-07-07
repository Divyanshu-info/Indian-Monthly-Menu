"""Recipe CRUD + delete-safety check."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from autofill import is_chicken
from database import get_db
from models import MenuEntry, Recipe
from schemas import RecipeCreate, RecipeOut, RecipeUpdate

router = APIRouter(prefix="/api/recipes", tags=["recipes"])


@router.get("/{recipe_id}/alternatives", response_model=list[RecipeOut])
def alternatives(
    recipe_id: int,
    year: int | None = None,
    month: int | None = None,
    day: int | None = None,
    db: Session = Depends(get_db),
):
    """Return same-meal-type recipes to swap in, excluding the current one.

    Chicken dishes are only offered on weekends (matching the autofill rule).
    """
    current = db.get(Recipe, recipe_id)
    if not current:
        raise HTTPException(404, "Recipe not found")
    query = db.query(Recipe).filter(
        Recipe.meal_type == current.meal_type, Recipe.id != recipe_id
    )
    candidates = query.order_by(Recipe.name).all()
    is_weekend = False
    if year and month and day:
        try:
            is_weekend = date(year, month, day).weekday() >= 5
        except ValueError:
            is_weekend = False
    if not is_weekend:
        candidates = [r for r in candidates if not is_chicken(r)]
    return candidates


@router.get("", response_model=list[RecipeOut])
def list_recipes(
    meal_type: str | None = None,
    season: str | None = None,
    region: str | None = None,
    spice: str | None = None,
    tags: str | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Recipe)
    if meal_type:
        query = query.filter(Recipe.meal_type == meal_type)
    if season:
        query = query.filter(Recipe.season == season)
    if region:
        query = query.filter(Recipe.region == region)
    if spice:
        query = query.filter(Recipe.spice_level == spice)
    if tags:
        query = query.filter(Recipe.tags.like(f"%{tags}%"))
    if q:
        like = f"%{q}%"
        query = query.filter((Recipe.name.like(like)) | (Recipe.name_hindi.like(like)))
    return query.order_by(Recipe.name).all()


@router.post("", response_model=RecipeOut, status_code=201)
def create_recipe(payload: RecipeCreate, db: Session = Depends(get_db)):
    recipe = Recipe(**payload.model_dump(), is_custom=True)
    db.add(recipe)
    db.commit()
    db.refresh(recipe)
    return recipe


@router.get("/{recipe_id}", response_model=RecipeOut)
def get_recipe(recipe_id: int, db: Session = Depends(get_db)):
    recipe = db.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(404, "Recipe not found")
    return recipe


@router.put("/{recipe_id}", response_model=RecipeOut)
def update_recipe(recipe_id: int, payload: RecipeUpdate, db: Session = Depends(get_db)):
    recipe = db.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(404, "Recipe not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(recipe, key, value)
    db.commit()
    db.refresh(recipe)
    return recipe


def _used_on_days(db: Session, recipe_id: int) -> list[str]:
    entries = db.query(MenuEntry).filter(MenuEntry.recipe_id == recipe_id).all()
    days = []
    for e in entries:
        try:
            d = date(e.year, e.month, e.day)
            days.append(f"{d.strftime('%a %b')} {d.day} ({e.meal_type})")
        except ValueError:
            days.append(f"{e.year}-{e.month}-{e.day} ({e.meal_type})")
    return days


@router.get("/{recipe_id}/used-on")
def used_on(recipe_id: int, db: Session = Depends(get_db)):
    recipe = db.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(404, "Recipe not found")
    return {"recipe_id": recipe_id, "days": _used_on_days(db, recipe_id)}


@router.delete("/{recipe_id}")
def delete_recipe(recipe_id: int, db: Session = Depends(get_db)):
    recipe = db.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(404, "Recipe not found")
    days = _used_on_days(db, recipe_id)
    if days:
        raise HTTPException(
            status_code=409,
            detail={"error": "Recipe in use", "days": days},
        )
    db.delete(recipe)
    db.commit()
    return {"deleted": recipe_id}
