import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 요청 인터셉터: 토큰 자동 추가
client.interceptors.request.use(
  (config) => {
    const token = sessionStorage.getItem('admin_token');
    console.log('🔑 [Interceptor] 토큰:', token ? '있음' : '없음'); // ⭐ 디버깅
    console.log('📡 [Interceptor] 요청 URL:', config.url); // ⭐ 디버깅
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log('✅ [Interceptor] Authorization 헤더 추가'); // ⭐ 디버깅
    } else {
      console.error('❌ [Interceptor] 토큰 없음!'); // ⭐ 디버깅
    }
    return config;
  },
  (error) => {
    console.error('❌ [Interceptor] 요청 에러:', error);
    return Promise.reject(error);
  }
);

// ⭐ 응답 인터셉터 추가 (401 에러 자동 처리)
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      console.error('❌ 401 Unauthorized - 토큰 만료 또는 유효하지 않음');
      sessionStorage.removeItem('admin_token');
      window.location.href = '/admin'; // 로그인 페이지로 리다이렉트
    }
    return Promise.reject(error);
  }
);

export const adminService = {
  // 관리자 로그인
  login: async (password: string) => {
    const response = await axios.post(`${API_BASE_URL}/admin/login`, { password });
    return response.data;
  },

  // 회원 목록 조회
  getMembers: async (params?: {
    page?: number;
    size?: number;
    search?: string;
    status?: string;
    sort_by?: string;
  }) => {
    console.log('📞 [getMembers] 호출, params:', params); // ⭐ 디버깅
    const response = await client.get('/admin/members', { params });
    console.log('✅ [getMembers] 응답 성공'); // ⭐ 디버깅
    return response.data;
  },

  // 회원 상세 조회
  getMember: async (memberId: number) => {
    const response = await client.get(`/admin/members/${memberId}`);
    return response.data;
  },

  // 회원 추가 (백엔드와 구조 일치)
  createMember: async (data: {
    name: string;
    phone_number: string;
    gender: 'M' | 'F'; // 성별 필수
    membership_type: string;
    membership_start_date: string;
    membership_end_date: string;
    locker_type?: string | null;
    locker_start_date?: string | null;
    locker_end_date?: string | null;
    uniform_type?: string | null;
    uniform_start_date?: string | null;
    uniform_end_date?: string | null;
  }) => {
    const response = await client.post('/admin/members', data);
    return response.data;
  },

  // 회원 정보 수정 (백엔드와 구조 일치)
  updateMember: async (memberId: number, data: {
    name?: string;
    phone_number?: string;
    gender?: 'M' | 'F';
    membership_type?: string;
    membership_start_date?: string;
    membership_end_date?: string;
    locker_number?: number | null;
    locker_type?: string | null;
    locker_start_date?: string | null;
    locker_end_date?: string | null;
    uniform_type?: string | null;
    uniform_start_date?: string | null;
    uniform_end_date?: string | null;
  }) => {
    const response = await client.put(`/admin/members/${memberId}`, data);
    return response.data;
  },

  // 회원 삭제
  deleteMember: async (memberId: number) => {
    const response = await client.delete(`/admin/members/${memberId}`);
    return response.data;
  },

  // 출입 기록 조회 ⭐ 새로 추가
  getCheckinHistory: async (memberId: number) => {
    const response = await client.get(`/admin/members/${memberId}/checkins`);
    return response.data;
  },

  // 당일 입장 회원 목록
  getTodayCheckins: async () => {
    const response = await client.get('/admin/today-checkins');
    return response.data;
  },

  // 비밀번호 변경
  changePassword: async (currentPassword: string, newPassword: string) => {
    const response = await client.put('/admin/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
    return response.data;
  },

  // 삭제된 회원 목록 조회
  getDeletedMembers: async (params?: {
    page?: number;
    size?: number;
    search?: string;
  }) => {
    const response = await client.get('/deleted-members', { params });
    return response.data;
  },

  // 회원 복원
  restoreMember: async (memberId: number) => {
    const response = await client.post(`/deleted-members/${memberId}/restore`);
    return response.data;
  },

  // 모든 삭제된 회원 복원
  restoreAll: async () => {
    const response = await client.post('/deleted-members/restore-all');
    return response.data;
  },

  // 회원 영구 삭제
  permanentDeleteMember: async (memberId: number) => {
    const response = await client.delete(`/deleted-members/${memberId}`);
    return response.data;
  },

  // 모든 삭제된 회원 영구 삭제
  permanentDeleteAll: async () => {
    const response = await client.delete('/deleted-members');
    return response.data;
  },
};