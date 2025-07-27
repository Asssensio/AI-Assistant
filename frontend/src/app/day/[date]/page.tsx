// путь: frontend/src/app/day/[date]/page.tsx
'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { daysAPI, DayDetails, AudioPlaylist } from '@/lib/api';
import AudioPlayer from '@/components/AudioPlayer';
import SynchronizedText from '@/components/SynchronizedText';
import RetrospectiveEditor from '@/components/RetrospectiveEditor';
import { 
  ArrowLeft, 
  FileText, 
  Edit3, 
  Sparkles, 
  Play, 
  Pause,
  CheckCircle,
  XCircle,
  Loader2
} from 'lucide-react';

type TabType = 'full-text' | 'retrospective' | 'summary';

export default function DayPage() {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuth();
  
  const [dayDetails, setDayDetails] = useState<DayDetails | null>(null);
  const [playlist, setPlaylist] = useState<AudioPlaylist | null>(null);
  const [currentTab, setCurrentTab] = useState<TabType>('full-text');
  const [currentTime, setCurrentTime] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState('');

  const date = params.date as string;

  useEffect(() => {
    loadDayData();
  }, [date]);

  const loadDayData = async () => {
    try {
      setIsLoading(true);
      setError('');

      const [details, audioPlaylist] = await Promise.all([
        daysAPI.getDayDetails(date),
        daysAPI.getAudioPlaylist(date)
      ]);

      setDayDetails(details);
      setPlaylist(audioPlaylist);
    } catch (error) {
      console.error('Failed to load day data:', error);
      setError('Ошибка загрузки данных дня');
    } finally {
      setIsLoading(false);
    }
  };

  const handleTimeUpdate = (time: number) => {
    setCurrentTime(time);
  };

  const handleSegmentClick = (segmentIndex: number, startTime: number) => {
    // Здесь можно добавить логику для перехода к конкретному моменту в аудио
    console.log('Segment clicked:', segmentIndex, startTime);
  };

  const handleSaveRetrospective = async (summary: string) => {
    try {
      setIsSaving(true);
      await daysAPI.updateSummary(date, { medium_summary: summary });
      await loadDayData(); // Перезагружаем данные
    } catch (error) {
      console.error('Failed to save retrospective:', error);
      setError('Ошибка сохранения ретроспективы');
    } finally {
      setIsSaving(false);
    }
  };

  const handleGenerateShortSummary = async () => {
    try {
      setIsGenerating(true);
      const updatedDay = await daysAPI.generateShortSummary(date);
      setDayDetails(updatedDay);
    } catch (error) {
      console.error('Failed to generate short summary:', error);
      setError('Ошибка генерации краткого summary');
    } finally {
      setIsGenerating(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={loadDayData}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Попробовать снова
          </button>
        </div>
      </div>
    );
  }

  if (!dayDetails) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600 mb-4">День не найден</p>
          <Link
            href="/days"
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Вернуться к списку дней
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-6">
            <div className="flex items-center space-x-4">
              <Link
                href="/days"
                className="flex items-center space-x-2 text-gray-600 hover:text-gray-900"
              >
                <ArrowLeft className="h-5 w-5" />
                <span>Назад к дням</span>
              </Link>
              <div className="h-6 w-px bg-gray-300" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  {formatDate(dayDetails.date)}
                </h1>
                <p className="text-sm text-gray-600">
                  {dayDetails.total_fragments} фрагментов • {Math.round(dayDetails.total_duration_minutes)} минут
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">
                {user?.full_name || user?.username}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Audio Player */}
          {playlist && playlist.playlist.length > 0 && (
            <div className="mb-8">
              <AudioPlayer
                playlist={playlist}
                onTimeUpdate={handleTimeUpdate}
                onSegmentClick={handleSegmentClick}
              />
            </div>
          )}

          {/* Tabs */}
          <div className="mb-6">
            <div className="border-b border-gray-200">
              <nav className="-mb-px flex space-x-8">
                <button
                  onClick={() => setCurrentTab('full-text')}
                  className={`py-2 px-1 border-b-2 font-medium text-sm ${
                    currentTab === 'full-text'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    <FileText className="h-4 w-4" />
                    <span>Полный текст</span>
                  </div>
                </button>
                
                <button
                  onClick={() => setCurrentTab('retrospective')}
                  className={`py-2 px-1 border-b-2 font-medium text-sm ${
                    currentTab === 'retrospective'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    <Edit3 className="h-4 w-4" />
                    <span>Ретроспектива</span>
                    {dayDetails.has_medium_summary ? (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    ) : (
                      <XCircle className="h-4 w-4 text-gray-400" />
                    )}
                  </div>
                </button>
                
                <button
                  onClick={() => setCurrentTab('summary')}
                  className={`py-2 px-1 border-b-2 font-medium text-sm ${
                    currentTab === 'summary'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    <Sparkles className="h-4 w-4" />
                    <span>Суть дня</span>
                    {dayDetails.has_short_summary ? (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    ) : (
                      <XCircle className="h-4 w-4 text-gray-400" />
                    )}
                  </div>
                </button>
              </nav>
            </div>
          </div>

          {/* Tab content */}
          <div className="space-y-6">
            {currentTab === 'full-text' && (
              <SynchronizedText
                playlist={playlist!}
                currentTime={currentTime}
                onSegmentClick={handleSegmentClick}
              />
            )}

            {currentTab === 'retrospective' && (
              <RetrospectiveEditor
                fullText={dayDetails.full_text || ''}
                mediumSummary={dayDetails.medium_summary}
                onSave={handleSaveRetrospective}
                isSaving={isSaving}
              />
            )}

            {currentTab === 'summary' && (
              <div className="bg-white rounded-lg shadow-lg p-6">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      Суть дня
                    </h3>
                    <p className="text-sm text-gray-600">
                      Краткое резюме основных событий и ключевых моментов
                    </p>
                  </div>
                  
                  {!dayDetails.has_short_summary && dayDetails.has_medium_summary && (
                    <button
                      onClick={handleGenerateShortSummary}
                      disabled={isGenerating}
                      className="flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors disabled:opacity-50"
                    >
                      {isGenerating ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Sparkles className="h-4 w-4" />
                      )}
                      <span>{isGenerating ? 'Генерация...' : 'Сгенерировать суть дня'}</span>
                    </button>
                  )}
                </div>

                {dayDetails.short_summary ? (
                  <div className="prose max-w-none">
                    <div className="bg-gray-50 rounded-lg p-4">
                      <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                        {dayDetails.short_summary}
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    {dayDetails.has_medium_summary ? (
                      <div>
                        <p>Краткое резюме еще не создано</p>
                        <p className="text-sm mt-2">Нажмите "Сгенерировать суть дня" для создания</p>
                      </div>
                    ) : (
                      <div>
                        <p>Сначала создайте ретроспективу дня</p>
                        <p className="text-sm mt-2">Перейдите на вкладку "Ретроспектива"</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
} 