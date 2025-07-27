# путь: backend/app/models/day.py
"""
ORM модель для дней записей.
"""

from datetime import date, datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, Date, DateTime, Float, Boolean, Text
from sqlalchemy.orm import relationship
from .database import Base


class Day(Base):
    """Модель дня с записями."""
    
    __tablename__ = "days"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, index=True, nullable=False)
    total_fragments = Column(Integer, default=0)
    total_duration_seconds = Column(Float, default=0.0)
    
    # Summary fields
    short_summary = Column(Text, nullable=True)
    medium_summary = Column(Text, nullable=True)
    full_text = Column(Text, nullable=True)
    
    # Processing status
    is_processed = Column(Boolean, default=False)
    whisper_completed = Column(Boolean, default=False)
    summary_generated = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    fragments = relationship("Fragment", back_populates="day", cascade="all, delete-orphan")
    
    @property
    def total_duration_minutes(self) -> float:
        """Общая продолжительность в минутах."""
        return self.total_duration_seconds / 60.0
    
    @property
    def has_short_summary(self) -> bool:
        """Есть ли короткое резюме."""
        return bool(self.short_summary)
    
    @property
    def has_medium_summary(self) -> bool:
        """Есть ли среднее резюме."""
        return bool(self.medium_summary)
    
    def __repr__(self) -> str:
        return f"<Day(date={self.date}, fragments={self.total_fragments})>" 