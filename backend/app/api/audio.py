# путь: backend/app/api/audio.py
"""
API для работы с аудиофайлами.
"""

import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.models.database import get_db
from backend.app.models.fragment import Fragment
from libs.config import get_paths_config

router = APIRouter()


@router.get("/{fragment_id}")
async def get_audio_file(fragment_id: int, db: Session = Depends(get_db)):
    """Получение аудиофайла по ID фрагмента."""
    fragment = db.query(Fragment).filter(Fragment.id == fragment_id).first()
    if not fragment:
        raise HTTPException(status_code=404, detail="Fragment not found")
    
    # Проверяем существование файла
    file_path = Path(fragment.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    # Возвращаем файл
    return FileResponse(
        path=str(file_path),
        media_type="audio/wav",
        filename=fragment.original_filename
    )


@router.get("/{fragment_id}/info")
async def get_audio_info(fragment_id: int, db: Session = Depends(get_db)):
    """Получение информации об аудиофайле."""
    fragment = db.query(Fragment).filter(Fragment.id == fragment_id).first()
    if not fragment:
        raise HTTPException(status_code=404, detail="Fragment not found")
    
    return {
        "id": fragment.id,
        "filename": fragment.original_filename,
        "file_path": fragment.file_path,
        "file_size_bytes": fragment.file_size_bytes,
        "duration_seconds": fragment.duration_seconds,
        "sample_rate": fragment.sample_rate,
        "channels": fragment.channels,
        "start_time": fragment.start_time.isoformat(),
        "transcribed": fragment.transcribed,
        "transcript_text": fragment.transcript_text
    } 