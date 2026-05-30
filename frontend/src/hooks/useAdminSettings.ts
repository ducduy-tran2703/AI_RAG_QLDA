import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../lib/api';

export function useAdminSettings() {
  return useQuery({
    queryKey: ['admin-settings'],
    queryFn: async () => {
      const res = await api.get('/admin/settings');
      return res.data;
    },
  });
}

export function useUpdateSetting() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ key, value }: { key: string, value: string }) => {
      const res = await api.put(`/admin/settings/${key}`, { value });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-settings'] });
    },
  });
}

export function useAuditLogs(page = 1, limit = 50) {
  return useQuery({
    queryKey: ['audit-logs', page, limit],
    queryFn: async () => {
      const res = await api.get('/admin/audit-logs', { params: { page, limit } });
      return res.data;
    },
  });
}
