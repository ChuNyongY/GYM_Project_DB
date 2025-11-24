import api from './api';

export interface KioskSearchResponse {
  status: string;
  count: number;
  members: Array<{
    member_id: number;
    name: string;
    phone_number: string;
    membership_type?: string;
    membership_end_date?: string;
    is_active: boolean;
  }>;
}

export interface CheckInResponse {
  status: string;
  message: string;
  checkin_id?: number;
  member_name?: string;
  checkin_time?: string;
  membership_end_date?: string;
  member_info?: {
    name?: string;
    membership_end_date?: string;
  };
}

export const kioskService = {
  searchByPhone: async (lastFourDigits: string): Promise<KioskSearchResponse> => {
    const response = await api.post<KioskSearchResponse>('/kiosk/search-by-phone', {
      phone_number: lastFourDigits,
    });
    return response.data;
  },

  checkIn: async (memberId: number): Promise<CheckInResponse> => {
  const response = await api.post<CheckInResponse>(`/kiosk/checkin/${memberId}`);
  return response.data;
},

  checkout: async (memberId: number) => {
  const response = await api.post(`/kiosk/checkout/${memberId}`);
  return response.data;
},
};
