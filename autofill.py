"""Week auto-fill algorithm: season-aware, variety-guaranteed, weekend-special priority."""

import random
from datetime import date, timedelta

from sqlalchemy.orm import Session

from models import MenuEntry, Recipe
from seasonal_data import get_season

MEAL_TYPES = ["breakfast", "lunch", "dinner", "dessert"]


def week_dates(year: int, week: int) -> list[date]:
    """Return the 7 dates (Mon-Sun) of an ISO week."""
    monday = date.fromisocalendar(year, week, 1)
    return [monday + timedelta(days=i) for i in range(7)]


def _pool(recipes: list[Recipe], season: str) -> list[Recipe]:
    return [r for r in recipes if r.season == season or r.season == "All"]


def is_chicken(recipe: Recipe) -> bool:
    """A recipe counts as chicken (weekend-only) by name or tag."""
    name = (recipe.name or "").lower()
    tags = (recipe.tags or "").lower()
    return "chicken" in name or "chicken" in tags


def autofill_week(db: Session, year: int, week: int) -> int:
    """Delete existing entries for the week and bulk-insert new ones.

    Returns the number of entries created.
    """
    dates = week_dates(year, week)

    # Determine dominant season from the week's mid-point month.
    mid_month = dates[3].month
    season = get_season(mid_month)

    # Remove existing entries for these dates.
    for d in dates:
        db.query(MenuEntry).filter(
            MenuEntry.year == d.year,
            MenuEntry.month == d.month,
            MenuEntry.day == d.day,
        ).delete(synchronize_session=False)

    created = 0
    for meal in MEAL_TYPES:
        all_meal = db.query(Recipe).filter(Recipe.meal_type == meal).all()
        pool = _pool(all_meal, season)
        if not pool:
            continue

        # Chicken dishes are reserved for weekends only.
        weekday_pool = [
            r for r in pool if not r.is_weekend_special and not is_chicken(r)
        ]
        if not weekday_pool:
            weekday_pool = [r for r in pool if not is_chicken(r)] or pool
        weekend_pool = [
            r for r in pool if r.is_weekend_special or is_chicken(r)
        ] or pool

        used_ids: set[int] = set()

        def pick(candidates: list[Recipe]) -> Recipe | None:
            fresh = [r for r in candidates if r.id not in used_ids]
            source = fresh if fresh else candidates
            if not source:
                return None
            choice = random.choice(source)
            used_ids.add(choice.id)
            return choice

        for d in dates:
            is_weekend = d.weekday() >= 5  # Sat=5, Sun=6
            # Dessert is optional on weekdays; always assign on weekends.
            if meal == "dessert" and not is_weekend and random.random() < 0.5:
                continue
            candidates = weekend_pool if is_weekend else weekday_pool
            recipe = pick(candidates)
            if recipe is None:
                continue
            db.add(
                MenuEntry(
                    year=d.year,
                    month=d.month,
                    day=d.day,
                    meal_type=meal,
                    recipe_id=recipe.id,
                )
            )
            created += 1

    db.commit()
    return created


def week_has_entries(db: Session, year: int, week: int) -> bool:
    for d in week_dates(year, week):
        exists = (
            db.query(MenuEntry)
            .filter(
                MenuEntry.year == d.year,
                MenuEntry.month == d.month,
                MenuEntry.day == d.day,
            )
            .first()
        )
        if exists:
            return True
    return False
