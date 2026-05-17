import { useDashboard } from '../../hooks/useDashboard';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function DashboardPage() {
  const { data, isLoading } = useDashboard();

  if (isLoading) return <div className="p-4">Đang tải dashboard...</div>;
  if (!data) return null;

  const stats = [
    { label: 'Văn bản tháng này', value: data.total_documents, color: 'bg-blue-500' },
    { label: 'Kiểm tra hôm nay', value: data.documents_today, color: 'bg-green-500' },
    { label: 'Tỷ lệ đạt chuẩn', value: `${data.pass_rate}%`, color: 'bg-yellow-500' },
    { label: 'Điểm trung bình', value: `${data.average_score}/100`, color: 'bg-purple-500' },
  ];

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Tổng quan</h2>

      <div className="grid grid-cols-4 gap-4 mb-8">
        {stats.map((stat) => (
          <div key={stat.label} className="bg-white rounded shadow p-4">
            <p className="text-sm text-gray-500">{stat.label}</p>
            <p className={`text-3xl font-bold text-${stat.color.split('-')[1]}-600`}>{stat.value}</p>
          </div>
        ))}
      </div>

      <div className="bg-white rounded shadow p-4 mb-8">
        <h3 className="text-lg font-semibold mb-4">Xu hướng điểm tuân thủ (30 ngày)</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data.trend_data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" tick={{ fontSize: 12 }} />
            <YAxis domain={[0, 100]} />
            <Tooltip />
            <Line type="monotone" dataKey="score" stroke="#3b82f6" strokeWidth={2} dot={{ r: 4 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}