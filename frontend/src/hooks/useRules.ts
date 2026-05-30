import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { rulesApi } from '../lib/api';

export const useRuleSets = () => {
  return useQuery({
    queryKey: ['rule-sets'],
    queryFn: async () => {
      const res = await rulesApi.getSets();
      return res.data;
    },
  });
};

export const useRuleSet = (id: number) => {
  return useQuery({
    queryKey: ['rule-set', id],
    queryFn: async () => {
      const res = await rulesApi.getSet(id);
      return res.data;
    },
    enabled: !!id,
  });
};

export const useCreateRuleSet = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: any) => rulesApi.createSet(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['rule-sets'] }),
  });
};

export const useUpdateRuleSet = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => rulesApi.updateSet(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['rule-sets'] });
      queryClient.invalidateQueries({ queryKey: ['rule-set', variables.id] });
    },
  });
};

export const useCloneRuleSet = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => rulesApi.cloneSet(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['rule-sets'] }),
  });
};

export const useCreateRule = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ setId, data }: { setId: number; data: any }) => rulesApi.createRule(setId, data),
    onSuccess: (_, variables) => queryClient.invalidateQueries({ queryKey: ['rule-set', variables.setId] }),
  });
};

export const useUpdateRule = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, setId, data }: { id: string; setId: number; data: any }) => rulesApi.updateRule(id, data),
    onSuccess: (_, variables) => queryClient.invalidateQueries({ queryKey: ['rule-set', variables.setId] }),
  });
};

export const useDeleteRule = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, setId }: { id: string; setId: number }) => rulesApi.deleteRule(id),
    onSuccess: (_, variables) => queryClient.invalidateQueries({ queryKey: ['rule-set', variables.setId] }),
  });
};