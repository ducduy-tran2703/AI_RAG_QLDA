import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { knowledgeApi } from '../lib/api';

export const useKnowledgeCategories = () => {
  return useQuery({
    queryKey: ['knowledge-categories'],
    queryFn: async () => {
      const res = await knowledgeApi.getCategories();
      return res.data;
    },
  });
};

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
    mutationFn: (data: any) => knowledgeApi.uploadDocument(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-documents'] });
      queryClient.invalidateQueries({ queryKey: ['knowledge-stats'] });
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