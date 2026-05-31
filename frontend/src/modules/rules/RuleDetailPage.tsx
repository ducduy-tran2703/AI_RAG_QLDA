import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useRules, useCreateRule, useUpdateRule, useDeleteRules } from '@/hooks/useRules';
import { rulesApi } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
    ArrowLeft, Plus, Search, Trash2, Edit2,
    Loader2, Eye, EyeOff, Tag, X, PlusCircle
} from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';

export default function RuleDetailPage() {
  const { id: setId } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [keywords, setKeywords] = useState('');

  const { data, isLoading, refetch } = useRules(setId!, { page, limit: 20, keywords });
  const createMutation = useCreateRule();
  const updateMutation = useUpdateRule();
  const deleteMutation = useDeleteRules();

  // States cho Add
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [newRule, setNewRule] = useState({ content: '', keywords: [] as string[], questions: [] as string[], tags: [] as string[] });
  const [newInput, setNewInput] = useState({ keyword: '', question: '', tag: '' });

  // States cho Edit
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isEditLoading, setIsEditLoading] = useState(false);
  const [editingRuleId, setEditingRuleId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState({
    content: '',
    keywords: [] as string[],
    questions: [] as string[],
    tags: [] as string[],
    available: true
  });
  const [editInput, setEditInput] = useState({ keyword: '', question: '', tag: '' });

  const handleAdd = async () => {
    if (!newRule.content.trim()) return;
    try {
      await createMutation.mutateAsync({
        setId: setId!,
        data: {
          content: newRule.content,
          important_keywords: newRule.keywords,
          questions: newRule.questions,
          tag_kwd: newRule.tags,
        }
      });
      setIsAddOpen(false);
      setNewRule({ content: '', keywords: [], questions: [], tags: [] });
    } catch (error) {
        alert('Lỗi khi tạo quy tắc');
    }
  };

  const handleOpenEdit = async (ruleId: string) => {
    setEditingRuleId(ruleId);
    setIsEditLoading(true);
    setIsEditOpen(true);
    try {
        const res = await rulesApi.getRule(setId!, ruleId);
        const rule = res.data;
        setEditForm({
            content: rule.content || rule.content_with_weight || '',
            keywords: [...(rule.important_keywords || rule.important_kwd || [])],
            questions: [...(rule.questions || rule.question_kwd || [])],
            tags: [...(rule.tag_kwd || [])],
            available: rule.available ?? true
        });
        setEditInput({ keyword: '', question: '', tag: '' });
    } catch (error) {
        alert('Lỗi khi tải thông tin quy tắc');
        setIsEditOpen(false);
    } finally {
        setIsEditLoading(false);
    }
  };

  const handleUpdate = async () => {
    if (!editingRuleId || !editForm.content.trim()) return;
    try {
        await updateMutation.mutateAsync({
            setId: setId!,
            ruleId: editingRuleId,
            data: {
                content: editForm.content,
                important_keywords: editForm.keywords,
                questions: editForm.questions,
                tag_kwd: editForm.tags,
                available: editForm.available
            }
        });
        setIsEditOpen(false);
        setEditingRuleId(null);
    } catch (error) {
        alert('Lỗi khi cập nhật quy tắc');
    }
  };

  const handleToggle = async (rule: any) => {
    const newAvailable = !rule.available;
    try {
      await updateMutation.mutateAsync({
        setId: setId!,
        ruleId: rule.id,
        data: { available: newAvailable }
      });
    } catch (error) {
      alert('Lỗi khi thay đổi trạng thái');
    }
  };

  const handleDelete = async (ruleId: string) => {
    if (confirm('Xóa quy tắc này?')) {
        try {
            await deleteMutation.mutateAsync({ setId: setId!, ruleIds: [ruleId] });
        } catch (error) {
            alert('Lỗi khi xóa');
        }
    }
  };

  const addItem = (field: 'keywords' | 'questions' | 'tags', value: string, isEdit: boolean) => {
    if (!value.trim()) return;
    const form = isEdit ? editForm : newRule;
    const setter = isEdit ? setEditForm : setNewRule;
    const inputSetter = isEdit ? setEditInput : setNewInput;
    const currentInput = isEdit ? editInput : newInput;

    if (!form[field].includes(value.trim())) {
        setter({ ...form, [field]: [...form[field], value.trim()] });
        inputSetter({ ...currentInput, [field.slice(0, -1) as any]: '' });
    }
  };

  const removeItem = (field: 'keywords' | 'questions' | 'tags', index: number, isEdit: boolean) => {
    const form = isEdit ? editForm : newRule;
    const setter = isEdit ? setEditForm : setNewRule;

    const newList = [...form[field]];
    newList.splice(index, 1);
    setter({ ...form, [field]: newList });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate('/rules')}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Chi tiết quy tắc</h2>
          <p className="text-sm text-muted-foreground">ID Bộ quy tắc: {setId}</p>
        </div>
        <div className="ml-auto">
            <Button onClick={() => setIsAddOpen(true)}>
                <Plus className="w-4 h-4 mr-2" /> Thêm quy tắc mới
            </Button>
        </div>
      </div>

      <Card>
        <CardHeader className="pb-3 border-b">
          <div className="flex items-center justify-between gap-4">
            <div className="relative flex-1 max-w-sm">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                    placeholder="Tìm kiếm quy tắc..."
                    value={keywords}
                    onChange={(e) => { setKeywords(e.target.value); setPage(1); }}
                    className="pl-9"
                />
            </div>
            <div className="text-sm font-medium text-muted-foreground">
               Tổng số: <span className="text-foreground">{data?.total || 0}</span> quy tắc
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="space-y-4">
            {isLoading ? (
              <div className="flex justify-center py-12"><Loader2 className="animate-spin h-8 w-8 text-primary" /></div>
            ) : data?.chunks.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground border-2 border-dashed rounded-lg">
                <p>Không tìm thấy quy tắc nào.</p>
              </div>
            ) : (
              <>
                <div className="grid gap-4">
                  {data?.chunks.map((rule: any) => (
                    <div key={rule.id} className="p-4 border rounded-xl hover:bg-muted/30 transition-all group relative">
                      <div className="flex justify-between items-start gap-4">
                        <div className="flex-1 space-y-3">
                            <div className="text-sm leading-relaxed whitespace-pre-wrap font-medium">{rule.content}</div>

                            <div className="flex flex-wrap gap-2">
                                {/* Tags */}
                                {rule.tag_kwd?.map((tag: string) => (
                                    <Badge key={tag} variant="outline" className="text-[10px] bg-primary/5 border-primary/20 flex items-center gap-1">
                                        <Tag className="w-2 h-2" /> {tag}
                                    </Badge>
                                ))}
                                {/* Keywords */}
                                {rule.important_keywords?.map((kw: string) => (
                                    <Badge key={kw} variant="secondary" className="text-[10px] bg-blue-50 text-blue-700 border-blue-100">{kw}</Badge>
                                ))}
                            </div>

                            {rule.questions?.length > 0 && (
                                <div className="space-y-1">
                                    <p className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider">Câu hỏi liên quan:</p>
                                    <div className="text-xs text-muted-foreground italic pl-2 border-l-2 border-muted">
                                        {rule.questions[0]} {rule.questions.length > 1 && `(+${rule.questions.length - 1} khác)`}
                                    </div>
                                </div>
                            )}
                        </div>

                        <div className="flex flex-col gap-2 shrink-0 items-end">
                            <Badge
                              variant={rule.available ? 'success' : 'outline'}
                              className="cursor-default h-fit w-fit"
                            >
                                {rule.available ? "Đang bật" : "Đang tắt"}
                            </Badge>
                            <div className="flex gap-1">
                                 <Button variant="outline" size="icon" className="h-8 w-8 hover:text-blue-600 hover:border-blue-200" onClick={() => handleOpenEdit(rule.id)}>
                                    <Edit2 className="h-4 w-4" />
                                 </Button>
                                 <Button variant="outline" size="icon" className="h-8 w-8 hover:text-destructive hover:border-red-200" onClick={() => handleDelete(rule.id)}>
                                    <Trash2 className="h-4 w-4" />
                                 </Button>
                            </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Pagination */}
                {data && data.total > 20 && (
                  <div className="flex items-center justify-between pt-6 border-t mt-4">
                    <p className="text-xs text-muted-foreground">
                      Hiển thị {((page - 1) * 20) + 1}-{Math.min(page * 20, data.total)} / {data.total} quy tắc
                    </p>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={page <= 1}
                        onClick={() => { setPage(page - 1); window.scrollTo(0, 0); }}
                      >
                        Trước
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={page >= Math.ceil(data.total / 20)}
                        onClick={() => { setPage(page + 1); window.scrollTo(0, 0); }}
                      >
                        Sau
                      </Button>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Overhauled Dialog Template for Add/Edit */}
      <RuleFormDialog
        isOpen={isAddOpen}
        onOpenChange={setIsAddOpen}
        title="Thêm quy tắc mới"
        description="Quy tắc này sẽ được lưu trực tiếp vào RAGFlow để AI tra cứu."
        formData={newRule}
        setFormData={setNewRule}
        inputValues={newInput}
        setInputValues={setNewInput}
        onSubmit={handleAdd}
        isLoading={createMutation.isPending}
        addItem={addItem}
        removeItem={removeItem}
        isEdit={false}
      />

      <RuleFormDialog
        isOpen={isEditOpen}
        onOpenChange={setIsEditOpen}
        title="Chỉnh sửa quy tắc"
        description="Cập nhật nội dung hoặc cấu hình cho quy tắc này."
        formData={editForm}
        setFormData={setEditForm}
        inputValues={editInput}
        setInputValues={setEditInput}
        onSubmit={handleUpdate}
        isLoading={updateMutation.isPending || isEditLoading}
        addItem={addItem}
        removeItem={removeItem}
        isEdit={true}
        isEditLoading={isEditLoading}
      />
    </div>
  );
}

// Helper component for the form to avoid code duplication
function RuleFormDialog({
    isOpen, onOpenChange, title, description, formData, setFormData,
    inputValues, setInputValues, onSubmit, isLoading, addItem, removeItem, isEdit, isEditLoading
}: any) {
    return (
        <Dialog open={isOpen} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>{title}</DialogTitle>
                    <DialogDescription>{description}</DialogDescription>
                </DialogHeader>

                {isEditLoading ? (
                    <div className="flex flex-col items-center justify-center py-12 space-y-4">
                        <Loader2 className="h-8 w-8 animate-spin text-primary" />
                        <p className="text-sm text-muted-foreground">Đang tải dữ liệu từ RAGFlow...</p>
                    </div>
                ) : (
                    <div className="space-y-6 py-4">
                        {/* Content Section */}
                        <div className="space-y-2">
                            <Label className="text-sm font-bold">Nội dung quy tắc</Label>
                            <textarea
                                className="w-full min-h-[120px] border rounded-md p-3 text-sm focus:ring-2 focus:ring-primary outline-none transition-all"
                                placeholder="Mô tả quy định..."
                                value={formData.content}
                                onChange={(e) => setFormData({...formData, content: e.target.value})}
                            />
                        </div>

                        <Separator />

                        {/* Tags Section */}
                        <div className="space-y-3">
                            <Label className="text-sm font-bold">Tags (Nhãn phân loại)</Label>
                            <div className="flex gap-2">
                                <Input
                                    placeholder="Ví dụ: dinh-dang, nghi-dinh-30..."
                                    value={inputValues.tag}
                                    onChange={(e) => setInputValues({...inputValues, tag: e.target.value})}
                                    onKeyDown={(e) => e.key === 'Enter' && addItem('tags', inputValues.tag, isEdit)}
                                />
                                <Button type="button" variant="secondary" onClick={() => addItem('tags', inputValues.tag, isEdit)}>
                                    <PlusCircle className="w-4 h-4" />
                                </Button>
                            </div>
                            <div className="flex flex-wrap gap-2">
                                {formData.tags.map((tag: string, i: number) => (
                                    <Badge key={i} variant="outline" className="pl-2 pr-1 py-1 gap-1 border-primary/30 text-primary bg-primary/5">
                                        {tag}
                                        <X className="w-3 h-3 cursor-pointer hover:text-destructive" onClick={() => removeItem('tags', i, isEdit)} />
                                    </Badge>
                                ))}
                            </div>
                        </div>

                        {/* Keywords Section */}
                        <div className="space-y-3">
                            <Label className="text-sm font-bold">Từ khóa quan trọng</Label>
                            <div className="flex gap-2">
                                <Input
                                    placeholder="Ví dụ: font-size, Times New Roman..."
                                    value={inputValues.keyword}
                                    onChange={(e) => setInputValues({...inputValues, keyword: e.target.value})}
                                    onKeyDown={(e) => e.key === 'Enter' && addItem('keywords', inputValues.keyword, isEdit)}
                                />
                                <Button type="button" variant="secondary" onClick={() => addItem('keywords', inputValues.keyword, isEdit)}>
                                    <PlusCircle className="w-4 h-4" />
                                </Button>
                            </div>
                            <div className="flex flex-wrap gap-2">
                                {formData.keywords.map((kw: string, i: number) => (
                                    <Badge key={i} variant="secondary" className="pl-2 pr-1 py-1 gap-1">
                                        {kw}
                                        <X className="w-3 h-3 cursor-pointer hover:text-destructive" onClick={() => removeItem('keywords', i, isEdit)} />
                                    </Badge>
                                ))}
                            </div>
                        </div>

                        {/* Questions Section */}
                        <div className="space-y-3">
                            <Label className="text-sm font-bold">Câu hỏi gợi ý</Label>
                            <div className="flex gap-2">
                                <Input
                                    placeholder="Ví dụ: Quy định về cỡ chữ như thế nào?"
                                    value={inputValues.question}
                                    onChange={(e) => setInputValues({...inputValues, question: e.target.value})}
                                    onKeyDown={(e) => e.key === 'Enter' && addItem('questions', inputValues.question, isEdit)}
                                />
                                <Button type="button" variant="secondary" onClick={() => addItem('questions', inputValues.question, isEdit)}>
                                    <PlusCircle className="w-4 h-4" />
                                </Button>
                            </div>
                            <div className="flex flex-col gap-2">
                                {formData.questions.map((q: string, i: number) => (
                                    <div key={i} className="flex items-center justify-between text-xs bg-muted p-2 rounded-md">
                                        <span className="italic">"{q}"</span>
                                        <X className="w-3 h-3 cursor-pointer hover:text-destructive ml-2 shrink-0" onClick={() => removeItem('questions', i, isEdit)} />
                                    </div>
                                ))}
                            </div>
                        </div>

                        {isEdit && (
                            <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                                <Label className="font-bold">Trạng thái kích hoạt</Label>
                                <Button
                                    type="button"
                                    variant={formData.available ? "success" : "outline"}
                                    size="sm"
                                    onClick={() => setFormData({...formData, available: !formData.available})}
                                >
                                    {formData.available ? "Đang bật" : "Đang tắt"}
                                </Button>
                            </div>
                        )}
                    </div>
                )}

                <DialogFooter className="border-t pt-4">
                    <Button variant="outline" onClick={() => onOpenChange(false)}>Hủy</Button>
                    <Button onClick={onSubmit} disabled={isLoading}>
                        {isLoading && !isEditLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                        {isEdit ? "Lưu thay đổi" : "Thêm quy tắc"}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
