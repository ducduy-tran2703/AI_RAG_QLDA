import { useParams, Link, useNavigate } from 'react-router-dom';
import { useCheckResult } from '../../hooks/useCheckResult';

const severityConfig: Record<string, { bg: string; text: string; border: string }> = {
  critical: { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200' },
  warning: { bg: 'bg-yellow-50', text: 'text-yellow-700', border: 'border-yellow-200' },
  info: { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200' },
};

export default function CheckResultPage() {
  const { id } = useParams<{ id: string }>();
  const { data, isLoading, error } = useCheckResult(id!);
  const navigate = useNavigate();

  if (isLoading) return <div className="p-4">Đang tải kết quả...</div>;
  if (error || !data) return <div className="p-4 text-red-500">Không tìm thấy kết quả</div>;

  const scoreColor = data.score
    ? data.score >= 90 ? 'text-green-600' : data.score >= 75 ? 'text-lime-600' : data.score >= 60 ? 'text-yellow-600' : 'text-red-600'
    : 'text-gray-500';

  return (
    <div className="max-w-4xl mx-auto">
      <Link to="/documents" className="text-blue-600 mb-4 inline-block">← Quay lại danh sách</Link>
      
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="flex items-center gap-4">
          <div className={`text-5xl font-bold ${scoreColor}`}>{data.score}/100</div>
          <div>
            <h2 className="text-2xl font-bold">Kết quả kiểm tra</h2>
            <p className="text-gray-500">
              {new Date(data.checked_at).toLocaleString('vi-VN')} · {data.ai_model} · ~{data.processing_time_ms}ms
            </p>
          </div>
        </div>
        <div className="grid grid-cols-3 gap-4 mt-4">
          <div className="bg-red-50 p-3 rounded text-center">
            <div className="text-xl font-bold text-red-600">{data.critical_count}</div>
            <div className="text-sm">Nghiêm trọng</div>
          </div>
          <div className="bg-yellow-50 p-3 rounded text-center">
            <div className="text-xl font-bold text-yellow-600">{data.warning_count}</div>
            <div className="text-sm">Cảnh báo</div>
          </div>
          <div className="bg-blue-50 p-3 rounded text-center">
            <div className="text-xl font-bold text-blue-600">{data.info_count}</div>
            <div className="text-sm">Thông tin</div>
          </div>
        </div>
      </div>

      <h3 className="text-xl font-semibold mb-3">Chi tiết lỗi ({data.total_errors})</h3>
      <div className="space-y-4">
        {data.errors.map((err) => {
          const sev = severityConfig[err.severity] || severityConfig.info;
          return (
            <div key={err.id} className={`${sev.bg} ${sev.border} border p-4 rounded-lg`}>
              <div className="flex justify-between items-start">
                <h4 className={`font-semibold ${sev.text}`}>{err.description}</h4>
                <span className={`capitalize px-2 py-0.5 rounded text-xs font-semibold ${sev.bg} ${sev.text}`}>
                  {err.severity}
                </span>
              </div>
              {err.location_info && (
                <p className="text-sm mt-1">
                  📍 Trang {err.location_info.page}{err.location_info.paragraph ? `, đoạn ${err.location_info.paragraph}` : ''}
                </p>
              )}
              <div className="mt-2 text-sm grid grid-cols-2 gap-2">
                <div><span className="text-red-500">❌</span> {err.current_value}</div>
                <div><span className="text-green-500">✅</span> {err.expected_value}</div>
              </div>
              {err.suggested_fix && <p className="mt-2 text-sm">💡 <strong>Gợi ý:</strong> {err.suggested_fix}</p>}
              {err.rag_reference && <p className="text-xs text-gray-600 mt-1">📖 {err.rag_reference}</p>}
              {err.confidence && <p className="text-xs text-gray-400 mt-1">Độ tin cậy: {(err.confidence * 100).toFixed(0)}%</p>}
            </div>
          );
        })}
      </div>

      {/* Nút gửi phê duyệt */}
      {data.status === 'completed' && (
        <div className="mt-6">
          <button
            onClick={() => navigate(`/submit-approval?docId=${data.document_id}&checkId=${data.id}`)}
            className="bg-orange-500 hover:bg-orange-600 text-white px-4 py-2 rounded"
          >
            Gửi phê duyệt
          </button>
        </div>
      )}
    </div>
  );
}