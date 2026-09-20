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
  PanelLeft,
  Plus
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

// Friendly AI Robot & Foliage Mascot matching the reference image style
const RobotMascot: React.FC = () => (
  <svg
    viewBox="0 0 160 160"
    className="w-24 h-24 sm:w-28 sm:h-28 text-emerald-600 dark:text-emerald-400 drop-shadow-xs"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    {/* Background Tree / Foliage with gentle leaves like in reference */}
    <path
      d="M48 118 C32 112, 16 95, 22 68 C28 42, 54 38, 66 50 C72 32, 98 30, 108 46 C118 40, 134 48, 134 66 C140 84, 128 106, 112 118 Z"
      className="fill-emerald-50/90 dark:fill-emerald-950/40 stroke-emerald-600/80 dark:stroke-emerald-400/80"
      strokeWidth="2.5"
      strokeLinejoin="round"
    />
    <path
      d="M52 118 L52 86 C52 80, 62 74, 72 78"
      className="stroke-emerald-700/60 dark:stroke-emerald-500/60"
      strokeWidth="2"
      strokeLinecap="round"
    />

    {/* Floating bilingual glyph pill near top foliage */}
    <g transform="translate(112, 32)">
      <circle cx="10" cy="10" r="10" className="fill-emerald-100 dark:fill-emerald-900/90 stroke-emerald-600 dark:stroke-emerald-400" strokeWidth="1.5" />
      <text x="10" y="14" textAnchor="middle" fontSize="10" fontWeight="bold" className="fill-emerald-700 dark:fill-emerald-300 font-sans">अ</text>
    </g>

    {/* Antenna */}
    <line x1="95" y1="65" x2="95" y2="52" className="stroke-stone-700 dark:stroke-stone-300" strokeWidth="2.5" strokeLinecap="round" />
    <circle cx="95" cy="50" r="4.5" className="fill-emerald-500 stroke-stone-700 dark:stroke-stone-300" strokeWidth="2" />

    {/* Robot Head */}
    <rect x="74" y="65" width="42" height="34" rx="10" className="fill-white dark:fill-stone-900 stroke-stone-800 dark:stroke-stone-200" strokeWidth="2.5" />
    {/* Ears */}
    <rect x="69" y="75" width="5" height="12" rx="2" className="fill-emerald-500 stroke-stone-800 dark:stroke-stone-200" strokeWidth="2" />
    <rect x="116" y="75" width="5" height="12" rx="2" className="fill-emerald-500 stroke-stone-800 dark:stroke-stone-200" strokeWidth="2" />
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
    <rect x="86" y="110" width="18" height="12" rx="3" className="fill-emerald-100/90 dark:fill-emerald-950/80 stroke-emerald-600/70 dark:stroke-emerald-400/70" strokeWidth="1.5" />
    <circle cx="90" cy="116" r="1.5" className="fill-emerald-600 dark:fill-emerald-400" />
    <circle cx="95" cy="116" r="1.5" className="fill-emerald-600 dark:fill-emerald-400" />
    <circle cx="100" cy="116" r="1.5" className="fill-emerald-600 dark:fill-emerald-400" />

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

// Green Leaf icon matching the prompt cards in the reference image
const CardLeafIcon: React.FC = () => (
  <svg
    viewBox="0 0 24 24"
    className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5"
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

  // 4 Curated prompt cards matching the 2x2 grid from the reference image
  const suggestionCards = [
    {
      title: 'Operating Systems & Deadlocks',
      description: 'What are the four necessary conditions for deadlock?',
    },
    {
      title: 'Hinglish Deep Dive',
      description: 'Round robin scheduling mechanism kaise kaam karta hai?',
    },
    {
      title: 'हिंदी में विस्तृत सारांश',
      description: 'दस्तावेज़ के मुख्य सिद्धांतों और कार्यों का विवरण दें',
    },
    {
      title: 'Verified Source Citations',
      description: 'Cite exact page numbers and quotes from uploaded documents',
    },
  ];

  return (
    <main className="flex-1 flex flex-col h-screen bg-[#fcfdfa] dark:bg-stone-950 relative transition-colors overflow-hidden">
      {/* Hidden file input for hero quick-upload */}
      <input
        type="file"
        ref={heroFileInputRef}
        onChange={handleHeroFileSelect}
        accept=".pdf,.docx"
        className="hidden"
      />

      {/* Top Floating Banner (Inspired by reference banner pill) */}
      <div className="w-full pt-3 px-4 flex justify-center z-20 shrink-0">
        <div className="inline-flex items-center justify-between gap-3 px-4 py-1.5 rounded-full bg-white/95 dark:bg-stone-900/95 border border-stone-200/80 dark:border-stone-800 shadow-xs backdrop-blur-sm text-xs text-stone-600 dark:text-stone-300 max-w-2xl w-full">
          {/* Left status / brand pill */}
          <div className="flex items-center gap-2 truncate">
            {onToggleSidebar && (
              <button
                onClick={onToggleSidebar}
                className="p-1 rounded-full hover:bg-stone-100 dark:hover:bg-stone-800 text-stone-500 hover:text-stone-800 dark:hover:text-stone-200 transition-colors shrink-0"
                title={isSidebarOpen ? 'Hide Sidebar' : 'Open Document Library & Chats'}
              >
                <PanelLeft className="w-3.5 h-3.5" />
              </button>
            )}
            <span className="w-2 h-2 rounded-full bg-emerald-500 shrink-0" />
            <span className="truncate text-[11px] sm:text-xs font-normal">
              {documents.length > 0
                ? `${documents.length} document${documents.length > 1 ? 's' : ''} indexed • Cross-lingual RAG Active`
                : 'Isolated Workspace • Ask across English, Hindi & Hinglish'}
            </span>
          </div>

          {/* Right Action Button: Upgrade Pro style pill adapted to User Workspace */}
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={onOpenAuthModal}
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-indigo-500/90 hover:bg-indigo-600 text-white font-medium text-[11px] transition-colors shadow-2xs"
              title="Manage workspace or switch user account"
            >
              <Sparkles className="w-3 h-3" />
              <span className="max-w-[110px] truncate">
                {currentUser?.is_guest ? 'Guest Session' : currentUser?.username || 'Account'}
              </span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto px-4 sm:px-6 md:px-8 py-4 flex flex-col">
        {messages.length === 0 ? (
          /* Empty / Hero State (Faithfully formatted like the reference image) */
          <div className="flex-1 flex flex-col items-center justify-center max-w-2xl w-full mx-auto text-center px-2 py-6">
            {/* Mascot Illustration */}
            <div className="mb-2 transition-transform hover:scale-105 duration-300">
              <RobotMascot />
            </div>

            {/* Hero Heading */}
            <h1 className="text-3xl sm:text-4xl font-medium tracking-tight text-stone-800 dark:text-stone-100 mb-6">
              How can I help you?
            </h1>

            {/* Centered Large Prompt Input Pill */}
            <div className="w-full relative flex items-center rounded-full border border-stone-200/90 dark:border-stone-800 bg-white dark:bg-stone-900 shadow-sm hover:shadow-md focus-within:shadow-md focus-within:border-emerald-500 focus-within:ring-2 focus-within:ring-emerald-500/20 transition-all pl-5 pr-2 py-1.5 mb-4">
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

              {/* Green Circular Send Button */}
              <button
                onClick={() => handleSubmit()}
                disabled={!input.trim() || isLoading}
                className="w-10 h-10 rounded-full bg-emerald-600 hover:bg-emerald-700 disabled:opacity-40 text-white flex items-center justify-center transition-all shrink-0 hover:scale-105 active:scale-95 shadow-sm"
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
                  className="rounded-2xl p-3.5 bg-[#f6f8f5] dark:bg-stone-900/60 border border-stone-200/60 dark:border-stone-800/80 hover:bg-[#edf2eb] dark:hover:bg-stone-800 hover:border-emerald-500/30 transition-all cursor-pointer flex items-start gap-2.5 group shadow-2xs hover:shadow-xs text-left"
                >
                  <CardLeafIcon />
                  <div className="min-w-0 flex-1">
                    <div className="font-semibold text-xs text-stone-800 dark:text-stone-200 group-hover:text-emerald-700 dark:group-hover:text-emerald-400 transition-colors truncate">
                      {card.title}
                    </div>
                    <div className="text-[11px] text-stone-500 dark:text-stone-400 mt-0.5 line-clamp-2 leading-relaxed">
                      {card.description}
                    </div>
                  </div>
                </button>
              ))}
            </div>

            {/* Quick Upload & Document Scope Indicator */}
            <div className="flex flex-wrap items-center justify-center gap-2.5 mt-5 text-[11px] text-stone-500 dark:text-stone-400">
              <button
                onClick={() => heroFileInputRef.current?.click()}
                disabled={isUploading}
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full border border-dashed border-stone-300 dark:border-stone-700 hover:border-emerald-500 dark:hover:border-emerald-500 hover:bg-emerald-50/50 dark:hover:bg-emerald-950/30 text-stone-600 dark:text-stone-300 transition-colors"
              >
                {isUploading ? (
                  <Loader2 className="w-3 h-3 text-emerald-600 animate-spin" />
                ) : (
                  <UploadCloud className="w-3 h-3 text-emerald-600" />
                )}
                <span>{isUploading ? 'Indexing Document...' : 'Upload PDF / DOCX'}</span>
              </button>

              <div className="relative" ref={dropdownRef}>
                <button
                  onClick={() => setIsContextDropdownOpen(!isContextDropdownOpen)}
                  className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full border border-stone-200 dark:border-stone-800 bg-white/80 dark:bg-stone-900/80 hover:bg-stone-50 dark:hover:bg-stone-800 text-stone-600 dark:text-stone-300 transition-colors"
                >
                  <span className="text-stone-400">Context:</span>
                  <span className="font-medium text-emerald-700 dark:text-emerald-400 max-w-[140px] truncate">
                    {selectedDoc ? selectedDoc.filename : `All Documents (${documents.length})`}
                  </span>
                  <ChevronDown className="w-3 h-3 text-stone-400" />
                </button>

                {isContextDropdownOpen && (
                  <div className="absolute top-full left-1/2 -translate-x-1/2 mt-1 w-64 bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 rounded-xl shadow-lg z-50 p-1.5 space-y-1 text-left">
                    <button
                      onClick={() => {
                        onSelectDoc(null);
                        setIsContextDropdownOpen(false);
                      }}
                      className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs transition-colors ${
                        selectedDocId === null
                          ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 font-semibold'
                          : 'text-stone-700 dark:text-stone-300 hover:bg-stone-100 dark:hover:bg-stone-800'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <Layers className="w-3.5 h-3.5 text-emerald-600" />
                        <span>All Documents</span>
                      </div>
                      {selectedDocId === null && <Check className="w-3 h-3 text-emerald-600" />}
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
                          className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs transition-colors ${
                            isSelected
                              ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 font-semibold'
                              : 'text-stone-700 dark:text-stone-300 hover:bg-stone-100 dark:hover:bg-stone-800'
                          }`}
                        >
                          <div className="flex items-center gap-2 min-w-0 pr-2">
                            <FileText className={`w-3.5 h-3.5 shrink-0 ${isSelected ? 'text-emerald-600' : 'text-stone-400'}`} />
                            <span className="truncate">{doc.filename}</span>
                          </div>
                          {isSelected && <Check className="w-3 h-3 text-emerald-600 shrink-0" />}
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>

              <LanguageSelector value={targetLanguage} onChange={onLanguageChange} />
              <ThemeToggle />
            </div>
          </div>
        ) : (
          /* Active Conversation Messages View */
          <div className="max-w-3xl w-full mx-auto space-y-6 pb-4">
            {/* Conversation Header Pill */}
            <div className="flex items-center justify-between py-2 border-b border-stone-200/70 dark:border-stone-800 text-xs">
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
                    className="text-xs font-semibold px-2 py-1 rounded border border-emerald-500 bg-white dark:bg-stone-900 text-stone-800 dark:text-stone-100 focus:outline-none"
                  />
                  <button onClick={saveRename} className="p-1 text-emerald-600 hover:bg-stone-100 dark:hover:bg-stone-800 rounded">
                    <Check className="w-3.5 h-3.5" />
                  </button>
                  <button onClick={() => setIsEditingTitle(false)} className="p-1 text-stone-400 hover:bg-stone-100 dark:hover:bg-stone-800 rounded">
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              ) : (
                <div className="flex items-center gap-1.5 truncate">
                  <span className="font-semibold text-stone-800 dark:text-stone-200 truncate">
                    {activeSessionTitle || 'Conversation'}
                  </span>
                  {onRenameSession && (
                    <button
                      onClick={startRename}
                      className="p-1 text-stone-400 hover:text-stone-600 dark:hover:text-stone-300 rounded hover:bg-stone-100 dark:hover:bg-stone-800 transition-colors"
                      title="Rename conversation"
                    >
                      <Pencil className="w-3 h-3" />
                    </button>
                  )}
                </div>
              )}

              <div className="flex items-center gap-2">
                <LanguageSelector value={targetLanguage} onChange={onLanguageChange} />
                <ThemeToggle />
                <button
                  onClick={onClearChat}
                  className="p-1.5 rounded-full text-stone-400 hover:text-stone-600 dark:hover:text-stone-300 hover:bg-stone-100 dark:hover:bg-stone-800 transition-colors"
                  title="Clear messages"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                </button>
                {onNewChat && (
                  <button
                    onClick={onNewChat}
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-emerald-600 hover:bg-emerald-700 text-white font-medium text-[11px] transition-colors"
                  >
                    <Plus className="w-3 h-3" />
                    <span>New</span>
                  </button>
                )}
              </div>
            </div>

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
                      ? 'bg-emerald-600 text-white shadow-xs'
                      : 'bg-stone-100 dark:bg-stone-800 text-emerald-600 dark:text-emerald-400 border border-stone-200/80 dark:border-stone-700'
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
                        ? 'bg-emerald-600 text-white rounded-tr-xs shadow-xs'
                        : 'bg-white dark:bg-stone-900 text-stone-800 dark:text-stone-200 rounded-tl-xs border border-stone-200/80 dark:border-stone-800 shadow-2xs'
                    }`}
                  >
                    {msg.content}
                  </div>

                  {/* Language indicators */}
                  {msg.role === 'assistant' && (msg.detected_language || msg.target_language) && (
                    <div className="flex items-center gap-2 text-[10px] text-stone-400 dark:text-stone-500 px-1">
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
            ))}

            {/* Loading Indicator */}
            {isLoading && (
              <div className="flex gap-3.5 max-w-3xl mr-auto">
                <div className="w-7 h-7 rounded-full bg-stone-100 dark:bg-stone-800 text-emerald-600 dark:text-emerald-400 border border-stone-200/80 dark:border-stone-700 flex items-center justify-center shrink-0 mt-0.5">
                  <Bot className="w-3.5 h-3.5" />
                </div>
                <div className="p-3.5 rounded-2xl rounded-tl-xs bg-white dark:bg-stone-900 border border-stone-200/80 dark:border-stone-800 text-xs text-stone-500 dark:text-stone-400 flex items-center gap-2 shadow-2xs">
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-emerald-600" />
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
        <div className="p-4 border-t border-stone-200/70 dark:border-stone-800 bg-[#fcfdfa]/95 dark:bg-stone-950/95 backdrop-blur-sm shrink-0">
          <div className="max-w-2xl mx-auto w-full">
            <div className="relative flex items-center rounded-full border border-stone-200/90 dark:border-stone-800 bg-white dark:bg-stone-900 shadow-sm hover:shadow-md focus-within:shadow-md focus-within:border-emerald-500 focus-within:ring-2 focus-within:ring-emerald-500/20 transition-all pl-5 pr-2 py-1.5">
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
                className="w-10 h-10 rounded-full bg-emerald-600 hover:bg-emerald-700 disabled:opacity-40 text-white flex items-center justify-center transition-all shrink-0 hover:scale-105 active:scale-95 shadow-sm"
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
