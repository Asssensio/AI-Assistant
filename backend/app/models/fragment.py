# путь: backend/app/models/fragment.py
"""
ORM модель для аудио фрагментов.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .database import Base


class Fragment(Base):
    """Модель аудио фрагмента."""
    
    __tablename__ = "fragments"
    
    id = Column(Integer, primary_key=True, index=True)
    day_id = Column(Integer, ForeignKey("days.id"), nullable=False)
    
    # File information
    file_path = Column(String(512), nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)
    file_size_bytes = Column(Integer, nullable=True)
    
    # Audio metadata
    duration_seconds = Column(Float, nullable=True)
    sample_rate = Column(Integer, default=16000)
    channels = Column(Integer, default=1)
    
    # Time information
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    
    # Processing status
    transcribed = Column(Boolean, default=False)
    transcription_completed_at = Column(DateTime, nullable=True)
    
    # Whisper output
    transcript_text = Column(Text, nullable=True)
    whisper_segments = Column(JSON, nullable=True)  # Whisper segments with timestamps
    whisper_model_used = Column(String(50), nullable=True)
    
    # Processing metadata
    processing_error = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    day = relationship("Day", back_populates="fragments")
    
    @property
    def duration_minutes(self) -> Optional[float]:
        """Продолжительность в минутах."""
        return self.duration_seconds / 60.0 if self.duration_seconds else None
    
    @property
    def is_ready_for_processing(self) -> bool:
        """Готов ли к обработке."""
        return bool(self.file_path and not self.transcribed and not self.processing_error)
    
    def get_whisper_timestamps(self) -> list:
        """Получить timestamps из Whisper."""
        if not self.whisper_segments:
            return []
        return [
            {
                "start": segment.get("start", 0),
                "end": segment.get("end", 0),
                "text": segment.get("text", "")
            }
            for segment in self.whisper_segments
        ]
    
    def __repr__(self) -> str:
        return f"<Fragment(id={self.id}, file={self.original_filename}, transcribed={self.transcribed})>" 