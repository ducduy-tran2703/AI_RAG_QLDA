export interface DocumentDto {
  id: string;
  original_filename: string;
  display_name: string;
  file_type: 'docx' | 'pdf';
  file_size_bytes: number;
  doc_type?: string;
  tags: string[];
  folder_id?: string;
  created_at: string;
  updated_at: string;
}

export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
  total_pages: number;
}