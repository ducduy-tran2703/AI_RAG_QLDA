import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../lib/api';

export interface Folder {
  id: string;
  user_id: string;
  parent_id: string | null;
  name: string;
  color?: string;
  icon?: string;
  position: number;
  created_at: string;
  updated_at: string;
}

export function useFolders() {
  return useQuery({
    queryKey: ['folders'],
    queryFn: async () => {
      const res = await api.get('/documents/folders');
      return res.data as Folder[];
    },
  });
}

export function useCreateFolder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: { name: string; parent_id?: string | null; color?: string }) => {
      const res = await api.post('/documents/folders', data);
      return res.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['folders'] }),
  });
}

export function useDeleteFolder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/documents/folders/${id}`);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['folders'] }),
  });
}