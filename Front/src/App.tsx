
import { Routes, Route, Navigate } from "react-router-dom";
import { useState, useEffect } from "react";
import UserApp from "./pages/UserApp.tsx";
import AdminDashboard from "./components/AdminDashboard.tsx";
import AdminLogin from "./components/AdminLogin.tsx";

export default function App() {
  // 관리자 인증 상태 관리
  const [isAdminAuthed, setIsAdminAuthed] = useState(false);

  // 새로고침 시 세션 유지
  useEffect(() => {
    const token = sessionStorage.getItem('admin_token');
    setIsAdminAuthed(!!token);
  }, []);

  // 관리자 라우트 element
  const adminElement = isAdminAuthed ? (
    <AdminDashboard onLogout={() => {
      sessionStorage.removeItem('admin_token');
      setIsAdminAuthed(false);
    }} />
  ) : (
    <AdminLogin onAuth={() => setIsAdminAuthed(true)} />
  );

  return (
    <Routes>
      {/* 기본 경로 - 키오스크로 리다이렉트 */}
      <Route path="/" element={<Navigate to="/kiosk" replace />} />

      {/* 회원용 키오스크 */}
      <Route path="/kiosk" element={<UserApp />} />
      <Route path="/user" element={<Navigate to="/kiosk" replace />} />

      {/* 관리자 페이지: 로그인 → 대시보드 순차 플로우 */}
      <Route path="/admin/*" element={adminElement} />

      {/* 404 페이지 */}
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}

// 404 Not Found 페이지
function NotFound() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-12 max-w-md w-full text-center">
        <div className="text-8xl mb-6">🤔</div>
        <h1 className="text-4xl font-bold text-gray-800 mb-4">404</h1>
        <p className="text-gray-600 mb-8">
          페이지를 찾을 수 없습니다.
        </p>
        <div className="space-y-3">
          <a
            href="/kiosk"
            className="block w-full px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white font-semibold rounded-lg hover:from-blue-700 hover:to-blue-800 transition-all"
          >
            키오스크로 이동
          </a>
          <a
            href="/admin"
            className="block w-full px-6 py-3 bg-gradient-to-r from-gray-600 to-gray-700 text-white font-semibold rounded-lg hover:from-gray-700 hover:to-gray-800 transition-all"
          >
            관리자 페이지로 이동
          </a>
        </div>
      </div>
    </div>
  );
}