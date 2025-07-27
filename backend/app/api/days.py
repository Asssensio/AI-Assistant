# путь: backend/app/api/days.py
"""
API для работы с днями записей.
"""

from typing import List, Optional
from datetime import date, datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.app.models.database import get_db
from backend.app.models.day import Day
from backend.app.models.fragment import Fragment

router = APIRouter()


# Pydantic модели
class DayInfo(BaseModel):
    """Информация о дне."""
    id: int
    date: date
    total_fragments: int
    total_duration_minutes: float
    has_short_summary: bool
    has_medium_summary: bool
    is_processed: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class DayDetails(BaseModel):
    """Детальная информация о дне."""
    id: int
    date: date
    total_fragments: int
    total_duration_minutes: float
    short_summary: Optional[str] = None
    medium_summary: Optional[str] = None
    full_text: Optional[str] = None
    is_processed: bool
    whisper_completed: bool
    summary_generated: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class FragmentInfo(BaseModel):
    """Информация о фрагменте."""
    id: int
    original_filename: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_minutes: Optional[float]
    transcribed: bool
    transcript_text: Optional[str] = None
    
    class Config:
        from_attributes = True


class SummaryUpdate(BaseModel):
    """Модель для обновления summary."""
    short_summary: Optional[str] = None
    medium_summary: Optional[str] = None


@router.get("/", response_model=List[DayInfo])
async def get_days(
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Получение списка дней с записями."""
    days = db.query(Day).order_by(Day.date.desc()).offset(offset).limit(limit).all()
    return days


@router.get("/{day_date}", response_model=DayDetails)
async def get_day_details(day_date: str, db: Session = Depends(get_db)):
    """Получение детальной информации о дне."""
    try:
        parsed_date = datetime.strptime(day_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    day = db.query(Day).filter(Day.date == parsed_date).first()
    if not day:
        raise HTTPException(status_code=404, detail="Day not found")
    
    return day


@router.get("/{day_date}/fragments", response_model=List[FragmentInfo])
async def get_day_fragments(day_date: str, db: Session = Depends(get_db)):
    """Получение фрагментов дня."""
    try:
        parsed_date = datetime.strptime(day_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    day = db.query(Day).filter(Day.date == parsed_date).first()
    if not day:
        raise HTTPException(status_code=404, detail="Day not found")
    
    fragments = db.query(Fragment).filter(Fragment.day_id == day.id).order_by(Fragment.start_time).all()
    return fragments


@router.put("/{day_date}/summary", response_model=DayDetails)
async def update_day_summary(
    day_date: str, 
    summary_update: SummaryUpdate,
    db: Session = Depends(get_db)
):
    """Обновление summary дня."""
    try:
        parsed_date = datetime.strptime(day_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    day = db.query(Day).filter(Day.date == parsed_date).first()
    if not day:
        raise HTTPException(status_code=404, detail="Day not found")
    
    if summary_update.short_summary is not None:
        day.short_summary = summary_update.short_summary
    if summary_update.medium_summary is not None:
        day.medium_summary = summary_update.medium_summary
    
    day.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(day)
    
    return day


@router.get("/{day_date}/audio-player")
async def get_audio_player_data(day_date: str, db: Session = Depends(get_db)):
    """Получение данных для аудио плеера."""
    try:
        parsed_date = datetime.strptime(day_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    day = db.query(Day).filter(Day.date == parsed_date).first()
    if not day:
        raise HTTPException(status_code=404, detail="Day not found")
    
    fragments = db.query(Fragment).filter(Fragment.day_id == day.id).order_by(Fragment.start_time).all()
    
    playlist = []
    for fragment in fragments:
        playlist.append({
            "id": fragment.id,
            "file_path": fragment.file_path,
            "start_time": fragment.start_time.isoformat(),
            "duration": fragment.duration_seconds,
            "transcript": fragment.transcript_text,
            "timestamps": fragment.get_whisper_timestamps()
        })
    
    return {
        "date": day_date,
        "total_duration": day.total_duration_seconds,
        "playlist": playlist
    }


@router.post("/", response_model=DayDetails)
async def create_day(day_date: str, db: Session = Depends(get_db)):
    """Создание нового дня."""
    try:
        parsed_date = datetime.strptime(day_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Проверяем, что день не существует
    existing_day = db.query(Day).filter(Day.date == parsed_date).first()
    if existing_day:
        raise HTTPException(status_code=409, detail="Day already exists")
    
    new_day = Day(date=parsed_date)
    db.add(new_day)
    db.commit()
    db.refresh(new_day)
    
    return new_day 