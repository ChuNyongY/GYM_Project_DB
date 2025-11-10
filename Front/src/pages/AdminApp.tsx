import { useState, useEffect } from "react";
import { adminService } from "../services/adminService";

function AdminLogin({ onAuth }: { onAuth: () => void }) {
  const [pw, setPw] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await adminService.login(pw);
      
      if (response.status === "success" && response.token) {
        localStorage.setItem('admin_token', response.token);
        onAuth();
      } else {
        setError("로그인에 실패했습니다.");
      }
    } catch (err: any) {
      console.error('Login error:', err);
      setError(err.response?.data?.detail || "비밀번호가 틀렸습니다.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-blue-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">관리자 로그인</h1>
          <p className="text-gray-500">비밀번호를 입력하세요</p>
        </div>
        <form onSubmit={submit} className="space-y-6">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">비밀번호</label>
            <input
              type="password"
              value={pw}
              onChange={(e) => setPw(e.target.value)}
              placeholder="관리자 비밀번호"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              autoFocus
              disabled={loading}
            />
          </div>
          
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-blue-600 to-blue-700 text-white font-semibold py-3 rounded-lg hover:from-blue-700 hover:to-blue-800 transition-all duration-200 shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "로그인 중..." : "입장하기"}
          </button>
        </form>
      </div>
    </div>
  );
}

