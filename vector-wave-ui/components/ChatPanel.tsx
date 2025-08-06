'use client';

import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Sparkles, X, Minimize2, Maximize2, Trash2, Pin, PinOff } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import ReactMarkdown from 'react-markdown';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  contextActions?: Array<{
    label: string;
    action: () => void;
  }>;
}

interface ChatPanelProps {
  onAnalyzeFolder?: (folderName: string) => void;
  analysisResult?: any;
  folders?: any[];
  onEditDraft?: (draft: string, topicTitle: string, platform: string) => void;
}

// Helper function for SSE streaming
async function analyzeIdeasWithProgress(
  folder: string,
  ideas: string[],
  platform: string,
  loadingMsgId: string,
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>
) {
  const analyzedResults: any[] = [];
  let currentProgress = 0;

  console.log('🔄 Starting SSE analysis for:', { folder, ideas, platform });

  try {
    const response = await fetch('/api/analyze-custom-ideas-stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ folder, ideas, platform })
    });

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    if (!reader) throw new Error('No response body');

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      // Append new chunk to buffer
      buffer += decoder.decode(value, { stream: true });
      
      // Process complete lines
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // Keep incomplete line in buffer

      for (const line of lines) {
        const trimmedLine = line.trim();
        if (trimmedLine.startsWith('data: ')) {
          try {
            const data = JSON.parse(trimmedLine.substring(6));
            console.log('SSE Event:', data);

            switch (data.type) {
              case 'start':
                console.log('🚀 SSE Start event received:', data);
                // Update initial message with total count
                setMessages(prev => prev.map(msg => 
                  msg.id === loadingMsgId 
                    ? {
                        ...msg,
                        content: `📝 Rozpoczynam analizę ${data.total_ideas} pomysłów dla folderu "${folder}"...\n\n⏳ Przygotowuję AI do analizy...`
                      }
                    : msg
                ));
                break;

              case 'progress':
                console.log('📊 SSE Progress event:', data);
                currentProgress = data.percentage;
                const progressBarLength = 20;
                const filledBars = Math.floor((currentProgress / 100) * progressBarLength);
                const emptyBars = progressBarLength - filledBars;
                
                // Try both updating existing message and logging
                const progressContent = `📝 Analizuję pomysły dla folderu "${folder}"...\n\n**Pomysł ${data.current} z ${data.total}:** ${data.analyzing}\n\n**Postęp:** ${currentProgress}%\n[${'█'.repeat(filledBars)}${'░'.repeat(emptyBars)}]\n\n💡 _Używam AI do oceny potencjału wiralowego i dopasowania do materiałów_`;
                
                console.log('Progress update:', progressContent);
                console.log('Looking for message with ID:', loadingMsgId);
                
                setMessages(prev => {
                  console.log('Current messages:', prev.map(m => ({ id: m.id, content: m.content.substring(0, 50) })));
                  return prev.map(msg => 
                    msg.id === loadingMsgId 
                      ? {
                          ...msg,
                          content: progressContent
                        }
                      : msg
                  );
                });
                break;

              case 'result':
                console.log('✅ SSE Result event for idea:', data.idea);
                analyzedResults.push(data.analysis);
                break;

              case 'error':
                console.error('❌ SSE Error event:', data);
                break;

              case 'complete':
                console.log('🎉 SSE Complete event:', data);
                // Show final results
                const bestScore = data.best_idea?.overall_score ? (data.best_idea.overall_score * 10).toFixed(1) : '0';
                const scoreEmoji = parseFloat(bestScore) >= 7 ? '✅' : parseFloat(bestScore) >= 5 ? '⚠️' : '❌';
                
                setMessages(prev => prev.map(msg => 
                  msg.id === loadingMsgId 
                    ? {
                        ...msg,
                        content: `✅ **Analiza zakończona!**\n\n🥇 **${data.best_idea?.idea || 'Brak'}\n**Ocena:** ${bestScore}/10 ${scoreEmoji}\n\n${data.best_idea?.recommendation || 'Brak rekomendacji'}${data.best_idea?.suggested_angle ? `\n\n💡 **Sugerowany angle:** ${data.best_idea.suggested_angle}` : ''}`,
                        contextActions: data.best_idea ? [{
                          label: '✍️ Wygeneruj draft',
                          action: () => {
                            console.log('Generate draft for custom idea:', data.best_idea.idea);
                          }
                        }] : []
                      }
                    : msg
                ));

                // Add detailed results
                if (analyzedResults.length > 1) {
                  setTimeout(() => {
                    setMessages(prev => [...prev, {
                      id: `custom-ideas-details-${Date.now()}`,
                      role: 'assistant',
                      content: `📊 **Wszystkie pomysły:**\n\n${analyzedResults.map((idea: any, idx: number) => {
                        const isFirst = idx === 0;
                        const emoji = isFirst ? '🥇' : idx === 1 ? '🥈' : idx === 2 ? '🥉' : `${idx + 1}.`;
                        const overallScore = (idea.overall_score * 10).toFixed(1);
                        const scoreEmoji = overallScore >= 7 ? '✅' : overallScore >= 5 ? '⚠️' : '❌';
                        
                        return `${emoji} **${idea.idea}**\n\n${idea.recommendation || 'Brak rekomendacji'}\n\n**Ocena:** ${overallScore}/10 ${scoreEmoji}\n• Viral Score: ${(idea.viral_score * 10).toFixed(1)}/10\n• Dopasowanie: ${(idea.content_alignment * 10).toFixed(1)}/10\n• Materiał: ${(idea.available_material * 10).toFixed(1)}/10${idea.suggested_angle ? `\n\n💡 **Sugerowany angle:** ${idea.suggested_angle}` : ''}`;
                      }).join('\n\n---\n\n')}`,
                      timestamp: new Date()
                    }]);
                  }, 100);
                }
                break;

              case 'cached_result':
                // Handle cached results
                const cachedData = data.data;
                setMessages(prev => prev.map(msg => 
                  msg.id === loadingMsgId 
                    ? {
                        ...msg,
                        content: `✅ Analiza zakończona (z cache)!\n\n**Najlepszy pomysł:** ${cachedData.best_idea?.idea || 'Brak'}\n**Ocena:** ${cachedData.best_idea?.overall_score ? (cachedData.best_idea.overall_score * 10).toFixed(1) : '0'}/10\n\n${cachedData.best_idea?.recommendation || ''}`,
                        contextActions: cachedData.best_idea ? [{
                          label: '✍️ Wygeneruj draft',
                          action: () => {
                            console.log('Generate draft for custom idea:', cachedData.best_idea.idea);
                          }
                        }] : []
                      }
                    : msg
                ));
                break;
            }
          } catch (e) {
            console.error('Error parsing SSE data:', e);
          }
        }
      }
    }
  } catch (err) {
    console.error('SSE streaming error:', err);
    setMessages(prev => prev.map(msg => 
      msg.id === loadingMsgId 
        ? { ...msg, content: `❌ Błąd analizy: ${err instanceof Error ? err.message : 'Nieznany błąd'}` }
        : msg
    ));
  }
}

