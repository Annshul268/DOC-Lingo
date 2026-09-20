'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Message, Language, Citation, DocumentMetadata, User as UserType } from '@/types';
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
  X,
  UploadCloud,
  PanelLeft
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
  currentUser?: UserType | null;
  onOpenAuthModal?: () => void;
  onUpload?: (file: File) => Promise<void>;
  isUploading?: boolean;
  isSidebarOpen?: boolean;
  onToggleSidebar?: () => void;
  onNewChat?: () => void;
}

// Friendly AI Robot & Foliage Mascot matching the warm golden amber & ivory theme
const RobotMascot: React.FC = () => (
  <svg
    viewBox="0 0 160 160"
    className="w-24 h-24 sm:w-28 sm:h-28 text-amber-500 dark:text-amber-400 drop-shadow-xs"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    {/* Background Tree / Foliage in soft golden cream and amber line art */}
    <path
      d="M48 118 C32 112, 16 95, 22 68 C28 42, 54 38, 66 50 C72 32, 98 30, 108 46 C118 40, 134 48, 134 66 C140 84, 128 106, 112 118 Z"
      className="fill-amber-50/90 dark:fill-amber-950/30 stroke-amber-500/80 dark:stroke-amber-400/80"
      strokeWidth="2.5"
      strokeLinejoin="round"
    />
    <path
      d="M52 118 L52 86 C52 80, 62 74, 72 78"
      className="stroke-amber-600/70 dark:stroke-amber-500/70"
      strokeWidth="2"
      strokeLinecap="round"
    />

    {/* Floating bilingual glyph pill near top foliage */}
    <g transform="translate(112, 32)">
      <circle cx="10" cy="10" r="10" className="fill-amber-100 dark:fill-amber-900/90 stroke-amber-400 dark:stroke-amber-400" strokeWidth="1.5" />
      <text x="10" y="14" textAnchor="middle" fontSize="10" fontWeight="bold" className="fill-amber-800 dark:fill-amber-200 font-sans">अ</text>
    </g>

    {/* Antenna */}
    <line x1="95" y1="65" x2="95" y2="52" className="stroke-stone-700 dark:stroke-stone-300" strokeWidth="2.5" strokeLinecap="round" />
    <circle cx="95" cy="50" r="4.5" className="fill-amber-400 stroke-stone-700 dark:stroke-stone-300" strokeWidth="2" />

    {/* Robot Head */}
    <rect x="74" y="65" width="42" height="34" rx="10" className="fill-white dark:fill-stone-900 stroke-stone-800 dark:stroke-stone-200" strokeWidth="2.5" />
    {/* Ears */}
    <rect x="69" y="75" width="5" height="12" rx="2" className="fill-amber-400 stroke-stone-800 dark:stroke-stone-200" strokeWidth="2" />
    <rect x="116" y="75" width="5" height="12" rx="2" className="fill-amber-400 stroke-stone-800 dark:stroke-stone-200" strokeWidth="2" />
    {/* Eyes */}
    <circle cx="87" cy="80" r="3.5" className="fill-stone-800 dark:fill-stone-200" />
    <circle cx="103" cy="80" r="3.5" className="fill-stone-800 dark:fill-stone-200" />
    {/* Smile */}
    <path d="M89 89 Q95 94 101 89" className="stroke-stone-800 dark:stroke-stone-200" strokeWidth="2" strokeLinecap="round" fill="none" />

    {/* Robot Body */}
    <rect x="80" y="104" width="30" height="26" rx="7" className="fill-white dark:fill-stone-900 stroke-stone-800 dark:stroke-stone-200" strokeWidth="2.5" />
    {/* Neck */}
    <line x1="90" y1="99" x2="100" y2="99" className="stroke-stone-800 dark:stroke-stone-200" strokeWidth="4" strokeLinecap="round" />
    {/* Screen on chest */}
    <rect x="86" y="110" width="18" height="12" rx="3" className="fill-amber-100/90 dark:fill-amber-950/80 stroke-amber-500/70 dark:stroke-amber-400/70" strokeWidth="1.5" />
    <circle cx="90" cy="116" r="1.5" className="fill-amber-500 dark:fill-amber-400" />
    <circle cx="95" cy="116" r="1.5" className="fill-amber-500 dark:fill-amber-400" />
    <circle cx="100" cy="116" r="1.5" className="fill-amber-500 dark:fill-amber-400" />

    {/* Arms */}
    <path d="M78 108 C68 112, 66 120, 70 126" className="stroke-stone-800 dark:stroke-stone-200" strokeWidth="2.5" strokeLinecap="round" fill="none" />
    <path d="M112 108 C122 112, 124 120, 120 126" className="stroke-stone-800 dark:stroke-stone-200" strokeWidth="2.5" strokeLinecap="round" fill="none" />

    {/* Legs */}
    <line x1="88" y1="130" x2="88" y2="142" className="stroke-stone-800 dark:stroke-stone-200" strokeWidth="3" strokeLinecap="round" />
    <line x1="102" y1="130" x2="102" y2="142" className="stroke-stone-800 dark:stroke-stone-200" strokeWidth="3" strokeLinecap="round" />
    {/* Feet */}
    <ellipse cx="86" cy="144" rx="5" ry="2.5" className="fill-stone-800 dark:fill-stone-200" />
    <ellipse cx="104" cy="144" rx="5" ry="2.5" className="fill-stone-800 dark:fill-stone-200" />
  </svg>
);

