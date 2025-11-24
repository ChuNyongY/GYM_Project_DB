import { useState, useEffect } from "react";
import { adminService } from "../services/adminService";
import MemberDrawer from "./MemberDrawer";

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
  const [selectedMemberIndex, setSelectedMemberIndex] = useState<number>(0);
  const [isAddingNew, setIsAddingNew] = useState(false);
  const [isClosing, setIsClosing] = useState(false);

  // 탭 상태 관리
  const [selectedTabs, setSelectedTabs] = useState<string[]>(["전체"]);
  const [selectedGender, setSelectedGender] = useState<"남" | "여" | null>(null);

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
    { key: "회원번호", label: "회원번호" },
    { key: "남", label: "남" },
    { key: "여", label: "여" },
    { key: "PT권", label: "PT권" },
    { key: "회원권", label: "회원권" },
    { key: "라커룸", label: "라커룸" },
    { key: "회원복", label: "회원복" },
    { key: "활성", label: "활성" },
    { key: "비활성", label: "비활성" },
    { key: "전체", label: "전체" },
  ];

  // 탭 클릭 핸들러
  const handleTabClick = (key: string) => {
    if (key === "남" || key === "여") {
      setSelectedGender((prev) => (prev === key ? null : (key as "남" | "여")));
    } else {
      setSelectedTabs((prev) => {
        // PT권/회원권 동시 선택 방지
        let newTabs = prev;
        if (prev.includes(key)) {
          // 이미 선택된 탭이면 해제
          newTabs = prev.filter((k) => k !== key);
        } else {
          if (key === "전체") {
            newTabs = ["전체"];
          } else {
            newTabs = prev.filter((k) => k !== "전체").concat(key);
          }
        }
        // PT권/회원권 상호 배제
        if (key === "PT권" && newTabs.includes("PT권") && newTabs.includes("회원권")) {
          newTabs = newTabs.filter((k) => k !== "회원권");
        } else if (key === "회원권" && newTabs.includes("PT권") && newTabs.includes("회원권")) {
          newTabs = newTabs.filter((k) => k !== "PT권");
        }
        return newTabs;
      });
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
      if (statusFilter === null) {
        params.sort_by = 'recent_checkin';
      } else if (statusFilter === 'all') {
        params.sort_by = '-member_id';
      } else {
        params.status = statusFilter;
      }
      if (selectedGender) {
        params.gender = selectedGender;
      }
      const response = await adminService.getMembers(params);
      setMembers(response.members);
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
  }, [currentPage, statusFilter]);

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
    setSelectedMemberIndex(0);
  };

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

      {/* 탭 버튼 영역 */}
      <div className="bg-white border-b border-gray-200 px-6 pt-4 pb-2">
        <div className="flex flex-wrap gap-2">
          {tabList.map((tab) => {
            // 성별 탭은 단일 선택, 나머지는 중복 선택
            const isGender = tab.key === "남" || tab.key === "여";
            const isSelected = isGender
              ? selectedGender === tab.key
              : selectedTabs.includes(tab.key);
            return (
              <button
                key={tab.key}
                type="button"
                onClick={() => handleTabClick(tab.key)}
                className={`px-4 py-2 rounded-lg border transition-colors font-semibold text-sm
                  ${isSelected
                    ? isGender
                      ? 'bg-blue-600 text-white border-blue-600'
                      : 'bg-green-600 text-white border-green-600'
                    : 'bg-gray-100 text-gray-700 border-gray-300 hover:bg-gray-200'}
                `}
              >
                {tab.label}
              </button>
            );
          })}
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
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">회원번호</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">이름</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">성별</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">전화번호</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">회원권</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">락커룸</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">회원복</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">출입기록</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">퇴장기록</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">상태</th>
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
                  members.map((member, index) => {
                    const membershipDaysLeft = getDaysLeft(member.membership_end_date);
                    const lockerDaysLeft = getDaysLeft(member.locker_end_date);
                    const uniformDaysLeft = getDaysLeft(member.uniform_end_date);
                    return (
                      <tr
                        key={member.member_rank}
                        onClick={() => handleRowClick(member, index)}
                        className={`hover:bg-blue-50 transition-colors cursor-pointer ${
                          selectedMember?.member_rank === member.member_rank ? 'bg-blue-100' : ''
                        }`}
                      >
                        {/* 회원번호 */}
                        <td className="px-4 py-4 whitespace-nowrap text-sm font-mono">{member.member_rank}</td>
                        {/* 이름 */}
                        <td className="px-4 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">{member.name}</td>
                        {/* 성별 */}
                        <td className="px-4 py-4 whitespace-nowrap text-sm">
                          {member.gender === 'M' ? (
                            <span className="inline-block px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded font-semibold">
                              남
                            </span>
                          ) : member.gender === 'F' ? (
                            <span className="inline-block px-2 py-1 text-xs bg-pink-100 text-pink-700 rounded font-semibold">
                              여
                            </span>
                          ) : (
                            <span className="inline-block px-2 py-1 text-xs bg-gray-100 text-gray-500 rounded">
                              -
                            </span>
                          )}
                        </td>
                        {/* 전화번호 */}
                        <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-600">{member.phone_number}</td>
                        {/* 회원권 (PT권 포함) */}
                        <td className="px-4 py-4 whitespace-nowrap text-sm">
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
                        <td className="px-4 py-4 whitespace-nowrap text-sm">
                          {member.locker_number ? (
                            <span className="inline-block px-2 py-1 text-xs bg-yellow-100 text-yellow-700 rounded font-semibold">
                              {member.locker_type}{member.locker_number ? ` (${member.locker_number}번)` : ' (미배정)'}
                            </span>
                          ) : (
                            <span className="inline-block px-2 py-1 text-xs bg-gray-100 text-gray-500 rounded">-</span>
                          )}
                        </td>
                        {/* 회원복 */}
                        <td className="px-4 py-4 whitespace-nowrap text-sm">
                          {member.uniform_type ? (
                            <span className="inline-block px-2 py-1 text-xs bg-purple-100 text-purple-700 rounded font-semibold">
                              {member.uniform_type}
                            </span>
                          ) : (
                            <span className="inline-block px-2 py-1 text-xs bg-gray-100 text-gray-500 rounded">-</span>
                          )}
                        </td>
                        
                        {/* 출입기록 (퇴장했으면 - 표시) */}
                        <td className="px-4 py-4 whitespace-nowrap text-sm">
                          {member.is_active && member.checkin_time ? (
                            <span className="inline-block px-2 py-1 text-xs bg-green-100 text-green-700 rounded font-semibold">
                              {formatTime(member.checkin_time)}
                            </span>
                          ) : (
                            <span className="inline-block px-2 py-1 text-xs bg-gray-100 text-gray-500 rounded">-</span>
                          )}
                        </td>

                        {/* 퇴장기록 (퇴장했을 때만 표시) */}
                        <td className="px-4 py-4 whitespace-nowrap text-sm">
                          {!member.is_active && member.checkout_time ? (
                            <span className="inline-block px-2 py-1 text-xs bg-red-100 text-red-700 rounded font-semibold">
                              {formatTime(member.checkout_time)}
                            </span>
                          ) : (
                            <span className="inline-block px-2 py-1 text-xs bg-gray-100 text-gray-500 rounded">-</span>
                          )}
                        </td>

                        {/* 상태 (초록원 / 빨간원) */}
                        <td className="px-4 py-4 whitespace-nowrap text-sm">
                          <div className="flex items-center justify-center"> {/* 가운데 정렬 추가 */}
                            {member.is_active ? (
                              <div className="group relative flex items-center" title="출입중">
                                <div className="w-3 h-3 rounded-full bg-green-500 shadow-md animate-pulse"></div>
                              </div>
                            ) : (
                              <div className="flex items-center" title="퇴장">
                                <div className="w-3 h-3 rounded-full bg-red-500 shadow-sm"></div>
                              </div>
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
              memberIndex={selectedMemberIndex}
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
  );
}