// 통합 Drawer 컴포넌트
function MemberDrawer({ 
  member, 
  memberIndex,
  onClose, 
  onSave,
  isNewMember = false
}: { 
  member: any | null; 
  memberIndex?: number;
  onClose: () => void; 
  onSave: () => void;
  isNewMember?: boolean;
}) {
  const [isEditMode, setIsEditMode] = useState(isNewMember);
  const [editForm, setEditForm] = useState({
    name: member?.name || '',
    phone_number: member?.phone_number || '',
    membership_type: member?.membership_type || '3개월',
    membership_start_date: member?.membership_start_date || new Date().toISOString().split('T')[0],
    membership_end_date: member?.membership_end_date || '',
  });
  const [checkinHistory, setCheckinHistory] = useState<any[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(!isNewMember);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);

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

  // 새 회원일 때 종료일 자동 설정
  useEffect(() => {
    if (isNewMember && editForm.membership_start_date) {
      handleMembershipChange(editForm.membership_type);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const getMemberStatus = () => {
    if (!member || !member.is_active) {
      return <span className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded-full font-semibold">비활성</span>;
    }
    
    if (member.membership_end_date) {
      const endDate = new Date(member.membership_end_date);
      const today = new Date();
      const daysLeft = Math.ceil((endDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
      
      if (daysLeft < 0) {
        return <span className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded-full font-semibold">만료</span>;
      } else if (daysLeft <= 7) {
        return <span className="px-3 py-1 text-sm bg-yellow-100 text-yellow-700 rounded-full font-semibold">곧 만료 ({daysLeft}일)</span>;
      }
    }
    
    return <span className="px-3 py-1 text-sm bg-green-100 text-green-700 rounded-full font-semibold">활성</span>;
  };

  // 회원권 선택
  const handleMembershipChange = (type: string) => {
    const startDate = editForm.membership_start_date || new Date().toISOString().split('T')[0];
    const start = new Date(startDate);
    let endDate = new Date(start);

    switch(type) {
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

    setEditForm({
      ...editForm,
      membership_type: type,
      membership_start_date: startDate,
      membership_end_date: endDate.toISOString().split('T')[0],
    });
  };

  // 시작일 변경
  const handleStartDateChange = (newStartDate: string) => {
    if (!newStartDate) return;

    const start = new Date(newStartDate);
    let endDate = new Date(start);

    switch(editForm.membership_type) {
      case '3개월':
        endDate.setMonth(endDate.getMonth() + 3);
        break;
      case '6개월':
        endDate.setMonth(endDate.getMonth() + 6);
        break;
      case '1년':
        endDate.setFullYear(endDate.getFullYear() + 1);
        break;
      default:
        endDate.setMonth(endDate.getMonth() + 3);
    }

    setEditForm({
      ...editForm,
      membership_start_date: newStartDate,
      membership_end_date: endDate.toISOString().split('T')[0],
    });
  };

  // 저장
  const handleSave = async () => {
    // 이름 유효성 검사
    if (!editForm.name.trim()) {
      alert('이름을 입력해주세요.');
      return;
    }

    // 이름 형식 검사 (한글 2-10자, 영문 2-20자)
    const nameRegex = /^[가-힣]{2,10}$|^[a-zA-Z\s]{2,20}$/;
    if (!nameRegex.test(editForm.name.trim())) {
      alert('올바른 이름 형식이 아닙니다.\n한글 2-10자 또는 영문 2-20자로 입력해주세요.');
      return;
    }

    // 전화번호 유효성 검사
    if (!editForm.phone_number.trim()) {
      alert('전화번호를 입력해주세요.');
      return;
    }

    // 전화번호 형식 검사 (010-1234-5678 또는 01012345678)
    const phoneRegex = /^010-\d{4}-\d{4}$|^010\d{8}$/;
    if (!phoneRegex.test(editForm.phone_number.replace(/\s/g, ''))) {
      alert('올바른 번호가 아닙니다.\n010으로 시작하는 11자리 번호를 입력해주세요.');
      return;
    }

    // 시작일 검사
    if (!editForm.membership_start_date) {
      alert('시작일을 선택해주세요.');
      return;
    }

    try {
      setSaving(true);
      
      if (isNewMember) {
        await adminService.createMember({
          name: editForm.name.trim(),
          phone_number: editForm.phone_number,
          membership_type: editForm.membership_type,
          membership_start_date: editForm.membership_start_date,
          membership_end_date: editForm.membership_end_date,
        });
        alert('회원이 추가되었습니다.');
      } else {
        await adminService.updateMember(member.member_id, {
          name: editForm.name.trim(),
          phone_number: editForm.phone_number,
          membership_type: editForm.membership_type,
          membership_start_date: editForm.membership_start_date,
          membership_end_date: editForm.membership_end_date,
        });
        alert('회원 정보가 수정되었습니다.');
      }
      
      onSave();
    } catch (error: any) {
      console.error('저장 실패:', error);
      alert(error.response?.data?.detail || `회원 ${isNewMember ? '추가' : '수정'}에 실패했습니다.`);
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
        membership_type: member.membership_type || '3개월',
        membership_start_date: member.membership_start_date || '',
        membership_end_date: member.membership_end_date || '',
      });
      setIsEditMode(false);
    }
  };

  // 회원 삭제
  const handleDelete = async () => {
    if (!member) return;

    const confirmMessage = `정말로 "${member.name}" 회원을 삭제하시겠습니까?\n삭제된 회원은 복구할 수 없습니다.`;
    
    if (!window.confirm(confirmMessage)) {
      return;
    }

    try {
      setDeleting(true);
      await adminService.deleteMember(member.member_id);
      alert('회원이 삭제되었습니다.');
      onSave();
    } catch (error: any) {
      console.error('삭제 실패:', error);
      alert(error.response?.data?.detail || '회원 삭제에 실패했습니다.');
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
                <>
                  <span className="text-3xl">✨</span>
                  새 회원 추가
                </>
              ) : isEditMode ? (
                <>
                  <span className="text-3xl">📝</span>
                  회원 정보 수정
                </>
              ) : (
                <>
                  <span className="text-3xl">👤</span>
                  {member?.name}님
                </>
              )}
            </h2>
            {/* ⭐ 순번 표시로 변경 */}
            {!isNewMember && memberIndex && (
              <p className="text-blue-100 text-sm mt-1">
                회원번호: {memberIndex}번
              </p>
            )}
          </div>
          <div className="flex gap-2">
            {isEditMode || isNewMember ? (
              <>
                <button
                  onClick={handleCancel}
                  disabled={saving}
                  className="px-5 py-2 bg-white/20 hover:bg-white/30 rounded-lg transition-colors disabled:opacity-50"
                >
                  취소
                </button>
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="px-5 py-2 bg-white text-blue-600 rounded-lg hover:bg-blue-50 transition-colors font-semibold disabled:opacity-50 flex items-center gap-2"
                >
                  {saving ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                      <span>{isNewMember ? '추가 중...' : '저장 중...'}</span>
                    </>
                  ) : (
                    isNewMember ? '추가' : '저장'
                  )}
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={() => setIsEditMode(true)}
                  className="px-5 py-2 bg-white text-blue-600 rounded-lg hover:bg-blue-50 transition-colors font-semibold"
                >
                  수정
                </button>
                <button
                  onClick={onClose}
                  className="px-5 py-2 bg-white/20 hover:bg-white/30 rounded-lg transition-colors"
                >
                  닫기
                </button>
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
            <span className="text-2xl">📋</span>
            기본 정보
          </h3>
          
          {isEditMode || isNewMember ? (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  이름 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={editForm.name}
                  onChange={(e) => setEditForm({...editForm, name: e.target.value})}
                  placeholder="회원 이름"
                  className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  전화번호 <span className="text-red-500">*</span>
                </label>
                <input
                  type="tel"
                  value={editForm.phone_number}
                  onChange={handlePhoneChange}
                  placeholder="01012345678"
                  maxLength={13}
                  className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                />
                <p className="text-xs text-gray-500 mt-1">숫자만 입력하세요</p>
              </div>
            </div>
          ) : (
            <dl className="grid grid-cols-2 gap-4">
              <div>
                <dt className="text-sm text-gray-600 mb-1">이름</dt>
                <dd className="text-xl font-bold text-gray-900">{member?.name}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-600 mb-1">전화번호</dt>
                <dd className="text-xl font-bold text-gray-900">{member?.phone_number}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-600 mb-1">상태</dt>
                <dd className="mt-1">{getMemberStatus()}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-600 mb-1">등록일</dt>
                <dd className="text-base font-semibold text-gray-900">
                  {member?.created_at 
                    ? new Date(member.created_at).toLocaleDateString('ko-KR', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric'
                      })
                    : '-'
                  }
                </dd>
              </div>
            </dl>
          )}
        </div>

        {/* 회원권 정보 */}
        <div className="bg-white rounded-xl border-2 border-gray-200 p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
            <span className="text-2xl">🎫</span>
            회원권 정보
          </h3>
          
          {isEditMode || isNewMember ? (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-3">
                  회원권 종류 <span className="text-red-500">*</span>
                </label>
                <div className="grid grid-cols-3 gap-3">
                  {['3개월', '6개월', '1년'].map((type) => (
                    <button
                      key={type}
                      type="button"
                      onClick={() => handleMembershipChange(type)}
                      className={`px-6 py-3 rounded-lg font-semibold transition-all ${
                        editForm.membership_type === type
                          ? 'bg-blue-600 text-white shadow-lg scale-105'
                          : 'bg-gray-100 text-gray-700 border-2 border-gray-300 hover:border-blue-400 hover:bg-gray-50'
                      }`}
                    >
                      {type}
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    시작일 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="date"
                    value={editForm.membership_start_date}
                    onChange={(e) => handleStartDateChange(e.target.value)}
                    className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-500 mb-2">종료일</label>
                  <input
                    type="date"
                    value={editForm.membership_end_date}
                    readOnly
                    disabled
                    className="w-full px-4 py-2 border-2 border-gray-200 rounded-lg bg-gray-100 text-gray-500 cursor-not-allowed"
                  />
                </div>
              </div>
            </div>
          ) : (
            <dl className="grid grid-cols-2 gap-4">
              <div>
                <dt className="text-sm text-gray-600 mb-1">회원권 종류</dt>
                <dd>
                  <span className="inline-block px-4 py-2 bg-blue-600 text-white rounded-lg font-bold text-lg">
                    {member?.membership_type || '-'}
                  </span>
                </dd>
              </div>
              <div className="col-span-2 grid grid-cols-2 gap-4 mt-2">
                <div>
                  <dt className="text-sm text-gray-600 mb-1">시작일</dt>
                  <dd className="text-lg font-semibold text-gray-900">
                    {member?.membership_start_date 
                      ? new Date(member.membership_start_date).toLocaleDateString('ko-KR', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric'
                        })
                      : '-'
                    }
                  </dd>
                </div>
                <div>
                  <dt className="text-sm text-gray-600 mb-1">종료일</dt>
                  <dd className="text-lg font-semibold text-gray-900">
                    {member?.membership_end_date 
                      ? new Date(member.membership_end_date).toLocaleDateString('ko-KR', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric'
                        })
                      : '-'
                    }
                  </dd>
                </div>
              </div>
            </dl>
          )}
        </div>

        {/* 출입 기록 */}
        {!isNewMember && (
          <div className={`bg-white rounded-xl border-2 border-gray-200 p-6 ${isEditMode ? 'opacity-75' : ''}`}>
            <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
              <span className="text-2xl">📈</span>
              최근 출입 기록
              {isEditMode && <span className="text-sm text-gray-500 font-normal">(수정 불가)</span>}
            </h3>
            
            {loadingHistory ? (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <span className="ml-3 text-gray-500">로딩 중...</span>
              </div>
            ) : checkinHistory.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <span className="text-4xl mb-3 block">📭</span>
                출입 기록이 없습니다.
              </div>
            ) : (
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {checkinHistory.map((record, index) => (
                  <div 
                    key={record.id} 
                    className="flex items-center justify-between p-4 bg-gradient-to-r from-gray-50 to-gray-100 rounded-lg hover:from-blue-50 hover:to-blue-100 transition-all border border-gray-200"
                  >
                    <div className="flex items-center gap-4">
                      <div className="flex items-center justify-center w-8 h-8 bg-green-500 text-white rounded-full font-bold text-sm">
                        {index + 1}
                      </div>
                      <div>
                        <span className="font-bold text-gray-900 text-lg block">
                          {new Date(record.date).toLocaleDateString('ko-KR', {
                            month: 'long',
                            day: 'numeric',
                            weekday: 'short'
                          })}
                        </span>
                        <span className="text-sm text-gray-500">
                          {new Date(record.date).getFullYear()}년
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-gray-700 font-semibold text-lg">{record.time}</span>
                      <span className="px-3 py-1 text-xs bg-green-100 text-green-700 rounded-full font-bold">
                        {record.type}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* 삭제 버튼 (우측 하단 고정) */}
      {!isNewMember && !isEditMode && (
        <button
          onClick={handleDelete}
          disabled={deleting}
          className="fixed bottom-8 right-8 px-6 py-3 bg-red-500 hover:bg-red-600 text-white rounded-lg shadow-2xl hover:shadow-3xl transition-all duration-300 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed z-10"
          title="회원 삭제"
        >
          {deleting ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              <span>삭제 중...</span>
            </>
          ) : (
            <>
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              <span className="font-semibold">삭제</span>
            </>
          )}
        </button>
      )}
    </div>
  );
}

function AdminDashboard({ onLogout }: { onLogout: () => void }) {
  const [members, setMembers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive' | 'expiring_soon'>('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalMembers, setTotalMembers] = useState(0);
  const [selectedMember, setSelectedMember] = useState<any>(null);
  const [selectedMemberIndex, setSelectedMemberIndex] = useState<number>(0); // ⭐ 추가
  const [isAddingNew, setIsAddingNew] = useState(false);
  const [isClosing, setIsClosing] = useState(false);

  const fetchMembers = async () => {
    setLoading(true);
    try {
      const params: any = {
        page: currentPage,
        size: 20,
      };

      if (searchTerm) {
        params.search = searchTerm;
      }

      if (statusFilter !== 'all') {
        params.status = statusFilter;
      }

      const response = await adminService.getMembers(params);

      setMembers(response.members);
      setTotalMembers(response.total);
      setTotalPages(Math.ceil(response.total / response.size));
    } catch (error) {
      console.error('회원 목록 조회 실패:', error);
      alert('회원 목록을 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMembers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPage, statusFilter]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentPage(1);
    fetchMembers();
  };

  const handleFilterChange = (newFilter: typeof statusFilter) => {
    setStatusFilter(newFilter);
    setCurrentPage(1);
  };

  const getMemberStatus = (member: any) => {
    if (!member.is_active) {
      return <span className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded-full">비활성</span>;
    }
    
    if (member.membership_end_date) {
      const endDate = new Date(member.membership_end_date);
      const today = new Date();
      const daysLeft = Math.ceil((endDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
      
      if (daysLeft < 0) {
        return <span className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded-full">만료</span>;
      } else if (daysLeft <= 7) {
        return <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-700 rounded-full">곧 만료 ({daysLeft}일)</span>;
      }
    }
    
    return <span className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded-full">활성</span>;
  };

  const handleLogout = () => {
    localStorage.removeItem('admin_token');
    onLogout();
  };

  // ⭐ handleAddMember 수정
  const handleAddMember = () => {
    setIsAddingNew(true);
    setSelectedMember(null);
    setSelectedMemberIndex(0);
  };

  // ⭐ handleRowClick 수정
  const handleRowClick = (member: any, index: number) => {
    setSelectedMember(member);
    setSelectedMemberIndex((currentPage - 1) * 20 + index + 1);
    setIsAddingNew(false);
  };

  const handleCloseDrawer = () => {
    setIsClosing(true);
    setTimeout(() => {
      setSelectedMember(null);
      setIsAddingNew(false);
      setIsClosing(false);
    }, 300);
  };

  const handleSaveSuccess = () => {
    setIsClosing(true);
    setTimeout(() => {
      setSelectedMember(null);
      setIsAddingNew(false);
      setIsClosing(false);
      fetchMembers();
    }, 300);
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50 relative">
      {/* 헤더 */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">헬스장 관리 시스템</h1>
            <p className="text-sm text-gray-500 mt-0.5">총 {totalMembers}명의 회원</p>
          </div>
          <button 
            onClick={handleLogout} 
            className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
          >
            로그아웃
          </button>
        </div>
      </header>

      {/* 검색 및 필터 */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <form onSubmit={handleSearch} className="flex gap-4 items-center">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="이름 또는 전화번호로 검색..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            검색
          </button>

          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => handleFilterChange('all')}
              className={`px-4 py-2 rounded-lg transition-colors ${
                statusFilter === 'all' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              전체
            </button>
            <button
              type="button"
              onClick={() => handleFilterChange('active')}
              className={`px-4 py-2 rounded-lg transition-colors ${
                statusFilter === 'active' 
                  ? 'bg-green-600 text-white' 
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              활성
            </button>
            <button
              type="button"
              onClick={() => handleFilterChange('expiring_soon')}
              className={`px-4 py-2 rounded-lg transition-colors ${
                statusFilter === 'expiring_soon' 
                  ? 'bg-yellow-600 text-white' 
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              곧 만료
            </button>
          </div>
        </form>
      </div>

      {/* 테이블 */}
      <main className="flex-1 overflow-auto p-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">회원번호</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">이름</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">전화번호</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">회원권</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">시작일</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">종료일</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">상태</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {loading ? (
                  <tr>
                    <td colSpan={7} className="px-6 py-12 text-center text-gray-500">
                      <div className="flex items-center justify-center">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                        <span className="ml-3">로딩 중...</span>
                      </div>
                    </td>
                  </tr>
                ) : members.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-6 py-12 text-center text-gray-500">
                      회원이 없습니다.
                    </td>
                  </tr>
                ) : (
                  members.map((member, index) => (
                    <tr
                      key={member.member_id} 
                      onClick={() => handleRowClick(member, index)}
                      className={`hover:bg-blue-50 transition-colors cursor-pointer ${
                        selectedMember?.member_id === member.member_id ? 'bg-blue-100' : ''
                      }`}
                    >
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-mono">
                        {(currentPage - 1) * 20 + index + 1}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">
                        {member.name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {member.phone_number}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span className="inline-block px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded">
                          {member.membership_type || '-'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {member.membership_start_date 
                          ? new Date(member.membership_start_date).toLocaleDateString('ko-KR')
                          : '-'
                        }
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {member.membership_end_date 
                          ? new Date(member.membership_end_date).toLocaleDateString('ko-KR')
                          : '-'
                        }
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {getMemberStatus(member)}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* 페이지네이션 */}
        {!loading && totalPages > 1 && (
          <div className="mt-6 flex justify-center gap-2">
            <button
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              이전
            </button>
            <span className="px-4 py-2 bg-white border border-gray-300 rounded-lg">
              {currentPage} / {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              다음
            </button>
          </div>
        )}
      </main>

      {/* Drawer */}
      {(selectedMember || isAddingNew) && (
        <>
          <div 
            className={`fixed inset-0 bg-black/60 z-40 transition-opacity duration-300 ${
              isClosing ? 'opacity-0' : 'opacity-100'
            }`}
            onClick={handleCloseDrawer}
          />
          
          <div 
            className={`fixed top-0 right-0 h-full w-2/5 bg-white shadow-2xl z-50 transition-transform duration-300 ease-in-out ${
              isClosing ? 'translate-x-full' : 'translate-x-0'
            }`}
          >
            <MemberDrawer
              member={selectedMember}
              memberIndex={selectedMemberIndex}
              onClose={handleCloseDrawer}
              onSave={handleSaveSuccess}
              isNewMember={isAddingNew}
            />
          </div>
        </>
      )}

      {/* 회원 추가 버튼 */}
      <button
        onClick={handleAddMember}
        className="fixed bottom-8 right-8 w-16 h-16 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-2xl hover:shadow-3xl transition-all duration-300 flex items-center justify-center group z-30"
        title="회원 추가"
      >
        <svg 
          className="w-8 h-8 group-hover:rotate-90 transition-transform duration-300" 
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
        </svg>
      </button>
    </div>
  );
}

export default function AdminApp() {
  const [authed, setAuthed] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('admin_token');
    if (token) {
      setAuthed(true);
    }
  }, []);

  return !authed 
    ? <AdminLogin onAuth={() => setAuthed(true)} /> 
    : <AdminDashboard onLogout={() => setAuthed(false)} />;
}