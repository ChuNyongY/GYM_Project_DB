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
    const token = localStorage.getItem('admin_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
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
  }) => {
    const response = await client.get('/admin/members', { params });
    return response.data;
  },

  // 회원 상세 조회
  getMember: async (memberId: number) => {
    const response = await client.get(`/admin/members/${memberId}`);
    return response.data;
  },

  // 회원 추가
  createMember: async (data: {
    name: string;
    phone_number: string;
    membership_type: string;
    membership_start_date: string;
    membership_end_date: string;
  }) => {
    const response = await client.post('/admin/members', data);
    return response.data;
  },

  // 회원 정보 수정
  updateMember: async (memberId: number, data: {
    name?: string;
    phone_number?: string;
    membership_type?: string;
    membership_start_date?: string;
    membership_end_date?: string;
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
};