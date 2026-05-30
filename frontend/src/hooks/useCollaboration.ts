import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../lib/api';

export function useComments(documentId: string) {
  return useQuery({
    queryKey: ['comments', documentId],
    queryFn: async () => {
      const res = await api.get(`/collaboration/comments/${documentId}`);
      return res.data;
    },
    enabled: !!documentId,
  });
}

export function useAddComment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: { document_id: string, error_id?: string, content: string }) => {
      const res = await api.post('/collaboration/comments', data);
      return res.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['comments', data.document_id] });
    },
  });
}
