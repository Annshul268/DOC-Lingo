'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Message, Language, Citation, DocumentMetadata } from '@/types';
import { CitationsList } from '@/components/CitationsList';
import { LanguageSelector } from '@/components/LanguageSelector';
import { 
  Send, 
  Sparkles, 
  User, 
  Bot, 
  RotateCcw, 
  CornerDownLeft,
  FileSearch,
  MessageSquarePlus,
  Loader2
} from 'lucide-react';

interface ChatAreaProps {
  messages: Message[];
  onSendMessage: (query: string) => Promise<void>;
  onClearChat: () => void;
  isLoading: boolean;
  targetLanguage: Language;
  onLanguageChange: (lang: Language) => void;
  selectedDocId: string | null;
  documents: DocumentMetadata[];
}

export const ChatArea: React.FC<ChatAreaProps> = ({
  messages,
  onSendMessage,
  onClearChat,
  isLoading,
  targetLanguage,
  onLanguageChange,
  selectedDocId,
  documents,
}) => {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleSubmit = () => {
    if (!input.trim() || isLoading) return;
    onSendMessage(input.trim());
    setInput('');
  };

  const selectedDoc = documents.find(d => d.document_id === selectedDocId);

  return (
    <main className="flex-1 flex flex-col h-screen bg-white relative">
      {/* Top Navigation Bar */}
      <header className="h-14 border-b border-slate-200/80 px-6 flex items-center justify-between bg-white z-10">
        <div className="flex items-center gap-3">
          <div className="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
            <span className="text-slate-400">Context:</span>
            {selectedDoc ? (
              <span className="inline-flex items-center gap-1 text-blue-600 bg-blue-50 px-2 py-0.5 rounded border border-blue-100">
                📄 {selectedDoc.filename}
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 text-slate-600 bg-slate-100 px-2 py-0.5 rounded">
                🌐 All Documents ({documents.length})
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-4">
          <LanguageSelector value={targetLanguage} onChange={onLanguageChange} />
          {messages.length > 0 && (
            <button
              onClick={onClearChat}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
              title="Start New Chat"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
          )}
        </div>
      </header>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto px-4 md:px-8 py-6 space-y-6">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center max-w-xl mx-auto text-center px-4">
            <div className="w-12 h-12 rounded-2xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600 shadow-sm mb-4">
              <Sparkles className="w-6 h-6" />
            </div>
            <h2 className="text-lg font-bold text-slate-900 mb-1">
              Ask Anything Across Languages
            </h2>
            <p className="text-xs text-slate-500 mb-6 leading-relaxed">
              Upload documents in English or Hindi, and ask questions in Hindi, Hinglish, or English.
              DOC-Lingo performs genuine semantic cross-lingual retrieval.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 w-full text-left mt-2">
              <div className="p-3.5 rounded-xl border border-slate-200/80 bg-slate-50/50 text-xs">
                <div className="font-semibold text-slate-800 mb-1 flex items-center gap-1.5">
                  <span className="text-base">📄</span> Any Topic or Domain
                </div>
                <p className="text-[11px] text-slate-500 leading-relaxed">
                  Upload legal contracts, textbooks, technical documentation, or research papers.
                </p>
              </div>

              <div className="p-3.5 rounded-xl border border-slate-200/80 bg-slate-50/50 text-xs">
                <div className="font-semibold text-slate-800 mb-1 flex items-center gap-1.5">
                  <span className="text-base">🌐</span> Cross-Lingual Search
                </div>
                <p className="text-[11px] text-slate-500 leading-relaxed">
                  Ask in Hindi or Hinglish even if the document was written entirely in English.
                </p>
              </div>

              <div className="p-3.5 rounded-xl border border-slate-200/80 bg-slate-50/50 text-xs">
                <div className="font-semibold text-slate-800 mb-1 flex items-center gap-1.5">
                  <span className="text-base">📌</span> Verified Citations
                </div>
                <p className="text-[11px] text-slate-500 leading-relaxed">
                  Every answer links directly to verified source pages and chunks without hallucinations.
                </p>
              </div>
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 max-w-3xl mx-auto ${
                msg.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              {msg.role === 'assistant' && (
                <div className="w-8 h-8 rounded-lg bg-blue-600 text-white flex items-center justify-center shrink-0 shadow-sm shadow-blue-500/20">
                  <Bot className="w-4 h-4" />
                </div>
              )}

              <div
                className={`rounded-2xl px-4 py-3 text-xs leading-relaxed max-w-[85%] ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white shadow-sm shadow-blue-500/10'
                    : 'bg-white border border-slate-200/80 text-slate-800 shadow-xs'
                }`}
              >
                {/* Language Tag Indicator */}
                {msg.role === 'assistant' && msg.detected_language && (
                  <div className="flex items-center gap-2 mb-2 pb-1.5 border-b border-slate-100 text-[10px] text-slate-400 font-mono">
                    <span>Query detected: <b className="text-slate-600 uppercase">{msg.detected_language}</b></span>
                    <span>•</span>
                    <span>Answer: <b className="text-blue-600 uppercase">{msg.target_language || 'Auto'}</b></span>
                  </div>
                )}

                <div className="whitespace-pre-wrap">{msg.content}</div>

                {msg.citations && msg.citations.length > 0 && (
                  <CitationsList citations={msg.citations} />
                )}
              </div>

              {msg.role === 'user' && (
                <div className="w-8 h-8 rounded-lg bg-slate-200 text-slate-700 flex items-center justify-center shrink-0 font-bold text-xs">
                  <User className="w-4 h-4" />
                </div>
              )}
            </div>
          ))
        )}

        {isLoading && (
          <div className="flex gap-3 max-w-3xl mx-auto justify-start">
            <div className="w-8 h-8 rounded-lg bg-blue-600 text-white flex items-center justify-center shrink-0">
              <Bot className="w-4 h-4" />
            </div>
            <div className="rounded-2xl px-4 py-3 bg-white border border-slate-200/80 shadow-xs flex items-center gap-2 text-xs text-slate-500">
              <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />
              <span>Retrieving relevant chunks & synthesizing response...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-slate-200/80 bg-white">
        <div className="max-w-3xl mx-auto relative flex items-end rounded-xl border border-slate-200 bg-slate-50/50 focus-within:bg-white focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-100 transition-all p-2">
          <textarea
            ref={textareaRef}
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question in English, Hindi, or Hinglish... (Shift + Enter for newline)"
            className="flex-1 bg-transparent border-0 resize-none text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none max-h-32 p-1.5 leading-normal"
          />
          <button
            onClick={handleSubmit}
            disabled={!input.trim() || isLoading}
            className={`p-2 rounded-lg transition-all shrink-0 ${
              input.trim() && !isLoading
                ? 'bg-blue-600 text-white shadow-sm hover:bg-blue-700'
                : 'bg-slate-200 text-slate-400 cursor-not-allowed'
            }`}
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
        <p className="text-center text-[11px] text-slate-400 mt-2">
          DOC-Lingo ground responses strictly on retrieved document chunks.
        </p>
      </div>
    </main>
  );
};
