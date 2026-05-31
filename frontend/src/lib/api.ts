import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor: gắn token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Interceptor: auto refresh token khi 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const res = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          const newToken = res.data.access_token;
          localStorage.setItem('access_token', newToken);
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          return api(originalRequest);
        } catch {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      } else {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// ===================== AUTH API =====================
export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  register: (data: { email: string; full_name: string; password: string; department_code?: string }) =>
    api.post('/auth/register', data),
  refresh: (refresh_token: string) =>
    api.post('/auth/refresh', { refresh_token }),
  logout: (logout_all = false) =>
    api.post('/auth/logout', { logout_all }),
  getProfile: () => api.get('/auth/me'),
  updateProfile: (data: any) => api.put('/auth/me', data),
  changePassword: (current_password: string, new_password: string) =>
    api.put('/auth/me/password', { current_password, new_password }),
  forgotPassword: (email: string) =>
    api.post('/auth/forgot-password', { email }),
  resetPassword: (token: string, new_password: string) =>
    api.post('/auth/reset-password', { token, new_password }),
};

// ===================== DOCUMENT API =====================
export const documentApi = {
  upload: (file: File, folder_id?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    if (folder_id) formData.append('folder_id', folder_id);
    return api.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  list: (params?: {
    page?: number; limit?: number; folder_id?: string;
    search?: string; file_type?: string; sort?: string; order?: string;
  }) => api.get('/documents/', { params }),
  get: (id: string) => api.get(`/documents/${id}`),
  update: (id: string, data: any) => api.put(`/documents/${id}`, data),
  delete: (id: string) => api.delete(`/documents/${id}`),
  download: (id: string) => api.get(`/documents/${id}/download`, { responseType: 'blob' }),
  preview: (id: string) => api.get(`/documents/${id}/preview`),
  listVersions: (id: string) => api.get(`/documents/${id}/versions`),
  createVersion: (id: string, file: File, change_notes?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    if (change_notes) formData.append('change_notes', change_notes);
    return api.post(`/documents/${id}/versions`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  getFolders: () => api.get('/documents/folders'),
  createFolder: (data: { name: string; parent_id?: string; color?: string; icon?: string }) =>
    api.post('/documents/folders', data),
  updateFolder: (id: string, data: any) => api.put(`/documents/folders/${id}`, data),
  deleteFolder: (id: string) => api.delete(`/documents/folders/${id}`),
};

// ===================== CHECK API =====================
export const checkApi = {
  create: (document_id: string, rule_set_id?: number) =>
    api.post('/checks', { document_id, rule_set_id }),
  get: (id: string) => api.get(`/checks/${id}`),
  listByDocument: (document_id: string) => api.get(`/checks/document/${document_id}`),
  recheck: (id: string) => api.post(`/checks/${id}/recheck`),
  sendFeedback: (check_id: string, error_id: string, is_correct: boolean, user_note?: string) =>
    api.post(`/checks/${check_id}/errors/${error_id}/feedback`, { is_correct, user_note }),
  exportJson: (id: string) => api.get(`/checks/${id}/export/json`),
  previewNormalize: (id: string) => api.get(`/checks/${id}/normalize/preview`),
  applyNormalize: (id: string, change_ids: string[]) =>
    api.post(`/checks/${id}/normalize/apply`, change_ids),
};

// ===================== RULES API =====================
export const rulesApi = {
  getSets: (params?: { page?: number; limit?: number; search?: string }) =>
    api.get('/rules/sets', { params }),
  updateSet: (id: string, data: { name: string }) =>
    api.put(`/rules/sets/${id}`, data),
  deleteSet: (id: string) =>
    api.delete(`/rules/sets/${id}`),

  listRules: (setId: string, params?: { page?: number; limit?: number; keywords?: string }) =>
    api.get(`/rules/sets/${setId}/rules`, { params }),
  getRule: (setId: string, ruleId: string) =>
    api.get(`/rules/sets/${setId}/rules/${ruleId}`),
  createRule: (setId: string, data: any) =>
    api.post(`/rules/sets/${setId}/rules`, data),
  updateRule: (setId: string, ruleId: string, data: any) =>
    api.patch(`/rules/sets/${setId}/rules/${ruleId}`, data),
  deleteRules: (setId: string, ruleIds: string[]) =>
    api.delete(`/rules/sets/${setId}/rules`, { data: ruleIds }),
};

// ===================== KNOWLEDGE API =====================
export const knowledgeApi = {
  listDocuments: (params?: {
    page?: number; limit?: number; search?: string;
  }) => api.get('/knowledge/documents', { params }),
  uploadDocument: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/knowledge/documents', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  updateDocument: (id: string, data: any) => api.put(`/knowledge/documents/${id}`, data),
  deleteDocument: (id: string) => api.delete(`/knowledge/documents/${id}`),
  reindexDocument: (id: string) => api.post(`/knowledge/documents/${id}/reindex`),
  getStats: () => api.get('/knowledge/stats'),
};

// ===================== TEMPLATE API =====================
export const templateApi = {
  list: (params?: { page?: number; limit?: number; doc_type?: string; is_active?: boolean }) =>
    api.get('/templates', { params }),
  get: (id: number) => api.get(`/templates/${id}`),
  download: (id: number) => api.get(`/templates/${id}/download`),
  create: (data: FormData) => api.post('/templates', data, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  update: (id: number, data: any) => api.put(`/templates/${id}`, data),
  compare: (check_result_id: string, template_id: number) =>
    api.post(`/templates/${check_result_id}/compare/${template_id}`),
};

// ===================== APPROVAL API =====================
export const approvalApi = {
  submit: (data: { document_id: string; approver_id: string; check_result_id?: string; note?: string }) =>
    api.post('/approval/requests', data),
  listPending: () => api.get('/approval/requests/pending'),
  process: (id: string, action: 'approve' | 'reject', note?: string) =>
    api.put(`/approval/requests/${id}`, { action, note }),
};

// ===================== NOTIFICATION API =====================
export const notificationApi = {
  list: (limit?: number) => api.get('/notifications/', { params: { limit } }),
  markRead: (notification_ids: string[]) =>
    api.post('/notifications/mark-read', { notification_ids }),
};

// ===================== ADMIN API =====================
export const adminApi = {
  listUsers: (params?: { page?: number; limit?: number; role?: string; department_id?: string; is_active?: boolean; search?: string }) =>
    api.get('/admin/users', { params }),
  createUser: (data: any) => api.post('/admin/users', data),
  updateUser: (id: string, data: any) => api.put(`/admin/users/${id}`, data),
  lockUser: (id: string) => api.post(`/admin/users/${id}/lock`),
  unlockUser: (id: string) => api.post(`/admin/users/${id}/unlock`),
  resetPassword: (id: string) => api.post(`/admin/users/${id}/reset-password`),
  getSettings: () => api.get('/admin/settings'),
  updateSetting: (key: string, value: string) => api.put(`/admin/settings/${key}`, { value }),
  getAuditLogs: (params?: { page?: number; limit?: number; action?: string }) =>
    api.get('/admin/audit-logs', { params }),
  getApiKeys: () => api.get('/admin/api-keys'),
  createApiKey: (name: string) => api.post('/admin/api-keys', { name }),
  revokeApiKey: (id: string) => api.delete(`/admin/api-keys/${id}`),
};

// ===================== ANALYTICS API =====================
export const analyticsApi = {
  getDashboard: () => api.get('/analytics/dashboard'),
};

export default api;