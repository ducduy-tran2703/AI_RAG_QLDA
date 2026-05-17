import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useDocuments } from '../../hooks/useDocuments';
import FolderSelector from '../../components/folders/FolderSelector';

export default function DocumentListPage() {
  const [folderId, setFolderId] = useState<string | null>(null);
  const { data, isLoading, error } = useDocuments(1, 20, folderId);

  if (isLoading) return <div className="p-4">Đang tải...</div>;
  if (error) return <div className="p-4 text-red-500">Lỗi tải dữ liệu</div>;

  const documents = data?.documents || [];
  const meta = data?.meta || { total: 0 };

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold">Danh sách văn bản ({meta.total})</h2>
        <Link to="/upload" className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
          + Upload
        </Link>
      </div>

      <div className="mb-4">
        <FolderSelector selectedFolderId={folderId} onSelect={setFolderId} />
      </div>

      <div className="bg-white shadow rounded">
        <table className="min-w-full">
          <thead>
            <tr className="border-b bg-gray-50">
              <th className="text-left p-3">Tên file</th>
              <th className="text-left p-3">Loại</th>
              <th className="text-left p-3">Dung lượng</th>
              <th className="text-left p-3">Ngày tạo</th>
              <th className="text-left p-3"></th>
            </tr>
          </thead>
          <tbody>
            {documents.map((doc: any) => (
              <tr key={doc.id} className="border-b hover:bg-gray-50">
                <td className="p-3">{doc.original_filename}</td>
                <td className="p-3 uppercase">{doc.file_type}</td>
                <td className="p-3">{(doc.file_size_bytes / 1024).toFixed(1)} KB</td>
                <td className="p-3">{new Date(doc.created_at).toLocaleDateString('vi-VN')}</td>
                <td className="p-3">
                  <Link to={`/checks/${doc.id}`} className="text-blue-600 hover:underline text-sm">Xem kết quả</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}