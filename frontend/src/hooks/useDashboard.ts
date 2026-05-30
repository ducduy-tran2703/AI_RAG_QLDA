import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '../lib/api';

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
      const res = await analyticsApi.getDashboard();
      return res.data as DashboardData;
    },
  });
}

export const useDashboardStats = () => {
  return useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const res = await analyticsApi.getDashboard();
      return res.data;
    },
  });
};