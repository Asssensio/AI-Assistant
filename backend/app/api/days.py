# путь: backend/app/api/days.py
"""
API для работы с днями записей.
"""

from typing import List
from datetime import date

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class DayInfo(BaseModel):
    """Информация о дне."""
    date: date
    total_fragments: int
    total_duration_minutes: int
    has_short_summary: bool
    has_medium_summary: bool


@router.get("/", response_model=List[DayInfo])
async def get_days():
    """Получение списка дней с записями."""
    # TODO: Реализовать получение из БД
    return []


@router.get("/{date}")
async def get_day_details(date: str):
    """Получение детальной информации о дне."""
    # TODO: Реализовать получение деталей дня
    return {
        "date": date,
        "fragments": [],
        "short_summary": "",
        "medium_summary": "",
        "full_text": ""
    } 