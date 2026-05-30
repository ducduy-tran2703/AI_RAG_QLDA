import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useDocuments } from '../../hooks/useDocuments';
import FolderSelector from '../../components/folders/FolderSelector';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Plus, Search, FileText, Trash2, Download, ArrowUpDown } from 'lucide-react';
import { DocumentDto } from '@/types/index';
import { documentApi } from '@/lib/api';

export default function DocumentListPage() {
  const [folderId, setFolderId] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [sort, setSort] = useState('created_at');
  const [order, setOrder] = useState('desc');
  const navigate = useNavigate();

  const { data, isLoading, error, refetch } = useDocuments(page, 20, folderId, search, undefined, sort, order);

  if (isLoading) return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
    </div>
  );

  if (error) return (
    <div className="p-6 text-center">
      <p className="text-destructive mb-2">Lỗi tải dữ liệu</p>
      <Button variant="outline" onClick={() => refetch()}>Thử lại</Button>
    </div>
  );

  const documents: DocumentDto[] = data?.documents || [];
  const meta = data?.meta || { total: 0, page: 1, limit: 20, total_pages: 1 };

  const handleDelete = async (id: string) => {
    if (confirm('Xóa văn bản này?')) {
      await documentApi.delete(id);
      refetch();
    }
  };

  const handleSort = (column: string) => {
    if (sort === column) {
      setOrder(order === 'asc' ? 'desc' : 'asc');
    } else {
      setSort(column);
      setOrder('desc');
    }
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight">
          Văn bản <span className="text-muted-foreground text-lg font-normal">({meta.total})</span>
        </h1>
        <Button onClick={() => navigate('/upload')}>
          <Plus className="h-4 w-4 mr-1" /> Kiểm tra mới
        </Button>
      </div>

      {/* Search & Filter */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Tìm kiếm tên file..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="pl-9"
          />
        </div>
        <FolderSelector selectedFolderId={folderId} onSelect={setFolderId} />
      </div>

      {/* Table */}
      <div className="rounded-lg border bg-card">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b bg-muted/50">
                <th className="text-left p-3 text-sm font-medium text-muted-foreground">
                  <button onClick={() => handleSort('display_name')} className="flex items-center gap-1 hover:text-foreground">
                    Tên file <ArrowUpDown className="h-3 w-3" />
                  </button>
                </th>
                <th className="text-left p-3 text-sm font-medium text-muted-foreground">Loại</th>
                <th className="text-left p-3 text-sm font-medium text-muted-foreground">Dung lượng</th>
                <th className="text-left p-3 text-sm font-medium text-muted-foreground">
                  <button onClick={() => handleSort('created_at')} className="flex items-center gap-1 hover:text-foreground">
                    Ngày tạo <ArrowUpDown className="h-3 w-3" />
                  </button>
                </th>
                <th className="text-right p-3 text-sm font-medium text-muted-foreground">Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {documents.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-12 text-center text-muted-foreground">
                    <FileText className="h-12 w-12 mx-auto mb-2 opacity-20" />
                    <p>Chưa có văn bản nào</p>
                    <Button variant="outline" className="mt-2" onClick={() => navigate('/upload')}>
                      Tải lên văn bản đầu tiên
                    </Button>
                  </td>
                </tr>
              ) : (
                documents.map((doc) => (
                  <tr key={doc.id} className="border-b hover:bg-muted/30 transition-colors">
                    <td className="p-3">
                      <Link to={`/checks/${doc.id}`} className="flex items-center gap-2 hover:text-primary">
                        <FileText className="h-4 w-4 text-muted-foreground shrink-0" />
                        <span className="text-sm font-medium truncate max-w-xs">{doc.display_name}</span>
                      </Link>
                    </td>
                    <td className="p-3 text-sm uppercase text-muted-foreground">{doc.file_type}</td>
                    <td className="p-3 text-sm text-muted-foreground">
                      {(doc.file_size_bytes / 1024).toFixed(1)} KB
                    </td>
                    <td className="p-3 text-sm text-muted-foreground">
                      {new Date(doc.created_at).toLocaleDateString('vi-VN', {
                        day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit'
                      })}
                    </td>
                    <td className="p-3 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Button variant="ghost" size="icon" asChild>
                          <Link to={`/checks/${doc.id}`}><FileText className="h-4 w-4" /></Link>
                        </Button>
                        <Button variant="ghost" size="icon" onClick={() => documentApi.download(doc.id)}>
                          <Download className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="icon" onClick={() => handleDelete(doc.id)}>
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {meta.total_pages > 1 && (
          <div className="flex items-center justify-between p-3 border-t">
            <p className="text-sm text-muted-foreground">
              Hiển thị {((page - 1) * meta.limit) + 1}-{Math.min(page * meta.limit, meta.total)} / {meta.total}
            </p>
            <div className="flex gap-1">
              <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>
                Trước
              </Button>
              <Button variant="outline" size="sm" disabled={page >= meta.total_pages} onClick={() => setPage(page + 1)}>
                Sau
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}