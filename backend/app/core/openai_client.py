# путь: backend/app/core/openai_client.py
"""
OpenAI API клиент для генерации summary.
"""

import logging
from typing import Optional
from openai import OpenAI
from libs.config import get_openai_config

logger = logging.getLogger(__name__)


class OpenAIClient:
    """Клиент для работы с OpenAI API."""
    
    def __init__(self):
        """Инициализация OpenAI клиента."""
        self.config = get_openai_config()
        self.client = OpenAI(api_key=self.config["api_key"])
        
    async def generate_short_summary(self, medium_summary: str) -> Optional[str]:
        """Генерация краткого summary из medium summary."""
        try:
            prompt = f"""
            Создай краткую суть дня на основе следующего текста. 
            Выдели только самые важные события и ключевые моменты.
            Формат: краткий список основных пунктов.
            
            Текст для анализа:
            {medium_summary}
            
            Краткая суть дня:
            """
            
            response = self.client.chat.completions.create(
                model=self.config["model"],
                messages=[
                    {"role": "system", "content": "Ты помощник для создания кратких summary. Отвечай только по существу."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.config.get("max_tokens", 500),
                temperature=0.3
            )
            
            summary = response.choices[0].message.content.strip()
            logger.info(f"✅ Short summary сгенерирован: {len(summary)} символов")
            return summary
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации short summary: {e}")
            return None
    
    async def generate_medium_summary(self, full_text: str) -> Optional[str]:
        """Генерация среднего summary из полного текста."""
        try:
            prompt = f"""
            Создай ретроспективу дня на основе следующего текста.
            Структурируй информацию по времени и важности.
            Убери лишние детали, оставь только значимые события.
            
            Полный текст дня:
            {full_text}
            
            Ретроспектива дня:
            """
            
            response = self.client.chat.completions.create(
                model=self.config["model"],
                messages=[
                    {"role": "system", "content": "Ты помощник для создания ретроспектив. Структурируй информацию логично."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.config.get("max_tokens", 1000),
                temperature=0.4
            )
            
            summary = response.choices[0].message.content.strip()
            logger.info(f"✅ Medium summary сгенерирован: {len(summary)} символов")
            return summary
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации medium summary: {e}")
            return None
    
    def is_available(self) -> bool:
        """Проверка доступности OpenAI API."""
        return bool(self.config.get("api_key")) 