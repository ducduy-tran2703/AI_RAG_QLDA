import { usePendingApprovals, useProcessApproval } from '../../hooks/useApproval';

export default function PendingApprovalsPage() {
  const { data: requests, isLoading } = usePendingApprovals();
  const processApproval = useProcessApproval();

  const handleAction = async (requestId: string, action: 'approve' | 'reject') => {
    const note = prompt(`Lý do (nếu có):`);
    await processApproval.mutateAsync({ requestId, action, note: note || undefined });
  };

  if (isLoading) return <div className="p-4">Đang tải...</div>;
  if (!requests || requests.length === 0) return <div className="p-4">Không có yêu cầu chờ phê duyệt.</div>;

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Yêu cầu chờ phê duyệt ({requests.length})</h2>
      <div className="space-y-4">
        {requests.map((req) => (
          <div key={req.id} className="bg-white rounded shadow p-4">
            <div className="flex justify-between">
              <div>
                <p className="font-semibold">Document: {req.document_id}</p>
                <p className="text-sm text-gray-500">Gửi lúc: {new Date(req.submitted_at).toLocaleString('vi-VN')}</p>
                {req.deadline_at && <p className="text-sm text-red-500">Hạn: {new Date(req.deadline_at).toLocaleString('vi-VN')}</p>}
              </div>
              <div className="flex gap-2">
                <button onClick={() => handleAction(req.id, 'approve')} className="bg-green-600 text-white px-3 py-1 rounded">Duyệt</button>
                <button onClick={() => handleAction(req.id, 'reject')} className="bg-red-600 text-white px-3 py-1 rounded">Từ chối</button>
              </div>
            </div>
            {req.submitter_note && <p className="mt-2 text-sm italic">Ghi chú: {req.submitter_note}</p>}
          </div>
        ))}
      </div>
    </div>
  );
}