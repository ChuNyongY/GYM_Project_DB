from datetime import timedelta
from typing import Dict, Optional, Any, List
from fastapi import HTTPException, status, Depends
from jose import JWTError
from ..repositories.admin_repository import AdminRepository
from ..repositories.member_repository import MemberRepository
from ..utils.security import create_access_token, verify_token, oauth2_scheme
from ..config import get_settings

settings = get_settings()


class AdminService:
    def __init__(self, db: Any):
        self.db = db
        self.admin_repo = AdminRepository()
        self.member_repo = MemberRepository()

    # ==================== 인증 관련 ====================
    def verify_admin(self, password: str) -> Dict:
        if not self.admin_repo.verify_password(self.db, password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="비밀번호가 일치하지 않습니다."
            )

        access_token = create_access_token(
            data={"sub": "admin", "role": "admin"},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        return {
            "status": "success",
            "token": access_token,
            "message": "인증 성공"
        }

    def change_password(self, current_password: str, new_password: str) -> Dict:
        admin = self.admin_repo.get_admin(self.db)
        if not admin:
            raise HTTPException(status_code=404, detail="관리자 계정이 존재하지 않습니다.")

        if not self.admin_repo.verify_password(self.db, current_password):
            raise HTTPException(status_code=401, detail="현재 비밀번호가 일치하지 않습니다.")

        self.admin_repo.update_password(self.db, admin.get('id'), new_password)

        return {"status": "success", "message": "비밀번호가 변경되었습니다."}

    async def get_current_admin(self, token: str = Depends(oauth2_scheme)) -> Dict:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증이 필요합니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = verify_token(token)
            if payload.get("sub") != "admin":
                raise credentials_exception
        except JWTError:
            raise credentials_exception

        admin = self.admin_repo.get_admin(self.db)
        if not admin:
            raise credentials_exception

        return {"admin_id": admin.get('id')}

    # ==================== 헬퍼 메서드 ====================
    def _get_available_locker_number(self) -> int:
        sql = """
            SELECT locker_number 
            FROM members 
            WHERE locker_end_date >= CURDATE() 
            AND locker_number IS NOT NULL
        """
        self.db.execute(sql)
        result = self.db.fetchall()
        
        used_lockers = {row['locker_number'] for row in result}
        
        for i in range(1, 101):
            if i not in used_lockers:
                return i
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="남은 락커가 없습니다. (1~100번 모두 사용 중)"
        )

    # ==================== 회원 관리 메서드 ====================

    def get_members(
        self, 
        page: int = 1, 
        size: int = 20, 
        search: Optional[str] = None, 
        status_filter: str = 'all',
        sort_by: Optional[str] = None,
        gender: Optional[str] = None,
        membership_filter: Optional[str] = None,
        locker_filter: bool = False,
        uniform_filter: bool = False,
        checkin_status: Optional[str] = None
    ) -> Dict:
        """회원 목록 조회 (출입기록 복구 완료)"""
        try:
            # 🔍 디버그 로그 추가
            print(f"🔍 [DEBUG] get_members 호출됨 - sort_by: {sort_by}, page: {page}, size: {size}")
            
            offset = (page - 1) * size
            params = []
            
            # ✅ [수정] checkins 테이블을 직접 조회하는 서브쿼리로 변경 (데이터 나옴!)
            sql = """
                SELECT 
                    m.member_id,
                    m.member_rank,
                    m.name,
                    m.gender,
                    m.phone_number,
                    m.membership_type,
                    m.membership_start_date,
                    m.membership_end_date,
                    m.locker_number,
                    m.locker_type,
                    m.locker_start_date,
                    m.locker_end_date,
                    m.uniform_type,
                    m.uniform_start_date,
                    m.uniform_end_date,
                    m.is_active,
                    m.created_at,
                    (SELECT checkin_time FROM checkins WHERE member_id = m.member_id ORDER BY checkin_time DESC LIMIT 1) as last_checkin_time,
                    (SELECT checkout_time FROM checkins WHERE member_id = m.member_id ORDER BY checkin_time DESC LIMIT 1) as last_checkout_time
                FROM members m
                WHERE 1=1
            """
            
            # 1. 검색 조건
            if search:
                sql += " AND (m.name LIKE %s OR m.phone_number LIKE %s)"
                search_param = f"%{search}%"
                params.extend([search_param, search_param])
            
            # 2. 상태 필터
            if status_filter == 'active':
                sql += " AND m.is_active = TRUE AND (m.membership_end_date IS NULL OR m.membership_end_date >= CURDATE())"
            elif status_filter == 'inactive':
                 sql += " AND (m.is_active = FALSE OR m.membership_end_date < CURDATE())"
            elif status_filter == 'expiring_soon':
                sql += """ AND m.is_active = TRUE AND (
                    m.membership_end_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 7 DAY)
                )"""

            # 3. 성별 필터
            if gender:
                sql += " AND m.gender = %s"
                params.append(gender)
            
            # 4. 라커룸 필터
            if locker_filter:
                sql += " AND m.locker_type IS NOT NULL"
            
            # 5. 회원복 필터
            if uniform_filter:
                sql += " AND m.uniform_type IS NOT NULL"
            
            # 6. 활성/비활성 필터
            if checkin_status == "active":
                sql += " AND (SELECT checkin_time FROM checkins WHERE member_id = m.member_id AND checkout_time IS NULL ORDER BY checkin_time DESC LIMIT 1) IS NOT NULL"
            elif checkin_status == "inactive":
                sql += " AND (SELECT checkout_time FROM checkins WHERE member_id = m.member_id ORDER BY checkin_time DESC LIMIT 1) IS NOT NULL"
            
            # 7. PT권 / 회원권 필터
            if membership_filter == "pt":
                sql += " AND m.membership_type LIKE 'PT%%'"
            elif membership_filter == "membership":
                sql += " AND m.membership_type NOT LIKE 'PT%%' AND m.membership_type IS NOT NULL"

            # 8. 정렬 로직
            order_clause = "m.created_at DESC" # 기본값
            
            if sort_by == 'recent_checkin':
                order_clause = "last_checkin_time DESC" # 서브쿼리 별칭 사용
            elif sort_by == 'name':
                order_clause = "m.name ASC"
            elif sort_by == 'end_date':
                order_clause = "m.membership_end_date ASC"
            elif sort_by == 'member_rank_desc':
                order_clause = "m.member_id DESC"  # member_id 내림차순
            elif sort_by == 'member_rank_asc':
                order_clause = "m.member_id ASC"   # member_id 오름차순
            elif sort_by == 'membership_type_asc':
                order_clause = """CASE 
                    WHEN m.membership_type = 'PT(1개월)' THEN 1
                    WHEN m.membership_type = 'PT(3개월)' THEN 2
                    WHEN m.membership_type = 'PT(6개월)' THEN 3
                    WHEN m.membership_type = 'PT(1년)' THEN 4
                    WHEN m.membership_type = '1개월' THEN 5
                    WHEN m.membership_type = '3개월' THEN 6
                    WHEN m.membership_type = '6개월' THEN 7
                    WHEN m.membership_type = '1년' THEN 8
                    ELSE 9 
                END ASC"""
            elif sort_by == 'locker_type_asc':
                order_clause = """CASE 
                    WHEN m.locker_type LIKE '1개월%%' THEN 1
                    WHEN m.locker_type LIKE '3개월%%' THEN 2
                    WHEN m.locker_type LIKE '6개월%%' THEN 3
                    WHEN m.locker_type LIKE '12개월%%' OR m.locker_type LIKE '1년%%' THEN 4
                    ELSE 5 
                END ASC"""
            elif sort_by == 'uniform_type_asc':
                order_clause = """CASE 
                    WHEN m.uniform_type LIKE '1개월%%' THEN 1
                    WHEN m.uniform_type LIKE '3개월%%' THEN 2
                    WHEN m.uniform_type LIKE '6개월%%' THEN 3
                    WHEN m.uniform_type LIKE '12개월%%' OR m.uniform_type LIKE '1년%%' THEN 4
                    ELSE 5 
                END ASC"""
            
            # 🔍 디버그 로그 추가
            print(f"🔍 [DEBUG] sort_by: '{sort_by}', order_clause: '{order_clause}'")
            
            sql += f" ORDER BY {order_clause}"
            sql += " LIMIT %s OFFSET %s"
            params.extend([size, offset])
            
            self.db.execute(sql, tuple(params))
            members = self.db.fetchall()
            
            # 5. 전체 개수 조회
            count_sql = "SELECT COUNT(*) as count FROM members m WHERE 1=1"
            count_params = []
            
            if search:
                count_sql += " AND (m.name LIKE %s OR m.phone_number LIKE %s)"
                count_params.extend([search_param, search_param])
            if status_filter == 'active':
                count_sql += " AND m.is_active = TRUE AND (m.membership_end_date IS NULL OR m.membership_end_date >= CURDATE())"
            if status_filter == 'inactive':
                 count_sql += " AND (m.is_active = FALSE OR m.membership_end_date < CURDATE())"
            if status_filter == 'expiring_soon':
                count_sql += " AND m.is_active = TRUE AND (m.membership_end_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 7 DAY))"
            if gender:
                count_sql += " AND m.gender = %s"
                count_params.append(gender)
            if locker_filter:
                count_sql += " AND m.locker_type IS NOT NULL"
            if uniform_filter:
                count_sql += " AND m.uniform_type IS NOT NULL"
            if checkin_status == "active":
                count_sql += " AND (SELECT checkin_time FROM checkins WHERE member_id = m.member_id AND checkout_time IS NULL ORDER BY checkin_time DESC LIMIT 1) IS NOT NULL"
            elif checkin_status == "inactive":
                count_sql += " AND (SELECT checkout_time FROM checkins WHERE member_id = m.member_id ORDER BY checkin_time DESC LIMIT 1) IS NOT NULL"
            
            self.db.execute(count_sql, tuple(count_params))
            result = self.db.fetchone()
            total = result['count'] if result else 0
            
            # 6. 데이터 포맷팅
            formatted_members = []
            for i, m in enumerate(members):
                # 프론트엔드 id 매핑
                m['id'] = m['member_id']

                # 회원번호 자동 계산 (DB값이 없으면)
                if m['member_rank'] is None:
                    m['member_rank'] = (page - 1) * size + (i + 1)

                # 별칭을 원래 키 이름으로 변경
                checkin = m.pop('last_checkin_time', None)
                checkout = m.pop('last_checkout_time', None)
                
                if checkin:
                    m['checkin_time'] = checkin.strftime('%Y-%m-%d %H:%M')
                else:
                    m['checkin_time'] = None
                    
                if checkout:
                    m['checkout_time'] = checkout.strftime('%Y-%m-%d %H:%M')
                else:
                    m['checkout_time'] = None
                
                # date 객체 변환
                for date_field in ['membership_start_date', 'membership_end_date', 'locker_start_date', 'locker_end_date', 'uniform_start_date', 'uniform_end_date']:
                    if m.get(date_field):
                        m[date_field] = str(m[date_field])
                        
                formatted_members.append(m)

            return {
                "members": formatted_members,
                "total": total,
                "page": page,
                "size": size
            }
            
        except Exception as e:
            import traceback
            print(f"❌ Error in get_members: {str(e)}")
            print(f"❌ Traceback: {traceback.format_exc()}")
            print(f"❌ SQL: {sql if 'sql' in locals() else 'SQL not generated'}")
            print(f"❌ Params: {params if 'params' in locals() else 'No params'}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"회원 목록 조회 실패: {str(e)}"
            )

    def create_member(self, **kwargs) -> Dict:
        phone_number = kwargs.get('phone_number')
        existing = self.member_repo.get_member_by_phone(self.db, phone_number)
        if existing:
            raise HTTPException(status_code=400, detail="이미 등록된 전화번호입니다.")

        if kwargs.get('locker_type') and not kwargs.get('locker_number'):
            kwargs['locker_number'] = self._get_available_locker_number()

        try:
            keys = kwargs.keys()
            columns = ', '.join(keys)
            placeholders = ', '.join(['%s'] * len(keys))
            sql = f"INSERT INTO members ({columns}, is_active, created_at) VALUES ({placeholders}, TRUE, NOW())"
            
            self.db.execute(sql, tuple(kwargs.values()))
            self.db.connection.commit()
            
            member_id = self.db.lastrowid
            return {
                "status": "success",
                "message": "회원이 추가되었습니다.",
                "member": self.member_repo.get_member_by_id(self.db, member_id)
            }
        except Exception as e:
            self.db.connection.rollback()
            raise HTTPException(status_code=500, detail=f"회원 추가 실패: {str(e)}")

    def get_member(self, member_id: int) -> Dict:
        member = self.member_repo.get_member_by_id(self.db, member_id)
        if not member:
            raise HTTPException(status_code=404, detail="회원을 찾을 수 없습니다.")
        return member

    def update_member(self, member_id: int, **kwargs) -> Dict:
        member = self.member_repo.get_member_by_id(self.db, member_id)
        if not member:
            raise HTTPException(status_code=404, detail="회원을 찾을 수 없습니다.")

        phone_number = kwargs.get('phone_number')
        if phone_number and phone_number != member.get('phone_number'):
            existing = self.member_repo.get_member_by_phone(self.db, phone_number)
            if existing and existing.get('member_id') != member_id:
                raise HTTPException(status_code=400, detail="이미 사용 중인 전화번호입니다.")

        update_fields = []
        values = []
        
        for key, value in kwargs.items():
            update_fields.append(f"{key} = %s")
            values.append(value)

        if not update_fields:
            return {"status": "success", "message": "변경사항 없음", "member": member}

        try:
            sql = f"UPDATE members SET {', '.join(update_fields)} WHERE member_id = %s"
            values.append(member_id)
            self.db.execute(sql, tuple(values))
            self.db.connection.commit()
            
            return {
                "status": "success", 
                "message": "수정 완료", 
                "member": self.member_repo.get_member_by_id(self.db, member_id)
            }
        except Exception as e:
            self.db.connection.rollback()
            raise HTTPException(status_code=500, detail=f"수정 실패: {str(e)}")

    def delete_member(self, member_id: int) -> Dict:
        try:
            self.db.execute("DELETE FROM checkins WHERE member_id = %s", (member_id,))
            sql = "DELETE FROM members WHERE member_id = %s"
            self.db.execute(sql, (member_id,))
            self.db.connection.commit()
            return {"status": "success", "message": "삭제 완료", "member_id": member_id}
        except Exception as e:
            self.db.connection.rollback()
            raise HTTPException(status_code=500, detail=f"삭제 실패: {str(e)}")

    def get_today_checkins(self) -> List[Dict]:
        try:
            sql = """
                SELECT 
                    c.id as checkin_id,
                    c.member_id,
                    c.checkin_time,
                    c.checkout_time,
                    m.name,
                    m.phone_number,
                    m.gender,
                    m.membership_type
                FROM checkins c
                JOIN members m ON c.member_id = m.member_id
                WHERE DATE(c.checkin_time) = CURDATE()
                ORDER BY c.checkin_time DESC
            """
            self.db.execute(sql)
            result = self.db.fetchall()
            
            formatted_result = []
            for row in result:
                formatted_result.append({
                    'checkin_id': row['checkin_id'],
                    'member_id': row['member_id'],
                    'name': row['name'],
                    'phone_number': row['phone_number'],
                    'gender': row['gender'],
                    'membership_type': row['membership_type'],
                    'checkin_time_formatted': row['checkin_time'].strftime('%H:%M') if row['checkin_time'] else None,
                    'checkout_time_formatted': row['checkout_time'].strftime('%H:%M') if row['checkout_time'] else '입장 중'
                })
                
            return formatted_result
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"당일 입장 조회 실패: {str(e)}")