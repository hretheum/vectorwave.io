'use client';

import { useState } from "react";
import { ArrowLeft, Save, Eye, EyeOff, Download, Copy, CheckCircle2, FileText, Sparkles, Target } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import ReactMarkdown from 'react-markdown';
import { FlowDiagnostics } from './FlowDiagnostics';

interface DraftEditorProps {
  initialDraft: string;
  topicTitle: string;
  platform: string;
  onBack: () => void;
  onPublish: (draft: string) => void;
}

export function DraftEditor({ 
  initialDraft, 
  topicTitle, 
  platform, 
  onBack,
  onPublish 
}: DraftEditorProps) {
  const [draft, setDraft] = useState(initialDraft);
  const [activeView, setActiveView] = useState<'edit' | 'preview' | 'linkedin' | 'diagnostics'>('edit');
  const [saved, setSaved] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleSave = () => {
    // Save to localStorage as backup
    localStorage.setItem(`draft-${Date.now()}`, JSON.stringify({
      content: draft,
      topic: topicTitle,
      platform,
      timestamp: new Date().toISOString()
    }));
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(draft);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([draft], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${topicTitle.toLowerCase().replace(/\s+/g, '-')}-${platform.toLowerCase()}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const wordCount = draft.split(/\s+/).filter(word => word.length > 0).length;
  const charCount = draft.length;

  // Format draft for LinkedIn (preserves LinkedIn formatting)
  const formatForLinkedIn = (text: string): string => {
    return text
      // Clean up title formatting (remove "Title:" prefix if present)
      .replace(/^Title:\s*\*?\*?(.+?)\*?\*?\n*/i, '$1\n\n')
      // Keep **bold** as is (LinkedIn supports this)
      .replace(/\*\*(.*?)\*\*/g, '**$1**')
      // Keep hashtags as is (LinkedIn will auto-link them)
      .replace(/#([a-zA-Z0-9_]+)/g, '#$1')
      // Clean up multiple line breaks but preserve intentional spacing
      .replace(/\n{3,}/g, '\n\n')
      // Remove any markdown remnants
      .replace(/^\s*-\s*/gm, '• ')  // Convert - to bullet points
      .trim();
  };

  const linkedInFormattedText = formatForLinkedIn(draft);

  return (
    <div className="h-full flex flex-col max-w-5xl mx-auto">
      {/* Header */}
      <div className="border-b border-gray-200 bg-white sticky top-0 z-10">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={onBack}
                className="gap-2"
              >
                <ArrowLeft className="w-4 h-4" />
                Wróć do dashboardu
              </Button>
              <div className="h-8 w-px bg-gray-300" />
              <div>
                <h2 className="text-lg font-semibold">{topicTitle}</h2>
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <Badge variant="secondary">{platform}</Badge>
                  <span>•</span>
                  <span>{wordCount} słów</span>
                  <span>•</span>
                  <span>{charCount} znaków</span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {/* View Toggle Buttons */}
              <div className="flex items-center gap-1 p-1 bg-gray-100 rounded-lg">
                <Button
                  variant={activeView === 'edit' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setActiveView('edit')}
                  className="gap-2 h-8"
                >
                  <FileText className="w-4 h-4" />
                  Edytor
                </Button>
                <Button
                  variant={activeView === 'preview' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setActiveView('preview')}
                  className="gap-2 h-8"
                >
                  <Eye className="w-4 h-4" />
                  Podgląd
                </Button>
                <Button
                  variant={activeView === 'linkedin' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setActiveView('linkedin')}
                  className="gap-2 h-8"
                >
                  <Target className="w-4 h-4" />
                  LinkedIn
                </Button>
                <Button
                  variant={activeView === 'diagnostics' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setActiveView('diagnostics')}
                  className="gap-2 h-8"
                >
                  <Sparkles className="w-4 h-4" />
                  Pipeline
                </Button>
              </div>
              <div className="h-8 w-px bg-gray-300" />
              <Button
                variant="outline"
                size="sm"
                onClick={handleCopy}
              >
                {copied ? (
                  <>
                    <CheckCircle2 className="w-4 h-4" />
                    Skopiowano
                  </>
                ) : (
                  <>
                    <Copy className="w-4 h-4" />
                    Kopiuj
                  </>
                )}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleDownload}
                className="gap-2"
              >
                <Download className="w-4 h-4" />
                Pobierz
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleSave}
              >
                {saved ? (
                  <>
                    <CheckCircle2 className="w-4 h-4" />
                    Zapisano
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4" />
                    Zapisz
                  </>
                )}
              </Button>
              <div className="h-8 w-px bg-gray-300" />
              <Button
                className="gap-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700"
                onClick={() => onPublish(draft)}
              >
                <Sparkles className="w-4 h-4" />
                Publikuj
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-hidden">
        {activeView === 'preview' && (
          <Card className="h-full m-6 overflow-auto">
            <CardHeader>
              <CardTitle>Podgląd</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="prose prose-gray max-w-none">
                {/* Enhanced text formatting with line breaks, bold, hashtags */}
                <div 
                  className="whitespace-pre-wrap leading-relaxed"
                  dangerouslySetInnerHTML={{
                    __html: draft
                      // Convert \n to <br> for line breaks
                      .replace(/\n/g, '<br>')
                      // Convert **text** to <strong>text</strong>
                      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                      // Convert *text* to <em>text</em> 
                      .replace(/(?<!\*)\*([^\*\n]+?)\*(?!\*)/g, '<em>$1</em>')
                      // Convert #hashtags to styled spans
                      .replace(/#([a-zA-Z0-9_]+)/g, '<span class="text-blue-600 font-medium">#$1</span>')
                      // Convert URLs to links
                      .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:underline">$1</a>')
                      // Convert email addresses to links
                      .replace(/\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b/g, '<a href="mailto:$1" class="text-blue-600 hover:underline">$1</a>')
                  }}
                />
              </div>
            </CardContent>
          </Card>
        )}

        {activeView === 'linkedin' && (
          <Card className="h-full m-6 overflow-auto">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Target className="w-5 h-5 text-blue-600" />
                  LinkedIn Preview
                </CardTitle>
                <div className="flex items-center gap-4 text-sm text-gray-600">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      navigator.clipboard.writeText(linkedInFormattedText);
                      setCopied(true);
                      setTimeout(() => setCopied(false), 2000);
                    }}
                  >
                    {copied ? (
                      <>
                        <CheckCircle2 className="w-4 h-4" />
                        Skopiowano dla LinkedIn
                      </>
                    ) : (
                      <>
                        <Copy className="w-4 h-4" />
                        Kopiuj dla LinkedIn
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {/* LinkedIn Post Preview */}
              <div className="bg-white border border-gray-200 rounded-lg shadow-sm max-w-xl mx-auto">
                {/* LinkedIn Post Header */}
                <div className="p-4 border-b border-gray-100">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-full flex items-center justify-center">
                      <span className="text-white font-semibold text-lg">VW</span>
                    </div>
                    <div>
                      <div className="font-semibold text-gray-900">Vector Wave</div>
                      <div className="text-sm text-gray-600">AI Content Creator • Now</div>
                    </div>
                  </div>
                </div>
                
                {/* LinkedIn Post Content */}
                <div className="p-4">
                  <div 
                    className="text-gray-900 whitespace-pre-line leading-relaxed"
                    style={{ fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' }}
                  >
                    {linkedInFormattedText.split('\n').map((line, index) => (
                      <div key={`linkedin-line-${index}`}>
                        <span dangerouslySetInnerHTML={{
                          __html: line
                            // Render hashtags with LinkedIn blue color
                            .replace(/#([a-zA-Z0-9_]+)/g, '<span style="color: #0077b5; font-weight: 500;">#$1</span>')
                            // Render bold text
                            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                            // Convert bullet points to proper bullets
                            .replace(/^• /g, '• ')
                        }} />
                        {index < linkedInFormattedText.split('\n').length - 1 && <br />}
                      </div>
                    ))}
                  </div>
                </div>
                
                {/* LinkedIn Post Actions */}
                <div className="border-t border-gray-100 p-3">
                  <div className="flex items-center justify-between text-sm text-gray-600">
                    <div className="flex items-center gap-4">
                      <span className="flex items-center gap-1">👍 Like</span>
                      <span className="flex items-center gap-1">💬 Comment</span>
                      <span className="flex items-center gap-1">🔄 Repost</span>
                      <span className="flex items-center gap-1">📤 Send</span>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* LinkedIn Formatting Tips */}
              <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <h4 className="font-semibold text-blue-900 mb-2">💡 LinkedIn Formatting Tips:</h4>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• <strong>Bold text:</strong> Use **text** (będzie sformatowane jako bold)</li>
                  <li>• <strong>Hashtagi:</strong> #AI #ContentMarketing (automatycznie linkowane)</li>
                  <li>• <strong>Linki:</strong> Automatycznie przekształcane w klikalnie linki</li>
                  <li>• <strong>Łamanie linii:</strong> Podwójne naciśnięcie Enter dla nowego akapitu</li>
                  <li>• <strong>Emoji:</strong> 🚀 Zwiększają engagement o ~25%</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        )}
        
        {activeView === 'edit' && (
          <div className="flex-1 p-6">
            <textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              className="w-full h-full min-h-96 p-6 border border-gray-300 rounded-lg font-mono text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              placeholder="Zacznij pisać swój content..."
              spellCheck={false}
            />
          </div>
        )}
        
        {activeView === 'diagnostics' && (
          <div className="p-6 h-full">
            <FlowDiagnostics 
              topicTitle={topicTitle}
              platform={platform}
              onRefresh={() => {
                // In real implementation, this would trigger a refresh of flow diagnostics data
                console.log('Refreshing flow diagnostics...');
              }}
            />
          </div>
        )}
      </div>

      {/* Help Text */}
      <div className="border-t border-gray-200 bg-gray-50 px-6 py-3">
        <div className="text-sm text-gray-600">
          {activeView === 'edit' && (
            <p>
              💡 <strong>Wskazówka:</strong> Możesz edytować draft ręcznie lub użyć AI Assistant (panel po prawej) do ulepszeń. 
              Wpisz w chacie np. "Skróć ten draft" lub "Dodaj więcej emocji" aby otrzymać sugestie.
            </p>
          )}
          {activeView === 'preview' && (
            <p>
              👁️ <strong>Podgląd:</strong> Zobacz jak będzie wyglądał Twój content po opublikowaniu. 
              Przełącz na "Edytor" aby wprowadzić zmiany.
            </p>
          )}
          {activeView === 'linkedin' && (
            <p>
              🔵 <strong>LinkedIn Preview:</strong> Zobacz dokładnie jak Twój post będzie wyglądał na LinkedIn. 
              Użyj przycisku "Kopiuj dla LinkedIn" aby skopiować tekst z poprawnym formatowaniem.
            </p>
          )}
          {activeView === 'diagnostics' && (
            <p>
              🔍 <strong>Pipeline Diagnostics:</strong> Zobacz dokładnie jak AI agenty przetwarzały Twój content. 
              Sprawdź gdzie treść mogła zostać utracona i jak system podejmował decyzje.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}