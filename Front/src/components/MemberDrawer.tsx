import { useState, useEffect } from "react";
import { adminService } from "../services/adminService";

interface MemberDrawerProps {
  member: any | null;
  onClose: () => void;
  onSave: () => void;
  isNewMember?: boolean;
}

export default function MemberDrawer({ 
  member, 
  onClose, 
  onSave,
  isNewMember = false
}: MemberDrawerProps) {
  const [isEditMode, setIsEditMode] = useState(isNewMember);
  
  // ✅ [수정 1] locker_period -> locker_type으로 변경하여 초기화
  const [editForm, setEditForm] = useState({
    name: member?.name || '',
    phone_number: member?.phone_number || '',
    gender: member?.gender || '',
    membership_type: member?.membership_type || '',
    membership_start_date: member?.membership_start_date || new Date().toISOString().split('T')[0],
    membership_end_date: member?.membership_end_date || '',
    locker_number: member?.locker_number || null,
    locker_type: member?.locker_type || '', // period 대신 type 사용
    locker_start_date: member?.locker_start_date || '',
    locker_end_date: member?.locker_end_date || '',
    uniform_type: member?.uniform_type || '',
    uniform_start_date: member?.uniform_start_date || '',
    uniform_end_date: member?.uniform_end_date || '',
  });

  const [checkinHistory, setCheckinHistory] = useState<any[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(!isNewMember);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);

  // 디버깅: member 객체 확인
  useEffect(() => {
    if (member) {
      console.log('🔍 [MemberDrawer] member 객체:', member);
      console.log('🔍 [MemberDrawer] member.member_rank:', member.member_rank);
      console.log('🔍 [MemberDrawer] member.member_id:', member.member_id);
    }
  }, [member]);

  // 전화번호 자동 포맷팅
  const formatPhoneNumber = (value: string) => {
    const numbers = value.replace(/[^\d]/g, '');
    
    if (numbers.length <= 3) {
      return numbers;
    } else if (numbers.length <= 7) {
      return `${numbers.slice(0, 3)}-${numbers.slice(3)}`;
    } else if (numbers.length <= 11) {
      return `${numbers.slice(0, 3)}-${numbers.slice(3, 7)}-${numbers.slice(7)}`;
    } else {
      return `${numbers.slice(0, 3)}-${numbers.slice(3, 7)}-${numbers.slice(7, 11)}`;
    }
  };

  const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const formatted = formatPhoneNumber(e.target.value);
    setEditForm({...editForm, phone_number: formatted});
  };

  // 출입 기록 로드
  useEffect(() => {
    if (isNewMember || !member) {
      setLoadingHistory(false);
      return;
    }

    const fetchHistory = async () => {
      try {
        setLoadingHistory(true);
        const response = await adminService.getCheckinHistory(member.member_id);
        setCheckinHistory(response.checkins || []);
      } catch (error) {
        console.error('출입 기록 조회 실패:', error);
        setCheckinHistory([]);
      } finally {
        setLoadingHistory(false);
      }
    };

    fetchHistory();
  }, [member?.member_id, isNewMember, member]);

  // 기간 계산 함수
  const calculateEndDate = (startDate: string, type: string) => {
    const start = new Date(startDate);
    let endDate = new Date(start);

    // PT권 처리
    if (type.startsWith('PT(')) {
      const innerType = type.slice(3, -1); // 'PT(1개월)' -> '1개월'
      switch(innerType) {
        case '1개월':
          endDate.setMonth(endDate.getMonth() + 1);
          break;
        case '3개월':
          endDate.setMonth(endDate.getMonth() + 3);
          break;
        case '6개월':
          endDate.setMonth(endDate.getMonth() + 6);
          break;
        case '1년':
          endDate.setFullYear(endDate.getFullYear() + 1);
          break;
      }
    } else {
      // 일반 회원권 처리
      switch(type) {
        case '1개월':
          endDate.setMonth(endDate.getMonth() + 1);
          break;
        case '3개월':
          endDate.setMonth(endDate.getMonth() + 3);
          break;
        case '6개월':
          endDate.setMonth(endDate.getMonth() + 6);
          break;
        case '1년':
          endDate.setFullYear(endDate.getFullYear() + 1);
          break;
      }
    }

    return endDate.toISOString().split('T')[0];
  };

  // 회원권 선택
  const handleMembershipChange = (type: string) => {
    if (editForm.membership_type === type) {
      setEditForm({
        ...editForm,
        membership_type: '',
        membership_start_date: new Date().toISOString().split('T')[0],
        membership_end_date: '',
      });
      return;
    }

    const startDate = editForm.membership_start_date || new Date().toISOString().split('T')[0];
    const endDate = calculateEndDate(startDate, type);

    setEditForm({
      ...editForm,
      membership_type: type,
      membership_start_date: startDate,
      membership_end_date: endDate,
    });
  };

  // ✅ [수정 2] 락커 선택 (locker_type 사용)
  const handleLockerChange = async (type: string) => {
    if (editForm.locker_type === type) {
      setEditForm({
        ...editForm,
        locker_type: '', // 초기화
        locker_number: null,
        locker_start_date: '',
        locker_end_date: '',
      });
      return;
    }

    const startDate = new Date().toISOString().split('T')[0];
    const endDate = calculateEndDate(startDate, type);

    setEditForm({
      ...editForm,
      locker_number: null,  // 서버에서 자동 부여
      locker_type: type,    // ✅ locker_type에 값 저장
      locker_start_date: startDate,
      locker_end_date: endDate,
    });
  };

  // 회원복 선택
  const handleUniformChange = (type: string) => {
    if (editForm.uniform_type === type) {
      setEditForm({
        ...editForm,
        uniform_type: '',
        uniform_start_date: '',
        uniform_end_date: '',
      });
      return;
    }

    const startDate = new Date().toISOString().split('T')[0];
    const endDate = calculateEndDate(startDate, type);

    setEditForm({
      ...editForm,
      uniform_type: type,
      uniform_start_date: startDate,
      uniform_end_date: endDate,
    });
  };

  // 시작일 변경 핸들러들
  const handleStartDateChange = (newStartDate: string) => {
    if (!newStartDate) return;
    const endDate = calculateEndDate(newStartDate, editForm.membership_type);
    setEditForm({ ...editForm, membership_start_date: newStartDate, membership_end_date: endDate });
  };

  const handleLockerStartDateChange = (newStartDate: string) => {
    if (!newStartDate) return;
    // ✅ locker_period 대신 locker_type 사용
    const endDate = calculateEndDate(newStartDate, editForm.locker_type); 
    setEditForm({ ...editForm, locker_start_date: newStartDate, locker_end_date: endDate });
  };

  const handleUniformStartDateChange = (newStartDate: string) => {
    if (!newStartDate) return;
    const endDate = calculateEndDate(newStartDate, editForm.uniform_type);
    setEditForm({ ...editForm, uniform_start_date: newStartDate, uniform_end_date: endDate });
  };

  // 저장
  const handleSave = async () => {
    // 유효성 검사
    if (!editForm.name.trim()) { alert('이름을 입력해주세요.'); return; }
    
    const nameRegex = /^[가-힣]{2,10}$|^[a-zA-Z\s]{2,20}$/;
    if (!nameRegex.test(editForm.name.trim())) { alert('올바른 이름 형식이 아닙니다.'); return; }

    if (!editForm.phone_number.trim()) { alert('전화번호를 입력해주세요.'); return; }
    
    const phoneRegex = /^010-\d{4}-\d{4}$|^010\d{8}$/;
    if (!phoneRegex.test(editForm.phone_number.replace(/\s/g, ''))) { alert('올바른 번호가 아닙니다.'); return; }

    if (!editForm.gender) { alert('성별을 선택해주세요.'); return; }
    if (!editForm.membership_type) { alert('회원권 종류를 선택해주세요.'); return; }
    if (!editForm.membership_start_date) { alert('시작일을 선택해주세요.'); return; }

    try {
      setSaving(true);
      
      // 백엔드와 일치하는 회원 데이터 구조 생성
      const memberData: any = {
        name: editForm.name.trim(),
        phone_number: editForm.phone_number,
        gender: editForm.gender ? (editForm.gender as 'M' | 'F') : undefined,
        membership_type: editForm.membership_type || undefined,
        membership_start_date: editForm.membership_start_date || undefined,
        membership_end_date: editForm.membership_end_date || undefined,
        locker_type: editForm.locker_type || undefined,
        locker_start_date: editForm.locker_start_date || undefined,
        locker_end_date: editForm.locker_end_date || undefined,
        uniform_type: editForm.uniform_type || undefined,
        uniform_start_date: editForm.uniform_start_date || undefined,
        uniform_end_date: editForm.uniform_end_date || undefined,
      };

      // 기존 회원 수정 시 locker_number도 포함
      if (!isNewMember) {
        memberData.locker_number = editForm.locker_number ?? undefined;
      }

      // 전송 데이터 콘솔 출력
      console.log('💾 전송할 데이터:', memberData);

      if (isNewMember) {
        await adminService.createMember(memberData);
        alert('회원이 추가되었습니다.');
      } else {
        await adminService.updateMember(member.member_id, memberData);
        alert('회원 정보가 수정되었습니다.');
      }

      onSave();
      
    } catch (error: any) {
      console.error('저장 실패:', error);
      alert('저장에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  };

  // 수정 취소
  const handleCancel = () => {
    if (isNewMember) {
      onClose();
    } else {
      setEditForm({
        name: member.name,
        phone_number: member.phone_number,
        gender: member.gender || '',
        membership_type: member.membership_type || '',
        membership_start_date: member.membership_start_date || '',
        membership_end_date: member.membership_end_date || '',
        locker_number: member.locker_number || null,
        locker_type: member.locker_type || '', // period -> type
        locker_start_date: member.locker_start_date || '',
        locker_end_date: member.locker_end_date || '',
        uniform_type: member.uniform_type || '',
        uniform_start_date: member.uniform_start_date || '',
        uniform_end_date: member.uniform_end_date || '',
      });
      setIsEditMode(false);
    }
  };

  const handleDelete = async () => {
    if (!member) return;
    if (!window.confirm(`정말로 "${member.name}" 회원을 삭제하시겠습니까?`)) return;

    try {
      setDeleting(true);
      await adminService.deleteMember(member.member_id);
      alert('회원이 삭제되었습니다.');
      onSave();
    } catch (error: any) {
      console.error('삭제 실패:', error);
      alert('회원 삭제에 실패했습니다.');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="h-full flex flex-col bg-white">
      {/* 헤더 */}
      <div className="sticky top-0 bg-gradient-to-r from-blue-600 to-blue-700 text-white px-6 py-5 z-20 shadow-lg">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold flex items-center gap-2">
              {isNewMember ? (
                <> <span className="text-3xl">✨</span> 새 회원 추가 </>
              ) : isEditMode ? (
                <> <span className="text-3xl">📝</span> 회원 정보 수정 </>
              ) : (
                <> <span className="text-3xl">👤</span> {member?.name}님 </>
              )}
            </h2>
            {!isNewMember && member && (
              <p className="text-blue-100 text-sm mt-1">회원번호: {member.displayRank || member.member_rank}번</p>
            )}
          </div>
          <div className="flex gap-2">
            {isEditMode || isNewMember ? (
              <>
                <button onClick={handleCancel} disabled={saving} className="px-5 py-2 bg-white/20 hover:bg-white/30 rounded-lg transition-colors disabled:opacity-50">취소</button>
                <button onClick={handleSave} disabled={saving} className="px-5 py-2 bg-white text-blue-600 rounded-lg hover:bg-blue-50 transition-colors font-semibold disabled:opacity-50 flex items-center gap-2">
                  {saving ? '저장 중...' : (isNewMember ? '추가' : '저장')}
                </button>
              </>
            ) : (
              <>
                <button onClick={() => setIsEditMode(true)} className="px-5 py-2 bg-white text-blue-600 rounded-lg hover:bg-blue-50 transition-colors font-semibold">수정</button>
                <button onClick={onClose} className="px-5 py-2 bg-white/20 hover:bg-white/30 rounded-lg transition-colors">닫기</button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* 내용 */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6 pb-24">
        {/* 기본 정보 */}
        <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-6 border-2 border-blue-100">
          <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
            <span className="text-2xl">📋</span> 기본 정보
          </h3>
          
          {isEditMode || isNewMember ? (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">이름 <span className="text-red-500">*</span></label>
                <input type="text" value={editForm.name} onChange={(e) => setEditForm({...editForm, name: e.target.value})} placeholder="회원 이름" className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" required />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">성별 <span className="text-red-500">*</span></label>
                <div className="flex gap-2">
                  <button type="button" onClick={() => setEditForm({...editForm, gender: 'M'})} className={`flex-1 px-4 py-2 rounded-lg font-semibold transition-all ${editForm.gender === 'M' ? 'bg-blue-600 text-white shadow-lg' : 'bg-gray-100 text-gray-700 border-2 border-gray-300'}`}>남자</button>
                  <button type="button" onClick={() => setEditForm({...editForm, gender: 'F'})} className={`flex-1 px-4 py-2 rounded-lg font-semibold transition-all ${editForm.gender === 'F' ? 'bg-pink-600 text-white shadow-lg' : 'bg-gray-100 text-gray-700 border-2 border-gray-300'}`}>여자</button>
                </div>
              </div>
              <div className="col-span-2">
                <label className="block text-sm font-semibold text-gray-700 mb-2">전화번호 <span className="text-red-500">*</span></label>
                <input type="tel" value={editForm.phone_number} onChange={handlePhoneChange} placeholder="01012345678" maxLength={13} className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" required />
              </div>
            </div>
          ) : (
            <dl className="grid grid-cols-2 gap-4">
              <div><dt className="text-sm text-gray-600 mb-1">이름</dt><dd className="text-xl font-bold text-gray-900">{member?.name}</dd></div>
              <div><dt className="text-sm text-gray-600 mb-1">성별</dt><dd className="text-xl font-bold text-gray-900">{member?.gender === 'M' ? '남자' : member?.gender === 'F' ? '여자' : '-'}</dd></div>
              <div className="col-span-2"><dt className="text-sm text-gray-600 mb-1">전화번호</dt><dd className="text-xl font-bold text-gray-900">{member?.phone_number}</dd></div>
            </dl>
          )}
        </div>

        {/* 회원권 정보 */}
        <div className="bg-white rounded-xl border-2 border-gray-200 p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2"><span className="text-2xl">🎫</span> 회원권 정보</h3>
          {isEditMode || isNewMember ? (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-3">회원권 종류 <span className="text-red-500">*</span></label>
                <div className="grid grid-cols-4 gap-3 mb-3">
                  {['1개월', '3개월', '6개월', '1년'].map((type) => (
                    <button key={type} type="button" onClick={() => handleMembershipChange(type)} className={`px-6 py-3 rounded-lg font-semibold transition-all ${editForm.membership_type === type ? 'bg-blue-600 text-white shadow-lg scale-105' : 'bg-gray-100 text-gray-700 border-2 border-gray-300 hover:bg-gray-50'}`}>{type}</button>
                  ))}
                </div>
                <div className="border-t-2 border-gray-200 pt-3 mt-3">
                  <label className="block text-sm font-semibold text-green-700 mb-3">🏋️ PT권</label>
                  <div className="grid grid-cols-4 gap-3">
                    {['PT(1개월)', 'PT(3개월)', 'PT(6개월)', 'PT(1년)'].map((type) => (
                      <button key={type} type="button" onClick={() => handleMembershipChange(type)} className={`px-6 py-3 rounded-lg font-semibold transition-all ${editForm.membership_type === type ? 'bg-green-600 text-white shadow-lg scale-105' : 'bg-green-50 text-green-700 border-2 border-green-300 hover:bg-green-100'}`}>{type}</button>
                    ))}
                  </div>
                </div>
              </div>
              {editForm.membership_type && (
                <div className="grid grid-cols-2 gap-4">
                  <div><label className="block text-sm font-semibold text-gray-700 mb-2">시작일 <span className="text-red-500">*</span></label><input type="date" value={editForm.membership_start_date} onChange={(e) => handleStartDateChange(e.target.value)} className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg" required /></div>
                  <div><label className="block text-sm font-semibold text-gray-500 mb-2">종료일</label><input type="date" value={editForm.membership_end_date} readOnly disabled className="w-full px-4 py-2 border-2 border-gray-200 rounded-lg bg-gray-100 text-gray-500" /></div>
                </div>
              )}
            </div>
          ) : (
            <dl className="grid grid-cols-2 gap-4">
              <div>
                <dt className="text-sm text-gray-600 mb-1">회원권 종류</dt>
                <dd>
                  <span className={`inline-block px-4 py-2 rounded-lg font-bold text-lg ${
                    member?.membership_type?.startsWith('PT') 
                      ? 'bg-green-600 text-white' 
                      : 'bg-blue-600 text-white'
                  }`}>
                    {member?.membership_type || '-'}
                  </span>
                </dd>
              </div>
              <div className="col-span-2 grid grid-cols-2 gap-4 mt-2">
                <div><dt className="text-sm text-gray-600 mb-1">시작일</dt><dd className="text-lg font-semibold text-gray-900">{member?.membership_start_date || '-'}</dd></div>
                <div><dt className="text-sm text-gray-600 mb-1">종료일</dt><dd className="text-lg font-semibold text-gray-900">{member?.membership_end_date || '-'}</dd></div>
              </div>
            </dl>
          )}
        </div>

        {/* ✅ [수정 4] 락커 정보 (locker_type으로 통일) */}
        <div className="bg-white rounded-xl border-2 border-gray-200 p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2"><span className="text-2xl">🔑</span> 락커 정보</h3>
          
          {isEditMode || isNewMember ? (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-3">락커 기간 (선택사항)</label>
                <div className="grid grid-cols-4 gap-3">
                  {['1개월', '3개월', '6개월', '1년'].map((type) => (
                    <button 
                      key={type} 
                      type="button" 
                      onClick={() => handleLockerChange(type)} 
                      // locker_period 대신 editForm.locker_type 체크
                      className={`px-6 py-3 rounded-lg font-semibold transition-all ${
                        editForm.locker_type === type
                          ? 'bg-yellow-500 text-white shadow-lg scale-105'
                          : 'bg-gray-100 text-gray-700 border-2 border-gray-300 hover:border-yellow-400 hover:bg-gray-50'
                      }`}
                    >
                      {type}
                    </button>
                  ))}
                </div>
              </div>

              {editForm.locker_type && (
                <div className="grid grid-cols-3 gap-4">
                  <div><label className="block text-sm font-semibold text-gray-700 mb-2">시작일</label><input type="date" value={editForm.locker_start_date} onChange={(e) => handleLockerStartDateChange(e.target.value)} className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:ring-yellow-500" /></div>
                  <div><label className="block text-sm font-semibold text-gray-500 mb-2">종료일</label><input type="date" value={editForm.locker_end_date} readOnly disabled className="w-full px-4 py-2 border-2 border-gray-200 rounded-lg bg-gray-100 text-gray-500" /></div>
                  <div><label className="block text-sm font-semibold text-gray-500 mb-2">락커 번호</label><div className="w-full px-4 py-2 border-2 border-gray-200 rounded-lg bg-gray-100 text-gray-500 flex items-center justify-center font-bold">자동 부여</div></div>
                </div>
              )}
            </div>
          ) : (
            <dl className="grid grid-cols-2 gap-4">
              <div>
                <dt className="text-sm text-gray-600 mb-1">락커 기간</dt>
                <dd>
                  {/* member.locker_type 체크 */}
                  {member?.locker_type ? (
                    <span className="inline-block px-4 py-2 bg-yellow-500 text-white rounded-lg font-bold text-lg">{member.locker_type}</span>
                  ) : (<span className="text-gray-400">미선택</span>)}
                </dd>
              </div>
              {member?.locker_type && (
                <>
                  <div><dt className="text-sm text-gray-600 mb-1">락커 번호</dt><dd><span className="inline-block px-4 py-2 bg-blue-600 text-white rounded-lg font-bold text-lg">{member.locker_number ? `${member.locker_number}번` : '미배정'}</span></dd></div>
                  <div className="col-span-2 grid grid-cols-2 gap-4 mt-2">
                    <div><dt className="text-sm text-gray-600 mb-1">시작일</dt><dd className="text-lg font-semibold text-gray-900">{member?.locker_start_date || '-'}</dd></div>
                    <div><dt className="text-sm text-gray-600 mb-1">종료일</dt><dd className="text-lg font-semibold text-gray-900">{member?.locker_end_date || '-'}</dd></div>
                  </div>
                </>
              )}
            </dl>
          )}
        </div>

        {/* 회원복 정보 */}
        <div className="bg-white rounded-xl border-2 border-gray-200 p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2"><span className="text-2xl">👕</span> 회원복 정보</h3>
          {isEditMode || isNewMember ? (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-3">회원복 기간 (선택사항)</label>
                <div className="grid grid-cols-4 gap-3">
                  {['1개월', '3개월', '6개월', '1년'].map((type) => (
                    <button key={type} type="button" onClick={() => handleUniformChange(type)} className={`px-6 py-3 rounded-lg font-semibold transition-all ${editForm.uniform_type === type ? 'bg-purple-600 text-white shadow-lg scale-105' : 'bg-gray-100 text-gray-700 border-2 border-gray-300 hover:bg-gray-50'}`}>{type}</button>
                  ))}
                </div>
              </div>
              {editForm.uniform_type && (
                <div className="grid grid-cols-2 gap-4">
                  <div><label className="block text-sm font-semibold text-gray-700 mb-2">시작일</label><input type="date" value={editForm.uniform_start_date} onChange={(e) => handleUniformStartDateChange(e.target.value)} className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:ring-purple-500" /></div>
                  <div><label className="block text-sm font-semibold text-gray-500 mb-2">종료일</label><input type="date" value={editForm.uniform_end_date} readOnly disabled className="w-full px-4 py-2 border-2 border-gray-200 rounded-lg bg-gray-100 text-gray-500" /></div>
                </div>
              )}
            </div>
          ) : (
            <dl className="grid grid-cols-2 gap-4">
              <div><dt className="text-sm text-gray-600 mb-1">회원복 기간</dt><dd>{member?.uniform_type ? (<span className="inline-block px-4 py-2 bg-purple-600 text-white rounded-lg font-bold text-lg">{member.uniform_type}</span>) : (<span className="text-gray-400">미선택</span>)}</dd></div>
              {member?.uniform_type && (
                <div className="col-span-2 grid grid-cols-2 gap-4 mt-2">
                  <div><dt className="text-sm text-gray-600 mb-1">시작일</dt><dd className="text-lg font-semibold text-gray-900">{member?.uniform_start_date || '-'}</dd></div>
                  <div><dt className="text-sm text-gray-600 mb-1">종료일</dt><dd className="text-lg font-semibold text-gray-900">{member?.uniform_end_date || '-'}</dd></div>
                </div>
              )}
            </dl>
          )}
        </div>

        {/* 출입 기록 */}
        {!isNewMember && (
          <div className={`bg-white rounded-xl border-2 border-gray-200 p-6 ${isEditMode ? 'opacity-75' : ''}`}>
            <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
              <span className="text-2xl">📈</span> 최근 출입 기록 {isEditMode && <span className="text-sm text-gray-500 font-normal">(수정 불가)</span>}
            </h3>
            {loadingHistory ? (
              <div className="flex items-center justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div><span className="ml-3 text-gray-500">로딩 중...</span></div>
            ) : checkinHistory.length === 0 ? (
              <div className="text-center py-12 text-gray-500"><span className="text-4xl mb-3 block">📭</span>출입 기록이 없습니다.</div>
            ) : (
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {checkinHistory.map((record, index) => (
                  <div key={record.id} className="flex items-center justify-between p-4 bg-gradient-to-r from-gray-50 to-gray-100 rounded-lg border border-gray-200">
                    <div className="flex items-center gap-4">
                      <div className="flex items-center justify-center w-8 h-8 bg-green-500 text-white rounded-full font-bold text-sm">{index + 1}</div>
                      <div>
                        <span className="font-bold text-gray-900 text-lg block">{new Date(record.date).toLocaleDateString('ko-KR', { month: 'long', day: 'numeric', weekday: 'short' })}</span>
                        <span className="text-sm text-gray-500">{new Date(record.date).getFullYear()}년</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-gray-700 font-semibold text-lg">{record.time}</span>
                      <span className="px-3 py-1 text-xs bg-green-100 text-green-700 rounded-full font-bold">{record.type}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* 삭제 버튼 */}
      {!isNewMember && !isEditMode && (
        <button onClick={handleDelete} disabled={deleting} className="fixed bottom-8 right-8 px-6 py-3 bg-red-500 hover:bg-red-600 text-white rounded-lg shadow-2xl transition-all disabled:opacity-50 z-30 flex items-center gap-2">
          {deleting ? '삭제 중...' : '삭제'}
        </button>
      )}
    </div>
  );
}