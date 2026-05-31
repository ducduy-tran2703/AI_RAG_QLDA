import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { checkApi } from '@/lib/api';
import { CheckResultDto } from '@/types/index';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { AlertCircle, CheckCircle, XCircle, Download, ArrowLeft, RotateCcw, ThumbsUp, ThumbsDown, FileText } from 'lucide-react';

const SEVERITY_CONFIG = {
  critical: { color: 'destructive', icon: XCircle, label: 'Nghiêm trọng' },
  warning: { color: 'warning', icon: AlertCircle, label: 'Cảnh báo' },
  info: { color: 'info', icon: CheckCircle, label: 'Thông tin' },
} as const;

function getScoreColor(score: number | null | undefined): string {
  if (!score && score !== 0) return 'text-gray-400';
  if (score >= 90) return 'text-green-600';
  if (score >= 75) return 'text-lime-600';
  if (score >= 60) return 'text-amber-600';
  return 'text-red-600';
}

function getScoreLabel(score: number | null | undefined): string {
  if (!score && score !== 0) return 'Chưa có';
  if (score >= 90) return 'Xuất sắc';
  if (score >= 75) return 'Đạt chuẩn';
  if (score >= 60) return 'Cần cải thiện';
  return 'Chưa đạt';
}

export default function CheckResultPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [filterSeverity, setFilterSeverity] = useState<string | null>(null);
  const [feedbackMap, setFeedbackMap] = useState<Record<string, 'correct' | 'incorrect'>>({});

  const { data: check, isLoading, error } = useQuery<CheckResultDto>({
    queryKey: ['check', id],
    queryFn: async () => {
      const res = await checkApi.get(id!);
      return res.data;
    },
    enabled: !!id,
  });

  const handleFeedback = async (errorId: string, isCorrect: boolean) => {
    try {
      await checkApi.sendFeedback(id!, errorId, isCorrect);
      setFeedbackMap(prev => ({ ...prev, [errorId]: isCorrect ? 'correct' : 'incorrect' }));
    } catch (err) {
      console.error('Feedback error:', err);
    }
  };

  const handleExport = async (format: 'json' | 'pdf') => {
    try {
      if (format === 'json') {
        const axiosRes = await checkApi.exportJson(id!);
        const blob = new Blob([JSON.stringify(axiosRes.data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `check_result_${id}.json`;
        a.click();
      } else {
        const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
        const response = await fetch(`${baseUrl}/checks/${id}/export/pdf`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
        });
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        window.open(url, '_blank');
      }
    } catch (err) {
      console.error('Export error:', err);
    }
  };

  if (isLoading) return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
    </div>
  );

  if (error || !check) return (
    <div className="p-6 text-center">
      <p className="text-destructive mb-2">Không tìm thấy kết quả kiểm tra</p>
      <Button variant="outline" onClick={() => navigate('/documents')}>Quay lại</Button>
    </div>
  );

  const filteredErrors = filterSeverity
    ? check.errors.filter(e => e.severity === filterSeverity)
    : check.errors;

  const severityCounts = {
    critical: check.critical_count,
    warning: check.warning_count,
    info: check.info_count,
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => navigate('/documents')}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-xl font-bold tracking-tight">Kết quả kiểm tra</h1>
            <p className="text-sm text-muted-foreground">
              {new Date(check.checked_at).toLocaleString('vi-VN')}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => handleExport('json')}>
            <Download className="h-4 w-4 mr-1" /> JSON
          </Button>
          <Button variant="outline" size="sm" onClick={() => handleExport('pdf')}>
            <Download className="h-4 w-4 mr-1" /> PDF
          </Button>
        </div>
      </div>

      {/* Score & Summary */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-wrap gap-6 items-start">
            {/* Score */}
            <div className="flex flex-col items-center">
              <div className={`text-5xl font-bold ${getScoreColor(check.score)}`}>
                {check.score ?? '--'}
              </div>
              <div className="text-sm text-muted-foreground mt-1">/ 100</div>
              <Badge variant={check.score && check.score >= 75 ? 'success' : check.score && check.score >= 60 ? 'warning' : 'destructive'}>
                {getScoreLabel(check.score)}
              </Badge>
            </div>

            {/* Stats */}
            <div className="flex gap-6 flex-wrap">
              <div className="text-center">
                <div className="text-2xl font-bold text-destructive">{check.critical_count}</div>
                <div className="text-xs text-muted-foreground">Nghiêm trọng</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-amber-500">{check.warning_count}</div>
                <div className="text-xs text-muted-foreground">Cảnh báo</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-500">{check.info_count}</div>
                <div className="text-xs text-muted-foreground">Thông tin</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold">{check.total_errors}</div>
                <div className="text-xs text-muted-foreground">Tổng lỗi</div>
              </div>
            </div>

            {/* Info */}
            <div className="ml-auto text-sm text-muted-foreground space-y-1">
              <p>⏱️ {check.processing_time_ms ? `${(check.processing_time_ms / 1000).toFixed(1)}s` : '--'}</p>
              <p>🤖 {check.ai_model || 'N/A'}</p>
              <p>📋 {check.status === 'completed' ? '✅ Hoàn tất' : check.status}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Filter */}
      <div className="flex gap-2 flex-wrap">
        <Button
          variant={filterSeverity === null ? 'default' : 'outline'}
          size="sm"
          onClick={() => setFilterSeverity(null)}
        >
          Tất cả ({check.errors.length})
        </Button>
        {(['critical', 'warning', 'info'] as const).map((sev) => (
          <Button
            key={sev}
            variant={filterSeverity === sev ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilterSeverity(sev)}
          >
            {SEVERITY_CONFIG[sev].label} ({severityCounts[sev]})
          </Button>
        ))}
      </div>

      {/* Errors List */}
      <div className="space-y-3">
        {filteredErrors.length === 0 ? (
          <Card>
            <CardContent className="p-12 text-center text-muted-foreground">
              <CheckCircle className="h-12 w-12 mx-auto mb-2 text-green-500" />
              <p className="text-lg font-medium">Không có lỗi nào!</p>
              <p className="text-sm">Văn bản đáp ứng đầy đủ thể thức theo quy định</p>
            </CardContent>
          </Card>
        ) : (
          filteredErrors.map((error) => {
            const SeverityIcon = SEVERITY_CONFIG[error.severity]?.icon || AlertCircle;
            const feedback = feedbackMap[error.id];

            return (
              <Card key={error.id} className={`border-l-4 ${
                error.severity === 'critical' ? 'border-l-red-500' :
                error.severity === 'warning' ? 'border-l-amber-500' :
                'border-l-blue-500'
              }`}>
                <CardContent className="p-4">
                  <div className="flex items-start gap-3">
                    <SeverityIcon className={`h-5 w-5 mt-0.5 ${
                      error.severity === 'critical' ? 'text-red-500' :
                      error.severity === 'warning' ? 'text-amber-500' :
                      'text-blue-500'
                    }`} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant={
                          error.severity === 'critical' ? 'destructive' :
                          error.severity === 'warning' ? 'warning' : 'info'
                        }>
                          {SEVERITY_CONFIG[error.severity]?.label}
                        </Badge>
                        <span className="text-sm font-semibold">{error.description}</span>
                      </div>

                      {error.location_info && (
                        <p className="text-xs text-muted-foreground mb-2">
                          📍 Trang {String((error.location_info as any).page || '?')}
                          {(error.location_info as any).paragraph ? `, Đoạn ${String((error.location_info as any).paragraph)}` : ''}
                        </p>
                      )}

                      <div className="space-y-1 text-sm mb-3">
                        {error.current_value && (
                          <p><span className="text-destructive">❌ Hiện tại:</span> {error.current_value}</p>
                        )}
                        {error.expected_value && (
                          <p><span className="text-green-600">✅ Yêu cầu:</span> {error.expected_value}</p>
                        )}
                        {error.suggested_fix && (
                          <p className="text-muted-foreground">💡 {error.suggested_fix}</p>
                        )}
                        {error.rag_reference && (
                          <p className="text-xs text-muted-foreground">📖 {error.rag_reference}</p>
                        )}
                        {error.confidence !== null && error.confidence !== undefined && (
                          <p className="text-xs text-muted-foreground">🎯 Độ tin cậy: {(error.confidence * 100).toFixed(0)}%</p>
                        )}
                      </div>

                      {/* Feedback Buttons */}
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-muted-foreground">Phản hồi:</span>
                        <Button
                          variant={feedback === 'correct' ? 'default' : 'ghost'}
                          size="sm"
                          onClick={() => handleFeedback(error.id, true)}
                          className={feedback === 'correct' ? 'bg-green-600 hover:bg-green-700' : ''}
                        >
                          <ThumbsUp className="h-3 w-3 mr-1" /> Đúng
                        </Button>
                        <Button
                          variant={feedback === 'incorrect' ? 'default' : 'ghost'}
                          size="sm"
                          onClick={() => handleFeedback(error.id, false)}
                          className={feedback === 'incorrect' ? 'bg-red-600 hover:bg-red-700' : ''}
                        >
                          <ThumbsDown className="h-3 w-3 mr-1" /> Sai
                        </Button>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })
        )}
      </div>

      {/* Actions */}
      <div className="flex gap-2 justify-center pb-6">
        <Button variant="outline" onClick={() => navigate(`/documents`)}>
          <FileText className="h-4 w-4 mr-1" /> Danh sách văn bản
        </Button>
        <Button variant="outline" onClick={() => checkApi.recheck(id!)}>
          <RotateCcw className="h-4 w-4 mr-1" /> Kiểm tra lại
        </Button>
      </div>
    </div>
  );
}