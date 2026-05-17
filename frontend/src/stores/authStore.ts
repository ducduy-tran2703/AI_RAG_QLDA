import { create } from 'zustand';
import api from '../lib/api';

interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isInitialized: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  setToken: (token: string) => void;
  loadUserFromToken: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem('access_token'),
  isLoading: false,
  isInitialized: false,
  login: async (email, password) => {
    set({ isLoading: true });
    try {
      const res = await api.post('/auth/login', { email, password });
      const { access_token, user } = res.data;
      localStorage.setItem('access_token', access_token);
      set({ token: access_token, user, isLoading: false });
    } catch (err) {
      set({ isLoading: false });
      throw err;
    }
  },
  logout: () => {
    localStorage.removeItem('access_token');
    set({ token: null, user: null });
  },
  setToken: (token) => {
    localStorage.setItem('access_token', token);
    set({ token });
  },
  loadUserFromToken: async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      set({ isInitialized: true });
      return;
    }
    try {
      const res = await api.get('/auth/me');
      set({ token, user: res.data, isInitialized: true });
    } catch (err) {
      localStorage.removeItem('access_token');
      set({ token: null, user: null, isInitialized: true });
    }
  },
}));