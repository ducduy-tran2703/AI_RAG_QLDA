import { useQuery } from '@tanstack/react-query';
import api from '../lib/api';
import { CheckResult } from '../types/check';

export function useCheckResult(checkId: string) {
  return useQuery({
    queryKey: ['check', checkId],
    queryFn: async () => {
      const res = await api.get(`/checks/${checkId}`);
      return res.data as CheckResult;
    },
    enabled: !!checkId,
  });
}