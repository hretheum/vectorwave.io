'use client';

import { useState, useEffect } from "react";
import { Folder, Sparkles, Clock, FileText, BarChart3, Zap, Brain, Target, TrendingUp, ArrowRight, Loader2, CheckCircle2, AlertCircle, MessageSquare } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ChatPanel } from "@/components/ChatPanel";

export default function Home() {
  const [folders, setFolders] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [selectedFolder, setSelectedFolder] = useState<string | null>(null);
  const [showChat, setShowChat] = useState(true);

  // Auto-load content folders on mount
  useEffect(() => {
    const loadFolders = async () => {
      try {
        console.log('🔄 Loading folders...');
        const response = await fetch('/api/list-content-folders');
        console.log('📡 Response status:', response.status);
        const data = await response.json();
        console.log('📂 Data received:', data);
        if (data.folders) {
          setFolders(data.folders);
          console.log('✅ Folders set:', data.folders);
        }
      } catch (error) {
        console.error('❌ Failed to load folders:', error);
      } finally {
        setIsLoading(false);
      }
    };

    // Simulate assistant-ui auto-execution
    setTimeout(loadFolders, 500);
  }, []);

  const analyzeFolder = async (folderName: string) => {
    console.log('🎯 Starting analysis for:', folderName);
    alert('Analyzing folder: ' + folderName); // Test alert
    setIsAnalyzing(true);
    setAnalysisResult(null);
    setSelectedFolder(folderName);
    
    try {
      const response = await fetch('/api/analyze-folder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ folder_path: `content/raw/${folderName}` })
      });
      
      console.log('📡 Response status:', response.status);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ Analysis error:', errorText);
        throw new Error(`Analysis failed: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('✅ Analysis data:', data);
      setAnalysisResult({ ...data, folder: folderName });
    } catch (error) {
      console.error('❌ Analysis failed:', error);
      // Show error to user
      setAnalysisResult({
        folder: folderName,
        error: true,
        message: 'Nie udało się przeanalizować folderu. Sprawdź czy backend działa.',
        filesCount: 0,
        contentType: 'ERROR',
        valueScore: 0,
        recommendation: 'Spróbuj ponownie za chwilę.'
      });
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-indigo-50">
      {/* Animated Background Pattern */}
      <div className="fixed inset-0 -z-10 overflow-hidden">
        <div className="absolute -top-40 -right-40 h-80 w-80 rounded-full bg-gradient-to-br from-indigo-300/20 to-purple-300/20 blur-3xl animate-pulse" />
        <div className="absolute -bottom-40 -left-40 h-80 w-80 rounded-full bg-gradient-to-tr from-purple-300/20 to-pink-300/20 blur-3xl animate-pulse delay-1000" />
      </div>

      {/* Header */}
      <header className="sticky top-0 z-50 backdrop-blur-lg bg-white/80 border-b border-gray-200/50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-lg blur animate-pulse" />
                <div className="relative bg-gradient-to-r from-indigo-600 to-purple-600 p-2 rounded-lg">
                  <Sparkles className="w-6 h-6 text-white" />
                </div>
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
                  Vector Wave Editorial AI
                </h1>
                <p className="text-sm text-gray-600">Inteligentny system zarządzania contentem</p>
              </div>
            </div>
            <div className="flex items-center gap-6">
              <Badge variant="success" className="gap-1">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                System Online
              </Badge>
              <div className="flex items-center gap-4 text-sm">
                <div className="flex items-center gap-1.5 text-gray-600">
                  <Clock className="w-4 h-4" />
                  <span>Auto-Execution</span>
                </div>
                <div className="flex items-center gap-1.5 text-gray-600">
                  <Brain className="w-4 h-4" />
                  <span>AI-Powered</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {/* Welcome Section */}
        <Card className="mb-8 border-0 shadow-xl bg-gradient-to-br from-white to-indigo-50/50">
          <CardHeader className="pb-4">
            <div className="flex items-start gap-4">
              <div className="p-3 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl shadow-lg">
                <Brain className="w-8 h-8 text-white" />
              </div>
              <div className="flex-1">
                <CardTitle className="text-2xl mb-2">Cześć! Jestem Twoim AI Asystentem Redakcyjnym 👋</CardTitle>
                <CardDescription className="text-base">
                  Automatycznie załadowałem dostępne tematy do analizy. Kliknij przy folderze, który Cię interesuje,
                  a pokażę Ci jego potencjał marketingowy i propozycje wykorzystania.
                </CardDescription>
              </div>
            </div>
          </CardHeader>
        </Card>

        {/* Folders Grid */}
        {isLoading ? (
          <Card className="p-12">
            <div className="flex flex-col items-center justify-center gap-4">
              <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
              <p className="text-gray-600">Ładuję dostępne tematy...</p>
            </div>
          </Card>
        ) : (
          <div className="grid gap-6 mb-8">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-100 rounded-lg">
                  <Folder className="w-5 h-5 text-green-600" />
                </div>
                <h2 className="text-xl font-semibold text-gray-900">
                  Dostępne tematy ({folders.length})
                </h2>
              </div>
              <Badge variant="secondary">
                Ostatnia aktualizacja: {new Date().toLocaleTimeString('pl')}
              </Badge>
            </div>
            
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3" onClick={() => console.log('🔥 Grid clicked!')}>
              {folders.map((folder, idx) => (
                <Card 
                  key={idx} 
                  className={cn(
                    "group relative overflow-hidden transition-all duration-300 hover:shadow-xl hover:-translate-y-1",
                    selectedFolder === folder.name && "ring-2 ring-indigo-500"
                  )}
                >
                  <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 to-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
                  <CardHeader className="pb-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <CardTitle className="text-lg group-hover:text-indigo-600 transition-colors">
                          {folder.name}
                        </CardTitle>
                        <div className="flex items-center gap-4 mt-2">
                          <Badge variant="outline" className="gap-1">
                            <FileText className="w-3 h-3" />
                            {folder.files_count} plików
                          </Badge>
                          {folder.modified && (
                            <span className="text-xs text-gray-500">
                              {new Date(folder.modified * 1000).toLocaleDateString('pl', {
                                day: 'numeric',
                                month: 'short',
                                hour: '2-digit',
                                minute: '2-digit'
                              })}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </CardHeader>
                  <CardFooter className="pt-0 relative z-10">
                    <button 
                      className="w-full inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-sm font-medium transition-all cursor-pointer bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg hover:from-indigo-700 hover:to-purple-700 hover:shadow-xl hover:-translate-y-0.5 h-10 px-4 py-2 group-hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        console.log('🔘 Button clicked for folder:', folder.name);
                        console.log('🔘 isAnalyzing:', isAnalyzing);
                        analyzeFolder(folder.name);
                      }}
                      disabled={isAnalyzing && selectedFolder === folder.name}
                      type="button"
                    >
                      {isAnalyzing && selectedFolder === folder.name ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          Analizuję...
                        </>
                      ) : (
                        <>
                          <BarChart3 className="w-4 h-4" />
                          Analizuj potencjał
                          <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                        </>
                      )}
                    </button>
                  </CardFooter>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Analysis Results */}
        {analysisResult && (
          <Card className="shadow-2xl border-0 overflow-hidden">
            <div className="h-2 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500" />
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3">
                  <div className={cn(
                    "p-2 rounded-lg",
                    analysisResult.error ? "bg-red-100" : "bg-indigo-100"
                  )}>
                    {analysisResult.error ? (
                      <AlertCircle className="w-5 h-5 text-red-600" />
                    ) : (
                      <BarChart3 className="w-5 h-5 text-indigo-600" />
                    )}
                  </div>
                  <div>
                    <CardTitle className="text-2xl mb-1">
                      {analysisResult.error ? "Błąd analizy" : "Analiza:"} {analysisResult.folder}
                    </CardTitle>
                    <CardDescription>
                      {analysisResult.error ? analysisResult.message : "Kompleksowa ocena potencjału marketingowego"}
                    </CardDescription>
                  </div>
                </div>
                {!analysisResult.error && (
                  <Badge variant={analysisResult.valueScore >= 8 ? "success" : "default"}>
                    Score: {analysisResult.valueScore}/10
                  </Badge>
                )}
              </div>
            </CardHeader>
            
            <CardContent className="space-y-6">
              {analysisResult.error ? (
                <div className="text-center py-8">
                  <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
                  <p className="text-lg font-medium text-gray-900 mb-2">Nie udało się przeanalizować folderu</p>
                  <p className="text-gray-600 mb-4">{analysisResult.message}</p>
                  <Button 
                    onClick={() => analyzeFolder(analysisResult.folder)}
                    variant="outline"
                  >
                    <ArrowRight className="w-4 h-4 mr-2" />
                    Spróbuj ponownie
                  </Button>
                </div>
              ) : (
                <>
              {/* Metrics Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card className="border-gray-100 shadow-sm">
                  <CardHeader className="pb-3">
                    <CardDescription>Liczba plików</CardDescription>
                    <CardTitle className="text-3xl font-bold text-indigo-600">
                      {analysisResult.filesCount}
                    </CardTitle>
                  </CardHeader>
                </Card>
                
                <Card className="border-gray-100 shadow-sm">
                  <CardHeader className="pb-3">
                    <CardDescription>Typ contentu</CardDescription>
                    <CardTitle className="text-xl text-green-600">
                      {analysisResult.contentType}
                    </CardTitle>
                  </CardHeader>
                </Card>
                
                <Card className="border-gray-100 shadow-sm">
                  <CardHeader className="pb-3">
                    <CardDescription>Ocena wartości</CardDescription>
                    <div className="flex items-center gap-2">
                      <CardTitle className="text-3xl font-bold text-purple-600">
                        {analysisResult.valueScore}
                      </CardTitle>
                      <div className="flex gap-0.5">
                        {[...Array(10)].map((_, i) => (
                          <div
                            key={i}
                            className={cn(
                              "w-2 h-8 rounded-sm transition-all",
                              i < analysisResult.valueScore
                                ? "bg-gradient-to-t from-purple-600 to-purple-400"
                                : "bg-gray-200"
                            )}
                          />
                        ))}
                      </div>
                    </div>
                  </CardHeader>
                </Card>
              </div>

              {/* Recommendation */}
              {analysisResult.recommendation && (
                <Card className="bg-gradient-to-br from-indigo-50 to-purple-50 border-indigo-200">
                  <CardHeader>
                    <div className="flex items-center gap-2 mb-2">
                      <Target className="w-5 h-5 text-indigo-600" />
                      <CardTitle className="text-lg">Rekomendacja AI</CardTitle>
                    </div>
                    <p className="text-gray-700 italic leading-relaxed">
                      "{analysisResult.recommendation}"
                    </p>
                  </CardHeader>
                </Card>
              )}

              {/* Topics */}
              {analysisResult.topics && analysisResult.topics.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <Zap className="w-5 h-5 text-yellow-500" />
                    Propozycje tematów ({analysisResult.topics.length})
                  </h3>
                  <div className="grid gap-3">
                    {analysisResult.topics.map((topic: any, idx: number) => (
                      <Card 
                        key={idx} 
                        className="group hover:shadow-lg transition-all duration-300 hover:-translate-y-0.5"
                      >
                        <CardHeader className="pb-3">
                          <div className="flex justify-between items-start">
                            <div className="flex-1">
                              <CardTitle className="text-lg group-hover:text-indigo-600 transition-colors">
                                {topic.title}
                              </CardTitle>
                              <div className="flex items-center gap-3 mt-2">
                                <Badge variant="secondary">{topic.platform}</Badge>
                                <div className="flex items-center gap-1">
                                  <TrendingUp className="w-4 h-4 text-orange-500" />
                                  <span className="text-sm font-medium">
                                    Potencjał: {topic.viralScore}/10
                                  </span>
                                </div>
                              </div>
                            </div>
                            <div className={cn(
                              "p-2 rounded-lg",
                              topic.viralScore >= 8 ? "bg-green-100" : "bg-yellow-100"
                            )}>
                              {topic.viralScore >= 8 ? (
                                <CheckCircle2 className="w-5 h-5 text-green-600" />
                              ) : (
                                <AlertCircle className="w-5 h-5 text-yellow-600" />
                              )}
                            </div>
                          </div>
                        </CardHeader>
                      </Card>
                    ))}
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex flex-wrap gap-3 pt-4">
                <Button 
                  size="lg" 
                  className="shadow-lg"
                  onClick={() => {
                    // TODO: Implement save metadata
                    console.log('Saving metadata for:', analysisResult);
                  }}
                >
                  <CheckCircle2 className="w-4 h-4" />
                  Zapisz metadane
                </Button>
                <Button 
                  size="lg" 
                  variant="secondary"
                  onClick={() => {
                    // TODO: Implement pipeline run
                    console.log('Running pipeline for:', analysisResult.folder);
                  }}
                >
                  <Zap className="w-4 h-4" />
                  Uruchom pipeline
                </Button>
                <Button 
                  size="lg" 
                  variant="outline"
                  onClick={() => {
                    // TODO: Implement detailed report
                    console.log('Generating detailed report for:', analysisResult);
                  }}
                >
                  <FileText className="w-4 h-4" />
                  Szczegółowy raport
                </Button>
              </div>
                </>
              )}
            </CardContent>
          </Card>
        )}
      </main>

      {/* Footer */}
      <footer className="mt-16 border-t border-gray-200 bg-white/80 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <div className="flex items-center gap-4">
              <Badge variant="outline" className="gap-1">
                <div className="w-2 h-2 bg-green-500 rounded-full" />
                Assistant-UI Integration
              </Badge>
              <span>Auto-execution enabled</span>
            </div>
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-indigo-600" />
              <span className="font-medium">Vector Wave AI v2.0</span>
            </div>
          </div>
        </div>
      </footer>

      {/* Chat Panel */}
      <ChatPanel 
        onAnalyzeFolder={analyzeFolder}
        analysisResult={analysisResult}
        folders={folders}
      />
    </div>
  );
}