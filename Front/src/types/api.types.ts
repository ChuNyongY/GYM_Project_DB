// 백엔드와 일치하도록 gender Enum, locker_type 등 추가, has_uniform 제거
export type Gender = 'M' | 'F'; // 성별 Enum

export interface Member {
  member_id: number; // 회원 고유번호
  member_rank?: number; // (선택) 회원 순번/랭크
  name: string; // 이름
  phone_number: string; // 전화번호
  gender: Gender; // 성별 (Enum)
  membership_type?: string; // 회원권 종류
  membership_start_date?: string; // 회원권 시작일
  membership_end_date?: string; // 회원권 종료일
  locker_number?: number | null; // 락커 번호
  locker_type?: string | null; // 락커 종류
  locker_start_date?: string | null; // 락커 시작일
  locker_end_date?: string | null; // 락커 종료일
  uniform_type?: string | null; // 유니폼 종류
  uniform_start_date?: string | null; // 유니폼 시작일
  uniform_end_date?: string | null; // 유니폼 종료일
  is_active: boolean; // 활성화 여부
  created_at: string; // 생성일
}

// 회원 목록 응답 타입 (Member 구조와 일치)
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

// 키오스크 회원 검색 응답 타입 (Member 구조와 일치)
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