import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { knowledgeApi } from '../lib/api';

export const useKnowledgeDocuments = (params: any) => {
  return useQuery({
    queryKey: ['knowledge-documents', params],
    queryFn: async () => {
      const res = await knowledgeApi.listDocuments(params);
      return res.data;
    },
  });
};

export const useUploadKnowledgeDocument = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => knowledgeApi.uploadDocument(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-documents'] });
      queryClient.invalidateQueries({ queryKey: ['knowledge-stats'] });
    },
  });
};

export const useDeleteKnowledgeDocument = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => knowledgeApi.deleteDocument(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-documents'] });
      queryClient.invalidateQueries({ queryKey: ['knowledge-stats'] });
    },
  });
};

export const useUpdateKnowledgeDocument = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => knowledgeApi.updateDocument(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-documents'] });
    },
  });
};

export const useKnowledgeStats = () => {
  return useQuery({
    queryKey: ['knowledge-stats'],
    queryFn: async () => {
      const res = await knowledgeApi.getStats();
      return res.data;
    },
  });
};