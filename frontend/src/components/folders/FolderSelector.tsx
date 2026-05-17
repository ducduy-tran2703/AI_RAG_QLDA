import { useState } from 'react';
import { useFolders, useCreateFolder } from '@/hooks/useFolders';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

interface Props {
  selectedFolderId: string | null;
  onSelect: (folderId: string | null) => void;
}

export default function FolderSelector({ selectedFolderId, onSelect }: Props) {
  const { data: folders } = useFolders();
  const createFolder = useCreateFolder();
  const [newFolderName, setNewFolderName] = useState('');

  const handleCreate = async () => {
    if (!newFolderName.trim()) return;
    try {
      await createFolder.mutateAsync({ name: newFolderName });
      setNewFolderName('');
    } catch (e: any) {
      alert(e?.response?.data?.detail || 'Lỗi tạo thư mục');
    }
  };

  return (
    <div className="flex items-center gap-2">
      <Select
        value={selectedFolderId || ''}
        onValueChange={(value) => onSelect(value === 'all' ? null : value)}
      >
        <SelectTrigger className="w-[200px]">
          <SelectValue placeholder="Tất cả thư mục" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Tất cả thư mục</SelectItem>
          {folders?.map((f) => (
            <SelectItem key={f.id} value={f.id}>{f.name}</SelectItem>
          ))}
        </SelectContent>
      </Select>
      <div className="flex gap-1">
        <Input
          placeholder="Thư mục mới"
          value={newFolderName}
          onChange={(e) => setNewFolderName(e.target.value)}
          className="h-9 w-40"
        />
        <Button onClick={handleCreate} size="sm" className="h-9">
          +
        </Button>
      </div>
    </div>
  );
}