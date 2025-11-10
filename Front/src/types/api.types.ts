export interface Member {
  member_id: number;
  name: string;
  phone_number: string;
  membership_type?: string;
  membership_start_date?: string;
  membership_end_date?: string;
  is_active: boolean;
  created_at: string;
  locker_number?: number | null;
  has_uniform: boolean;
}

export interface MembersResponse {
  total: number;
  page: number;
  size: number;
  members: Member[];
}

export interface CheckIn {
  checkin_id: number;
  member_id: number;
  member_name?: string;
  checkin_time: string;
  checkout_time?: string | null;
  duration_minutes?: number | null;
}

export interface CheckInsResponse {
  total: number;
  page: number;
  size: number;
  checkins: CheckIn[];
}

export interface LoginResponse {
  status: string;
  token: string;
}

export interface KioskSearchResponse {
  status: string;
  count: number;
  members: Member[];
}

export interface CheckInResponse {
  status: string;
  message: string;
  checkin_id: number;
  member_name: string;
  checkin_time: string;
  membership_end_date?: string;
}