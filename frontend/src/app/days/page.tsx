// путь: frontend/src/app/days/page.tsx
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { daysAPI, DayInfo } from '@/lib/api';
import { Calendar, Clock, FileText, CheckCircle, XCircle, LogOut } from 'lucide-react';

export default function DaysPage() {
  const [days, setDays] = useState<DayInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  
  const { user, logout } = useAuth();

  useEffect(() => {
    loadDays();
  }, []);

  const loadDays = async () => {
    try {
      setIsLoading(true);
      const daysData = await daysAPI.getDays();
      setDays(daysData);
    } catch (error) {
      console.error('Failed to load days:', error);
      setError('Ошибка загрузки данных');
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
      day: 'numeric',
      month: 'long',
      year: 'numeric'
    });
  };

  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = Math.floor(minutes % 60);
    
    if (hours > 0) {
      return `${hours}ч ${mins}м`;
    }
    return `${mins}м`;
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                AI Assistant
              </h1>
              <p className="text-sm text-gray-600">
                Система речевой записи и анализа
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">
                {user?.full_name || user?.username}
              </span>
              <button
                onClick={logout}
                className="flex items-center space-x-2 px-3 py-2 text-sm text-gray-600 hover:text-gray-900"
              >
                <LogOut className="h-4 w-4" />
                <span>Выйти</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-900">
              Дни записей
            </h2>
            <button
              onClick={loadDays}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Обновить
            </button>
          </div>

          {error && (
            <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
              <p className="text-red-800">{error}</p>
            </div>
          )}

          {days.length === 0 ? (
            <div className="text-center py-12">
              <Calendar className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">
                Нет записей
              </h3>
              <p className="mt-1 text-sm text-gray-500">
                Записи появятся здесь после обработки аудиофайлов
              </p>
            </div>
          ) : (
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {days.map((day) => (
                <Link
                  key={day.id}
                  href={`/day/${day.date}`}
                  className="block bg-white rounded-lg shadow hover:shadow-md transition-shadow duration-200"
                >
                  <div className="p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-gray-900">
                        {formatDate(day.date)}
                      </h3>
                                             <div className="flex space-x-2">
                         {day.has_medium_summary ? (
                           <CheckCircle className="h-5 w-5 text-green-500" />
                         ) : (
                           <XCircle className="h-5 w-5 text-gray-400" />
                         )}
                         {day.has_short_summary ? (
                           <CheckCircle className="h-5 w-5 text-green-500" />
                         ) : (
                           <XCircle className="h-5 w-5 text-gray-400" />
                         )}
                       </div>
                    </div>

                    <div className="space-y-3">
                      <div className="flex items-center text-sm text-gray-600">
                        <FileText className="h-4 w-4 mr-2" />
                        <span>{day.total_fragments} фрагментов</span>
                      </div>
                      
                      <div className="flex items-center text-sm text-gray-600">
                        <Clock className="h-4 w-4 mr-2" />
                        <span>{formatDuration(day.total_duration_minutes)}</span>
                      </div>
                    </div>

                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <div className="flex items-center justify-between text-xs text-gray-500">
                        <span>Статус обработки:</span>
                        <span className={`px-2 py-1 rounded-full text-xs ${
                          day.is_processed 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {day.is_processed ? 'Завершено' : 'В процессе'}
                        </span>
                      </div>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
} 