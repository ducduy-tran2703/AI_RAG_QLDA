import { useState } from 'react';
import { useRuleSets, useUpdateRuleSet, useDeleteRuleSet } from '@/hooks/useRules';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Gavel, Edit2, Trash2, ArrowRight, Loader2, Search } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export default function RuleSetPage() {
  const [search, setSearch] = useState('');
  const { data: ruleSets, isLoading } = useRuleSets({ search });

  const updateMutation = useUpdateRuleSet();
  const deleteMutation = useDeleteRuleSet();

  const [isEditOpen, setIsEditOpen] = useState(false);
  const [editingSet, setEditingDoc] = useState<any>(null);
  const [newName, setNewName] = useState('');

  const handleDelete = async (id: string, name: string) => {
    if (confirm(`Xác nhận xóa bộ quy tắc "${name}"?`)) {
      try {
        await deleteMutation.mutateAsync(id);
      } catch (error) {
        alert('Lỗi khi xóa');
      }
    }
  };

  const handleUpdate = async () => {
    if (!editingSet || !newName.trim()) return;
    try {
      await updateMutation.mutateAsync({ id: editingSet.id, data: { name: newName } });
      setIsEditOpen(false);
    } catch (error) {
      alert('Lỗi khi đổi tên');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Bộ quy tắc kiểm tra</h2>
          <p className="text-muted-foreground">Quản lý các phụ lục quy định (Documents) được lưu trữ trên RAGFlow</p>
        </div>
        {/* IT-ADMIN sẽ upload qua script riêng hoặc nút upload sau này */}
      </div>

      <div className="flex items-center gap-2 max-w-md">
         <Search className="w-4 h-4 text-muted-foreground" />
         <Input
          placeholder="Tìm kiếm bộ quy tắc..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
         />
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {isLoading ? (
          <div className="col-span-full py-12 flex justify-center"><Loader2 className="animate-spin h-8 w-8 text-primary" /></div>
        ) : (
          ruleSets?.map((set: any) => (
            <Card key={set.id} className="hover:shadow-md transition-shadow">
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div className="p-2 bg-primary/10 rounded-lg">
                    <Gavel className="w-6 h-6 text-primary" />
                  </div>
                  <Badge variant={set.run === 'DONE' ? 'success' : 'secondary'}>{set.run}</Badge>
                </div>
                <CardTitle className="mt-4 line-clamp-1" title={set.name}>{set.name}</CardTitle>
                <CardDescription>ID: {set.id.substring(0, 8)}...</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex justify-between items-center mt-2">
                  <div className="text-xs text-muted-foreground">
                    Số quy tắc: <span className="font-bold text-foreground">{set.chunk_count}</span>
                  </div>
                  <div className="flex gap-1">
                    <Button variant="ghost" size="icon" onClick={() => {
                        setEditingDoc(set);
                        setNewName(set.name);
                        setIsEditOpen(true);
                    }}>
                      <Edit2 className="w-4 h-4 text-blue-600" />
                    </Button>
                    <Button variant="ghost" size="icon" onClick={() => handleDelete(set.id, set.name)}>
                      <Trash2 className="w-4 h-4 text-destructive" />
                    </Button>
                    <Button asChild size="sm">
                      <Link to={`/rules/${set.id}`}>
                        Chi tiết <ArrowRight className="w-4 h-4 ml-2" />
                      </Link>
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Dialog Đổi tên */}
      <Dialog open={isEditOpen} onOpenChange={setIsEditOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Đổi tên bộ quy tắc</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <Label htmlFor="name">Tên hiển thị</Label>
            <Input id="name" value={newName} onChange={(e) => setNewName(e.target.value)} />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsEditOpen(false)}>Hủy</Button>
            <Button onClick={handleUpdate} disabled={updateMutation.isPending}>Lưu thay đổi</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
