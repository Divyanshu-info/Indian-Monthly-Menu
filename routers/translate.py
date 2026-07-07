"""LLM-powered translation of recipe fields and shopping-list lines, with DB cache."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

import llm
from database import get_db
from models import Recipe, Translation

router = APIRouter(prefix="/api/translate", tags=["translate"])

# Supported target languages (display name -> code used for prompting/caching).
LANGUAGES = {
    "English": "en",
    "Hindi": "hi",
    "Tamil": "ta",
    "Telugu": "te",
    "Bengali": "bn",
    "Marathi": "mr",
}

# Recipe fields we translate for display.
FIELDS = [
    "name",
    "description",
    "ingredients",
    "instructions",
    "accompaniment",
    "suggested_sides",
]


class TextsIn(BaseModel):
    texts: list[str]
    lang: str


@router.get("/languages")
def languages():
    return {"languages": list(LANGUAGES.keys()), "provider": llm.active_provider()}


@router.post("/recipe/{recipe_id}")
def translate_recipe(recipe_id: int, lang: str, db: Session = Depends(get_db)):
    """Return translated recipe fields for `lang`, using cache when available."""
    if lang not in LANGUAGES:
        raise HTTPException(400, f"Unsupported language: {lang}")
    recipe = db.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(404, "Recipe not found")

    # English is the source language — return as-is.
    if lang == "English":
        return {"recipe_id": recipe_id, "lang": lang, "fields": {f: getattr(recipe, f) or "" for f in FIELDS}}

    cached = {
        t.field: t.text
        for t in db.query(Translation).filter(
            Translation.recipe_id == recipe_id, Translation.lang == lang
        )
    }
    missing = {f: getattr(recipe, f) or "" for f in FIELDS if f not in cached}

    if missing:
        if not llm.is_available():
            raise HTTPException(
                status_code=501,
                detail="Translation needs an LLM API key. Set OPENAI_API_KEY or GEMINI_API_KEY in .env.",
            )
        try:
            translated = llm.translate_fields(missing, lang)
        except llm.LLMNotConfigured:
            raise HTTPException(501, "No LLM API key configured.")
        except Exception as exc:  # noqa: BLE001 - surface provider errors cleanly
            raise HTTPException(502, f"Translation failed: {exc}")
        for field, text in translated.items():
            db.add(Translation(recipe_id=recipe_id, lang=lang, field=field, text=text))
            cached[field] = text
        db.commit()

    return {"recipe_id": recipe_id, "lang": lang, "fields": {f: cached.get(f, "") for f in FIELDS}}


@router.post("/text")
def translate_text(payload: TextsIn):
    """Translate a list of free-text lines (e.g. shopping-list items)."""
    if payload.lang not in LANGUAGES:
        raise HTTPException(400, f"Unsupported language: {payload.lang}")
    if payload.lang == "English" or not payload.texts:
        return {"lang": payload.lang, "texts": payload.texts}
    if not llm.is_available():
        raise HTTPException(501, "Translation needs an LLM API key.")
    fields = {str(i): t for i, t in enumerate(payload.texts)}
    try:
        out = llm.translate_fields(fields, payload.lang)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"Translation failed: {exc}")
    return {"lang": payload.lang, "texts": [out.get(str(i), t) for i, t in enumerate(payload.texts)]}
