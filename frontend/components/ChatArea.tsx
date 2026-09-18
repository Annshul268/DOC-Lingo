'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Message, Language, Citation, DocumentMetadata } from '@/types';
import { CitationsList } from '@/components/CitationsList';
import { LanguageSelector } from '@/components/LanguageSelector';
import { ThemeToggle } from '@/components/ThemeToggle';
import { 
  Send, 
  Sparkles, 
  User, 
  Bot, 
  RotateCcw, 
  Loader2,
  ChevronDown,
  Layers,
  FileText,
  Check,
  Pencil,
  X
} from 'lucide-react';

interface ChatAreaProps {
  messages: Message[];
  onSendMessage: (query: string) => Promise<void>;
  onClearChat: () => void;
  isLoading: boolean;
  targetLanguage: Language;
  onLanguageChange: (lang: Language) => void;
  selectedDocId: string | null;
  onSelectDoc: (id: string | null) => void;
  documents: DocumentMetadata[];
  activeSessionTitle?: string;
  onRenameSession?: (newTitle: string) => void;
}

export const ChatArea: React.FC<ChatAreaProps> = ({
  messages,
  onSendMessage,
  onClearChat,
  isLoading,
  targetLanguage,
  onLanguageChange,
  selectedDocId,
  onSelectDoc,
  documents,
  activeSessionTitle,
  onRenameSession,
}) => {
  const [input, setInput] = useState('');
  const [isContextDropdownOpen, setIsContextDropdownOpen] = useState(false);
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [titleInput, setTitleInput] = useState('');

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsContextDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

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

  const startRename = () => {
    setTitleInput(activeSessionTitle || 'New Conversation');
    setIsEditingTitle(true);
  };

  const saveRename = () => {
    if (titleInput.trim() && onRenameSession) {
      onRenameSession(titleInput.trim());
    }
    setIsEditingTitle(false);
  };

  const selectedDoc = documents.find(d => d.document_id === selectedDocId);

  return (
    <main className="flex-1 flex flex-col h-screen bg-white dark:bg-slate-950 relative transition-colors">
      {/* Top Navigation Bar */}
      <header className="h-14 border-b border-slate-200/80 dark:border-slate-800 px-4 md:px-6 flex items-center justify-between bg-white dark:bg-slate-950 z-10 gap-3">
        <div className="flex items-center gap-3 min-w-0 flex-1">
          {/* Active Conversation Title */}
          {isEditingTitle ? (
            <div className="flex items-center gap-1.5 max-w-xs">
              <input
                type="text"
                value={titleInput}
                onChange={(e) => setTitleInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') saveRename();
                  if (e.key === 'Escape') setIsEditingTitle(false);
                }}
                autoFocus
                className="text-xs font-semibold px-2 py-1 rounded border border-blue-400 dark:border-blue-600 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-100 focus:outline-none"
              />
              <button
                onClick={saveRename}
                className="p-1 text-emerald-600 hover:bg-slate-100 dark:hover:bg-slate-800 rounded"
              >
                <Check className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => setIsEditingTitle(false)}
                className="p-1 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 min-w-0 max-w-[240px] md:max-w-md">
              <span className="font-semibold text-xs md:text-sm text-slate-800 dark:text-slate-200 truncate">
                {activeSessionTitle || 'DOC-Lingo Chat'}
              </span>
              {onRenameSession && (
                <button
                  onClick={startRename}
                  className="p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 rounded hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                  title="Rename chat"
                >
                  <Pencil className="w-3 h-3" />
                </button>
              )}
            </div>
          )}

          <div className="h-4 w-px bg-slate-200 dark:bg-slate-800 shrink-0" />

          {/* Universal Context Dropdown */}
          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setIsContextDropdownOpen(!isContextDropdownOpen)}
              className="flex items-center gap-1.5 text-xs font-medium px-2.5 py-1.5 rounded-lg border border-slate-200/80 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-900 transition-colors"
            >
              <span className="text-slate-400 dark:text-slate-500 font-normal">Context:</span>
              {selectedDoc ? (
                <span className="flex items-center gap-1 text-blue-600 dark:text-blue-400 font-semibold max-w-[140px] md:max-w-[200px] truncate">
                  <FileText className="w-3.5 h-3.5 shrink-0" />
                  <span className="truncate">{selectedDoc.filename}</span>
                </span>
              ) : (
                <span className="flex items-center gap-1 text-slate-700 dark:text-slate-300 font-semibold">
                  <Layers className="w-3.5 h-3.5 text-blue-500 shrink-0" />
                  <span>All Documents ({documents.length})</span>
                </span>
              )}
              <ChevronDown className="w-3.5 h-3.5 text-slate-400 shrink-0" />
            </button>

            {/* Dropdown Menu */}
            {isContextDropdownOpen && (
              <div className="absolute top-full left-0 mt-1 w-64 md:w-80 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-lg z-50 p-1.5 space-y-1">
                <div className="px-2 py-1 text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                  Select Search Scope
                </div>
                {/* Option: All Documents */}
                <button
                  onClick={() => {
                    onSelectDoc(null);
                    setIsContextDropdownOpen(false);
                  }}
                  className={`w-full flex items-center justify-between px-2.5 py-2 rounded-lg text-xs transition-colors ${
                    selectedDocId === null
                      ? 'bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 font-semibold'
                      : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100/80 dark:hover:bg-slate-800'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <Layers className="w-4 h-4 text-blue-500 shrink-0" />
                    <span>All Documents (Cross-Doc Search)</span>
                  </div>
                  {selectedDocId === null && <Check className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />}
                </button>

                <div className="h-px bg-slate-200 dark:bg-slate-800 my-1" />

                {/* Option: Individual Documents */}
                <div className="max-h-48 overflow-y-auto space-y-0.5">
                  {documents.length === 0 ? (
                    <div className="p-3 text-center text-xs text-slate-400">
                      No documents available.<br/>Upload documents in the sidebar.
                    </div>
                  ) : (
                    documents.map((doc) => {
                      const isSelected = selectedDocId === doc.document_id;
                      return (
                        <button
                          key={doc.document_id}
                          onClick={() => {
                            onSelectDoc(doc.document_id);
                            setIsContextDropdownOpen(false);
                          }}
                          className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs transition-colors text-left ${
                            isSelected
                              ? 'bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 font-semibold'
                              : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100/80 dark:hover:bg-slate-800'
                          }`}
                        >
                          <div className="flex items-center gap-2 min-w-0 pr-2">
                            <FileText className={`w-3.5 h-3.5 shrink-0 ${isSelected ? 'text-blue-600 dark:text-blue-400' : 'text-slate-400'}`} />
                            <span className="truncate">{doc.filename}</span>
                          </div>
                          {isSelected && <Check className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400 shrink-0" />}
                        </button>
                      );
                    })
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Action Icons */}
        <div className="flex items-center gap-2.5 shrink-0">
          <LanguageSelector value={targetLanguage} onChange={onLanguageChange} />
          <ThemeToggle />
          {messages.length > 0 && (
            <button
              onClick={onClearChat}
              className="p-1.5 rounded-lg text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              title="Clear messages in this chat"
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
            <div className="w-12 h-12 rounded-2xl bg-blue-50 dark:bg-blue-950/40 border border-blue-100 dark:border-blue-900 flex items-center justify-center text-blue-600 dark:text-blue-400 shadow-sm mb-4">
              <Sparkles className="w-6 h-6" />
            </div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-1">
              Ask Anything Across Languages
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-6 leading-relaxed">
              Upload documents in English or Hindi, and ask questions in Hindi, Hinglish, or English.
              DOC-Lingo performs genuine semantic cross-lingual retrieval.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 w-full text-left mt-2">
              <div className="p-3.5 rounded-xl border border-slate-200/80 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/60 text-xs">
                <div className="font-semibold text-slate-800 dark:text-slate-200 mb-1 flex items-center gap-1.5">
                  <span className="text-base">📄</span> Any Topic or Domain
                </div>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                  Upload corporate reports, technical guides, legal contracts, or textbooks.
                </p>
              </div>

              <div className="p-3.5 rounded-xl border border-slate-200/80 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/60 text-xs">
                <div className="font-semibold text-slate-800 dark:text-slate-200 mb-1 flex items-center gap-1.5">
                  <span className="text-base">🌐</span> Multilingual In & Out
                </div>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                  Ask in Hindi script or Hinglish; get concise factual answers in the same language.
                </p>
              </div>

              <div className="p-3.5 rounded-xl border border-slate-200/80 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/60 text-xs">
                <div className="font-semibold text-slate-800 dark:text-slate-200 mb-1 flex items-center gap-1.5">
                  <span className="text-base">🎯</span> Verified Citations
                </div>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                  Every answer includes exact page numbers and verifiable chunks from the original source.
                </p>
              </div>
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3.5 max-w-3xl ${
                msg.role === 'user' ? 'ml-auto flex-row-reverse' : 'mr-auto'
              }`}
            >
              {/* Avatar */}
              <div
                className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 mt-0.5 text-xs font-semibold ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white shadow-xs'
                    : 'bg-slate-100 dark:bg-slate-800 text-blue-600 dark:text-blue-400 border border-slate-200/80 dark:border-slate-700'
                }`}
              >
                {msg.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              {/* Bubble & Metadata */}
              <div
                className={`flex flex-col space-y-2 min-w-0 ${
                  msg.role === 'user' ? 'items-end' : 'items-start'
                }`}
              >
                <div
                  className={`p-3.5 rounded-2xl text-xs leading-relaxed max-w-xl md:max-w-2xl whitespace-pre-wrap ${
                    msg.role === 'user'
                      ? 'bg-blue-600 text-white rounded-tr-sm shadow-xs'
                      : 'bg-slate-50 dark:bg-slate-900 text-slate-800 dark:text-slate-200 rounded-tl-sm border border-slate-200/80 dark:border-slate-800'
                  }`}
                >
                  {msg.content}
                </div>

                {/* Language indicators */}
                {msg.role === 'assistant' && (msg.detected_language || msg.target_language) && (
                  <div className="flex items-center gap-2 text-[10px] text-slate-400 dark:text-slate-500 px-1">
                    {msg.detected_language && (
                      <span>Query: <strong className="uppercase font-semibold">{msg.detected_language}</strong></span>
                    )}
                    {msg.target_language && (
                      <>
                        <span>•</span>
                        <span>Answer: <strong className="uppercase font-semibold">{msg.target_language}</strong></span>
                      </>
                    )}
                  </div>
                )}

                {/* Citations Panel */}
                {msg.citations && msg.citations.length > 0 && (
                  <div className="w-full max-w-2xl mt-1">
                    <CitationsList citations={msg.citations} />
                  </div>
                )}
              </div>
            </div>
          ))
        )}

        {isLoading && (
          <div className="flex gap-3.5 max-w-3xl mr-auto">
            <div className="w-7 h-7 rounded-lg bg-slate-100 dark:bg-slate-800 text-blue-600 dark:text-blue-400 border border-slate-200/80 dark:border-slate-700 flex items-center justify-center shrink-0 mt-0.5">
              <Bot className="w-4 h-4" />
            </div>
            <div className="p-3.5 rounded-2xl rounded-tl-sm bg-slate-50 dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 text-xs text-slate-500 dark:text-slate-400 flex items-center gap-2">
              <Loader2 className="w-3.5 h-3.5 animate-spin text-blue-600" />
              <span>Retrieving & synthesizing grounded answer...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Form Bar */}
      <div className="p-4 border-t border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-950">
        <div className="max-w-3xl mx-auto">
          <div className="relative flex items-end rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 shadow-xs focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-500/20 transition-all">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                selectedDoc 
                  ? `Ask about "${selectedDoc.filename}" in English, Hindi, or Hinglish...`
                  : 'Ask anything across all indexed documents in English, Hindi, or Hinglish...'
              }
              rows={1}
              className="w-full resize-none bg-transparent px-4 py-3 text-xs text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none min-h-[44px] max-h-32"
            />
            <div className="p-2">
              <button
                onClick={handleSubmit}
                disabled={!input.trim() || isLoading}
                className="h-8 w-8 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-40 disabled:hover:bg-blue-600 text-white flex items-center justify-center transition-all shadow-xs"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
          <div className="flex items-center justify-between text-[11px] text-slate-400 dark:text-slate-500 mt-2 px-1">
            <span>Press <strong>Enter</strong> to send, <strong>Shift+Enter</strong> for new line</span>
            <span>Multilingual Semantic RAG</span>
          </div>
        </div>
      </div>
    </main>
  );
};
