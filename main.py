"""FastAPI app entrypoint: Indian Monthly Menu web app."""

# Trust the OS certificate store so outbound HTTPS (Gemini/OpenAI/Spoonacular)
# works behind corporate TLS-inspection proxies that inject a private root CA.
# Must run before any HTTPS client (httpx/google-genai) builds an SSL context.
try:
    import truststore

    truststore.inject_into_ssl()
except Exception:  # noqa: BLE001 - never block startup on this best-effort shim
    pass

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from database import Base, SessionLocal, engine
from models import AppSetting, Recipe
from routers import chat, export, menu_entries, recipes, settings, translate
from seed_data import RECIPES

STATIC_DIR = Path(__file__).parent / "static"


def init_db() -> None:
    """Create tables and seed recipes + default settings on first run."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Recipe).count() == 0:
            for data in RECIPES:
                db.add(Recipe(**data, is_custom=False))
            db.commit()
        else:
            # Add any newly-seeded recipes that are missing (idempotent, no data loss).
            existing = {name for (name,) in db.query(Recipe.name).all()}
            added = 0
            for data in RECIPES:
                if data["name"] not in existing:
                    db.add(Recipe(**data, is_custom=False))
                    added += 1
            if added:
                db.commit()
        if not db.query(AppSetting).filter(AppSetting.key == "household_size").first():
            db.add(AppSetting(key="household_size", value="4"))
            db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Indian Monthly Menu", lifespan=lifespan)

app.include_router(recipes.router)
app.include_router(menu_entries.router)
app.include_router(settings.router)
app.include_router(export.router)
app.include_router(translate.router)
app.include_router(chat.router)


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/library")
@app.get("/library.html")
def library():
    return FileResponse(STATIC_DIR / "library.html")


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def main():
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    main()
