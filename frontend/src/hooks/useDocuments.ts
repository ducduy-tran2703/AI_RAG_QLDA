import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { documentApi } from '@/lib/api';

export function useDocuments(
  page = 1,
  limit = 20,
  folderId?: string | null,
  search?: string,
  fileType?: string,
  sort = 'created_at',
  order = 'desc'
) {
  return useQuery({
    queryKey: ['documents', page, limit, folderId, search, fileType, sort, order],
    queryFn: async () => {
      const params: Record<string, any> = { page, limit, sort, order };
      if (folderId) params.folder_id = folderId;
      if (search) params.search = search;
      if (fileType) params.file_type = fileType;
      const res = await documentApi.list(params);
      return res.data;
    },
  });
}

export function useUploadDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (formData: FormData) => {
      const res = await documentApi.upload(formData.get('file') as File, formData.get('folder_id') as string || undefined);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });
}

export function useUpdateDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: any }) => {
      const res = await documentApi.update(id, data);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });
}

export function useDeleteDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      await documentApi.delete(id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });
}