import { useState, useEffect } from "react";
import { adminService } from "../services/adminService";

interface DeletedMembersProps {
  onClose: () => void;
}

export default function DeletedMembers({ onClose }: DeletedMembersProps) {
  const [members, setMembers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalMembers, setTotalMembers] = useState(0);

  const fetchDeletedMembers = async () => {
    setLoading(true);
    try {
      const token = sessionStorage.getItem('admin_token');
      if (!token) {
        alert('로그인이 필요합니다.');
        return;
      }

      const params: any = {
        page: currentPage,
        size: 20,
      };
      if (searchTerm) {
        params.search = searchTerm;
      }

      const response = await adminService.getDeletedMembers(params);
      setMembers(response.members);
      setTotalMembers(response.total);
      setTotalPages(Math.ceil(response.total / response.size));
    } catch (error: any) {
      if (error.response?.status === 401) {
        alert('인증이 만료되었습니다. 다시 로그인해주세요.');
        sessionStorage.removeItem('admin_token');
      } else {
        alert('삭제된 회원 목록을 불러오는데 실패했습니다.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDeletedMembers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPage]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentPage(1);
    fetchDeletedMembers();
  };

  const handlePermanentDelete = async (memberId: number, memberName: string) => {
    if (!confirm(`${memberName} 회원을 영구 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.`)) return;

    try {
      await adminService.permanentDeleteMember(memberId);
      alert('회원이 영구 삭제되었습니다.');
      fetchDeletedMembers();
    } catch (error) {
      alert('회원 삭제에 실패했습니다.');
    }
  };

  const handleDeleteAll = async () => {
    if (!confirm(`모든 삭제된 회원을 영구 삭제하시겠습니까?\n총 ${totalMembers}명이 영구 삭제됩니다.\n이 작업은 되돌릴 수 없습니다.`)) return;

    try {
      const result = await adminService.permanentDeleteAll();
      alert(result.message);
      fetchDeletedMembers();
    } catch (error) {
      alert('전체 삭제에 실패했습니다.');
    }
  };

  const handleRestoreMember = async (memberId: number, memberName: string) => {
    if (!confirm(`${memberName} 회원을 복원하시겠습니까?`)) return;

    try {
      await adminService.restoreMember(memberId);
      alert('회원이 복원되었습니다.');
      fetchDeletedMembers();
    } catch (error) {
      alert('회원 복원에 실패했습니다.');
    }
  };

  const handleRestoreAll = async () => {
    if (!confirm(`모든 삭제된 회원을 복원하시겠습니까?\n총 ${totalMembers}명이 복원됩니다.`)) return;

    try {
      const result = await adminService.restoreAll();
      alert(result.message);
      fetchDeletedMembers();
    } catch (error) {
      alert('전체 복원에 실패했습니다.');
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hour = String(date.getHours()).padStart(2, '0');
    const minute = String(date.getMinutes()).padStart(2, '0');
    return `${year}.${month}.${day} ${hour}:${minute}`;
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50 relative">
      {/* 헤더 */}
      <div className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={onClose}
            className="text-gray-600 hover:text-gray-800"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
          </button>
          <h1 className="text-2xl font-bold text-gray-800">최근 삭제 기록</h1>
          <span className="text-sm text-gray-500">({totalMembers}명)</span>
        </div>
      </div>

      {/* 검색 */}
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
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider w-28">이름</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider w-20">성별</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider w-36">전화번호</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider w-32">회원권</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider w-32">라커룸</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider w-28">회원복</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider w-40">삭제일시</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider w-40"></th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {loading ? (
                  <tr>
                    <td colSpan={8} className="px-6 py-12 text-center text-gray-500">
                      <div className="flex items-center justify-center">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                        <span className="ml-3">로딩 중...</span>
                      </div>
                    </td>
                  </tr>
                ) : members.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="px-6 py-16 text-center">
                      <div className="flex flex-col items-center justify-center">
                        <svg className="w-16 h-16 text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                        <p className="text-lg font-medium text-gray-500">삭제된 회원이 없습니다</p>
                        <p className="text-sm text-gray-400 mt-1">휴지통이 비어있습니다</p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  members.map((member) => (
                    <tr key={member.member_id} className="hover:bg-gray-50">
                      <td className="px-4 py-4 whitespace-nowrap text-sm font-semibold text-gray-900 text-center">{member.name}</td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm text-center">
                        {member.gender === 'M' ? (
                          <span className="inline-block px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded font-semibold">남</span>
                        ) : member.gender === 'F' ? (
                          <span className="inline-block px-2 py-1 text-xs bg-pink-100 text-pink-700 rounded font-semibold">여</span>
                        ) : (
                          <span className="inline-block px-2 py-1 text-xs bg-gray-100 text-gray-500 rounded">-</span>
                        )}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-600 text-center">{member.phone_number}</td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm text-center">
                        {member.membership_type ? (
                          <span className="inline-block px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded font-semibold">
                            {member.membership_type}
                          </span>
                        ) : (
                          <span className="inline-block px-2 py-1 text-xs bg-gray-100 text-gray-500 rounded">-</span>
                        )}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm text-center">
                        {member.locker_number ? (
                          <span className="inline-block px-2 py-1 text-xs bg-yellow-100 text-yellow-700 rounded font-semibold">
                            {member.locker_type}{member.locker_number ? ` (${member.locker_number}번)` : ' (미배정)'}
                          </span>
                        ) : (
                          <span className="inline-block px-2 py-1 text-xs bg-gray-100 text-gray-500 rounded">-</span>
                        )}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm text-center">
                        {member.uniform_type ? (
                          <span className="inline-block px-2 py-1 text-xs bg-purple-100 text-purple-700 rounded font-semibold">
                            {member.uniform_type}
                          </span>
                        ) : (
                          <span className="inline-block px-2 py-1 text-xs bg-gray-100 text-gray-500 rounded">-</span>
                        )}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm text-center text-gray-500">
                        {formatDate(member.deleted_at)}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm text-center">
                        <div className="flex items-center justify-center gap-2">
                          <button
                            onClick={() => handleRestoreMember(member.member_id, member.name)}
                            className="px-3 py-1.5 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors text-xs font-medium"
                            title="복원"
                          >
                            복원
                          </button>
                          <button
                            onClick={() => handlePermanentDelete(member.member_id, member.name)}
                            className="px-3 py-1.5 bg-red-600 text-white rounded hover:bg-red-700 transition-colors text-xs font-medium"
                            title="영구 삭제"
                          >
                            삭제
                          </button>
                        </div>
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
      
      {/* 하단 플로팅 버튼들 */}
      {totalMembers > 0 && (
        <>
          {/* 전체 비우기 버튼 (휴지통 아이콘) - 왼쪽 하단 */}
          <button
            onClick={handleDeleteAll}
            className="fixed bottom-8 left-8 w-16 h-16 bg-red-600 hover:bg-red-700 text-white rounded-full shadow-2xl hover:shadow-3xl transition-all duration-300 flex items-center justify-center group z-30"
            title="전체 비우기"
          >
            <svg 
              className="w-8 h-8 group-hover:scale-110 transition-transform duration-300" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>

          {/* 전체 복원 버튼 (동기화 아이콘) - 오른쪽 하단 */}
          <button
            onClick={handleRestoreAll}
            className="fixed bottom-8 right-8 w-16 h-16 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-2xl hover:shadow-3xl transition-all duration-300 flex items-center justify-center group z-30"
            title="전체 복원"
          >
            <svg 
              className="w-8 h-8 group-hover:scale-110 transition-transform duration-300" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </>
      )}
    </div>
  );
}
