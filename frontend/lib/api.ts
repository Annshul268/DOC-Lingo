import { DocumentMetadata, Citation, Language } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

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

  async uploadDocument(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(`${API_BASE_URL}/documents/upload`, {
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
    const res = await fetch(`${API_BASE_URL}/documents`);
    if (!res.ok) throw new Error('Failed to fetch documents');
    return res.json();
  },

  async deleteDocument(documentId: string): Promise<void> {
    const res = await fetch(`${API_BASE_URL}/documents/${documentId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to delete document');
  },

  async askQuestion(
    query: string,
    documentId: string | null = null,
    targetLanguage: Language = 'auto'
  ): Promise<ChatResponse> {
    const res = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query,
        document_id: documentId,
        target_language: targetLanguage,
        language: targetLanguage,
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
    onMeta: (meta: { detected_language: string; target_language: string; citations: Citation[] }) => void,
    onToken: (token: string) => void,
    onError: (err: any) => void
  ) {
    try {
      const res = await fetch(`${API_BASE_URL}/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          document_id: documentId,
          target_language: targetLanguage,
          language: targetLanguage,
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
