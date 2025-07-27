// путь: frontend/src/components/SynchronizedText.tsx
'use client';

import { useEffect, useState, useRef } from 'react';
import { AudioPlaylist } from '@/lib/api';

interface SynchronizedTextProps {
  playlist: AudioPlaylist;
  currentTime: number;
  onSegmentClick?: (segmentIndex: number, startTime: number) => void;
}

interface TextSegment {
  id: number;
  start: number;
  end: number;
  text: string;
  isActive: boolean;
  fragmentIndex: number;
}

export default function SynchronizedText({ playlist, currentTime, onSegmentClick }: SynchronizedTextProps) {
  const [segments, setSegments] = useState<TextSegment[]>([]);
  const [activeSegmentId, setActiveSegmentId] = useState<number | null>(null);
  const activeSegmentRef = useRef<HTMLDivElement>(null);

  // Парсим timestamps из всех фрагментов
  useEffect(() => {
    const allSegments: TextSegment[] = [];
    
    playlist.playlist.forEach((fragment, fragmentIndex) => {
      if (fragment.timestamps) {
        fragment.timestamps.forEach((timestamp, segmentIndex) => {
          allSegments.push({
            id: fragmentIndex * 1000 + segmentIndex,
            start: fragment.offset + timestamp.start,
            end: fragment.offset + timestamp.end,
            text: timestamp.text,
            isActive: false,
            fragmentIndex
          });
        });
      }
    });

    // Сортируем по времени начала
    allSegments.sort((a, b) => a.start - b.start);
    setSegments(allSegments);
  }, [playlist]);

  // Определяем активный сегмент
  useEffect(() => {
    const activeSegment = segments.find(segment => 
      currentTime >= segment.start && currentTime <= segment.end
    );

    if (activeSegment && activeSegment.id !== activeSegmentId) {
      setActiveSegmentId(activeSegment.id);
      
      // Прокручиваем к активному сегменту
      setTimeout(() => {
        if (activeSegmentRef.current) {
          activeSegmentRef.current.scrollIntoView({
            behavior: 'smooth',
            block: 'center'
          });
        }
      }, 100);
    }
  }, [currentTime, segments, activeSegmentId]);

  const handleSegmentClick = (segment: TextSegment) => {
    onSegmentClick?.(segment.fragmentIndex, segment.start);
  };

  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  if (segments.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="text-center text-gray-500">
          <p>Текст не найден</p>
          <p className="text-sm">Транскрипция будет доступна после обработки аудио</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Полный текст (синхронизированный)
        </h3>
        <p className="text-sm text-gray-600">
          Кликните по любому сегменту для перехода к этому моменту в аудио
        </p>
      </div>

      <div className="max-h-96 overflow-y-auto space-y-2">
        {segments.map((segment) => (
          <div
            key={segment.id}
            ref={segment.id === activeSegmentId ? activeSegmentRef : null}
            onClick={() => handleSegmentClick(segment)}
            className={`
              p-3 rounded-md cursor-pointer transition-all duration-200
              ${segment.id === activeSegmentId 
                ? 'bg-blue-50 border-l-4 border-blue-500 shadow-sm' 
                : 'bg-gray-50 hover:bg-gray-100 border-l-4 border-transparent'
              }
            `}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className={`text-sm leading-relaxed ${
                  segment.id === activeSegmentId ? 'text-blue-900' : 'text-gray-700'
                }`}>
                  {segment.text}
                </p>
              </div>
              <div className="ml-4 text-xs text-gray-500 whitespace-nowrap">
                {formatTime(segment.start)}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="flex items-center justify-between text-sm text-gray-600">
          <span>Всего сегментов: {segments.length}</span>
          {activeSegmentId !== null && (
            <span>Активный: {segments.find(s => s.id === activeSegmentId)?.text.substring(0, 50)}...</span>
          )}
        </div>
      </div>
    </div>
  );
} 