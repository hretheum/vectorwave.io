'use client';

import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Sparkles, X, Minimize2, Maximize2, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface ChatPanelProps {
  onAnalyzeFolder?: (folderName: string) => void;
  analysisResult?: any;
  folders?: any[];
}

export function ChatPanel({ onAnalyzeFolder, analysisResult, folders = [] }: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load messages from localStorage on mount
  useEffect(() => {
    const savedMessages = localStorage.getItem('chatMessages');
    if (savedMessages) {
      try {
        const parsed = JSON.parse(savedMessages);
        setMessages(parsed.map((msg: any) => ({
          ...msg,
          timestamp: new Date(msg.timestamp)
        })));
      } catch {
        // If parse fails, use default message
        setMessages([{
          id: '1',
          role: 'assistant',
          content: 'Cześć! 👋 Jestem Twoim AI asystentem. Mogę pomóc Ci:\n\n• Analizować foldery z contentem\n• Doradzać w strategii publikacji\n• Generować pomysły na posty\n• Odpowiadać na pytania o Vector Wave\n\nCo Cię dziś interesuje?',
          timestamp: new Date()
        }]);
      }
    } else {
      const greetings = [
        'Siema! 👋 Co tam słychać? Masz jakieś ciekawe tematy do przegadania?',
        'Hej! Widzę że mamy ' + folders.length + ' folderów do analizy. Ale możemy też pogadać o czymkolwiek - co Cię nurtuje?',
        'Cześć! Jestem tu żeby pomóc, ale też lubię dobrą pogawędkę. O czym chcesz porozmawiać?',
        'No cześć! 😊 Analizuję content, doradzam strategie, ale też po prostu gadam. Co dziś robimy?',
        'Witaj! Mam tu sporo materiałów do analizy, ale równie chętnie pogadam o życiu. Co wolisz?'
      ];
      
      setMessages([{
        id: '1',
        role: 'assistant',
        content: greetings[Math.floor(Math.random() * greetings.length)],
        timestamp: new Date()
      }]);
    }
  }, []);

  // Save messages to localStorage whenever they change
  useEffect(() => {
    if (messages.length > 0) {
      localStorage.setItem('chatMessages', JSON.stringify(messages));
    }
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // React to analysis results
  useEffect(() => {
    if (analysisResult && analysisResult.folder) {
      const resultMessage: Message = {
        id: `result-${Date.now()}`,
        role: 'assistant',
        content: `✅ Analiza zakończona!\n\n**${analysisResult.folder}**\n• Plików: ${analysisResult.filesCount}\n• Typ: ${analysisResult.contentType}\n• Ocena: ${analysisResult.valueScore}/10\n\n💡 "${analysisResult.recommendation}"\n\nZnalazłem ${analysisResult.topics?.length || 0} pomysłów na posty. Chcesz zobaczyć szczegóły?`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, resultMessage]);
    }
  }, [analysisResult]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);

    try {
      // Call the chat API
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: input,
          context: {
            folders,
            analysisResult,
            previousMessages: messages.slice(-5) // Last 5 messages for context
          }
        })
      });

      const data = await response.json();
      
      // Check if the response suggests analyzing a folder
      if (data.suggestAnalyze && onAnalyzeFolder) {
        const folderMatch = folders.find(f => 
          f.name.toLowerCase() === data.suggestAnalyze.toLowerCase() ||
          input.toLowerCase().includes(f.name.toLowerCase())
        );
        if (folderMatch) {
          onAnalyzeFolder(folderMatch.name);
        }
      }

      const assistantMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: data.response || data.message || 'Hmm, nie dostałem odpowiedzi. Spróbuj jeszcze raz?',
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      
      // Fallback to local logic for common queries
      let fallbackResponse = '';
      
      if (input.toLowerCase().includes('analizuj') || input.toLowerCase().includes('sprawdź')) {
        const folderMatch = folders.find(f => 
          input.toLowerCase().includes(f.name.toLowerCase()) ||
          input.toLowerCase().includes(f.name.split('-').join(' '))
        );

        if (folderMatch && onAnalyzeFolder) {
          onAnalyzeFolder(folderMatch.name);
          fallbackResponse = `Ok, analizuję folder "${folderMatch.name}"... 🔍`;
        } else {
          fallbackResponse = 'Hmm, nie kojarzę takiego folderu. Mamy:\n' + 
            folders.slice(0, 5).map(f => `• ${f.name}`).join('\n') +
            (folders.length > 5 ? `\n...i ${folders.length - 5} więcej` : '');
        }
      } else {
        // Natural, varied responses for general chat
        const responses = [
          'No to opowiadaj! Co tam u Ciebie? 😊',
          'Brzmi ciekawie! Powiedz mi więcej.',
          'Ha! Dobre. A co jeszcze?',
          'Serio? No to muszę to usłyszeć!',
          'O, to intrygujące. Jak to się stało?',
          'No proszę! A ja myślałem, że już wszystko słyszałem 😄',
          'Czekaj, czekaj... jak to "' + input.slice(0, 20) + '"...? Rozwiń myśl!',
          'Hah, ' + (input.length < 10 ? 'krótko i na temat' : 'no no, gadasz jak najęty') + '! Co dalej?'
        ];
        
        fallbackResponse = responses[Math.floor(Math.random() * responses.length)];
      }

      const assistantMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: fallbackResponse,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  if (isMinimized) {
    return (
      <Card 
        className="fixed bottom-4 right-4 w-16 h-16 flex items-center justify-center cursor-pointer shadow-2xl border-0 bg-gradient-to-br from-indigo-600 to-purple-600 hover:scale-105 transition-transform z-50"
        onClick={() => setIsMinimized(false)}
      >
        <Sparkles className="w-8 h-8 text-white" />
      </Card>
    );
  }

  return (
    <Card className="fixed bottom-4 right-4 w-96 h-[600px] flex flex-col shadow-2xl border-0 overflow-hidden z-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 p-4 text-white">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-white/20 rounded-lg backdrop-blur">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-semibold">AI Assistant</h3>
              <p className="text-xs opacity-90">Vector Wave Editorial</p>
            </div>
          </div>
          <div className="flex gap-1">
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-white hover:bg-white/20"
              onClick={() => {
                if (confirm('Czy na pewno chcesz wyczyścić historię czatu?')) {
                  setMessages([{
                    id: '1',
                    role: 'assistant',
                    content: 'Cześć! 👋 Jestem Twoim AI asystentem. Mogę pomóc Ci:\n\n• Analizować foldery z contentem\n• Doradzać w strategii publikacji\n• Generować pomysły na posty\n• Odpowiadać na pytania o Vector Wave\n\nCo Cię dziś interesuje?',
                    timestamp: new Date()
                  }]);
                  localStorage.removeItem('chatMessages');
                }
              }}
              title="Wyczyść historię"
            >
              <Trash2 className="w-4 h-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-white hover:bg-white/20"
              onClick={() => setIsMinimized(true)}
            >
              <Minimize2 className="w-4 h-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-white hover:bg-white/20"
              onClick={() => setIsMinimized(true)}
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
        {messages.map((message) => (
          <div
            key={message.id}
            className={cn(
              "flex gap-3",
              message.role === 'user' ? "justify-end" : "justify-start"
            )}
          >
            {message.role === 'assistant' && (
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-md">
                <Bot className="w-5 h-5 text-white" />
              </div>
            )}
            <div
              className={cn(
                "max-w-[75%] rounded-2xl px-4 py-3 shadow-sm",
                message.role === 'user' 
                  ? "bg-indigo-600 text-white" 
                  : "bg-white border border-gray-200"
              )}
            >
              <p className="text-sm whitespace-pre-wrap">
                {message.content}
              </p>
              <p className={cn(
                "text-xs mt-1",
                message.role === 'user' ? "text-indigo-200" : "text-gray-400"
              )}>
                {message.timestamp.toLocaleTimeString('pl', { 
                  hour: '2-digit', 
                  minute: '2-digit' 
                })}
              </p>
            </div>
            {message.role === 'user' && (
              <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
                <User className="w-5 h-5 text-gray-600" />
              </div>
            )}
          </div>
        ))}
        
        {isTyping && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-md">
              <Bot className="w-5 h-5 text-white" />
            </div>
            <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3 shadow-sm">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100" />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200" />
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Quick Actions */}
      {folders.length > 0 && (
        <div className="px-4 py-2 bg-white border-t border-gray-100">
          <div className="flex gap-2 overflow-x-auto">
            <Badge 
              variant="outline" 
              className="cursor-pointer hover:bg-gray-100 whitespace-nowrap"
              onClick={() => setInput('Pokaż dostępne tematy')}
            >
              📂 Lista tematów
            </Badge>
            <Badge 
              variant="outline" 
              className="cursor-pointer hover:bg-gray-100 whitespace-nowrap"
              onClick={() => setInput('Jaka strategia publikacji?')}
            >
              📅 Strategia
            </Badge>
            <Badge 
              variant="outline" 
              className="cursor-pointer hover:bg-gray-100 whitespace-nowrap"
              onClick={() => setInput(`Analizuj ${folders[0]?.name}`)}
            >
              🔍 Analizuj najnowszy
            </Badge>
          </div>
        </div>
      )}

      {/* Input */}
      <div className="p-4 bg-white border-t border-gray-200">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Napisz wiadomość..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          />
          <Button 
            onClick={handleSend}
            disabled={!input.trim() || isTyping}
            size="icon"
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </Card>
  );
}