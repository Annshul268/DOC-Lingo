import { User, AuthResponse } from '@/types';

const TOKEN_KEY = 'doc_lingo_auth_token';
const USER_KEY = 'doc_lingo_auth_user';

export const auth = {
  getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(TOKEN_KEY);
  },

  setToken(token: string): void {
    if (typeof window === 'undefined') return;
    localStorage.setItem(TOKEN_KEY, token);
  },

  clearToken(): void {
    if (typeof window === 'undefined') return;
    localStorage.removeItem(TOKEN_KEY);
  },

  getUser(): User | null {
    if (typeof window === 'undefined') return null;
    const raw = localStorage.getItem(USER_KEY);
    if (!raw) return null;
    try {
      return JSON.parse(raw) as User;
    } catch {
      return null;
    }
  },

  setUser(user: User): void {
    if (typeof window === 'undefined') return;
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  },

  clearUser(): void {
    if (typeof window === 'undefined') return;
    localStorage.removeItem(USER_KEY);
  },

  saveAuth(authData: AuthResponse): void {
    this.setToken(authData.access_token);
    this.setUser(authData.user);
  },

  clearAuth(): void {
    this.clearToken();
    this.clearUser();
  }
};
