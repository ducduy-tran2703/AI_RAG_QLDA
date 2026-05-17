import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../lib/api';

export interface ApprovalRequest {
  id: string;
  document_id: string;
  check_result_id?: string;
  submitted_by: string;
  approver_id: string;
  status: 'pending' | 'approved' | 'rejected';
  submitter_note?: string;
  approver_note?: string;
  submitted_at: string;
  reviewed_at?: string;
  deadline_at?: string;
}

export function usePendingApprovals() {
  return useQuery({
    queryKey: ['pending-approvals'],
    queryFn: async () => {
      const res = await api.get('/approval/requests/pending');
      return res.data as ApprovalRequest[];
    },
  });
}

export function useCreateApproval() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: {
      document_id: string;
      approver_id: string;
      note?: string;
      check_result_id?: string;
    }) => {
      const res = await api.post('/approval/requests', data);
      return res.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pending-approvals'] }),
  });
}

export function useProcessApproval() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ requestId, action, note }: { requestId: string; action: string; note?: string }) => {
      const res = await api.put(`/approval/requests/${requestId}`, { action, note });
      return res.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pending-approvals'] }),
  });
}