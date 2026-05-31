import { useState } from 'react';
import { useFolders, useCreateFolder, useDeleteFolder, useUpdateFolder } from '@/hooks/useFolders';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Edit2, Trash2, FolderPlus, Loader2 } from 'lucide-react';
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';

interface Props {
  selectedFolderId: string | null;
  onSelect: (folderId: string | null) => void;
}

export default function FolderSelector({ selectedFolderId, onSelect }: Props) {
  const { data: folders } = useFolders();
  const createFolder = useCreateFolder();
  const deleteFolder = useDeleteFolder();
  const updateFolder = useUpdateFolder();

  const [newFolderName, setNewFolderName] = useState('');
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [editName, setEditName] = useState('');

  const currentFolder = folders?.find(f => f.id === selectedFolderId);

  const NO_FOLDER_ID = '00000000-0000-0000-0000-000000000000';

  const handleCreate = async () => {
    if (!newFolderName.trim()) return;
    try {
      await createFolder.mutateAsync({ name: newFolderName });
      setNewFolderName('');
      setIsCreateOpen(false);
    } catch (e: any) {
      alert(e?.response?.data?.detail || 'Lỗi tạo thư mục');
    }
  };

  const handleRename = async () => {
    if (!editName.trim() || !selectedFolderId || selectedFolderId === NO_FOLDER_ID) return;
    try {
      await updateFolder.mutateAsync({ id: selectedFolderId, data: { name: editName } });
      setIsEditOpen(false);
    } catch (e: any) {
      alert(e?.response?.data?.detail || 'Lỗi đổi tên');
    }
  };

  const handleDelete = async () => {
    if (!selectedFolderId || !currentFolder || selectedFolderId === NO_FOLDER_ID) return;
    if (confirm(`Bạn có chắc chắn muốn xóa thư mục "${currentFolder.name}"? Thư mục phải trống mới có thể xóa.`)) {
      try {
        await deleteFolder.mutateAsync(selectedFolderId);
        onSelect(null);
      } catch (e: any) {
        alert(e?.response?.data?.detail || 'Lỗi khi xóa thư mục. Có thể thư mục vẫn còn chứa văn bản.');
      }
    }
  };

  return (
    <div className="flex items-center gap-2">
      <Select
        value={selectedFolderId || 'all'}
        onValueChange={(value) => onSelect(value === 'all' ? null : value)}
      >
        <SelectTrigger className="w-[220px]">
          <SelectValue placeholder="Tất cả thư mục" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Tất cả thư mục</SelectItem>
          <SelectItem value={NO_FOLDER_ID}>Mặc định (Chưa phân loại)</SelectItem>
          {folders?.map((f) => (
            <SelectItem key={f.id} value={f.id}>{f.name}</SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Nhóm nút điều khiển */}
      <div className="flex gap-1">
        {/* Nút Tạo mới */}
        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogTrigger asChild>
            <Button variant="outline" size="icon" className="h-10 w-10 shrink-0" title="Tạo thư mục mới">
              <FolderPlus className="h-4 w-4" />
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[400px]">
            <DialogHeader>
              <DialogTitle>Tạo thư mục mới</DialogTitle>
            </DialogHeader>
            <div className="py-4">
              <Label htmlFor="name" className="mb-2 block">Tên thư mục</Label>
              <Input
                id="name"
                placeholder="Văn bản đi, Văn bản đến..."
                value={newFolderName}
                onChange={(e) => setNewFolderName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
              />
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsCreateOpen(false)}>Hủy</Button>
              <Button onClick={handleCreate} disabled={createFolder.isPending}>
                {createFolder.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Tạo thư mục'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Nút Edit & Delete (Chỉ hiện khi đang chọn một thư mục cụ thể và không phải Mặc định) */}
        {selectedFolderId && selectedFolderId !== NO_FOLDER_ID && (
          <>
            <Dialog open={isEditOpen} onOpenChange={(open) => {
              if (open) setEditName(currentFolder?.name || '');
              setIsEditOpen(open);
            }}>
              <DialogTrigger asChild>
                <Button variant="outline" size="icon" className="h-10 w-10 shrink-0" title="Đổi tên thư mục">
                  <Edit2 className="h-4 w-4 text-blue-600" />
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[400px]">
                <DialogHeader>
                  <DialogTitle>Đổi tên thư mục</DialogTitle>
                </DialogHeader>
                <div className="py-4">
                  <Label htmlFor="edit-name" className="mb-2 block">Tên mới</Label>
                  <Input
                    id="edit-name"
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleRename()}
                  />
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setIsEditOpen(false)}>Hủy</Button>
                  <Button onClick={handleRename} disabled={updateFolder.isPending}>
                    {updateFolder.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Lưu thay đổi'}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>

            <Button
              variant="outline"
              size="icon"
              className="h-10 w-10 shrink-0 text-destructive"
              title="Xóa thư mục"
              onClick={handleDelete}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </>
        )}
      </div>
    </div>
  );
}
