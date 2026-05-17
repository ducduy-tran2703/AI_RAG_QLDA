import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../lib/api';

export function useDocuments(page = 1, limit = 20, folderId?: string | null) {
  return useQuery({
    queryKey: ['documents', page, limit, folderId],
    queryFn: async () => {
      const params: any = { page, limit };
      if (folderId) params.folder_id = folderId;
      const res = await api.get('/documents/', { params });
      return res.data;
    },
  });
}

export function useUploadDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (formData: FormData) => {
      const res = await api.post('/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });
}