export function ChatPanel({ onAnalyzeFolder, analysisResult, folders = [], onEditDraft }: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [isDocked, setIsDocked] = useState(true);
  const [showCustomIdeasInput, setShowCustomIdeasInput] = useState(false);
  const [customIdeasText, setCustomIdeasText] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load messages and docked state from localStorage on mount
  useEffect(() => {
    const savedMessages = localStorage.getItem('chatMessages');
    const savedDocked = localStorage.getItem('chatPanelDocked');
    
    if (savedDocked !== null) {
      setIsDocked(savedDocked === 'true');
    }
    
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
      // First show analysis summary
      const summaryMessage: Message = {
        id: `summary-${Date.now()}`,
        role: 'assistant',
        content: `✅ Analiza zakończona!\n\n**${analysisResult.folder}**\n• Plików: ${analysisResult.filesCount}\n• Typ: ${analysisResult.contentType}\n• Ocena: ${analysisResult.valueScore}/10\n\n💡 "${analysisResult.recommendation}"`,
        timestamp: new Date(),
        contextActions: [
          {
            label: '📊 Pokaż pełny raport',
            action: () => {
              const detailButton = document.querySelector('[data-action="detailed-report"]') as HTMLButtonElement;
              detailButton?.click();
            }
          },
          ...(analysisResult.contentOwnership === 'ORIGINAL' ? [{
            label: '🔍 Weryfikuj źródła',
            action: () => {
              const verifyButton = document.querySelector('[data-action="verify-sources"]') as HTMLButtonElement;
              verifyButton?.click();
            }
          }] : [])
        ]
      };
      setMessages(prev => [...prev, summaryMessage]);
      
      // Then show topics as separate messages
      if (analysisResult.topTopics && analysisResult.topTopics.length > 0) {
        setMessages(prev => [...prev, {
          id: `topics-header-${Date.now()}`,
          role: 'assistant',
          content: `📝 **Znalazłem ${analysisResult.topTopics.length} pomysłów na posty:**`,
          timestamp: new Date()
        }]);
        
        analysisResult.topTopics.forEach((topic: any, index: number) => {
          setTimeout(() => {
            setMessages(prev => [...prev, {
              id: `topic-${index}-${Date.now()}`,
              role: 'assistant',
              content: `**${topic.title}**\n\n📍 Platforma: ${topic.platform}\n\n⚡ Viral Score: ${topic.viralScore}/10${index < analysisResult.topTopics.length - 1 ? '\n\n---' : ''}`,
              timestamp: new Date(),
              contextActions: [{
                label: '✍️ Wygeneruj draft',
                action: async () => {
                  // Show generation message
                  const generatingMsgId = `draft-${Date.now()}`;
                  setMessages(prev => [...prev, {
                    id: generatingMsgId,
                    role: 'assistant',
                    content: `🚧 Generowanie draftu...\n\n**Temat:** ${topic.title}\n**Platforma:** ${topic.platform}\n**Folder:** ${analysisResult.folder}\n**Typ contentu:** ${analysisResult.contentOwnership}\n\n⏳ Uruchamiam AI Writing Flow...`,
                    timestamp: new Date()
                  }]);
                  
                  try {
                    // Call writing flow endpoint
                    const response = await fetch('/api/generate-draft', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({
                        topic_title: topic.title,
                        platform: topic.platform,
                        folder_path: analysisResult.folder,
                        content_type: analysisResult.contentType || 'STANDALONE',
                        content_ownership: analysisResult.contentOwnership || 'EXTERNAL',
                        viral_score: topic.viralScore,
                        editorial_recommendations: analysisResult.recommendation || '',
                        skip_research: analysisResult.contentOwnership === 'ORIGINAL'
                      })
                    });
                    
                    const data = await response.json();
                    
                    // Handle new synchronous response format
                    if (data.success && data.draft) {
                      // Replace generating message with result
                      setMessages(prev => prev.map(msg => 
                        msg.id === generatingMsgId 
                          ? { 
                              ...msg, 
                              content: `✅ Draft gotowy!\n\n**${topic.title}** (${topic.platform})\n\n${data.draft.content}\n\n📊 Metryki:\n• Słowa: ${data.draft.word_count}\n• Znaki: ${data.draft.character_count}\n• Viral Score: ${data.draft.viral_score}`,
                              contextActions: [{
                                label: '📝 Edytuj draft',
                                action: () => {
                                  if (onEditDraft) {
                                    onEditDraft(data.draft.content, topic.title, topic.platform);
                                  }
                                }
                              }]
                            }
                          : msg
                      ));
                    } else if (data.status === 'started' && data.flow_id) {
                      // Update message with flow ID
                      setMessages(prev => prev.map(msg => 
                        msg.id === generatingMsgId 
                          ? { ...msg, content: msg.content + `\n\n🆔 Flow ID: ${data.flow_id}` }
                          : msg
                      ));
                      
                      // Poll for results
                      const pollInterval = setInterval(async () => {
                        const statusResponse = await fetch(`/api/draft-status/${data.flow_id}`);
                        const statusData = await statusResponse.json();
                        
                        if (statusData.status === 'completed') {
                          clearInterval(pollInterval);
                          setMessages(prev => [...prev, {
                            id: `draft-result-${Date.now()}`,
                            role: 'assistant',
                            content: `✅ Draft gotowy!\n\n**${topic.title}**\n\n${statusData.draft || '[Brak draftu - sprawdź logi]'}\n\n📊 Metryki:\n• Quality Score: ${statusData.quality_score || 'N/A'}\n• Style Score: ${statusData.style_score || 'N/A'}\n• Rewizje: ${statusData.revision_count || 0}`,
                            timestamp: new Date(),
                            contextActions: [{
                              label: '📝 Edytuj draft',
                              action: () => {
                                if (onEditDraft && statusData.draft) {
                                  onEditDraft(statusData.draft, topic.title, topic.platform);
                                }
                              }
                            }, {
                              label: '📤 Publikuj',
                              action: () => {
                                // TODO: Trigger distribution flow
                                console.log('Publish draft');
                              }
                            }]
                          }]);
                        } else if (statusData.status === 'awaiting_feedback') {
                          clearInterval(pollInterval);
                          setMessages(prev => [...prev, {
                            id: `feedback-request-${Date.now()}`,
                            role: 'assistant',
                            content: `👤 **Draft wymaga Twojej opinii!**\n\n${statusData.current_draft || '[Draft w trakcie generowania]'}\n\n**Co chcesz zrobić?**`,
                            timestamp: new Date(),
                            contextActions: [{
                              label: '✅ Akceptuj',
                              action: async () => {
                                // Continue without changes
                                try {
                                  const feedbackResponse = await fetch('/api/draft-feedback', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({
                                      flow_id: data.flow_id,
                                      feedback_type: 'minor',
                                      feedback_text: 'Accepted as-is'
                                    })
                                  });
                                  if (feedbackResponse.ok) {
                                    setMessages(prev => [...prev, {
                                      id: `feedback-sent-${Date.now()}`,
                                      role: 'assistant',
                                      content: '✅ Zaakceptowano! Finalizuję draft...',
                                      timestamp: new Date()
                                    }]);
                                  }
                                } catch (error) {
                                  console.error('Feedback error:', error);
                                }
                              }
                            }, {
                              label: '✏️ Drobne poprawki',
                              action: () => {
                                // Minor edits -> style validation
                                setInput('[FEEDBACK] Drobne poprawki: ');
                                // Store flow_id for later use
                                (window as any).currentFlowId = data.flow_id;
                                (window as any).feedbackType = 'minor';
                              }
                            }, {
                              label: '🔄 Większe zmiany',
                              action: () => {
                                // Major changes -> audience re-alignment
                                setInput('[FEEDBACK] Większe zmiany: ');
                                (window as any).currentFlowId = data.flow_id;
                                (window as any).feedbackType = 'major';
                              }
                            }, {
                              label: '🔁 Zmień kierunek',
                              action: () => {
                                // Pivot -> new research (or audience for ORIGINAL)
                                setInput('[FEEDBACK] Nowy kierunek: ');
                                (window as any).currentFlowId = data.flow_id;
                                (window as any).feedbackType = 'pivot';
                              }
                            }]
                          }]);
                        } else if (statusData.status === 'failed') {
                          clearInterval(pollInterval);
                          
                          // Check if there's a draft despite failure
                          if (statusData.draft) {
                            setMessages(prev => [...prev, {
                              id: `draft-partial-${Date.now()}`,
                              role: 'assistant',
                              content: `⚠️ Draft wygenerowany mimo błędów!\n\n**${topic.title}**\n\n${statusData.draft}\n\n❌ **Błąd:** ${statusData.error || 'Quality gates failed'}\n\n📊 Metryki:\n• Quality Score: ${statusData.quality_score || 'N/A'}\n• Style Score: ${statusData.style_score || 'N/A'}`,
                              timestamp: new Date(),
                              contextActions: [{
                                label: '📝 Edytuj draft',
                                action: () => {
                                  if (onEditDraft && statusData.draft) {
                                    onEditDraft(statusData.draft, topic.title, topic.platform);
                                  }
                                }
                              }, {
                                label: '🔄 Spróbuj ponownie',
                                action: () => {
                                  // TODO: Restart generation
                                  console.log('Retry generation');
                                }
                              }]
                            }]);
                          } else {
                            setMessages(prev => [...prev, {
                              id: `draft-error-${Date.now()}`,
                              role: 'assistant',
                              content: `❌ Błąd podczas generowania draftu:\n\n${statusData.error || 'Nieznany błąd'}`,
                              timestamp: new Date()
                            }]);
                          }
                        }
                      }, 2000); // Poll every 2 seconds
                      
                      // Stop polling after 5 minutes
                      setTimeout(() => {
                        clearInterval(pollInterval);
                      }, 300000);
                    } else {
                      throw new Error(data.detail || 'Failed to start writing flow');
                    }
                  } catch (error) {
                    console.error('Draft generation error:', error);
                    setMessages(prev => [...prev, {
                      id: `draft-error-${Date.now()}`,
                      role: 'assistant',
                      content: `❌ Nie udało się wygenerować draftu:\n\n${error instanceof Error ? error.message : 'Nieznany błąd'}\n\n💡 Spróbuj ponownie za chwilę.`,
                      timestamp: new Date()
                    }]);
                  }
                }
              }]
            }]);
          }, (index + 1) * 200); // Stagger messages for nicer effect
        });
        
        // Add "Mam swoje propozycje" button after all topics
        setTimeout(() => {
          console.log('Adding custom ideas button message');
          setMessages(prev => {
            console.log('Previous messages:', prev.length);
            return [...prev, {
              id: `custom-ideas-prompt-${Date.now()}`,
              role: 'assistant',
              content: `Nie podoba Ci się żaden z pomysłów?`,
              timestamp: new Date(),
              contextActions: [{
                label: '💡 Mam swoje propozycje',
                action: () => {
                  console.log('Custom ideas clicked');
                  console.log('Setting showCustomIdeasInput to true');
                  setShowCustomIdeasInput(true);
                  setCustomIdeasText('');
                }
              }]
            }];
          });
        }, (analysisResult.topTopics.length + 1) * 200);
      }
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
      // Check if this is feedback for writing flow
      if (input.startsWith('[FEEDBACK]') && (window as any).currentFlowId) {
        const feedbackText = input.replace('[FEEDBACK]', '').replace(/^(Drobne poprawki|Większe zmiany|Nowy kierunek):\s*/, '').trim();
        const flowId = (window as any).currentFlowId;
        const feedbackType = (window as any).feedbackType || 'minor';
        
        const feedbackResponse = await fetch('/api/draft-feedback', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            flow_id: flowId,
            feedback_type: feedbackType,
            feedback_text: feedbackText
          })
        });
        
        if (feedbackResponse.ok) {
          setMessages(prev => [...prev, {
            id: Date.now().toString(),
            role: 'assistant',
            content: `✅ Feedback otrzymany! Typ: **${feedbackType}**\n\nPrzetwarzam zmiany...`,
            timestamp: new Date()
          }]);
          
          // Clear stored values
          delete (window as any).currentFlowId;
          delete (window as any).feedbackType;
        }
        
        setIsTyping(false);
        return;
      }
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

  const toggleDocked = () => {
    const newDocked = !isDocked;
    setIsDocked(newDocked);
    localStorage.setItem('chatPanelDocked', newDocked.toString());
  };

  if (isMinimized && !isDocked) {
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
    <div className={cn(
      "flex flex-col shadow-2xl border-0 overflow-hidden",
      isDocked ? "h-full w-full" : "fixed bottom-4 right-4 w-[500px] h-[600px] z-50 rounded-lg"
    )}>
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
                // Bezpośrednio czyść bez potwierdzenia
                setMessages([{
                  id: '1',
                  role: 'assistant',
                  content: 'Cześć! 👋 Jestem Twoim AI asystentem. Mogę pomóc Ci:\n\n• Analizować foldery z contentem\n• Doradzać w strategii publikacji\n• Generować pomysły na posty\n• Odpowiadać na pytania o Vector Wave\n\nCo Cię dziś interesuje?',
                  timestamp: new Date()
                }]);
                localStorage.removeItem('chatMessages');
              }}
              title="Wyczyść historię"
            >
              <Trash2 className="w-4 h-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-white hover:bg-white/20"
              onClick={toggleDocked}
              title={isDocked ? "Odepnij panel" : "Przypnij panel"}
            >
              {isDocked ? <PinOff className="w-4 h-4" /> : <Pin className="w-4 h-4" />}
            </Button>
            {!isDocked && (
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-white hover:bg-white/20"
                onClick={() => setIsMinimized(true)}
              >
                <Minimize2 className="w-4 h-4" />
              </Button>
            )}
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-white hover:bg-white/20"
              onClick={() => isDocked ? toggleDocked() : setIsMinimized(true)}
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
              <div className={cn(
                "text-sm prose prose-sm max-w-none",
                message.role === 'user' && "prose-invert"
              )}>
                <ReactMarkdown
                  components={{
                    p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                    strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                    hr: () => <hr className="my-2 border-gray-300" />,
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              </div>
              <p className={cn(
                "text-xs mt-1",
                message.role === 'user' ? "text-indigo-200" : "text-gray-400"
              )}>
                {message.timestamp.toLocaleTimeString('pl', { 
                  hour: '2-digit', 
                  minute: '2-digit' 
                })}
              </p>
              
              {/* Context Actions */}
              {message.contextActions && message.contextActions.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {message.contextActions.map((action, idx) => (
                    <Button
                      key={idx}
                      size="sm"
                      variant="outline"
                      className="text-xs whitespace-normal text-left break-words h-auto py-2 px-3"
                      onClick={action.action}
                    >
                      {action.label}
                    </Button>
                  ))}
                </div>
              )}
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
            <Badge 
              variant="outline" 
              className="cursor-pointer hover:bg-gray-100 whitespace-nowrap"
              onClick={() => {
                console.log('Test custom ideas clicked');
                // First analyze the latest folder if no analysis yet
                if (!analysisResult && folders[0]) {
                  onAnalyzeFolder?.(folders[0].name);
                  setMessages(prev => [...prev, {
                    id: `analyze-first-${Date.now()}`,
                    role: 'assistant',
                    content: `🔍 Najpierw analizuję folder "${folders[0].name}"...`,
                    timestamp: new Date()
                  }]);
                } else {
                  setShowCustomIdeasInput(true);
                  setCustomIdeasText('');
                }
              }}
            >
              💡 Własne pomysły
            </Badge>
          </div>
        </div>
      )}

      {/* Input */}
      {!showCustomIdeasInput ? (
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
      ) : (
        <div className="p-4 bg-white border-t border-gray-200">
          <div className="mb-2 text-sm text-gray-600">
            <span className="font-semibold">Twoje propozycje dla folderu: {analysisResult?.folder || 'nieznany'}</span>
            <button
              onClick={() => {
                setShowCustomIdeasInput(false);
                setCustomIdeasText('');
              }}
              className="float-right text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>
          <textarea
            value={customIdeasText}
            onChange={(e) => setCustomIdeasText(e.target.value)}
            onKeyDown={(e) => {
              // Option+Enter (Alt+Enter on Windows) for new line
              if (e.key === 'Enter' && e.altKey) {
                e.preventDefault();
                const textarea = e.target as HTMLTextAreaElement;
                const { selectionStart, selectionEnd } = textarea;
                const newContent = 
                  customIdeasText.substring(0, selectionStart) + 
                  '\n' + 
                  customIdeasText.substring(selectionEnd);
                setCustomIdeasText(newContent);
                // Restore cursor position
                setTimeout(() => {
                  textarea.selectionStart = textarea.selectionEnd = selectionStart + 1;
                }, 0);
                return;
              }
              
              // Enter without modifier submits
              if (e.key === 'Enter' && !e.altKey && !e.shiftKey) {
                e.preventDefault();
                const ideas = customIdeasText
                  .split('\n')
                  .map(idea => idea.trim())
                  .filter(idea => idea.length > 0);
                
                if (ideas.length > 0) {
                  console.log('Submit ideas:', ideas);
                  
                  // Hide input and show loading message
                  setShowCustomIdeasInput(false);
                  setCustomIdeasText('');
                  
                  const loadingMsgId = `custom-ideas-loading-${Date.now()}`;
                  setMessages(prev => [...prev, {
                    id: loadingMsgId,
                    role: 'assistant',
                    content: `📝 Analizuję ${ideas.length} pomysłów dla folderu "${analysisResult?.folder || 'nieznany'}"...`,
                    timestamp: new Date()
                  }]);
                  
                  // Call streaming API with progress
                  analyzeIdeasWithProgress(
                    analysisResult?.folder || 'unknown',
                    ideas,
                    'LinkedIn',
                    loadingMsgId,
                    setMessages
                  );
                }
              }
            }}
            placeholder="Wpisz swoje pomysły (jeden per linia)&#10;Option+Enter dla nowej linii"
            rows={5}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
            autoFocus
          />
          <div className="mt-2 flex justify-between text-xs text-gray-500">
            <span>Enter = wyślij • Option+Enter = nowa linia</span>
            <button
              onClick={() => {
                const ideas = customIdeasText
                  .split('\n')
                  .map(idea => idea.trim())
                  .filter(idea => idea.length > 0);
                
                if (ideas.length > 0) {
                  console.log('Submit ideas:', ideas);
                  
                  // Hide input and show loading message
                  setShowCustomIdeasInput(false);
                  setCustomIdeasText('');
                  
                  const loadingMsgId = `custom-ideas-loading-${Date.now()}`;
                  setMessages(prev => [...prev, {
                    id: loadingMsgId,
                    role: 'assistant',
                    content: `📝 Analizuję ${ideas.length} pomysłów dla folderu "${analysisResult?.folder || 'nieznany'}"...`,
                    timestamp: new Date()
                  }]);
                  
                  // Call streaming API with progress
                  analyzeIdeasWithProgress(
                    analysisResult?.folder || 'unknown',
                    ideas,
                    'LinkedIn',
                    loadingMsgId,
                    setMessages
                  );
                }
              }}
              disabled={!customIdeasText.trim()}
              className="px-3 py-1 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              Analizuj pomysły
            </button>
          </div>
        </div>
      )}
    </div>
  );
}