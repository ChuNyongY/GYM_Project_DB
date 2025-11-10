import axios, { AxiosError, AxiosResponse, InternalAxiosRequestConfig } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('admin_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    if (error.code === 'ECONNABORTED') {
      console.error('요청 시간 초과');
      alert('서버 응답 시간이 초과되었습니다. 다시 시도해주세요.');
    } else if (error.response?.status === 401) {
      if (window.location.pathname.includes('admin')) {
        localStorage.removeItem('admin_token');
        window.location.href = '/admin';
      }
    } else if (!error.response) {
      console.error('네트워크 오류');
      alert('서버에 연결할 수 없습니다. 네트워크를 확인해주세요.');
    }
    return Promise.reject(error);
  }
);

export default api;