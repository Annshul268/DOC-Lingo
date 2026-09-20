export type Language = 'auto' | 'en' | 'hi' | 'hinglish';

export interface User {
  id: string;
  username: string;
  email?: string | null;
  is_guest: boolean;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface DocumentMetadata {
  document_id: string;
  user_id?: string;
  filename: string;
  file_type: string;
  file_size_bytes: number;
  page_count: number;
  chunk_count: number;
  uploaded_at: string;
  status: 'uploading' | 'processing' | 'extracting' | 'embedding' | 'indexed' | 'error';
  error_message?: string;
  language?: string;
}

export interface Citation {
  document_id: string;
  filename: string;
  page_number: number;
  chunk_index: number;
  text_snippet: string;
  similarity_score: number;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  detected_language?: string;
  target_language?: string;
  timestamp: string;
}

export interface ChatSession {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  selectedDocId: string | null;
  targetLanguage: Language;
  messages: Message[];
}

