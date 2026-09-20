import { DocumentMetadata, Citation, Language, AuthResponse, User } from '@/types';
import { auth } from '@/lib/auth';

const getBaseUrl = (): string => {
  let url = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api').trim().replace(/\/+$/, '');
  if (!url.endsWith('/api')) {
    url = `${url}/api`;
  }
  return url;
};

const API_BASE_URL = getBaseUrl();

let guestSessionPromise: Promise<string | null> | null = null;

export const ensureToken = async (): Promise<string | null> => {
  let token = auth.getToken();
  if (token) return token;

  if (!guestSessionPromise) {
    guestSessionPromise = (async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/auth/session`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: null }),
        });
        if (!res.ok) return null;
        const data: AuthResponse = await res.json();
        auth.saveAuth(data);
        return data.access_token;
      } catch (e) {
        console.error('Failed to auto-create guest session:', e);
        return null;
      } finally {
        guestSessionPromise = null;
      }
    })();
  }
  return guestSessionPromise;
};

const getAuthHeaders = async (extra: Record<string, string> = {}): Promise<Record<string, string>> => {
  const headers: Record<string, string> = { ...extra };
  const token = await ensureToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
};

async function authFetch(url: string, init: RequestInit = {}): Promise<Response> {
  const customHeaders = (init.headers as Record<string, string>) || {};
  let headers = await getAuthHeaders(customHeaders);
  let res = await fetch(url, { ...init, headers });

  // Self-heal on 401 (e.g. token expired, cleared on server, or invalid)
  if (res.status === 401) {
    auth.clearAuth();
    headers = await getAuthHeaders(customHeaders);
    res = await fetch(url, { ...init, headers });
  }

  return res;
}

export interface ChatResponse {
  answer: string;
  citations: Citation[];
  detected_language: string;
  target_language: string;
  language?: string;
  sources?: Citation[];
  document_id?: string;
}

export const api = {
  async checkHealth() {
    const res = await fetch(`${API_BASE_URL}/health`);
    if (!res.ok) throw new Error('Backend health check failed');
    return res.json();
  },

  // --- Authentication ---
  async createGuestSession(username?: string): Promise<AuthResponse> {
    const res = await fetch(`${API_BASE_URL}/auth/session`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: username || null }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to create guest session' }));
      throw new Error(err.detail || 'Guest session creation failed');
    }
    const data: AuthResponse = await res.json();
    auth.saveAuth(data);
    return data;
  },

  async login(username: string, password: string): Promise<AuthResponse> {
    const res = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Login failed' }));
      throw new Error(err.detail || 'Invalid username or password');
    }
    const data: AuthResponse = await res.json();
    auth.saveAuth(data);
    return data;
  },

  async register(username: string, password: string, email?: string): Promise<AuthResponse> {
    const res = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password, email: email || null }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Registration failed' }));
      throw new Error(err.detail || 'Registration failed');
    }
    const data: AuthResponse = await res.json();
    auth.saveAuth(data);
    return data;
  },

  async getMe(): Promise<User> {
    const res = await authFetch(`${API_BASE_URL}/auth/me`);
    if (!res.ok) throw new Error('Failed to get user profile');
    return res.json();
  },

  // --- Documents ---
  async uploadDocument(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);

    const res = await authFetch(`${API_BASE_URL}/documents/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
  },

  async getDocuments(): Promise<{ documents: DocumentMetadata[]; total: number }> {
    const res = await authFetch(`${API_BASE_URL}/documents`);
    if (!res.ok) throw new Error('Failed to fetch documents');
    return res.json();
  },

  async deleteDocument(documentId: string): Promise<void> {
    const res = await authFetch(`${API_BASE_URL}/documents/${documentId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to delete document');
  },

  async downloadDocument(documentId: string, filename: string): Promise<void> {
    const res = await authFetch(`${API_BASE_URL}/documents/${documentId}/download`);
    if (!res.ok) throw new Error('Download failed or file not found');
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  },

  // --- Chat ---
  async askQuestion(
    query: string,
    documentId: string | null = null,
    targetLanguage: Language = 'auto',
    responseStyle: import('@/types').ResponseStyle = 'explain'
  ): Promise<ChatResponse> {
    const res = await authFetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query,
        document_id: documentId,
        target_language: targetLanguage,
        language: targetLanguage,
        response_style: responseStyle,
      }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to generate response' }));
      throw new Error(err.detail || 'Chat request failed');
    }
    return res.json();
  },

  async streamQuestion(
    query: string,
    documentId: string | null = null,
    targetLanguage: Language = 'auto',
    responseStyle: import('@/types').ResponseStyle = 'explain',
    onMeta: (meta: { detected_language: string; target_language: string; citations: Citation[] }) => void,
    onToken: (token: string) => void,
    onError: (err: any) => void
  ) {
    try {
      const res = await authFetch(`${API_BASE_URL}/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          document_id: documentId,
          target_language: targetLanguage,
          language: targetLanguage,
          response_style: responseStyle,
        }),
      });

      if (!res.ok || !res.body) {
        throw new Error('Streaming connection failed');
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6).trim();
            if (dataStr === '[DONE]') {
              return;
            }
            try {
              const parsed = JSON.parse(dataStr);
              if (parsed.type === 'meta') {
                onMeta(parsed);
              } else if (parsed.type === 'token') {
                onToken(parsed.token);
              }
            } catch (e) {
              // Ignore line parse errors
            }
          }
        }
      }
    } catch (err) {
      onError(err);
    }
  },
};
