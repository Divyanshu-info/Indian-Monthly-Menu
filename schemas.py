"""Pydantic request/response models."""
from typing import Optional

from pydantic import BaseModel, ConfigDict


class RecipeBase(BaseModel):
    name: str
    name_hindi: str = ""
    meal_type: str
    description: str = ""
    ingredients: str = ""
    instructions: str = ""
    season: str = "All"
    region: str = "Pan-Indian"
    spice_level: str = "Medium"
    servings: int = 4
    accompaniment: str = ""
    suggested_beverage: str = ""
    suggested_sides: str = ""
    tags: str = ""
    is_weekend_special: bool = False


class RecipeCreate(RecipeBase):
    pass


class RecipeUpdate(BaseModel):
    name: Optional[str] = None
    name_hindi: Optional[str] = None
    meal_type: Optional[str] = None
    description: Optional[str] = None
    ingredients: Optional[str] = None
    instructions: Optional[str] = None
    season: Optional[str] = None
    region: Optional[str] = None
    spice_level: Optional[str] = None
    servings: Optional[int] = None
    accompaniment: Optional[str] = None
    suggested_beverage: Optional[str] = None
    suggested_sides: Optional[str] = None
    tags: Optional[str] = None
    is_weekend_special: Optional[bool] = None


class RecipeOut(RecipeBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_custom: bool = False


class MenuEntryCreate(BaseModel):
    year: int
    month: int
    day: int
    meal_type: str
    recipe_id: int


class MenuEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    year: int
    month: int
    day: int
    meal_type: str
    recipe_id: int
    recipe: RecipeOut


class SettingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    key: str
    value: str


class SettingUpdate(BaseModel):
    value: str
