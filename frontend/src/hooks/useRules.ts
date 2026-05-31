import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { rulesApi } from '../lib/api';

export const useRuleSets = (params?: any) => {
  return useQuery({
    queryKey: ['rule-sets', params],
    queryFn: async () => {
      const res = await rulesApi.getSets(params);
      return res.data;
    },
  });
};

export const useUpdateRuleSet = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: { name: string } }) =>
      rulesApi.updateSet(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['rule-sets'] }),
  });
};

export const useDeleteRuleSet = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => rulesApi.deleteSet(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['rule-sets'] }),
  });
};

export const useRules = (setId: string, params?: any) => {
  return useQuery({
    queryKey: ['rules', setId, params],
    queryFn: async () => {
      const res = await rulesApi.listRules(setId, params);
      return res.data;
    },
    enabled: !!setId,
  });
};

export const useRuleDetail = (setId: string, ruleId: string | null) => {
  return useQuery({
    queryKey: ['rule-detail', setId, ruleId],
    queryFn: async () => {
      const res = await rulesApi.getRule(setId, ruleId!);
      return res.data;
    },
    enabled: !!setId && !!ruleId,
  });
};

export const useCreateRule = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ setId, data }: { setId: string; data: any }) =>
      rulesApi.createRule(setId, data),
    onSuccess: (_, { setId }) => queryClient.invalidateQueries({ queryKey: ['rules', setId] }),
  });
};

export const useUpdateRule = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ setId, ruleId, data }: { setId: string; ruleId: string; data: any }) =>
      rulesApi.updateRule(setId, ruleId, data),
    onSuccess: (_, { setId }) => queryClient.invalidateQueries({ queryKey: ['rules', setId] }),
  });
};

export const useDeleteRules = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ setId, ruleIds }: { setId: string; ruleIds: string[] }) =>
      rulesApi.deleteRules(setId, ruleIds),
    onSuccess: (_, { setId }) => queryClient.invalidateQueries({ queryKey: ['rules', setId] }),
  });
};