// Warm Golden Leaf / Feather icon for suggestion cards
const CardLeafIcon: React.FC = () => (
  <svg
    viewBox="0 0 24 24"
    className="w-4 h-4 text-amber-500 dark:text-amber-400 shrink-0 mt-0.5"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z" />
    <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12" />
  </svg>
);

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
  currentUser,
  onOpenAuthModal,
  onUpload,
  isUploading,
  isSidebarOpen,
  onToggleSidebar,
  onNewChat,
}) => {
  const [input, setInput] = useState('');
  const [isContextDropdownOpen, setIsContextDropdownOpen] = useState(false);
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [titleInput, setTitleInput] = useState('');

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const heroFileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  // Close context dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsContextDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleSubmit = (overrideQuery?: string) => {
    const query = (overrideQuery || input).trim();
    if (!query || isLoading) return;
    onSendMessage(query);
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

  const handleHeroFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0] && onUpload) {
      onUpload(e.target.files[0]);
    }
    if (heroFileInputRef.current) heroFileInputRef.current.value = '';
  };

  const selectedDoc = documents.find(d => d.document_id === selectedDocId);

  // 4 Curated generic prompt cards matching the home screen requirement
  const suggestionCards = [
    {
      title: 'Ask anything about your document',
      description: 'What are the main topics and key takeaways from this document?',
    },
    {
      title: 'Summarize a section',
      description: 'Provide a concise summary of the key sections and conclusions',
    },
    {
      title: 'Find specific information',
      description: 'Locate specific facts, figures, definitions, or instructions',
    },
    {
      title: 'Explain something simply',
      description: 'Break down complex concepts from the document into simple terms',
    },
  ];

  return (
    <main className="flex-1 flex flex-col h-screen bg-[#fffdfa] dark:bg-[#141210] relative transition-colors overflow-hidden">
      {/* Hidden file input for hero quick-upload */}
      <input
        type="file"
        ref={heroFileInputRef}
        onChange={handleHeroFileSelect}
        accept=".pdf,.docx"
        className="hidden"
      />

      {/* Top Header & Options Bar */}
      <header className="border-b border-stone-200/80 dark:border-stone-800 bg-[#fffdf9]/95 dark:bg-[#141210]/95 px-4 md:px-6 py-2.5 flex flex-wrap items-center justify-between gap-3 z-20 shrink-0 backdrop-blur-sm">
        {/* Left Side: Sidebar Toggle, Conversation Title, Context Dropdown */}
        <div className="flex items-center flex-wrap gap-2.5 min-w-0">
          {onToggleSidebar && (
            <button
              onClick={onToggleSidebar}
              className="p-1.5 rounded-lg hover:bg-amber-50 dark:hover:bg-stone-800 text-stone-500 hover:text-stone-800 dark:hover:text-stone-200 transition-colors shrink-0"
              title={isSidebarOpen ? 'Collapse sidebar' : 'Open sidebar'}
            >
              <PanelLeft className="w-4 h-4" />
            </button>
          )}

          {/* Active Conversation Title */}
          {isEditingTitle ? (
            <div className="flex items-center gap-1.5">
              <input
                type="text"
                value={titleInput}
                onChange={(e) => setTitleInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') saveRename();
                  if (e.key === 'Escape') setIsEditingTitle(false);
                }}
                autoFocus
                className="text-xs font-semibold px-2 py-1 rounded border border-amber-400 bg-white dark:bg-stone-900 text-stone-800 dark:text-stone-100 focus:outline-none"
              />
              <button onClick={saveRename} className="p-1 text-amber-600 hover:bg-amber-50 dark:hover:bg-stone-800 rounded">
                <Check className="w-3.5 h-3.5" />
              </button>
              <button onClick={() => setIsEditingTitle(false)} className="p-1 text-stone-400 hover:bg-amber-50 dark:hover:bg-stone-800 rounded">
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 min-w-0 max-w-[180px] md:max-w-xs">
              <span className="font-semibold text-xs md:text-sm text-stone-800 dark:text-stone-200 truncate">
                {activeSessionTitle || 'Conversation'}
              </span>
              {onRenameSession && (
                <button
                  onClick={startRename}
                  className="p-1 text-stone-400 hover:text-stone-600 dark:hover:text-stone-300 rounded hover:bg-amber-50 dark:hover:bg-stone-800 transition-colors shrink-0"
                  title="Rename conversation"
                >
                  <Pencil className="w-3 h-3" />
                </button>
              )}
            </div>
          )}

          <div className="hidden sm:block h-4 w-px bg-stone-200 dark:bg-stone-800 shrink-0" />

          {/* Context Dropdown */}
          <div className="relative shrink-0" ref={dropdownRef}>
            <button
              onClick={() => setIsContextDropdownOpen(!isContextDropdownOpen)}
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full border border-amber-200/90 dark:border-stone-800 bg-white/80 dark:bg-stone-900/80 hover:bg-amber-50/40 dark:hover:bg-stone-800 text-stone-700 dark:text-stone-300 text-xs transition-colors"
            >
              <span className="text-stone-400">Context:</span>
              <span className="font-semibold text-amber-900 dark:text-amber-300 max-w-[140px] truncate">
                {selectedDoc ? selectedDoc.filename : `All Documents (${documents.length})`}
              </span>
              <ChevronDown className="w-3 h-3 text-stone-400" />
            </button>

            {isContextDropdownOpen && (
              <div className="absolute top-full left-0 mt-1 w-64 bg-white dark:bg-stone-900 border border-amber-200 dark:border-stone-800 rounded-2xl shadow-lg z-50 p-1.5 space-y-1 text-left">
                <button
                  onClick={() => {
                    onSelectDoc(null);
                    setIsContextDropdownOpen(false);
                  }}
                  className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-xl text-xs transition-colors ${
                    selectedDocId === null
                      ? 'bg-amber-100/70 dark:bg-amber-950/40 text-amber-900 dark:text-amber-200 font-semibold'
                      : 'text-stone-700 dark:text-stone-300 hover:bg-amber-50/60 dark:hover:bg-stone-800'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <Layers className="w-3.5 h-3.5 text-amber-600" />
                    <span>All Documents</span>
                  </div>
                  {selectedDocId === null && <Check className="w-3 h-3 text-amber-600" />}
                </button>

                {documents.map((doc) => {
                  const isSelected = selectedDocId === doc.document_id;
                  return (
                    <button
                      key={doc.document_id}
                      onClick={() => {
                        onSelectDoc(doc.document_id);
                        setIsContextDropdownOpen(false);
                      }}
                      className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-xl text-xs transition-colors ${
                        isSelected
                          ? 'bg-amber-100/70 dark:bg-amber-950/40 text-amber-900 dark:text-amber-200 font-semibold'
                          : 'text-stone-700 dark:text-stone-300 hover:bg-amber-50/60 dark:hover:bg-stone-800'
                      }`}
                    >
                      <div className="flex items-center gap-2 min-w-0 pr-2">
                        <FileText className={`w-3.5 h-3.5 shrink-0 ${isSelected ? 'text-amber-600' : 'text-stone-400'}`} />
                        <span className="truncate">{doc.filename}</span>
                      </div>
                      {isSelected && <Check className="w-3 h-3 text-amber-600 shrink-0" />}
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Right Side: LanguageSelector, ThemeToggle, Clear Chat */}
        <div className="flex items-center gap-2 shrink-0">
          <LanguageSelector value={targetLanguage} onChange={onLanguageChange} />
          <ThemeToggle />
          {messages.length > 0 && (
            <button
              onClick={onClearChat}
              className="p-1.5 rounded-full text-stone-400 hover:text-stone-600 dark:hover:text-stone-300 hover:bg-amber-50 dark:hover:bg-stone-800 transition-colors"
              title="Clear messages"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </header>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto px-4 sm:px-6 md:px-8 py-4 flex flex-col">
        {messages.length === 0 ? (
          /* Empty / Hero State */
          <div className="flex-1 flex flex-col items-center justify-center max-w-2xl w-full mx-auto text-center px-2 py-6">
            {/* Mascot Illustration */}
            <div className="mb-2 transition-transform hover:scale-105 duration-300">
              <RobotMascot />
            </div>

            {/* Hero Heading */}
            <h1 className="text-3xl sm:text-4xl font-medium tracking-tight text-stone-900 dark:text-stone-100 mb-6">
              How can I help you?
            </h1>

            {/* Centered Large Prompt Input Pill */}
            <div className="w-full relative flex items-center rounded-full border border-amber-200/90 dark:border-stone-800 bg-white dark:bg-stone-900 shadow-xs hover:shadow-sm focus-within:shadow-md focus-within:border-amber-400 focus-within:ring-2 focus-within:ring-amber-400/20 transition-all pl-5 pr-2 py-1.5 mb-4">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={
                  selectedDoc
                    ? `Ask about "${selectedDoc.filename}" in English, Hindi, or Hinglish...`
                    : 'Ask anything about your documents in English, Hindi, or Hinglish...'
                }
                className="w-full bg-transparent text-sm text-stone-800 dark:text-stone-100 placeholder-stone-400 dark:placeholder-stone-500 focus:outline-none"
              />

              {/* Golden Yellow Circular Send Button */}
              <button
                onClick={() => handleSubmit()}
                disabled={!input.trim() || isLoading}
                className="w-10 h-10 rounded-full bg-amber-400 hover:bg-amber-500 active:bg-amber-600 disabled:opacity-40 text-stone-950 flex items-center justify-center transition-all shrink-0 hover:scale-105 active:scale-95 shadow-xs font-bold"
                title="Send query"
              >
                <Send className="w-4 h-4 ml-0.5" />
              </button>
            </div>

            {/* 2x2 Suggestion Cards Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full text-left">
              {suggestionCards.map((card, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSubmit(card.description)}
                  className="rounded-2xl p-3.5 bg-[#fefdf8] dark:bg-stone-900/60 border border-amber-200/60 dark:border-stone-800 hover:bg-[#fffbeb] dark:hover:bg-stone-800/80 hover:border-amber-400 transition-all cursor-pointer flex items-start gap-2.5 group shadow-2xs hover:shadow-xs text-left"
                >
                  <CardLeafIcon />
                  <div className="min-w-0 flex-1">
                    <div className="font-semibold text-xs text-stone-900 dark:text-stone-100 group-hover:text-amber-700 dark:group-hover:text-amber-400 transition-colors truncate">
                      {card.title}
                    </div>
                    <div className="text-[11px] text-stone-500 dark:text-stone-400 mt-0.5 line-clamp-2 leading-relaxed">
                      {card.description}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        ) : (
          /* Active Conversation Messages View */
          <div className="max-w-3xl w-full mx-auto space-y-6 pb-4">

            {/* Message List */}
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-3.5 max-w-3xl ${
                  msg.role === 'user' ? 'ml-auto flex-row-reverse' : 'mr-auto'
                }`}
              >
                {/* Avatar */}
                <div
                  className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 mt-0.5 text-xs font-semibold ${
                    msg.role === 'user'
                      ? 'bg-stone-900 dark:bg-amber-400 text-white dark:text-stone-950 shadow-xs'
                      : 'bg-amber-100 dark:bg-stone-800 text-amber-700 dark:text-amber-400 border border-amber-200/80 dark:border-stone-700'
                  }`}
                >
                  {msg.role === 'user' ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
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
                        ? 'bg-stone-900 dark:bg-amber-400 text-white dark:text-stone-950 rounded-tr-xs shadow-xs font-medium'
                        : 'bg-white dark:bg-stone-900 text-stone-800 dark:text-stone-200 rounded-tl-xs border border-amber-100/90 dark:border-stone-800 shadow-2xs'
                    }`}
                  >
                    {msg.content}
                  </div>

                  {/* Language indicators */}
                  {msg.role === 'assistant' && (msg.detected_language || msg.target_language) && (
                    <div className="flex items-center gap-2 text-[10px] text-stone-400 dark:text-stone-500 px-1">
                      {msg.detected_language && (
                        <span>Query: <strong className="uppercase font-semibold text-stone-600 dark:text-stone-300">{msg.detected_language}</strong></span>
                      )}
                      {msg.target_language && (
                        <>
                          <span>•</span>
                          <span>Answer: <strong className="uppercase font-semibold text-amber-700 dark:text-amber-400">{msg.target_language}</strong></span>
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
            ))}

            {/* Loading Indicator */}
            {isLoading && (
              <div className="flex gap-3.5 max-w-3xl mr-auto">
                <div className="w-7 h-7 rounded-full bg-amber-100 dark:bg-stone-800 text-amber-700 dark:text-amber-400 border border-amber-200/80 dark:border-stone-700 flex items-center justify-center shrink-0 mt-0.5">
                  <Bot className="w-3.5 h-3.5" />
                </div>
                <div className="p-3.5 rounded-2xl rounded-tl-xs bg-white dark:bg-stone-900 border border-amber-100 dark:border-stone-800 text-xs text-stone-600 dark:text-stone-400 flex items-center gap-2 shadow-2xs">
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-amber-500" />
                  <span>Retrieving & synthesizing cross-lingual answer...</span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Persistent Bottom Prompt Input Bar (Visible during active conversation) */}
      {messages.length > 0 && (
        <div className="p-4 border-t border-amber-100/80 dark:border-stone-800 bg-[#fffdfa]/95 dark:bg-[#141210]/95 backdrop-blur-sm shrink-0">
          <div className="max-w-2xl mx-auto w-full">
            <div className="relative flex items-center rounded-full border border-amber-200/90 dark:border-stone-800 bg-white dark:bg-stone-900 shadow-xs hover:shadow-sm focus-within:shadow-md focus-within:border-amber-400 focus-within:ring-2 focus-within:ring-amber-400/20 transition-all pl-5 pr-2 py-1.5">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={
                  selectedDoc
                    ? `Ask about "${selectedDoc.filename}" in English, Hindi, or Hinglish...`
                    : 'Ask anything across your documents in English, Hindi, or Hinglish...'
                }
                className="w-full bg-transparent text-sm text-stone-800 dark:text-stone-100 placeholder-stone-400 dark:placeholder-stone-500 focus:outline-none"
              />
              <button
                onClick={() => handleSubmit()}
                disabled={!input.trim() || isLoading}
                className="w-10 h-10 rounded-full bg-amber-400 hover:bg-amber-500 active:bg-amber-600 disabled:opacity-40 text-stone-950 flex items-center justify-center transition-all shrink-0 hover:scale-105 active:scale-95 shadow-xs font-bold"
                title="Send message"
              >
                <Send className="w-4 h-4 ml-0.5" />
              </button>
            </div>
            <div className="flex items-center justify-between text-[11px] text-stone-400 dark:text-stone-500 mt-1.5 px-3">
              <span>Press <strong>Enter</strong> to send</span>
              <span>DOC-Lingo Multilingual RAG</span>
            </div>
          </div>
        </div>
      )}
    </main>
  );
};
