import { ChatSession, Language } from '@/types';

const STORAGE_KEY_SESSIONS = 'doc_lingo_chat_sessions_v1';
const STORAGE_KEY_ACTIVE_ID = 'doc_lingo_active_session_id';

export function loadSessions(): ChatSession[] {
  if (typeof window === 'undefined') return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY_SESSIONS);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch (err) {
    console.error('Failed to load chat sessions from localStorage:', err);
    return [];
  }
}

export function saveSessions(sessions: ChatSession[]): void {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(STORAGE_KEY_SESSIONS, JSON.stringify(sessions));
  } catch (err) {
    console.error('Failed to save chat sessions to localStorage:', err);
  }
}

export function loadActiveSessionId(): string | null {
  if (typeof window === 'undefined') return null;
  try {
    return localStorage.getItem(STORAGE_KEY_ACTIVE_ID);
  } catch (err) {
    return null;
  }
}

export function saveActiveSessionId(id: string | null): void {
  if (typeof window === 'undefined') return;
  try {
    if (id) {
      localStorage.setItem(STORAGE_KEY_ACTIVE_ID, id);
    } else {
      localStorage.removeItem(STORAGE_KEY_ACTIVE_ID);
    }
  } catch (err) {
    console.error('Failed to save active session ID:', err);
  }
}

export function generateSessionTitle(firstMessage: string): string {
  if (!firstMessage) return 'New Conversation';
  const clean = firstMessage.trim().replace(/^[#\-*>\s]+/, '');
  if (clean.length <= 32) return clean;
  return clean.slice(0, 32) + '...';
}

export function createNewSession(
  selectedDocId: string | null = null,
  targetLanguage: Language = 'auto',
  customTitle?: string
): ChatSession {
  const now = new Date().toISOString();
  return {
    id: `chat_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
    title: customTitle || 'New Conversation',
    createdAt: now,
    updatedAt: now,
    selectedDocId,
    targetLanguage,
    messages: [],
  };
}

export function groupSessionsByDate(sessions: ChatSession[]): {
  today: ChatSession[];
  yesterday: ChatSession[];
  previous: ChatSession[];
} {
  const now = new Date();
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const startOfYesterday = startOfToday - 24 * 60 * 60 * 1000;

  const today: ChatSession[] = [];
  const yesterday: ChatSession[] = [];
  const previous: ChatSession[] = [];

  // Sort descending by updatedAt
  const sorted = [...sessions].sort(
    (a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
  );

  for (const session of sorted) {
    const time = new Date(session.updatedAt || session.createdAt).getTime();
    if (time >= startOfToday) {
      today.push(session);
    } else if (time >= startOfYesterday) {
      yesterday.push(session);
    } else {
      previous.push(session);
    }
  }

  return { today, yesterday, previous };
}
