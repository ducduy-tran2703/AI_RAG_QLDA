import { useQuery } from '@tanstack/react-query';
import api from '../lib/api';

export interface DashboardData {
  total_documents: number;
  documents_today: number;
  pass_rate: number;
  average_score: number;
  recent_checks: any[];
  trend_data: { date: string; score: number }[];
}

export function useDashboard() {
  return useQuery({
    queryKey: ['dashboard'],
    queryFn: async () => {
      const res = await api.get('/analytics/dashboard');
      return res.data as DashboardData;
    },
  });
}