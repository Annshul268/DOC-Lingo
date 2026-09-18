'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { Sidebar } from '@/components/Sidebar';
import { ChatArea } from '@/components/ChatArea';
import { DocumentMetadata, Message, Language, ChatSession } from '@/types';
import { api } from '@/lib/api';
import { 
  loadSessions, 
  saveSessions, 
  loadActiveSessionId, 
  saveActiveSessionId, 
  createNewSession, 
  generateSessionTitle 
} from '@/lib/chatStorage';

export default function Home() {
  const [documents, setDocuments] = useState<DocumentMetadata[]>([]);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);

  // Load documents and chat sessions on mount
  useEffect(() => {
    loadDocuments();

    // Load persisted sessions
    const storedSessions = loadSessions();
    const storedActiveId = loadActiveSessionId();

    if (storedSessions.length > 0) {
      setSessions(storedSessions);
      const validActive = storedSessions.find(s => s.id === storedActiveId);
      setActiveSessionId(validActive ? validActive.id : storedSessions[0].id);
    } else {
      // Initialize with a fresh conversation
      const initialSession = createNewSession(null, 'auto', 'New Conversation');
      setSessions([initialSession]);
      setActiveSessionId(initialSession.id);
      saveSessions([initialSession]);
      saveActiveSessionId(initialSession.id);
    }
    setIsInitialized(true);
  }, []);

  // Save sessions to localStorage whenever sessions change (after initialization)
  useEffect(() => {
    if (!isInitialized) return;
    saveSessions(sessions);
  }, [sessions, isInitialized]);

  // Save activeSessionId whenever it changes
  useEffect(() => {
    if (!isInitialized) return;
    saveActiveSessionId(activeSessionId);
  }, [activeSessionId, isInitialized]);

  const activeSession = useMemo(() => {
    return sessions.find(s => s.id === activeSessionId) || sessions[0] || null;
  }, [sessions, activeSessionId]);

  const loadDocuments = async () => {
    try {
      const data = await api.getDocuments();
      setDocuments(data.documents);
    } catch (err) {
      console.error('Failed to load documents:', err);
    }
  };

  const handleUpload = async (file: File) => {
    setIsUploading(true);
    try {
      await api.uploadDocument(file);
      await loadDocuments();
    } catch (err: any) {
      alert(`Upload error: ${err.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  const handleDeleteDocument = async (id: string) => {
    if (!confirm('Are you sure you want to delete this document?')) return;
    try {
      await api.deleteDocument(id);
      // If any sessions were pointing to this document, reset their context to All Documents (null)
      setSessions(prev =>
        prev.map(s => (s.selectedDocId === id ? { ...s, selectedDocId: null } : s))
      );
      await loadDocuments();
    } catch (err: any) {
      alert(`Delete error: ${err.message}`);
    }
  };

  const handleNewChat = () => {
    const newSession = createNewSession(null, 'auto', 'New Conversation');
    setSessions(prev => [newSession, ...prev]);
    setActiveSessionId(newSession.id);
  };

  const handleSelectSession = (id: string) => {
    setActiveSessionId(id);
  };

  const handleDeleteSession = (id: string) => {
    setSessions(prev => {
      const updated = prev.filter(s => s.id !== id);
      if (updated.length === 0) {
        const fresh = createNewSession(null, 'auto', 'New Conversation');
        setActiveSessionId(fresh.id);
        return [fresh];
      }
      if (activeSessionId === id) {
        setActiveSessionId(updated[0].id);
      }
      return updated;
    });
  };

  const handleRenameSession = (id: string, newTitle: string) => {
    setSessions(prev =>
      prev.map(s => (s.id === id ? { ...s, title: newTitle, updatedAt: new Date().toISOString() } : s))
    );
  };

  const handleSelectDoc = (id: string | null) => {
    if (!activeSession) return;
    setSessions(prev =>
      prev.map(s =>
        s.id === activeSession.id
          ? { ...s, selectedDocId: id, updatedAt: new Date().toISOString() }
          : s
      )
    );
  };

  const handleLanguageChange = (lang: Language) => {
    if (!activeSession) return;
    setSessions(prev =>
      prev.map(s =>
        s.id === activeSession.id
          ? { ...s, targetLanguage: lang, updatedAt: new Date().toISOString() }
          : s
      )
    );
  };

  const handleClearChat = () => {
    if (!activeSession) return;
    setSessions(prev =>
      prev.map(s =>
        s.id === activeSession.id
          ? { ...s, messages: [], updatedAt: new Date().toISOString() }
          : s
      )
    );
  };

  const handleSendMessage = async (query: string) => {
    if (!activeSession) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: query,
      timestamp: new Date().toISOString(),
    };

    const isFirstMessage = activeSession.messages.length === 0;
    const newTitle = isFirstMessage && activeSession.title === 'New Conversation'
      ? generateSessionTitle(query)
      : activeSession.title;

    // Immediately update UI with user message
    setSessions(prev =>
      prev.map(s =>
        s.id === activeSession.id
          ? {
              ...s,
              title: newTitle,
              messages: [...s.messages, userMessage],
              updatedAt: new Date().toISOString(),
            }
          : s
      )
    );

    setIsLoading(true);

    try {
      const res = await api.askQuestion(
        query,
        activeSession.selectedDocId,
        activeSession.targetLanguage
      );

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: res.answer,
        citations: res.citations,
        detected_language: res.detected_language,
        target_language: res.target_language,
        timestamp: new Date().toISOString(),
      };

      setSessions(prev =>
        prev.map(s =>
          s.id === activeSession.id
            ? {
                ...s,
                messages: [...s.messages, assistantMessage],
                updatedAt: new Date().toISOString(),
              }
            : s
        )
      );
    } catch (err: any) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Error: ${err.message || 'Failed to generate response'}`,
        timestamp: new Date().toISOString(),
      };

      setSessions(prev =>
        prev.map(s =>
          s.id === activeSession.id
            ? {
                ...s,
                messages: [...s.messages, errorMessage],
                updatedAt: new Date().toISOString(),
              }
            : s
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-white dark:bg-slate-950 transition-colors">
      <Sidebar
        documents={documents}
        selectedDocId={activeSession ? activeSession.selectedDocId : null}
        onSelectDoc={handleSelectDoc}
        onUpload={handleUpload}
        onDelete={handleDeleteDocument}
        isUploading={isUploading}
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={handleSelectSession}
        onNewChat={handleNewChat}
        onDeleteSession={handleDeleteSession}
        onRenameSession={handleRenameSession}
      />
      <ChatArea
        messages={activeSession ? activeSession.messages : []}
        onSendMessage={handleSendMessage}
        onClearChat={handleClearChat}
        isLoading={isLoading}
        targetLanguage={activeSession ? activeSession.targetLanguage : 'auto'}
        onLanguageChange={handleLanguageChange}
        selectedDocId={activeSession ? activeSession.selectedDocId : null}
        onSelectDoc={handleSelectDoc}
        documents={documents}
        activeSessionTitle={activeSession ? activeSession.title : 'New Conversation'}
        onRenameSession={(title) => {
          if (activeSession) handleRenameSession(activeSession.id, title);
        }}
      />
    </div>
  );
}
