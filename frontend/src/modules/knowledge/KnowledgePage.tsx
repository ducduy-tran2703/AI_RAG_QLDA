import { useState } from 'react';
import { useKnowledgeCategories, useKnowledgeDocuments, useKnowledgeStats, useUploadKnowledgeDocument } from '@/hooks/useKnowledge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Database, Upload, Search, Filter, BookOpen, AlertCircle, CheckCircle2, Clock } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

export default function KnowledgePage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [categoryId, setCategoryId] = useState<string>('all');

  const { data: stats } = useKnowledgeStats();
  const { data: categories } = useKnowledgeCategories();
  const { data: documentsData, isLoading } = useKnowledgeDocuments({
    page,
    limit: 10,
    search,
    category_id: categoryId === 'all' ? undefined : Number(categoryId),
  });

  const uploadMutation = useUploadKnowledgeDocument();

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const title = file.name;
    const doc_type = file.name.endsWith('.pdf') ? 'pdf' : 'docx';

    try {
      await uploadMutation.mutateAsync({
        file,
        title,
        doc_type,
        category_id: categoryId === 'all' ? undefined : Number(categoryId),
      });
      alert('Tải lên thành công!');
    } catch (error) {
      alert('Lỗi khi tải lên tài liệu');
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'ready':
        return <Badge className="bg-green-500 text-white"><CheckCircle2 className="w-3 h-3 mr-1" /> Sẵn sàng</Badge>;
      case 'indexing':
        return <Badge className="bg-blue-500 text-white"><Clock className="w-3 h-3 mr-1 animate-spin" /> Đang xử lý</Badge>;
      case 'error':
        return <Badge variant="destructive"><AlertCircle className="w-3 h-3 mr-1" /> Lỗi</Badge>;
      default:
        return <Badge variant="secondary">Chờ xử lý</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Cơ sở tri thức (RAG)</h2>
          <p className="text-muted-foreground">Quản lý tài liệu pháp lý và quy chuẩn tham chiếu cho AI</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">
            <Database className="w-4 h-4 mr-2" /> Reindex tất cả
          </Button>
          <label>
            <Button asChild>
              <span>
                <Upload className="w-4 h-4 mr-2" /> Tải lên tài liệu
              </span>
            </Button>
            <input type="file" className="hidden" onChange={handleUpload} accept=".pdf,.docx" />
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
            <CardTitle className="text-sm font-medium">Dữ liệu vector</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_chunks || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Sẵn sàng</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.ready_docs || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Dung lượng</CardTitle>
            <div className="h-4 w-4 text-muted-foreground">MB</div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.size_mb?.toFixed(2) || 0}</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <CardTitle>Danh sách tài liệu</CardTitle>
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
              <Select value={categoryId} onValueChange={setCategoryId}>
                <SelectTrigger className="w-[180px]">
                  <Filter className="w-4 h-4 mr-2" />
                  <SelectValue placeholder="Danh mục" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tất cả danh mục</SelectItem>
                  {categories?.map((cat: any) => (
                    <SelectItem key={cat.id} value={cat.id.toString()}>{cat.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <table className="w-full text-sm">
              <thead className="bg-muted/50 border-b">
                <tr>
                  <th className="h-10 px-4 text-left font-medium">Tên tài liệu</th>
                  <th className="h-10 px-4 text-left font-medium">Mã hiệu</th>
                  <th className="h-10 px-4 text-left font-medium">Loại</th>
                  <th className="h-10 px-4 text-left font-medium">Trạng thái</th>
                  <th className="h-10 px-4 text-right font-medium">Hành động</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {isLoading ? (
                  <tr><td colSpan={5} className="h-24 text-center">Đang tải...</td></tr>
                ) : documentsData?.documents.length === 0 ? (
                  <tr><td colSpan={5} className="h-24 text-center">Không tìm thấy tài liệu nào</td></tr>
                ) : (
                  documentsData?.documents.map((doc: any) => (
                    <tr key={doc.id} className="hover:bg-muted/50 transition-colors">
                      <td className="p-4 font-medium">{doc.title}</td>
                      <td className="p-4">{doc.doc_code || '-'}</td>
                      <td className="p-4 uppercase text-xs font-bold text-muted-foreground">{doc.doc_type}</td>
                      <td className="p-4">{getStatusBadge(doc.index_status)}</td>
                      <td className="p-4 text-right">
                        <Button variant="ghost" size="sm">Xem</Button>
                        <Button variant="ghost" size="sm" className="text-destructive">Xóa</Button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}