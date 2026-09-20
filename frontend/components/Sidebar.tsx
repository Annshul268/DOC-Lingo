'use client';

import React, { useRef, useState } from 'react';
import { DocumentMetadata, ChatSession, User } from '@/types';
import { groupSessionsByDate } from '@/lib/chatStorage';
import { api } from '@/lib/api';
import { auth } from '@/lib/auth';
import { 
  FileText, 
  UploadCloud, 
  Trash2, 
  Download,
  CheckCircle2, 
  Loader2, 
  AlertCircle, 
  Layers,
  Sparkles,
  MessageSquare,
  Plus,
  Pencil,
  Check,
  X,
  Clock,
  User as UserIcon,
  LogIn,
  UserPlus,
  Shield,
  RefreshCw
} from 'lucide-react';

interface SidebarProps {
  documents: DocumentMetadata[];
  selectedDocId: string | null;
  onSelectDoc: (id: string | null) => void;
  onUpload: (file: File) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
  isUploading: boolean;
  sessions: ChatSession[];
  activeSessionId: string | null;
  onSelectSession: (id: string) => void;
  onNewChat: () => void;
  onDeleteSession: (id: string) => void;
  onRenameSession: (id: string, newTitle: string) => void;
  currentUser?: User | null;
  onUserChange?: (user: User) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  documents,
  selectedDocId,
  onSelectDoc,
  onUpload,
  onDelete,
  isUploading,
  sessions,
  activeSessionId,
  onSelectSession,
  onNewChat,
  onDeleteSession,
  onRenameSession,
  currentUser,
  onUserChange,
}) => {
  const [activeTab, setActiveTab] = useState<'chats' | 'documents'>('chats');
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editTitleValue, setEditTitleValue] = useState('');

  // Auth & Multi-User State
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState<'switch' | 'login' | 'register'>('switch');
  const [usernameInput, setUsernameInput] = useState('');
  const [passwordInput, setPasswordInput] = useState('');
  const [authError, setAuthError] = useState<string | null>(null);
  const [isAuthSubmitting, setIsAuthSubmitting] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleDownload = async (doc: DocumentMetadata, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      let baseUrl = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api').trim().replace(/\/+$/, '');
      if (!baseUrl.endsWith('/api')) {
        baseUrl = `${baseUrl}/api`;
      }
      const token = auth.getToken();
      const headers: Record<string, string> = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch(`${baseUrl}/documents/${doc.document_id}/download`, { headers });
      if (!res.ok) throw new Error('Download failed or file not found');
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = doc.filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      alert(`Download error: ${err.message}`);
    }
  };

  const handleCreateNewGuest = async () => {
    setIsAuthSubmitting(true);
    setAuthError(null);
    try {
      const res = await api.createGuestSession();
      if (onUserChange) onUserChange(res.user);
      setIsAuthModalOpen(false);
    } catch (err: any) {
      setAuthError(err.message || 'Failed to create guest workspace');
    } finally {
      setIsAuthSubmitting(false);
    }
  };

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!usernameInput.trim() || !passwordInput.trim()) {
      setAuthError('Please provide both username and password');
      return;
    }
    setIsAuthSubmitting(true);
    setAuthError(null);
    try {
      const res = await api.login(usernameInput.trim(), passwordInput.trim());
      if (onUserChange) onUserChange(res.user);
      setUsernameInput('');
      setPasswordInput('');
      setIsAuthModalOpen(false);
    } catch (err: any) {
      setAuthError(err.message || 'Login failed');
    } finally {
      setIsAuthSubmitting(false);
    }
  };

  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!usernameInput.trim() || !passwordInput.trim()) {
      setAuthError('Please provide both username and password');
      return;
    }
    setIsAuthSubmitting(true);
    setAuthError(null);
    try {
      const res = await api.register(usernameInput.trim(), passwordInput.trim());
      if (onUserChange) onUserChange(res.user);
      setUsernameInput('');
      setPasswordInput('');
      setIsAuthModalOpen(false);
    } catch (err: any) {
      setAuthError(err.message || 'Registration failed');
    } finally {
      setIsAuthSubmitting(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      onUpload(e.target.files[0]);
    }
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onUpload(e.dataTransfer.files[0]);
    }
  };

  const startRename = (session: ChatSession, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingSessionId(session.id);
    setEditTitleValue(session.title);
  };

  const saveRename = (sessionId: string, e?: React.MouseEvent | React.FormEvent) => {
    if (e) e.stopPropagation();
    if (editTitleValue.trim()) {
      onRenameSession(sessionId, editTitleValue.trim());
    }
    setEditingSessionId(null);
  };

  const cancelRename = (e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingSessionId(null);
  };

  const { today, yesterday, previous } = groupSessionsByDate(sessions);

  const renderSessionItem = (session: ChatSession) => {
    const isActive = activeSessionId === session.id;
    const isEditing = editingSessionId === session.id;

    return (
      <div
        key={session.id}
        onClick={() => onSelectSession(session.id)}
        className={`group relative flex items-center justify-between p-2.5 rounded-lg text-xs cursor-pointer border transition-all ${
          isActive
            ? 'border-blue-200 dark:border-blue-800 bg-white dark:bg-slate-800 shadow-xs'
            : 'border-transparent hover:border-slate-200/60 dark:hover:border-slate-800 hover:bg-white dark:hover:bg-slate-800/60'
        }`}
      >
        <div className="flex items-center gap-2.5 min-w-0 pr-1 flex-1">
          <MessageSquare className={`w-3.5 h-3.5 shrink-0 ${isActive ? 'text-blue-600 dark:text-blue-400' : 'text-slate-400'}`} />
          {isEditing ? (
            <div className="flex items-center gap-1 flex-1" onClick={(e) => e.stopPropagation()}>
              <input
                type="text"
                value={editTitleValue}
                onChange={(e) => setEditTitleValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') saveRename(session.id);
                  if (e.key === 'Escape') setEditingSessionId(null);
                }}
                autoFocus
                className="w-full text-xs px-1.5 py-0.5 rounded border border-blue-400 dark:border-blue-600 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-100 focus:outline-none"
              />
              <button
                onClick={(e) => saveRename(session.id, e)}
                className="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-700 text-emerald-600"
                title="Save title"
              >
                <Check className="w-3 h-3" />
              </button>
              <button
                onClick={cancelRename}
                className="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-400"
                title="Cancel"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          ) : (
            <div className="min-w-0 flex-1">
              <p className={`truncate font-medium ${isActive ? 'text-blue-950 dark:text-blue-200 font-semibold' : 'text-slate-700 dark:text-slate-300'}`}>
                {session.title}
              </p>
              <div className="flex items-center gap-1.5 text-[10px] text-slate-400 dark:text-slate-500 mt-0.5">
                <span>{session.messages.length} msg{session.messages.length === 1 ? '' : 's'}</span>
                {session.selectedDocId ? (
                  <>
                    <span>•</span>
                    <span className="truncate max-w-[120px] text-blue-600 dark:text-blue-400">
                      {documents.find(d => d.document_id === session.selectedDocId)?.filename || 'Doc'}
                    </span>
                  </>
                ) : (
                  <>
                    <span>•</span>
                    <span>All Docs</span>
                  </>
                )}
              </div>
            </div>
          )}
        </div>

        {!isEditing && (
          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={(e) => startRename(session, e)}
              className="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
              title="Rename conversation"
            >
              <Pencil className="w-3 h-3" />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                if (confirm('Delete this chat?')) {
                  onDeleteSession(session.id);
                }
              }}
              className="p-1 rounded hover:bg-rose-50 dark:hover:bg-rose-950/40 text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 transition-colors"
              title="Delete conversation"
            >
              <Trash2 className="w-3 h-3" />
            </button>
          </div>
        )}
      </div>
    );
  };

  return (
    <aside className="w-80 border-r border-slate-200/80 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/60 flex flex-col h-screen shrink-0 transition-colors">
      {/* Brand Header */}
      <div className="p-4 border-b border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900">
        <div className="flex items-center gap-2">
          <div className="h-9 w-9 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-sm shadow-blue-500/20">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h1 className="font-bold text-lg text-slate-900 dark:text-white leading-tight">DOC-Lingo</h1>
            <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">Multilingual Document RAG</p>
          </div>
        </div>
      </div>

      {/* Tabs Navigation: Chats vs Documents */}
      <div className="p-2 border-b border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900/40">
        <div className="grid grid-cols-2 p-1 bg-slate-100 dark:bg-slate-800/80 rounded-lg text-xs font-medium">
          <button
            onClick={() => setActiveTab('chats')}
            className={`flex items-center justify-center gap-1.5 py-1.5 rounded-md transition-all ${
              activeTab === 'chats'
                ? 'bg-white dark:bg-slate-900 text-blue-600 dark:text-blue-400 font-semibold shadow-xs'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
            }`}
          >
            <MessageSquare className="w-3.5 h-3.5" />
            <span>Chats</span>
            <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300">
              {sessions.length}
            </span>
          </button>
          <button
            onClick={() => setActiveTab('documents')}
            className={`flex items-center justify-center gap-1.5 py-1.5 rounded-md transition-all ${
              activeTab === 'documents'
                ? 'bg-white dark:bg-slate-900 text-blue-600 dark:text-blue-400 font-semibold shadow-xs'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>My Documents</span>
            <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300">
              {documents.length}
            </span>
          </button>
        </div>
      </div>

      {/* TAB CONTENT: CHATS */}
      {activeTab === 'chats' && (
        <div className="flex-1 flex flex-col min-h-0">
          {/* New Chat Button */}
          <div className="p-3">
            <button
              onClick={onNewChat}
              className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-xs shadow-blue-500/20 transition-all hover:scale-[0.99]"
            >
              <Plus className="w-4 h-4" />
              <span>New Conversation</span>
            </button>
          </div>

          {/* Sessions List */}
          <div className="flex-1 overflow-y-auto px-3 space-y-3 pb-3">
            {sessions.length === 0 ? (
              <div className="p-6 text-center text-xs text-slate-400 dark:text-slate-500">
                No chat history yet.<br/>Start a conversation to see it saved here.
              </div>
            ) : (
              <>
                {today.length > 0 && (
                  <div className="space-y-1">
                    <p className="px-1 text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                      Today
                    </p>
                    {today.map(renderSessionItem)}
                  </div>
                )}

                {yesterday.length > 0 && (
                  <div className="space-y-1">
                    <p className="px-1 text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                      Yesterday
                    </p>
                    {yesterday.map(renderSessionItem)}
                  </div>
                )}

                {previous.length > 0 && (
                  <div className="space-y-1">
                    <p className="px-1 text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                      Previous
                    </p>
                    {previous.map(renderSessionItem)}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}

      {/* TAB CONTENT: DOCUMENTS */}
      {activeTab === 'documents' && (
        <div className="flex-1 flex flex-col min-h-0">
          {/* Upload Dropzone */}
          <div className="p-3">
            <div
              onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-3.5 text-center cursor-pointer transition-all ${
                isDragging 
                  ? 'border-blue-500 bg-blue-50/50 dark:bg-blue-950/20 scale-[0.99]' 
                  : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-blue-400 dark:hover:border-blue-500 hover:bg-slate-50/50 dark:hover:bg-slate-800/50'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx"
                className="hidden"
                onChange={handleFileChange}
                disabled={isUploading}
              />
              {isUploading ? (
                <div className="flex flex-col items-center gap-2 py-1">
                  <Loader2 className="w-6 h-6 text-blue-600 animate-spin" />
                  <div className="text-xs font-semibold text-slate-700 dark:text-slate-200">Indexing Document...</div>
                  <div className="text-[10px] text-slate-400">Embedding vectors into ChromaDB</div>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-1">
                  <div className="w-8 h-8 rounded-full bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 flex items-center justify-center">
                    <UploadCloud className="w-4 h-4" />
                  </div>
                  <p className="text-xs font-semibold text-slate-700 dark:text-slate-200">Drop PDF or DOCX here</p>
                  <p className="text-[10px] text-slate-400">or click to browse from device</p>
                </div>
              )}
            </div>
          </div>

          {/* Context Selector Section Header */}
          <div className="px-3 pb-1 flex items-center justify-between text-[10px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">
            <span>Query Context</span>
            <span>{documents.length} files</span>
          </div>

          {/* All Documents Button */}
          <div className="px-3 pb-2">
            <button
              onClick={() => onSelectDoc(null)}
              className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                selectedDocId === null
                  ? 'bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 font-semibold shadow-xs border border-blue-200 dark:border-blue-800'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100/80 dark:hover:bg-slate-800'
              }`}
            >
              <Layers className="w-4 h-4 text-blue-500" />
              <div className="text-left flex-1 min-w-0">
                <div className="truncate">All Documents</div>
                <div className="text-[10px] text-slate-400 font-normal">Cross-document search across library</div>
              </div>
            </button>
          </div>

          {/* Document List */}
          <div className="flex-1 overflow-y-auto px-3 space-y-1 pb-3">
            {documents.length === 0 ? (
              <div className="p-6 text-center text-xs text-slate-400 dark:text-slate-500">
                No documents uploaded yet.<br/>Upload a document to search with AI.
              </div>
            ) : (
              documents.map((doc) => {
                const isSelected = selectedDocId === doc.document_id;
                return (
                  <div
                    key={doc.document_id}
                    onClick={() => onSelectDoc(doc.document_id)}
                    className={`group flex items-start justify-between p-2.5 rounded-lg text-xs cursor-pointer border transition-all ${
                      isSelected
                        ? 'border-blue-200 dark:border-blue-800 bg-white dark:bg-slate-800 shadow-xs'
                        : 'border-transparent hover:border-slate-200/60 dark:hover:border-slate-800 hover:bg-white dark:hover:bg-slate-800/60'
                    }`}
                  >
                    <div className="flex items-start gap-2 min-w-0 pr-1 flex-1">
                      <FileText className={`w-4 h-4 mt-0.5 shrink-0 ${isSelected ? 'text-blue-600 dark:text-blue-400' : 'text-slate-400'}`} />
                      <div className="min-w-0 flex-1">
                        <p className={`truncate font-medium ${isSelected ? 'text-blue-950 dark:text-blue-200 font-semibold' : 'text-slate-700 dark:text-slate-300'}`}>
                          {doc.filename}
                        </p>
                        <div className="flex items-center gap-1.5 text-[10px] text-slate-400 dark:text-slate-500 mt-0.5">
                          <span>{doc.page_count} pg{doc.page_count > 1 ? 's' : ''}</span>
                          <span>•</span>
                          <span>{doc.chunk_count} chunks</span>
                          <span>•</span>
                          <span className="uppercase text-[9px] bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 px-1 py-0.2 rounded">
                            {doc.language || doc.file_type}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-1 shrink-0">
                      {doc.status === 'indexed' && (
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                      )}
                      {doc.status === 'error' && (
                        <AlertCircle className="w-3.5 h-3.5 text-rose-500" />
                      )}
                      <button
                        onClick={(e) => handleDownload(doc, e)}
                        className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 transition-opacity"
                        title="Download original file"
                      >
                        <Download className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onDelete(doc.document_id);
                        }}
                        className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-rose-50 dark:hover:bg-rose-950/40 text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 transition-opacity"
                        title="Delete document"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}

      {/* Footer Info & User Workspace Status */}
      <div className="p-3 border-t border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900 flex flex-col gap-2">
        <div className="flex items-center justify-between text-[11px] text-slate-600 dark:text-slate-300">
          <div className="flex items-center gap-1.5 min-w-0">
            <div className="w-5 h-5 rounded-full bg-blue-100 dark:bg-blue-900/50 flex items-center justify-center text-blue-600 dark:text-blue-400 shrink-0">
              <UserIcon className="w-3 h-3" />
            </div>
            <div className="truncate">
              <span className="font-semibold text-slate-800 dark:text-slate-200">{currentUser?.username || 'Guest'}</span>
              <span className="text-[10px] text-slate-400 dark:text-slate-500 ml-1">
                ({currentUser?.is_guest ? 'Guest' : 'Account'})
              </span>
            </div>
          </div>
          <button
            onClick={() => {
              setAuthError(null);
              setIsAuthModalOpen(true);
            }}
            className="text-[10px] font-medium text-blue-600 dark:text-blue-400 hover:underline shrink-0"
          >
            Switch User
          </button>
        </div>

        <div className="flex items-center justify-between text-[10px] text-slate-400 dark:text-slate-500 pt-1 border-t border-slate-100 dark:border-slate-800/60">
          <span className="flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
            Isolated Workspace
          </span>
          <span className="font-mono">ChromaDB</span>
        </div>
      </div>

      {/* User Switcher / Auth Modal */}
      {isAuthModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs">
          <div className="bg-white dark:bg-slate-900 rounded-xl max-w-sm w-full p-5 border border-slate-200 dark:border-slate-800 shadow-xl animate-in fade-in zoom-in duration-150">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
              <div className="flex items-center gap-2">
                <Shield className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                <h3 className="font-semibold text-sm text-slate-800 dark:text-slate-100">
                  {authMode === 'switch' && 'Switch Workspace'}
                  {authMode === 'login' && 'Log In to Account'}
                  {authMode === 'register' && 'Create New Account'}
                </h3>
              </div>
              <button
                onClick={() => setIsAuthModalOpen(false)}
                className="p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-md"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {authError && (
              <div className="mt-3 p-2 text-xs rounded-lg bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 border border-rose-200 dark:border-rose-900">
                {authError}
              </div>
            )}

            {authMode === 'switch' && (
              <div className="mt-4 space-y-3">
                <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-lg text-xs">
                  <div className="text-slate-500 dark:text-slate-400">Current Active Workspace:</div>
                  <div className="font-bold text-slate-800 dark:text-slate-100 mt-0.5">{currentUser?.username || 'Guest'}</div>
                  <div className="text-[10px] text-slate-400 font-mono mt-0.5">ID: {currentUser?.id}</div>
                </div>

                <button
                  type="button"
                  disabled={isAuthSubmitting}
                  onClick={handleCreateNewGuest}
                  className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg bg-blue-50 dark:bg-blue-950/50 hover:bg-blue-100 dark:hover:bg-blue-900/50 text-blue-600 dark:text-blue-400 text-xs font-semibold border border-blue-200 dark:border-blue-800 transition-colors"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isAuthSubmitting ? 'animate-spin' : ''}`} />
                  Create Clean Guest Workspace
                </button>

                <div className="grid grid-cols-2 gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => {
                      setAuthError(null);
                      setAuthMode('login');
                    }}
                    className="flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs font-medium"
                  >
                    <LogIn className="w-3.5 h-3.5" />
                    Log In
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setAuthError(null);
                      setAuthMode('register');
                    }}
                    className="flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs font-medium"
                  >
                    <UserPlus className="w-3.5 h-3.5" />
                    Register
                  </button>
                </div>
              </div>
            )}

            {authMode === 'login' && (
              <form onSubmit={handleLoginSubmit} className="mt-4 space-y-3">
                <div>
                  <label className="block text-xs font-medium text-slate-600 dark:text-slate-300 mb-1">Username</label>
                  <input
                    type="text"
                    value={usernameInput}
                    onChange={(e) => setUsernameInput(e.target.value)}
                    required
                    placeholder="e.g. user_alice"
                    className="w-full text-xs px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 focus:outline-hidden focus:ring-1 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 dark:text-slate-300 mb-1">Password</label>
                  <input
                    type="password"
                    value={passwordInput}
                    onChange={(e) => setPasswordInput(e.target.value)}
                    required
                    placeholder="••••••••"
                    className="w-full text-xs px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 focus:outline-hidden focus:ring-1 focus:ring-blue-500"
                  />
                </div>
                <div className="flex items-center gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setAuthMode('switch')}
                    className="flex-1 py-2 text-xs rounded-lg border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isAuthSubmitting}
                    className="flex-1 py-2 text-xs font-semibold rounded-lg bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50"
                  >
                    {isAuthSubmitting ? 'Logging in...' : 'Log In'}
                  </button>
                </div>
              </form>
            )}

            {authMode === 'register' && (
              <form onSubmit={handleRegisterSubmit} className="mt-4 space-y-3">
                <div>
                  <label className="block text-xs font-medium text-slate-600 dark:text-slate-300 mb-1">Username</label>
                  <input
                    type="text"
                    value={usernameInput}
                    onChange={(e) => setUsernameInput(e.target.value)}
                    required
                    placeholder="e.g. user_bob"
                    className="w-full text-xs px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 focus:outline-hidden focus:ring-1 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 dark:text-slate-300 mb-1">Password</label>
                  <input
                    type="password"
                    value={passwordInput}
                    onChange={(e) => setPasswordInput(e.target.value)}
                    required
                    placeholder="Min. 4 characters"
                    className="w-full text-xs px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 focus:outline-hidden focus:ring-1 focus:ring-blue-500"
                  />
                </div>
                <div className="flex items-center gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setAuthMode('switch')}
                    className="flex-1 py-2 text-xs rounded-lg border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isAuthSubmitting}
                    className="flex-1 py-2 text-xs font-semibold rounded-lg bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50"
                  >
                    {isAuthSubmitting ? 'Registering...' : 'Register'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </aside>
  );
};
