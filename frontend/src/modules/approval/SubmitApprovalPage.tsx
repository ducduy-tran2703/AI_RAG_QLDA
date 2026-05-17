import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useCreateApproval } from '../../hooks/useApproval';

export default function SubmitApprovalPage() {
  const [searchParams] = useSearchParams();
  const docId = searchParams.get('docId') || '';
  const checkId = searchParams.get('checkId') || '';
  const [note, setNote] = useState('');
  const navigate = useNavigate();
  const createApproval = useCreateApproval();

  const handleSubmit = async () => {
    if (!docId) return alert('Thiếu thông tin');
    // Giả sử ta có API lấy userId từ email (có thể dùng admin API). Tạm thời nhập thẳng UUID của approver.
    // Nhưng để đơn giản, ta sẽ thêm một ô nhập UUID (sau này hoàn thiện thành chọn người dùng).
    // Ở đây tạm dùng prompt nhập UUID.
    const approverId = prompt('Nhập UUID của người phê duyệt:');
    if (!approverId) return;

    try {
      await createApproval.mutateAsync({
        document_id: docId,
        approver_id: approverId,
        note,
        check_result_id: checkId || undefined,
      });
      alert('Đã gửi phê duyệt');
      navigate('/documents');
    } catch (e: any) {
      alert(e?.response?.data?.detail || 'Lỗi gửi phê duyệt');
    }
  };

  return (
    <div className="max-w-md mx-auto">
      <h2 className="text-xl font-bold mb-4">Gửi văn bản phê duyệt</h2>
      <p className="text-sm text-gray-600">Document ID: {docId}</p>
      <textarea
        className="w-full border p-2 rounded mt-2"
        rows={3}
        placeholder="Ghi chú (nếu có)"
        value={note}
        onChange={(e) => setNote(e.target.value)}
      />
      <div className="mt-4 flex gap-2">
        <button onClick={handleSubmit} className="bg-blue-600 text-white px-4 py-2 rounded">Gửi</button>
        <button onClick={() => navigate(-1)} className="bg-gray-300 px-4 py-2 rounded">Hủy</button>
      </div>
    </div>
  );
}