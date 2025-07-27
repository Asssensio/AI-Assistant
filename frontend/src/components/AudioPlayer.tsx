// путь: frontend/src/components/AudioPlayer.tsx
'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import WaveSurfer from 'wavesurfer.js';
import { Play, Pause, Volume2, VolumeX } from 'lucide-react';
import { AudioPlaylist } from '@/lib/api';

interface AudioPlayerProps {
  playlist: AudioPlaylist;
  onTimeUpdate?: (currentTime: number) => void;
  onSegmentClick?: (segmentIndex: number, startTime: number) => void;
}

export default function AudioPlayer({ playlist, onTimeUpdate, onSegmentClick }: AudioPlayerProps) {
  const waveformRef = useRef<HTMLDivElement>(null);
  const wavesurferRef = useRef<WaveSurfer | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(0.5);
  const [isMuted, setIsMuted] = useState(false);
  const [currentSegment, setCurrentSegment] = useState(0);

  // Инициализация WaveSurfer
  useEffect(() => {
    if (!waveformRef.current) return;

    const wavesurfer = WaveSurfer.create({
      container: waveformRef.current,
      waveColor: '#4F46E5',
      progressColor: '#7C3AED',
      cursorColor: '#1F2937',
      barWidth: 2,
      barRadius: 3,
      cursorWidth: 1,
      height: 80,
      barGap: 1,
      responsive: true,
      normalize: true,
    });

    wavesurferRef.current = wavesurfer;

    // Создаем единый аудиофайл из плейлиста
    const createAudioBlob = async () => {
      try {
        const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
        const audioBuffers: AudioBuffer[] = [];

        // Загружаем все аудиофайлы
        for (const fragment of playlist.playlist) {
          const response = await fetch(fragment.url);
          const arrayBuffer = await response.arrayBuffer();
          const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
          audioBuffers.push(audioBuffer);
        }

        // Объединяем все фрагменты
        const totalLength = audioBuffers.reduce((sum, buffer) => sum + buffer.length, 0);
        const mergedBuffer = audioContext.createBuffer(1, totalLength, audioBuffers[0].sampleRate);
        const mergedData = mergedBuffer.getChannelData(0);

        let offset = 0;
        for (const buffer of audioBuffers) {
          const data = buffer.getChannelData(0);
          mergedData.set(data, offset);
          offset += data.length;
        }

        // Конвертируем в WAV
        const wavBlob = audioBufferToWav(mergedBuffer);
        const url = URL.createObjectURL(wavBlob);
        
        wavesurfer.load(url);
        setDuration(playlist.total_duration);
      } catch (error) {
        console.error('Error creating audio blob:', error);
        // Fallback: загружаем первый фрагмент
        if (playlist.playlist.length > 0) {
          wavesurfer.load(playlist.playlist[0].url);
        }
      }
    };

    createAudioBlob();

    // Event listeners
    wavesurfer.on('ready', () => {
      setDuration(wavesurfer.getDuration());
      wavesurfer.setVolume(volume);
    });

    wavesurfer.on('audioprocess', (currentTime) => {
      setCurrentTime(currentTime);
      onTimeUpdate?.(currentTime);
      
      // Определяем текущий сегмент
      const segmentIndex = playlist.playlist.findIndex(fragment => 
        currentTime >= fragment.offset && 
        currentTime < fragment.offset + fragment.duration
      );
      if (segmentIndex !== -1 && segmentIndex !== currentSegment) {
        setCurrentSegment(segmentIndex);
      }
    });

    wavesurfer.on('play', () => setIsPlaying(true));
    wavesurfer.on('pause', () => setIsPlaying(false));
    wavesurfer.on('finish', () => setIsPlaying(false));

    return () => {
      wavesurfer.destroy();
    };
  }, [playlist]);

  // Обработчики управления
  const togglePlay = useCallback(() => {
    if (wavesurferRef.current) {
      wavesurferRef.current.playPause();
    }
  }, []);

  const handleVolumeChange = useCallback((newVolume: number) => {
    setVolume(newVolume);
    if (wavesurferRef.current) {
      wavesurferRef.current.setVolume(newVolume);
    }
  }, []);

  const toggleMute = useCallback(() => {
    setIsMuted(!isMuted);
    if (wavesurferRef.current) {
      wavesurferRef.current.setVolume(isMuted ? volume : 0);
    }
  }, [isMuted, volume]);

  const seekTo = useCallback((time: number) => {
    if (wavesurferRef.current) {
      wavesurferRef.current.seekTo(time / duration);
    }
  }, [duration]);

  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      {/* Waveform */}
      <div ref={waveformRef} className="mb-4" />
      
      {/* Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={togglePlay}
            className="flex items-center justify-center w-12 h-12 bg-blue-600 text-white rounded-full hover:bg-blue-700 transition-colors"
          >
            {isPlaying ? <Pause className="h-5 w-5" /> : <Play className="h-5 w-5" />}
          </button>
          
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">{formatTime(currentTime)}</span>
            <span className="text-sm text-gray-400">/</span>
            <span className="text-sm text-gray-600">{formatTime(duration)}</span>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <button
              onClick={toggleMute}
              className="text-gray-600 hover:text-gray-800"
            >
              {isMuted ? <VolumeX className="h-5 w-5" /> : <Volume2 className="h-5 w-5" />}
            </button>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={isMuted ? 0 : volume}
              onChange={(e) => handleVolumeChange(parseFloat(e.target.value))}
              className="w-20"
            />
          </div>
        </div>
      </div>

      {/* Progress bar */}
      <div className="mt-4">
        <input
          type="range"
          min="0"
          max={duration}
          step="0.1"
          value={currentTime}
          onChange={(e) => seekTo(parseFloat(e.target.value))}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
        />
      </div>

      {/* Current segment info */}
      {playlist.playlist[currentSegment] && (
        <div className="mt-4 p-3 bg-gray-50 rounded-md">
          <div className="text-sm text-gray-600">
            Текущий фрагмент: {playlist.playlist[currentSegment].filename}
          </div>
          <div className="text-xs text-gray-500">
            {formatTime(playlist.playlist[currentSegment].offset)} - {formatTime(playlist.playlist[currentSegment].offset + playlist.playlist[currentSegment].duration)}
          </div>
        </div>
      )}
    </div>
  );
}

// Вспомогательная функция для конвертации AudioBuffer в WAV
function audioBufferToWav(buffer: AudioBuffer): Blob {
  const length = buffer.length;
  const numberOfChannels = buffer.numberOfChannels;
  const sampleRate = buffer.sampleRate;
  const arrayBuffer = new ArrayBuffer(44 + length * numberOfChannels * 2);
  const view = new DataView(arrayBuffer);

  // WAV header
  const writeString = (offset: number, string: string) => {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  };

  writeString(0, 'RIFF');
  view.setUint32(4, 36 + length * numberOfChannels * 2, true);
  writeString(8, 'WAVE');
  writeString(12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, numberOfChannels, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * numberOfChannels * 2, true);
  view.setUint16(32, numberOfChannels * 2, true);
  view.setUint16(34, 16, true);
  writeString(36, 'data');
  view.setUint32(40, length * numberOfChannels * 2, true);

  // Audio data
  let offset = 44;
  for (let i = 0; i < length; i++) {
    for (let channel = 0; channel < numberOfChannels; channel++) {
      const sample = Math.max(-1, Math.min(1, buffer.getChannelData(channel)[i]));
      view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7FFF, true);
      offset += 2;
    }
  }

  return new Blob([arrayBuffer], { type: 'audio/wav' });
} 