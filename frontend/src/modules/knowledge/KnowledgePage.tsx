import { useState } from 'react';
import { useKnowledgeDocuments, useKnowledgeStats, useUploadKnowledgeDocument, useDeleteKnowledgeDocument, useUpdateKnowledgeDocument } from '@/hooks/useKnowledge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Database, Upload, Search, BookOpen, AlertCircle, CheckCircle2, Clock, Trash2, Edit2, Loader2, Eye, EyeOff } from 'lucide-react';

export default function KnowledgePage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');

  // States cho chỉnh sửa
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [editingDoc, setEditingDoc] = useState<any>(null);
  const [newName, setNewName] = useState('');

  const { data: stats } = useKnowledgeStats();
  const { data: documentsData, isLoading } = useKnowledgeDocuments({
    page,
    limit: 10,
    search,
  });

  const uploadMutation = useUploadKnowledgeDocument();
  const deleteMutation = useDeleteKnowledgeDocument();
  const updateMutation = useUpdateKnowledgeDocument();

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      await uploadMutation.mutateAsync(file);
      alert('Tải lên thành công!');
    } catch (error) {
      alert('Lỗi khi tải lên tài liệu');
    }
  };

  const handleDelete = async (id: string) => {
    if (confirm('Xác nhận xóa tài liệu tri thức này?')) {
      try {
        await deleteMutation.mutateAsync(id);
      } catch (error) {
        alert('Lỗi khi xóa tài liệu');
      }
    }
  };

  const handleToggleStatus = async (doc: any) => {
    const newStatus = doc.status === '1' ? '0' : '1';
    try {
      await updateMutation.mutateAsync({ id: doc.id, data: { status: newStatus } });
    } catch (error) {
      alert('Lỗi khi thay đổi trạng thái');
    }
  };

  const handleUpdate = async () => {
    if (!editingDoc || !newName.trim()) return;
    try {
      await updateMutation.mutateAsync({ id: editingDoc.id, data: { name: newName } });
      setIsEditOpen(false);
      setEditingDoc(null);
    } catch (error) {
      alert('Lỗi khi đổi tên tài liệu');
    }
  };

  const getRunBadge = (run: string) => {
    switch (run) {
      case 'DONE':
      case '3':
        return <Badge className="bg-green-500 text-white"><CheckCircle2 className="w-3 h-3 mr-1" /> Sẵn sàng</Badge>;
      case 'RUNNING':
      case '1':
        return <Badge className="bg-blue-500 text-white"><Clock className="w-3 h-3 mr-1 animate-spin" /> Đang xử lý</Badge>;
      case 'FAIL':
      case '4':
        return <Badge variant="destructive"><AlertCircle className="w-3 h-3 mr-1" /> Lỗi</Badge>;
      case 'UNSTART':
      case '0':
        return <Badge variant="secondary">Chờ xử lý</Badge>;
      default:
        return <Badge variant="outline">{run}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Cơ sở tri thức (RAG)</h2>
          <p className="text-muted-foreground">Quản lý tài liệu tham chuẩn được lưu trữ trực tiếp trên RAGFlow</p>
        </div>
        <div className="flex gap-2">
          <label>
            <Button asChild>
              <span>
                <Upload className="w-4 h-4 mr-2" /> Tải lên tài liệu
              </span>
            </Button>
            <input type="file" className="hidden" onChange={handleUpload} accept=".pdf,.docx,.txt" />
          </label>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Tổng tài liệu</CardTitle>
            <BookOpen className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_docs || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Dữ liệu vector (Chunks)</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_chunks || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Trạng thái Kết nối</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-xs text-muted-foreground">Dataset ID:</div>
            <div className="text-[10px] font-mono truncate text-muted-foreground">Lấy từ .env</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <CardTitle>Danh sách tài liệu trên RAGFlow</CardTitle>
            <div className="flex items-center gap-2">
              <div className="relative w-64">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Tìm kiếm tài liệu..."
                  className="pl-8"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <table className="w-full text-sm">
              <thead className="bg-muted/50 border-b">
                <tr>
                  <th className="h-10 px-4 text-left font-medium">Tên tài liệu</th>
                  <th className="h-10 px-4 text-left font-medium w-32">Dung lượng</th>
                  <th className="h-10 px-4 text-left font-medium w-32">Phân mảnh</th>
                  <th className="h-10 px-4 text-left font-medium w-40">Xử lý (Run)</th>
                  <th className="h-10 px-4 text-left font-medium w-32">Sử dụng (Status)</th>
                  <th className="h-10 px-4 text-right font-medium">Hành động</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {isLoading ? (
                  <tr><td colSpan={6} className="h-24 text-center">Đang tải dữ liệu từ RAGFlow...</td></tr>
                ) : documentsData?.documents.length === 0 ? (
                  <tr><td colSpan={6} className="h-24 text-center">Không tìm thấy tài liệu nào trong dataset</td></tr>
                ) : (
                  documentsData?.documents.map((doc: any) => (
                    <tr key={doc.id} className="hover:bg-muted/50 transition-colors">
                      <td className="p-4 font-medium">{doc.name}</td>
                      <td className="p-4">{(doc.size / 1024).toFixed(1)} KB</td>
                      <td className="p-4">{doc.chunk_count} chunks</td>
                      <td className="p-4">{getRunBadge(doc.run)}</td>
                      <td className="p-4">
                        <Badge
                          variant={doc.status === '1' ? 'success' : 'outline'}
                          className="cursor-pointer"
                          onClick={() => handleToggleStatus(doc)}
                        >
                          {doc.status === '1' ? (
                            <><Eye className="w-3 h-3 mr-1" /> Đang bật</>
                          ) : (
                            <><EyeOff className="w-3 h-3 mr-1" /> Đang tắt</>
                          )}
                        </Badge>
                      </td>
                      <td className="p-4 text-right">
                        <div className="flex justify-end gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            title="Đổi tên"
                            onClick={() => {
                              setEditingDoc(doc);
                              setNewName(doc.name);
                              setIsEditOpen(true);
                            }}
                          >
                            <Edit2 className="h-4 w-4 text-blue-600" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="text-destructive"
                            title="Xóa"
                            onClick={() => handleDelete(doc.id)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Dialog Chỉnh sửa tên tài liệu */}
      <Dialog open={isEditOpen} onOpenChange={setIsEditOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Chỉnh sửa tài liệu</DialogTitle>
            <DialogDescription>Thay đổi tên hiển thị của tài liệu trong cơ sở tri thức.</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="name">Tên tài liệu</Label>
              <Input
                id="name"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleUpdate()}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsEditOpen(false)}>Hủy</Button>
            <Button onClick={handleUpdate} disabled={updateMutation.isPending}>
              {updateMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Lưu thay đổi'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
