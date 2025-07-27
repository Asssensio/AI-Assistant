"""
API для работы с аудио фрагментами.
"""

from typing import List
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class FragmentInfo(BaseModel):
    """Информация о фрагменте."""
    id: int
    file_path: str
    start_time: str
    end_time: str
    duration_seconds: int
    transcribed: bool


@router.get("/", response_model=List[FragmentInfo])
async def get_fragments():
    """Получение списка всех фрагментов."""
    # TODO: Реализовать получение из БД
    return []


@router.get("/{fragment_id}")
async def get_fragment(fragment_id: int):
    """Получение конкретного фрагмента."""
    # TODO: Реализовать получение фрагмента
    return {
        "id": fragment_id,
        "transcript": "",
        "timestamps": []
    } 