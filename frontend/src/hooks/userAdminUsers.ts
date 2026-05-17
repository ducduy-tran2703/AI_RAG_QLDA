import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../lib/api';

export interface AdminUser {
  id: string;
  email: string;
  full_name: string;
  role: string;
  department_code?: string;
  is_active: boolean;
  last_login_at?: string;
  created_at: string;
}

export function useAdminUsers(page = 1, limit = 20, params?: Record<string, any>) {
  return useQuery({
    queryKey: ['admin-users', page, limit, params],
    queryFn: async () => {
      const res = await api.get('/admin/users/', { params: { page, limit, ...params } });
      return res.data;
    },
  });
}

export function useCreateUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: any) => (await api.post('/admin/users/', data)).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-users'] }),
  });
}

export function useLockUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (userId: string) => (await api.post(`/admin/users/${userId}/lock`)).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-users'] }),
  });
}

export function useUnlockUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (userId: string) => (await api.post(`/admin/users/${userId}/unlock`)).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-users'] }),
  });
}

export function useResetPassword() {
  return useMutation({
    mutationFn: async (userId: string) => {
      const res = await api.post(`/admin/users/${userId}/reset-password`);
      return res.data;
    },
  });
}