"""
API для работы с аудио фрагментами.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.app.models.database import get_db
from backend.app.models.fragment import Fragment
from backend.app.models.day import Day

router = APIRouter()


# Pydantic модели
class FragmentInfo(BaseModel):
    """Информация о фрагменте."""
    id: int
    day_id: int
    file_path: str
    original_filename: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: Optional[float]
    transcribed: bool
    transcript_text: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class FragmentDetails(BaseModel):
    """Детальная информация о фрагменте."""
    id: int
    day_id: int
    file_path: str
    original_filename: str
    file_size_bytes: Optional[int]
    duration_seconds: Optional[float]
    sample_rate: int
    channels: int
    start_time: datetime
    end_time: Optional[datetime]
    transcribed: bool
    transcript_text: Optional[str] = None
    whisper_segments: Optional[List[Dict[str, Any]]] = None
    whisper_model_used: Optional[str] = None
    processing_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class FragmentCreate(BaseModel):
    """Модель для создания фрагмента."""
    day_date: str
    file_path: str
    original_filename: str
    start_time: datetime
    duration_seconds: Optional[float] = None
    file_size_bytes: Optional[int] = None


class TranscriptionUpdate(BaseModel):
    """Модель для обновления транскрипции."""
    transcript_text: str
    whisper_segments: Optional[List[Dict[str, Any]]] = None
    whisper_model_used: Optional[str] = None


@router.get("/", response_model=List[FragmentInfo])
async def get_fragments(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    day_date: Optional[str] = None,
    transcribed: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Получение списка фрагментов."""
    query = db.query(Fragment)
    
    # Фильтр по дню
    if day_date:
        try:
            parsed_date = datetime.strptime(day_date, "%Y-%m-%d").date()
            day = db.query(Day).filter(Day.date == parsed_date).first()
            if day:
                query = query.filter(Fragment.day_id == day.id)
            else:
                return []  # День не найден
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Фильтр по статусу транскрипции
    if transcribed is not None:
        query = query.filter(Fragment.transcribed == transcribed)
    
    fragments = query.order_by(Fragment.start_time.desc()).offset(offset).limit(limit).all()
    return fragments


@router.get("/{fragment_id}", response_model=FragmentDetails)
async def get_fragment(fragment_id: int, db: Session = Depends(get_db)):
    """Получение конкретного фрагмента."""
    fragment = db.query(Fragment).filter(Fragment.id == fragment_id).first()
    if not fragment:
        raise HTTPException(status_code=404, detail="Fragment not found")
    
    return fragment


@router.post("/", response_model=FragmentDetails)
async def create_fragment(fragment_data: FragmentCreate, db: Session = Depends(get_db)):
    """Создание нового фрагмента."""
    # Найти или создать день
    try:
        parsed_date = datetime.strptime(fragment_data.day_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    day = db.query(Day).filter(Day.date == parsed_date).first()
    if not day:
        # Создаем новый день
        day = Day(date=parsed_date)
        db.add(day)
        db.commit()
        db.refresh(day)
    
    # Создаем фрагмент
    fragment = Fragment(
        day_id=day.id,
        file_path=fragment_data.file_path,
        original_filename=fragment_data.original_filename,
        start_time=fragment_data.start_time,
        duration_seconds=fragment_data.duration_seconds,
        file_size_bytes=fragment_data.file_size_bytes
    )
    
    # Обновляем статистику дня
    day.total_fragments += 1
    if fragment_data.duration_seconds:
        day.total_duration_seconds += fragment_data.duration_seconds
    
    db.add(fragment)
    db.commit()
    db.refresh(fragment)
    
    return fragment


@router.put("/{fragment_id}/transcription", response_model=FragmentDetails)
async def update_fragment_transcription(
    fragment_id: int,
    transcription: TranscriptionUpdate,
    db: Session = Depends(get_db)
):
    """Обновление транскрипции фрагмента."""
    fragment = db.query(Fragment).filter(Fragment.id == fragment_id).first()
    if not fragment:
        raise HTTPException(status_code=404, detail="Fragment not found")
    
    fragment.transcript_text = transcription.transcript_text
    fragment.whisper_segments = transcription.whisper_segments
    fragment.whisper_model_used = transcription.whisper_model_used
    fragment.transcribed = True
    fragment.transcription_completed_at = datetime.utcnow()
    fragment.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(fragment)
    
    return fragment


@router.get("/{fragment_id}/timestamps")
async def get_fragment_timestamps(fragment_id: int, db: Session = Depends(get_db)):
    """Получение временных меток фрагмента."""
    fragment = db.query(Fragment).filter(Fragment.id == fragment_id).first()
    if not fragment:
        raise HTTPException(status_code=404, detail="Fragment not found")
    
    if not fragment.transcribed or not fragment.whisper_segments:
        return {"timestamps": [], "transcript": fragment.transcript_text or ""}
    
    return {
        "timestamps": fragment.get_whisper_timestamps(),
        "transcript": fragment.transcript_text,
        "duration": fragment.duration_seconds
    }


@router.delete("/{fragment_id}")
async def delete_fragment(fragment_id: int, db: Session = Depends(get_db)):
    """Удаление фрагмента."""
    fragment = db.query(Fragment).filter(Fragment.id == fragment_id).first()
    if not fragment:
        raise HTTPException(status_code=404, detail="Fragment not found")
    
    # Обновляем статистику дня
    day = db.query(Day).filter(Day.id == fragment.day_id).first()
    if day:
        day.total_fragments = max(0, day.total_fragments - 1)
        if fragment.duration_seconds:
            day.total_duration_seconds = max(0, day.total_duration_seconds - fragment.duration_seconds)
    
    db.delete(fragment)
    db.commit()
    
    return {"message": "Fragment deleted successfully"}


@router.get("/pending/transcription", response_model=List[FragmentInfo])
async def get_pending_transcription(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Получение фрагментов, ожидающих транскрипции."""
    fragments = db.query(Fragment).filter(
        Fragment.transcribed == False,
        Fragment.processing_error.is_(None)
    ).order_by(Fragment.created_at).limit(limit).all()
    
    return fragments 