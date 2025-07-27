// путь: frontend/src/components/RetrospectiveEditor.tsx
'use client';

import { useState, useEffect } from 'react';
import { Trash2, Plus, Save, Edit3 } from 'lucide-react';

interface RetrospectiveEditorProps {
  fullText: string;
  mediumSummary?: string;
  onSave: (summary: string) => Promise<void>;
  isSaving?: boolean;
}

interface TextBlock {
  id: string;
  text: string;
  isEditing: boolean;
}

export default function RetrospectiveEditor({ 
  fullText, 
  mediumSummary, 
  onSave, 
  isSaving = false 
}: RetrospectiveEditorProps) {
  const [blocks, setBlocks] = useState<TextBlock[]>([]);
  const [isEditing, setIsEditing] = useState(false);

  // Инициализация блоков из medium summary или разбивка full text
  useEffect(() => {
    if (mediumSummary) {
      // Если есть medium summary, разбиваем его на блоки
      const summaryBlocks = mediumSummary.split('\n\n').filter(block => block.trim());
      setBlocks(summaryBlocks.map((text, index) => ({
        id: `block-${index}`,
        text: text.trim(),
        isEditing: false
      })));
    } else if (fullText) {
      // Если нет medium summary, разбиваем full text на блоки по предложениям
      const sentences = fullText.split(/[.!?]+/).filter(sentence => sentence.trim());
      const textBlocks = sentences.map((sentence, index) => ({
        id: `block-${index}`,
        text: sentence.trim(),
        isEditing: false
      }));
      setBlocks(textBlocks);
    }
  }, [fullText, mediumSummary]);

  const addBlock = () => {
    const newBlock: TextBlock = {
      id: `block-${Date.now()}`,
      text: '',
      isEditing: true
    };
    setBlocks([...blocks, newBlock]);
  };

  const updateBlock = (id: string, text: string) => {
    setBlocks(blocks.map(block => 
      block.id === id ? { ...block, text } : block
    ));
  };

  const deleteBlock = (id: string) => {
    setBlocks(blocks.filter(block => block.id !== id));
  };

  const mergeBlocks = (index: number) => {
    if (index >= blocks.length - 1) return;
    
    const newBlocks = [...blocks];
    const currentBlock = newBlocks[index];
    const nextBlock = newBlocks[index + 1];
    
    currentBlock.text = `${currentBlock.text} ${nextBlock.text}`;
    newBlocks.splice(index + 1, 1);
    
    setBlocks(newBlocks);
  };

  const toggleBlockEdit = (id: string) => {
    setBlocks(blocks.map(block => 
      block.id === id ? { ...block, isEditing: !block.isEditing } : block
    ));
  };

  const handleSave = async () => {
    const summary = blocks
      .map(block => block.text.trim())
      .filter(text => text.length > 0)
      .join('\n\n');
    
    await onSave(summary);
    setIsEditing(false);
  };

  const handleCancel = () => {
    // Восстанавливаем исходные блоки
    if (mediumSummary) {
      const summaryBlocks = mediumSummary.split('\n\n').filter(block => block.trim());
      setBlocks(summaryBlocks.map((text, index) => ({
        id: `block-${index}`,
        text: text.trim(),
        isEditing: false
      })));
    }
    setIsEditing(false);
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            Ретроспектива дня
          </h3>
          <p className="text-sm text-gray-600">
            Редактируйте текст, объединяйте или удаляйте блоки для создания ретроспективы
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          {!isEditing ? (
            <button
              onClick={() => setIsEditing(true)}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              <Edit3 className="h-4 w-4" />
              <span>Редактировать</span>
            </button>
          ) : (
            <>
              <button
                onClick={handleCancel}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
              >
                Отмена
              </button>
              <button
                onClick={handleSave}
                disabled={isSaving}
                className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors disabled:opacity-50"
              >
                <Save className="h-4 w-4" />
                <span>{isSaving ? 'Сохранение...' : 'Сохранить'}</span>
              </button>
            </>
          )}
        </div>
      </div>

      {blocks.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <p>Нет текста для редактирования</p>
        </div>
      ) : (
        <div className="space-y-4">
          {blocks.map((block, index) => (
            <div
              key={block.id}
              className="border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors"
            >
              <div className="flex items-start justify-between mb-2">
                <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                  Блок {index + 1}
                </span>
                
                {isEditing && (
                  <div className="flex items-center space-x-2">
                    {index < blocks.length - 1 && (
                      <button
                        onClick={() => mergeBlocks(index)}
                        className="text-blue-600 hover:text-blue-800 text-sm"
                      >
                        Объединить с следующим
                      </button>
                    )}
                    <button
                      onClick={() => deleteBlock(block.id)}
                      className="text-red-600 hover:text-red-800"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                )}
              </div>

              {block.isEditing ? (
                <textarea
                  value={block.text}
                  onChange={(e) => updateBlock(block.id, e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  rows={3}
                  placeholder="Введите текст блока..."
                />
              ) : (
                <div className="p-3 bg-gray-50 rounded-md">
                  <p className="text-gray-700 leading-relaxed">
                    {block.text || <span className="text-gray-400 italic">Пустой блок</span>}
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {isEditing && (
        <div className="mt-6 pt-6 border-t border-gray-200">
          <button
            onClick={addBlock}
            className="flex items-center space-x-2 px-4 py-2 text-blue-600 border border-blue-300 rounded-md hover:bg-blue-50 transition-colors"
          >
            <Plus className="h-4 w-4" />
            <span>Добавить блок</span>
          </button>
        </div>
      )}

      {!isEditing && blocks.length > 0 && (
        <div className="mt-6 pt-6 border-t border-gray-200">
          <div className="text-sm text-gray-600">
            <p>Всего блоков: {blocks.length}</p>
            <p>Общий объем текста: {blocks.reduce((sum, block) => sum + block.text.length, 0)} символов</p>
          </div>
        </div>
      )}
    </div>
  );
} 