import { useState, useEffect } from "react";
import { adminService } from "../services/adminService";
import MemberDrawer from "./MemberDrawer";
import DeletedMembers from "./DeletedMembers";

interface AdminDashboardProps {
  onLogout: () => void;
}

export default function AdminDashboard({ onLogout }: AdminDashboardProps) {
  const [members, setMembers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive' | 'expiring_soon' | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalMembers, setTotalMembers] = useState(0);
  const [selectedMember, setSelectedMember] = useState<any>(null);
  const [isAddingNew, setIsAddingNew] = useState(false);
  const [isClosing, setIsClosing] = useState(false);
  const [showDeletedMembers, setShowDeletedMembers] = useState(false);

  // 탭 상태 관리
  const [selectedTabs, setSelectedTabs] = useState<string[]>(["전체"]);
  const [selectedGender, setSelectedGender] = useState<"M" | "F" | null>(null);

  const formatTime = (dateStr: string | null) => {
  if (!dateStr) return null;
  const date = new Date(dateStr);
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hour = String(date.getHours()).padStart(2, '0');
  const minute = String(date.getMinutes()).padStart(2, '0');
  return `${month}.${day} ${hour}:${minute}`;
};

  // 탭 목록 정의
  const tabList = [
    { key: "전체", label: "전체" },
    { key: "회원순서", label: "회원순서" },
    { key: "남", label: "남" },
    { key: "여", label: "여" },
    { key: "PT권", label: "PT권" },
    { key: "회원권", label: "회원권" },
    { key: "라커룸", label: "라커룸" },
    { key: "회원복", label: "회원복" },
    { key: "활성", label: "활성" },
    { key: "비활성", label: "비활성" },
    { key: "최근삭제", label: "최근 삭제 기록" },
  ];

  // 탭 클릭 핸들러
  const handleTabClick = (key: string) => {
    if (key === "최근삭제") {
      // 최근 삭제 기록 탭 클릭 시 별도 페이지 표시
      setShowDeletedMembers(true);
      return;
    }
    
    if (key === "전체") {
      // 전체 버튼은 항상 단독 선택
      setSelectedTabs(["전체"]);
      setSelectedGender(null);
      setCurrentPage(1);
    } else if (key === "회원순서") {
      // 회원순서 버튼 토글 (단독)
      if (selectedTabs.includes("회원순서")) {
        setSelectedTabs(["전체"]);
      } else {
        setSelectedTabs(["회원순서"]);
      }
      setSelectedGender(null);
      setCurrentPage(1);
    } else if (key === "남" || key === "여") {
      // 성별 토글 ('남' -> 'M', '여' -> 'F') - 단독 선택
      const genderValue = key === "남" ? "M" : "F";
      if (selectedGender === genderValue) {
        setSelectedGender(null);
      } else {
        setSelectedGender(genderValue as "M" | "F");
      }
      setCurrentPage(1);
    } else if (key === "활성" || key === "비활성") {
      // 활성/비활성 상호 배제 (단독 선택)
      setSelectedTabs((prev) => {
        const filtered = prev.filter((k) => k !== "전체" && k !== "회원순서" && k !== "활성" && k !== "비활성");
        if (prev.includes(key)) {
          // 이미 선택되어 있으면 해제
          return filtered.length === 0 ? ["전체"] : filtered;
        } else {
          // 새로 선택
          return [...filtered, key];
        }
      });
      setCurrentPage(1);
    } else if (key === "회원권") {
      // 회원권 토글 (PT권과 상호 배제, 다른 필터와는 중복 가능)
      setSelectedTabs((prev) => {
        const filtered = prev.filter((k) => k !== "전체" && k !== "회원순서" && k !== "PT권");
        if (prev.includes(key)) {
          // 이미 선택되어 있으면 해제
          const result = filtered.filter((k) => k !== key);
          return result.length === 0 ? ["전체"] : result;
        } else {
          // 새로 선택
          return [...filtered, key];
        }
      });
      setCurrentPage(1);
    } else if (key === "라커룸" || key === "회원복") {
      // 라커룸/회원복 토글 (다른 필터와 중복 가능)
      setSelectedTabs((prev) => {
        const filtered = prev.filter((k) => k !== "전체" && k !== "회원순서");
        if (prev.includes(key)) {
          // 이미 선택되어 있으면 해제
          const result = filtered.filter((k) => k !== key);
          return result.length === 0 ? ["전체"] : result;
        } else {
          // 새로 선택
          return [...filtered, key];
        }
      });
      setCurrentPage(1);
    } else if (key === "PT권") {
      // PT권 토글 (회원권과 상호 배제, 다른 필터와는 중복 가능)
      setSelectedTabs((prev) => {
        const filtered = prev.filter((k) => k !== "전체" && k !== "회원순서" && k !== "회원권");
        if (prev.includes(key)) {
          // 이미 선택되어 있으면 해제
          const result = filtered.filter((k) => k !== key);
          return result.length === 0 ? ["전체"] : result;
        } else {
          // 새로 선택
          return [...filtered, key];
        }
      });
      setCurrentPage(1);
    }
  };

  const fetchMembers = async () => {
    setLoading(true);
    try {
      const token = sessionStorage.getItem('admin_token');
      if (!token) {
        alert('로그인이 필요합니다.');
        onLogout();
        return;
      }
      const params: any = {
        page: currentPage,
        size: 20,
      };
      if (searchTerm) {
        params.search = searchTerm;
      }
      
      console.log('🎯 selectedTabs:', selectedTabs);
      console.log('🎯 selectedGender:', selectedGender);
      
      // 정렬 및 필터 로직 (중복 필터 가능)
      if (selectedTabs.includes("회원순서")) {
        params.sort_by = 'member_rank_asc';
      } else if (selectedTabs.includes("전체")) {
        params.sort_by = 'member_rank_desc';
      } else if (statusFilter === null) {
        params.sort_by = 'recent_checkin';
      } else if (statusFilter === 'all') {
        params.sort_by = 'member_rank_desc';
      } else {
        params.status = statusFilter;
      }

      // 회원권 정렬
      if (selectedTabs.includes("회원권")) {
        console.log('✅ 회원권 필터 적용');
        params.membership_filter = 'membership';
        params.sort_by = 'membership_type_asc';
      }

      // PT권 필터 및 정렬
      if (selectedTabs.includes("PT권")) {
        console.log('✅ PT권 필터 적용');
        params.membership_filter = 'pt';
        params.sort_by = 'membership_type_asc';
      }

      // 라커룸 필터 및 정렬
      if (selectedTabs.includes("라커룸")) {
        console.log('✅ 라커룸 필터 적용');
        params.locker_filter = true;
        params.sort_by = 'locker_type_asc';
      }

      // 회원복 필터 및 정렬
      if (selectedTabs.includes("회원복")) {
        console.log('✅ 회원복 필터 적용');
        params.uniform_filter = true;
        params.sort_by = 'uniform_type_asc';
      }

      // 활성/비활성 필터
      if (selectedTabs.includes("활성")) {
        params.checkin_status = 'active';
      } else if (selectedTabs.includes("비활성")) {
        params.checkin_status = 'inactive';
      }
      
      // 성별 필터
      if (selectedGender) {
        params.gender = selectedGender;
      }
      
      console.log('📤 최종 요청 파라미터:', params);
      const response = await adminService.getMembers(params);
      console.log('📥 응답 데이터:', response);
      console.log('📊 회원 수:', response.members?.length, '/ 전체:', response.total);
      
      setMembers([...response.members]); // 강제 새 배열 생성
      setTotalMembers(response.total);
      setTotalPages(Math.ceil(response.total / response.size));
    } catch (error: any) {
      if (error.response?.status === 401) {
        alert('인증이 만료되었습니다. 다시 로그인해주세요.');
        sessionStorage.removeItem('admin_token');
        onLogout();
      } else {
        alert('회원 목록을 불러오는데 실패했습니다.');
      }
    } finally {
      setLoading(false);
    }
  };

  const getDaysLeft = (endDateStr: string | null): number => {
    if (!endDateStr) return Infinity;
    const endDate = new Date(endDateStr);
    const today = new Date();
    endDate.setHours(0, 0, 0, 0);
    today.setHours(0, 0, 0, 0);
    const timeDiff = endDate.getTime() - today.getTime();
    const daysLeft = Math.ceil(timeDiff / (1000 * 60 * 60 * 24));
    return daysLeft;
  };

  useEffect(() => {
    fetchMembers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPage, statusFilter, selectedTabs, selectedGender]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentPage(1);
    fetchMembers();
  };

  const handleFilterChange = (newFilter: typeof statusFilter) => {
    setStatusFilter(statusFilter === newFilter ? null : newFilter);
    setCurrentPage(1);
  };

  const handleLogout = () => {
    sessionStorage.removeItem('admin_token');
    onLogout();
  };

  const handleAddMember = () => {
    setIsAddingNew(true);
    setSelectedMember(null);
  };

  const handleRowClick = (member: any, index: number) => {
    // 표시용 회원순서 계산
    let displayRank;
    if (selectedTabs.includes("회원순서")) {
      displayRank = (currentPage - 1) * 20 + index + 1;
    } else {
      displayRank = totalMembers - ((currentPage - 1) * 20 + index);
    }
    
    // member 객체에 displayRank 추가
    const memberWithRank = {
      ...member,
      displayRank: displayRank
    };
    
    setSelectedMember(memberWithRank);
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

  const handleSave = () => {
    setIsClosing(true);
    setTimeout(() => {
      setSelectedMember(null);
      setIsAddingNew(false);
      setIsClosing(false);
      fetchMembers();  // 목록 새로고침
    }, 300);
  };

  // --- 실제 JSX 반환부 전체 ---
  return (
    <>
      {showDeletedMembers ? (
        <DeletedMembers onClose={() => setShowDeletedMembers(false)} />
      ) : (
    <div className="min-h-[100dvh] flex flex-col bg-gray-50 relative overflow-hidden">
      {/* 탭 버튼 영역 - 윈도우 탭 스타일 */}
      <div className="bg-gray-100 border-b border-gray-300 px-6 pt-2 pb-0 flex justify-between">
        <div className="flex gap-0.5 items-end">
          {tabList.map((tab) => {
            // 성별 탭은 단일 선택, 나머지는 중복 선택
            const isGender = tab.key === "남" || tab.key === "여";
            const genderValue = tab.key === "남" ? "M" : tab.key === "여" ? "F" : null;
            const isSelected = isGender
              ? selectedGender === genderValue
              : selectedTabs.includes(tab.key);
            return (
              <button
                key={tab.key}
                type="button"
                onClick={() => handleTabClick(tab.key)}
                className={`px-5 py-2.5 font-medium text-sm border-t border-l border-r transition-all relative
                  ${isSelected
                    ? 'bg-white text-gray-800 border-gray-300 border-b-0 z-10 -mb-px'
                    : 'bg-gray-200 text-gray-600 border-gray-400 hover:bg-gray-300 border-b border-gray-300'}
                  ${tab.key === tabList[0].key ? 'rounded-tl-lg' : ''}
                  ${tab.key === tabList[tabList.length - 1].key ? 'rounded-tr-lg' : ''}
                `}
              >
                {tab.label}
            </button>
          );
        })}
        </div>
        <div className="flex items-center">
          <button 
            onClick={handleLogout} 
            className="px-6 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors font-medium text-sm ml-auto"
            style={{marginTop: '8px', marginBottom: '8px'}}
          >
            로그아웃
          </button>
        </div>
      </div>

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
        </form>
      </div>

      {/* 테이블 */}
      <main className="flex-1 overflow-auto p-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider w-24">회원순서</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-28">이름</th>
                  <th className="px-2 py-3 text-left -translate-x-3 text-xs font-medium text-gray-500 uppercase tracking-wider w-20">성별</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-36">전화번호</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider w-32">회원권</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider w-32">락커룸</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider w-28">회원복</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider w-32">출입기록</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider w-32">퇴장기록</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider w-20">상태</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {loading ? (
                  <tr>
                    <td colSpan={10} className="px-6 py-12 text-center text-gray-500">
                      <div className="flex items-center justify-center">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                        <span className="ml-3">로딩 중...</span>
                      </div>
                    </td>
                  </tr>
                ) : members.length === 0 ? (
                  <tr>
                    <td colSpan={10} className="px-6 py-16 text-center">
                      <div className="flex flex-col items-center justify-center">
                        <svg className="w-16 h-16 text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                        </svg>
                        <p className="text-lg font-medium text-gray-500">회원이 없습니다</p>
                        <p className="text-sm text-gray-400 mt-1">새로운 회원을 추가해보세요</p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  members.map((member, index) => {
                    const membershipDaysLeft = getDaysLeft(member.membership_end_date);
                    const lockerDaysLeft = getDaysLeft(member.locker_end_date);
                    const uniformDaysLeft = getDaysLeft(member.uniform_end_date);
                    
                    // 표시용 회원순서 계산
                    let displayRank;
                    if (selectedTabs.includes("회원순서")) {
                      // 회원순서 버튼: 오름차순이므로 페이지 순서대로 1, 2, 3, 4...
                      displayRank = (currentPage - 1) * 20 + index + 1;
                    } else {
                      // 전체 버튼 (기본): 내림차순이므로 큰 숫자부터 (5, 4, 3, 2, 1)
                      displayRank = totalMembers - ((currentPage - 1) * 20 + index);
                    }
                    
                    return (
                      <tr
                        key={member.member_id}
                        onClick={() => handleRowClick(member, index)}
                        className={`hover:bg-blue-50 transition-colors cursor-pointer ${
                          selectedMember?.member_id === member.member_id ? 'bg-blue-100' : ''
                        }`}
                      >
                        {/* 회원순서 */}
                        <td className="px-4 py-4 whitespace-nowrap text-sm font-mono text-center">{displayRank}</td>
                        {/* 이름 */}
                        <td className="px-4 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">{member.name}</td>
                        {/* 성별 */}
                        <td className="px-2 py-4 whitespace-nowrap -translate-x-3 text-sm text-center">
                          {member.gender === 'M' ? (
                            <span className="inline-block transform -translate-x-8 px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded font-semibold">
                              남
                            </span>
                          ) : member.gender === 'F' ? (
                            <span className="inline-block transform -translate-x-8 px-2 py-1 text-xs bg-pink-100 text-pink-700 rounded font-semibold">
                              여
                            </span>
                          ) : (
                            <span className="inline-block transform -translate-x-8 px-2 py-1 text-xs bg-gray-100 text-gray-500 rounded">
                              -
                            </span>
                          )}
                        </td>
                        {/* 전화번호 */}
                        <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-600">{member.phone_number}</td>
                        {/* 회원권 (PT권 포함) */}
                        <td className="px-4 py-4 whitespace-nowrap text-sm text-center">
                          {member.membership_type?.startsWith('PT') ? (
                            <span className="inline-block px-2 py-1 text-xs bg-pink-100 text-pink-700 rounded font-semibold">
                              {member.membership_type}
                            </span>
                          ) : member.membership_type ? (
                            <span className="inline-block px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded font-semibold">
                              {member.membership_type}
                            </span>
                          ) : (
                            <span className="inline-block px-2 py-1 text-xs bg-gray-100 text-gray-500 rounded">-</span>
                          )}
                        </td>
                        {/* 라커룸 (번호/기간) */}
                        <td className="px-4 py-4 whitespace-nowrap text-sm text-center">
                          {member.locker_number ? (
                            <span className="inline-block px-2 py-1 text-xs bg-yellow-100 text-yellow-700 rounded font-semibold">
                              {member.locker_type}{member.locker_number ? ` (${member.locker_number}번)` : ' (미배정)'}
                            </span>
                          ) : (
                            <span className="inline-block px-2 py-1 text-xs bg-gray-100 text-gray-500 rounded">-</span>
                          )}
                        </td>
                        {/* 회원복 */}
                        <td className="px-4 py-4 whitespace-nowrap text-sm text-center">
                          {member.uniform_type ? (
                            <span className="inline-block px-2 py-1 text-xs bg-purple-100 text-purple-700 rounded font-semibold">
                              {member.uniform_type}
                            </span>
                          ) : (
                            <span className="inline-block px-2 py-1 text-xs bg-gray-100 text-gray-500 rounded">-</span>
                          )}
                        </td>
                        
                        {/* 출입기록 (출입중일 때만 표시, 퇴장 시 숨김) */}
                        <td className="px-4 py-4 whitespace-nowrap text-sm text-center">
                          {member.is_active && member.checkin_time && !member.checkout_time ? (
                            <span className="inline-block px-2 py-1 text-xs bg-green-100 text-green-700 rounded font-semibold">
                              {formatTime(member.checkin_time)}
                            </span>
                          ) : (
                            <span className="inline-block px-2 py-1 text-xs bg-gray-100 text-gray-500 rounded">-</span>
                          )}
                        </td>

                        {/* 퇴장기록 (퇴장했을 때만 표시) */}
                        <td className="px-4 py-4 whitespace-nowrap text-sm text-center">
                          {member.checkout_time ? (
                            <span className="inline-block px-2 py-1 text-xs bg-red-100 text-red-700 rounded font-semibold">
                              {formatTime(member.checkout_time)}
                            </span>
                          ) : (
                            <span className="inline-block px-2 py-1 text-xs bg-gray-100 text-gray-500 rounded">-</span>
                          )}
                        </td>

                        {/* 상태 (출입중: 초록색, 퇴장: 빨간색, 없으면 - 표시) */}
                        <td className="px-4 py-4 whitespace-nowrap text-sm">
                          <div className="flex items-center justify-center">
                            {member.checkout_time ? (
                              <div className="flex items-center" title="퇴장">
                                <div className="w-3 h-3 rounded-full bg-red-500 shadow-sm"></div>
                              </div>
                            ) : member.checkin_time ? (
                              <div className="group relative flex items-center" title="출입중">
                                <div className="w-3 h-3 rounded-full bg-green-500 shadow-md animate-pulse"></div>
                              </div>
                            ) : (
                              <span className="text-gray-400">-</span>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })
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
              onClose={handleCloseDrawer}
              onSave={handleSave}
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
      )}
    </>
  );
}
