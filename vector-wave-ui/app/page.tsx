'use client';

import { useState, useEffect } from "react";
import { Folder, MessageSquare, Sparkles, Clock, TrendingUp, FileText, BarChart3 } from "lucide-react";

export default function Home() {
  const [folders, setFolders] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Auto-load content folders on mount
  useEffect(() => {
    const loadFolders = async () => {
      try {
        const response = await fetch('/api/list-content-folders');
        const data = await response.json();
        if (data.folders) {
          setFolders(data.folders);
        }
      } catch (error) {
        console.error('Failed to load folders:', error);
      } finally {
        setIsLoading(false);
      }
    };

    // Simulate assistant-ui auto-execution
    setTimeout(loadFolders, 500);
  }, []);

  const analyzeFolder = async (folderName: string) => {
    setIsAnalyzing(true);
    setAnalysisResult(null);
    
    try {
      const response = await fetch('/api/analyze-folder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ folder_path: `content/raw/${folderName}` })
      });
      const data = await response.json();
      setAnalysisResult({ ...data, folder: folderName });
    } catch (error) {
      console.error('Analysis failed:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-gray-50">
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <Sparkles className="w-6 h-6 text-blue-600" />
              <h1 className="text-2xl font-bold text-gray-900">Vector Wave Editorial AI</h1>
            </div>
            <div className="ml-auto flex items-center gap-4 text-sm text-gray-600">
              <div className="flex items-center gap-1">
                <Clock className="w-4 h-4" />
                <span>Assistant-UI</span>
              </div>
              <div className="flex items-center gap-1">
                <TrendingUp className="w-4 h-4" />
                <span>Auto-Execution</span>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 p-6">
          <div className="max-w-4xl mx-auto">
            {/* Welcome Message */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                  <MessageSquare className="w-5 h-5 text-blue-600" />
                </div>
                <div className="flex-1">
                  <h2 className="text-lg font-semibold text-gray-900 mb-2">
                    Cześć! 👋 Jestem asystentem redakcyjnym Vector Wave
                  </h2>
                  <p className="text-gray-600">
                    Automatycznie załadowałem dostępne tematy do analizy. Kliknij "Analizuj" przy folderze aby rozpocząć.
                  </p>
                </div>
              </div>
            </div>

            {/* Folders List */}
            {isLoading ? (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center gap-3">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                  <span className="text-gray-600">Ładuję dostępne tematy...</span>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
                <div className="flex items-center gap-3 mb-4">
                  <Folder className="w-5 h-5 text-green-600" />
                  <h3 className="text-lg font-semibold text-gray-900">
                    📂 Dostępne tematy ({folders.length})
                  </h3>
                </div>
                
                <div className="grid gap-3">
                  {folders.map((folder, idx) => (
                    <div key={idx} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                      <div className="flex justify-between items-center">
                        <div className="flex-1">
                          <div className="font-medium text-gray-900">{folder.name}</div>
                          <div className="text-sm text-gray-600 flex items-center gap-4">
                            <span className="flex items-center gap-1">
                              <FileText className="w-4 h-4" />
                              {folder.files_count} plików
                            </span>
                            {folder.modified && (
                              <span className="text-xs text-gray-500">
                                Zmodyfikowany: {new Date(folder.modified).toLocaleDateString('pl')}
                              </span>
                            )}
                          </div>
                        </div>
                        <button 
                          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors flex items-center gap-2"
                          onClick={() => analyzeFolder(folder.name)}
                          disabled={isAnalyzing}
                        >
                          {isAnalyzing ? (
                            <>
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                              Analizuję...
                            </>
                          ) : (
                            <>
                              <BarChart3 className="w-4 h-4" />
                              Analizuj
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Analysis Results */}
            {analysisResult && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-start gap-3 mb-4">
                  <BarChart3 className="w-5 h-5 text-blue-600 mt-1" />
                  <h3 className="text-lg font-semibold text-gray-900">
                    Analiza folderu: {analysisResult.folder}
                  </h3>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                  <div className="bg-blue-50 rounded-lg p-4">
                    <div className="text-sm text-blue-600 font-medium">Liczba plików</div>
                    <div className="text-2xl font-bold text-blue-900">{analysisResult.filesCount}</div>
                  </div>
                  <div className="bg-green-50 rounded-lg p-4">
                    <div className="text-sm text-green-600 font-medium">Typ contentu</div>
                    <div className="text-lg font-semibold text-green-900">{analysisResult.contentType}</div>
                  </div>
                  <div className="bg-purple-50 rounded-lg p-4">
                    <div className="text-sm text-purple-600 font-medium">Ocena wartości</div>
                    <div className="text-2xl font-bold text-purple-900">{analysisResult.valueScore}/10</div>
                  </div>
                </div>

                {analysisResult.recommendation && (
                  <div className="mb-6">
                    <div className="text-sm font-medium text-gray-700 mb-2">💡 Rekomendacja</div>
                    <div className="bg-gray-50 rounded-lg p-4">
                      <p className="text-gray-800 italic">{analysisResult.recommendation}</p>
                    </div>
                  </div>
                )}

                {analysisResult.topics && analysisResult.topics.length > 0 && (
                  <div>
                    <div className="text-sm font-medium text-gray-700 mb-3">🎯 Propozycje tematów</div>
                    <div className="grid gap-3">
                      {analysisResult.topics.map((topic: any, idx: number) => (
                        <div key={idx} className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                          <div className="font-medium text-blue-900 mb-1">{topic.title}</div>
                          <div className="text-sm text-blue-700 flex items-center gap-4">
                            <span>📱 {topic.platform}</span>
                            <span>🔥 Potencjał: {topic.viralScore}/10</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="mt-6 flex gap-3">
                  <button className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-colors">
                    💾 Zapisz metadane
                  </button>
                  <button className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg transition-colors">
                    🚀 Uruchom pipeline
                  </button>
                  <button className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg transition-colors">
                    📊 Szczegółowy raport
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="bg-gray-100 px-6 py-3 border-t border-gray-200">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <div className="flex items-center gap-4">
              <span>💡 Asystent automatycznie załadował tematy przy starcie</span>
              <span>🚀 Implementacja assistant-ui z auto-execution</span>
            </div>
            <div className="flex items-center gap-1">
              <MessageSquare className="w-4 h-4" />
              <span>Vector Wave AI v2.0</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}