"""App settings (e.g. household_size) + seasonal info."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import AppSetting
from schemas import SettingOut, SettingUpdate
from seasonal_data import SEASONAL

router = APIRouter(prefix="/api", tags=["settings"])


@router.get("/settings", response_model=list[SettingOut])
def list_settings(db: Session = Depends(get_db)):
    return db.query(AppSetting).all()


@router.put("/settings/{key}", response_model=SettingOut)
def update_setting(key: str, payload: SettingUpdate, db: Session = Depends(get_db)):
    setting = db.query(AppSetting).filter(AppSetting.key == key).first()
    if setting:
        setting.value = payload.value
    else:
        setting = AppSetting(key=key, value=payload.value)
        db.add(setting)
    db.commit()
    db.refresh(setting)
    return setting


@router.get("/seasonal/{month}")
def seasonal(month: int):
    data = SEASONAL.get(month, {"season": "All", "vegetables": [], "fruits": []})
    return {"month": month, **data}
