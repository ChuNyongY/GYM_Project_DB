import { useState } from "react";
import { adminService } from "../services/adminService";

// 작은 비밀번호 변경 창을 같은 파일에 둡니다 (새 파일 생성하지 않음)
function ChangeAdminPassword({ onClose }: { onClose: () => void }) {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmNewPassword, setConfirmNewPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (newPassword !== confirmNewPassword) {
      setError("새 비밀번호가 일치하지 않습니다.");
      return;
    }

    if (!currentPassword || !newPassword) {
      setError("모든 항목을 입력해주세요.");
      return;
    }

    setLoading(true);
    try {
      // 만약 현재 세션에 admin token이 없으면, 현재 비밀번호로 로그인 시도
      const existingToken = sessionStorage.getItem('admin_token');
      if (!existingToken) {
        try {
          const loginResp = await adminService.login(currentPassword);
          if (loginResp?.status === 'success' && loginResp.token) {
            sessionStorage.setItem('admin_token', loginResp.token);
          } else {
            setError('현재 비밀번호로 인증에 실패했습니다.');
            setLoading(false);
            return;
          }
        } catch (loginErr: any) {
          console.error('Login before change failed', loginErr);
          setError(loginErr.response?.data?.detail || '현재 비밀번호가 일치하지 않습니다.');
          setLoading(false);
          return;
        }
      }

      const res = await adminService.changePassword(currentPassword, newPassword);
      if (res && res.status === "success") {
        setSuccess("비밀번호가 변경되었습니다.");
        setTimeout(() => onClose(), 800);
      } else {
        setError(res?.message || "비밀번호 변경에 실패했습니다.");
      }
    } catch (err: any) {
      console.error('Change password error', err);
      setError(err.response?.data?.detail || '비밀번호 변경 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black opacity-30" onClick={onClose} />

      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6 z-10">
        <h2 className="text-lg font-semibold mb-4">관리자 비밀번호 변경</h2>
        <form onSubmit={submit} className="space-y-3">
          <div>
            <label className="block text-sm text-gray-700 mb-1">현재 비밀번호</label>
            <input
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              className="w-full px-3 py-2 border rounded-md"
              disabled={loading}
            />
          </div>

          <div>
            <label className="block text-sm text-gray-700 mb-1">새 비밀번호</label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="w-full px-3 py-2 border rounded-md"
              disabled={loading}
            />
          </div>

          <div>
            <label className="block text-sm text-gray-700 mb-1">새 비밀번호 확인</label>
            <input
              type="password"
              value={confirmNewPassword}
              onChange={(e) => setConfirmNewPassword(e.target.value)}
              className="w-full px-3 py-2 border rounded-md"
              disabled={loading}
            />
          </div>

              {error && <div className="text-sm text-red-600">{error}</div>}
              {success && <div className="text-sm text-green-600">{success}</div>}

              <div className="flex justify-end gap-2 mt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-md border bg-white"
              disabled={loading}
            >
              취소
            </button>
            <button
              type="submit"
              className="px-4 py-2 rounded-md bg-blue-600 text-white"
              disabled={loading}
            >
              {loading ? '처리중...' : '변경'}
            </button>
          </div>
        </form>
        
      </div>
    </div>
  );
}

interface AdminLoginProps {
  onAuth: () => void;
}

export default function AdminLogin({ onAuth }: AdminLoginProps) {
  const [pw, setPw] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showChangeModal, setShowChangeModal] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await adminService.login(pw);
      
      if (response.status === "success" && response.token) {
        sessionStorage.setItem('admin_token', response.token);
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
            <div className="relative">
              <input
                type="password"
                value={pw}
                onChange={(e) => setPw(e.target.value)}
                placeholder="관리자 비밀번호"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                autoFocus
                disabled={loading}
              />
              <button
                type="button"
                aria-label="비밀번호 변경"
                onClick={() => setShowChangeModal(true)}
                className="absolute right-2 top-1/2 -translate-y-1/2 bg-transparent p-2 rounded-md hover:bg-gray-100"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-blue-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 1v2" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 21v2" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4.22 4.22l1.42 1.42" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M18.36 18.36l1.42 1.42" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M1 12h2" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21 12h2" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4.22 19.78l1.42-1.42" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M18.36 5.64l1.42-1.42" />
                  <circle cx="12" cy="12" r="3" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>
            </div>
          </div>
          
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-blue-600 to-blue-700 text-white font-semibold py-3 rounded-lg hover:from-blue-700 hover:to-blue-800 transition-all duration-200 shadow-lg hover:shadow-xl disabled:opacity-50"
          >
            {loading ? "로그인 중..." : "입장하기"}
          </button>
        </form>
        {showChangeModal && (
          <ChangeAdminPassword onClose={() => setShowChangeModal(false)} />
        )}
      </div>
    </div>
  );
}