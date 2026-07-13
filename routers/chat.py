"""AI chat grounded on the app's recipes, calendar and shopping list (EN + HI).

Streams responses via Server-Sent Events. Degrades gracefully when no LLM key
is configured. Kept read/answer-focused; it can *suggest* actions for the user
to perform in the UI.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

import llm
import mcp_client
from database import get_db
from models import MenuEntry, Recipe
from routers.export import _build_shopping_list, _week_entries

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatIn(BaseModel):
    messages: list[dict]
    year: int | None = None
    week: int | None = None


def _recipe_catalog(db: Session) -> str:
    """Compact catalogue of recipe names grouped by meal type for grounding."""
    rows = db.query(Recipe).order_by(Recipe.meal_type, Recipe.name).all()
    by_meal: dict[str, list[str]] = {}
    for r in rows:
        label = f"{r.name} ({r.name_hindi})" if r.name_hindi else r.name
        by_meal.setdefault(r.meal_type, []).append(label)
    parts = [f"Total recipes: {len(rows)}."]
    for meal, names in by_meal.items():
        parts.append(f"\n{meal.title()} ({len(names)}): " + ", ".join(names))
    return "".join(parts)


def _week_context(db: Session, year: int | None, week: int | None) -> str:
    if not year or not week:
        return ""
    entries = _week_entries(db, year, week)
    if not entries:
        return f"\n\nThe user's Week {week}, {year} calendar is currently empty."
    lines = [f"\n\nUser's Week {week}, {year} menu:"]
    for e in entries:
        r: Recipe = e.recipe
        if r:
            lines.append(
                f"- {e.year}-{e.month:02d}-{e.day:02d} {e.meal_type}: {r.name}"
            )
    shopping = _build_shopping_list(db, year, week)
    if shopping:
        lines.append("\nShopping list for that week: " + "; ".join(shopping))
    return "\n".join(lines)


def _tools_hint() -> str:
    avail = mcp_client.available()
    if not any(avail.values()):
        return ""
    tools = []
    if avail.get("sqlite"):
        tools.append(
            "a SQLite database tool. Key table `recipes` has columns: id, name, "
            "name_hindi, meal_type ('breakfast'|'lunch'|'dinner'|'dessert'|'beverage'), "
            "description, season, region, spice_level, servings, accompaniment, "
            "suggested_beverage, suggested_sides, tags, is_weekend_special, is_custom, "
            "ingredients, instructions. Other tables: menu_entries (the user's planned "
            "meals: year, month, day, meal_type, recipe_id), app_settings, translations. "
            "Filter meal types with the `meal_type` column (never a `type` column). "
            "If unsure of a schema, call the schema/list-tables tool first, then query"
        )
    if avail.get("spoonacular"):
        tools.append(
            "a Spoonacular tool — use it to find external recipes, nutrition and "
            "ingredient information not in the local catalogue"
        )
    return (
        "\n\nYou have access to these tools; call them to ground your answers in real "
        "data instead of guessing: " + "; ".join(tools) + ". "
        "Prefer the SQLite database for anything about this app's own recipes or the "
        "user's plan, and Spoonacular for outside recipes or nutrition. "
        "Do not give up after one failed query — inspect the schema and retry."
    )


def _system_prompt(db: Session, year: int | None, week: int | None) -> str:
    return (
        "You are the friendly assistant for an Indian Monthly Menu meal-planner web app. "
        "You help with recipes, ingredients, cooking steps, substitutions and the weekly shopping list. "
        "Answer using the app's own recipe catalogue below whenever relevant. "
        "IMPORTANT: Detect the language of the user's message and reply in that same language. "
        "If the user writes in Hindi (हिंदी), reply in Hindi; if in English, reply in English. "
        "Keep answers concise and practical. When the user asks to change their plan (add a meal to a day, "
        "auto-fill a week, or build a shopping list), explain clearly which button in the app to use "
        "(the + slot on a day, the Auto-Fill or Shopping buttons on a week row)."
        + _tools_hint()
        + "\n\n=== RECIPE CATALOGUE ===\n"
        + _recipe_catalog(db)
        + _week_context(db, year, week)
    )


@router.get("/status")
def status():
    st = llm.status()
    st["mcp"] = mcp_client.available()
    return st


def _sse(text: str) -> str:
    safe = text.replace("\r", "").replace("\n", "\\n")
    return f"data: {safe}\n\n"


@router.post("")
def chat(payload: ChatIn, db: Session = Depends(get_db)):
    system = _system_prompt(db, payload.year, payload.week)
    turns = list(payload.messages)
    messages = [{"role": "system", "content": system}, *turns]

    def event_stream():
        if not llm.is_available():
            yield (
                "data: \u26a0\ufe0f AI chat needs an API key. Add OPENAI_API_KEY or "
                "GEMINI_API_KEY to your .env file and restart the server.\n\n"
            )
            yield "event: done\ndata: end\n\n"
            return

        # Preferred path: Gemini + MCP tools (Spoonacular + sqlite-db) as
        # function-calls, grounded on live tool results.
        try:
            answer = mcp_client.answer_sync(system, turns)
        except Exception:  # noqa: BLE001
            answer = None
        if answer:
            yield _sse(answer)
            yield "event: done\ndata: end\n\n"
            return

        # Fallback: plain streamed chat grounded on the DB-built system prompt.
        try:
            for chunk in llm.stream_chat(messages):
                yield _sse(chunk)
        except Exception as exc:  # noqa: BLE001
            msg = str(exc).replace("\n", " ")
            yield f"data: \u26a0\ufe0f Error: {msg}\n\n"
        yield "event: done\ndata: end\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
