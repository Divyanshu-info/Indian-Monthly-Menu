"""ORM models: Recipe, MenuEntry, AppSetting."""

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from database import Base


class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    name_hindi = Column(String, default="")
    meal_type = Column(
        String, nullable=False, index=True
    )  # breakfast/lunch/dinner/dessert/beverage
    description = Column(Text, default="")
    ingredients = Column(Text, default="")  # newline-separated
    instructions = Column(Text, default="")  # numbered steps, newline-separated
    season = Column(String, default="All")  # Winter/Summer/Monsoon/All
    region = Column(String, default="Pan-Indian")
    spice_level = Column(String, default="Medium")  # Mild/Medium/Spicy
    servings = Column(Integer, default=4)
    accompaniment = Column(Text, default="")
    suggested_beverage = Column(Text, default="")
    suggested_sides = Column(Text, default="")
    tags = Column(Text, default="")  # comma-separated
    is_weekend_special = Column(Boolean, default=False)
    is_custom = Column(Boolean, default=False)

    entries = relationship("MenuEntry", back_populates="recipe")


class MenuEntry(Base):
    __tablename__ = "menu_entries"
    __table_args__ = (
        UniqueConstraint("year", "month", "day", "meal_type", name="uq_slot"),
    )

    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False, index=True)
    day = Column(Integer, nullable=False)
    meal_type = Column(String, nullable=False)  # breakfast/lunch/dinner/dessert
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)

    recipe = relationship("Recipe", back_populates="entries")


class AppSetting(Base):
    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False, index=True)
    value = Column(String, default="")


class Translation(Base):
    """Cached LLM translations of recipe fields, keyed by (recipe, lang, field)."""

    __tablename__ = "translations"
    __table_args__ = (
        UniqueConstraint("recipe_id", "lang", "field", name="uq_translation"),
    )

    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False, index=True)
    lang = Column(String, nullable=False, index=True)
    field = Column(String, nullable=False)
    text = Column(Text, default="")
