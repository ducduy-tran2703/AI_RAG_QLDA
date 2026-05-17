import { useState, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { useUploadDocument } from '../../hooks/useDocuments';
import { useCheckProgress } from '../../hooks/useWebSocket';

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [checkId, setCheckId] = useState<string | null>(null);
  const [progress, setProgress] = useState({ stage: '', percent: 0 });
  const [complete, setComplete] = useState(false);
  const [resultId, setResultId] = useState<string | null>(null);

  const navigate = useNavigate();
  const uploadMutation = useUploadDocument();

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) setFile(acceptedFiles[0]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    maxFiles: 1,
  });

  // Nhận progress từ WebSocket
  useCheckProgress(
    checkId,
    (data) => setProgress({ stage: data.stage, percent: data.percent }),
    (data) => {
      setComplete(true);
      setResultId(data.result_id);  // Lưu result_id từ sự kiện complete
      setProgress({ stage: 'done', percent: 100 });
    }
  );

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await uploadMutation.mutateAsync(formData);
      setCheckId(res.check_id);
    } catch (err) {
      alert('Upload thất bại');
      setUploading(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto">
      <h2 className="text-2xl font-bold mb-4">Upload văn bản mới</h2>

      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer ${
          isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
        }`}
      >
        <input {...getInputProps()} />
        {file ? (
          <p className="text-green-600">{file.name} ({(file.size / 1024).toFixed(1)} KB)</p>
        ) : (
          <p className="text-gray-500">Kéo thả file .docx hoặc .pdf vào đây, hoặc nhấn để chọn</p>
        )}
      </div>

      {checkId && (
        <div className="mt-4">
          <div className="bg-gray-200 rounded-full h-4">
            <div
              className="bg-blue-600 h-4 rounded-full transition-all"
              style={{ width: `${progress.percent}%` }}
            />
          </div>
          <p className="text-sm mt-1">
            {progress.stage === 'done' ? 'Hoàn tất!' : `Đang xử lý: ${progress.stage}`}
          </p>
        </div>
      )}

      <div className="mt-4 flex gap-2">
        <button
          onClick={handleUpload}
          disabled={!file || uploading}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {uploading && !checkId ? 'Đang upload...' : 'Upload & Kiểm tra'}
        </button>
        <button
          onClick={() => navigate('/documents')}
          className="bg-gray-300 px-4 py-2 rounded hover:bg-gray-400"
        >
          Hủy
        </button>
      </div>

      {complete && resultId && (
        <div className="mt-4">
          <Link
            to={`/checks/${resultId}`}
            className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 inline-block"
          >
            Xem kết quả chi tiết
          </Link>
        </div>
      )}
    </div>
  );
}