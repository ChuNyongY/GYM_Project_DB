import { useState, useEffect } from "react";
import NumericKeypad from "../components/NumericKeypad.tsx";
import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

export default function UserApp() {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // 성공 메시지 자동 숨김
  useEffect(() => {
    if (successMessage) {
      const timer = setTimeout(() => {
        setSuccessMessage(null);
        resetForm();
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [successMessage]);

  // 에러 메시지 자동 숨김
  useEffect(() => {
    if (errorMessage) {
      const timer = setTimeout(() => {
        setErrorMessage(null);
        resetForm();
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [errorMessage]);

  // 체크인 처리 ⭐ 완전히 새로 작성
  const handleCheckin = async () => {
    if (input.length !== 4) {
      setErrorMessage("전화번호 뒷자리 4자리를 입력해주세요.");
      return;
    }

    setLoading(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      // ⭐ 직접 체크인 API 호출
      const response = await axios.post(`${API_BASE_URL}/checkin`, {
        phone_last_four: input
      });

      if (response.data.status === 'success') {
        const memberName = response.data.member.name;
        
        // ⭐ 환영 메시지 표시
        setSuccessMessage(
          `✅ 출입이 확인되었습니다!\n\n${memberName}님\n입장 시간: ${new Date().toLocaleTimeString('ko-KR', { 
            hour: '2-digit', 
            minute: '2-digit' 
          })}`
        );
      }
    } catch (error: any) {
      console.error('체크인 실패:', error);
      const errorMsg = error.response?.data?.detail || "체크인에 실패했습니다.\n프론트 데스크에 문의하세요.";
      setErrorMessage(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  // 폼 초기화
  const resetForm = () => {
    setInput("");
  };

  return (
    <div className="flex h-screen bg-gray-900 overflow-hidden">
      {/* 좌측: 이미지 */}
      <div className="w-[60%] h-full relative flex flex-col overflow-hidden">
        <div className="w-full h-64 bg-gradient-to-r from-blue-500 via-blue-600 to-blue-700 flex items-center justify-center">
          <div className="text-center">
            <h1 className="text-white text-7xl font-bold mb-2">💪 GYM</h1>
            <p className="text-blue-100 text-2xl font-semibold">Health & Fitness Center</p>
          </div>
        </div>
        <div className="absolute inset-0 bg-gradient-to-r from-black/50 to-transparent" />
        
        {/* 체육관 로고/이름 오버레이 */}
        <div className="absolute top-12 left-12 text-white">
          <h1 className="text-6xl font-bold mb-3 drop-shadow-lg">
            FITNESS CENTER
          </h1>
          <p className="text-2xl opacity-90 drop-shadow-md">
            건강한 당신을 응원합니다 💪
          </p>
        </div>

        {/* 현재 시간 표시 */}
        <div className="absolute bottom-12 left-12 text-white z-50">
          <p className="text-4xl font-bold drop-shadow-lg">
            {new Date().toLocaleTimeString('ko-KR', { 
              hour: '2-digit', 
              minute: '2-digit' 
            })}
          </p>
          <p className="text-sm opacity-80 drop-shadow-md">
            {new Date().toLocaleDateString('ko-KR', { 
              year: 'numeric',
              month: 'long',
              day: 'numeric',
              weekday: 'long'
            })}
          </p>
        </div>
      </div>

      {/* 우측: 패널 */}
      <div className="w-[40%] bg-white flex flex-col shadow-2xl relative overflow-y-auto">
        {/* 성공 메시지 오버레이 */}
        {successMessage && (
          <div className="absolute inset-0 bg-green-500/95 backdrop-blur-sm z-50 flex items-center justify-center animate-pulse-once">
            <div className="text-white text-center p-8">
              <div className="text-7xl mb-6">✅</div>
              <p className="text-3xl font-bold whitespace-pre-line leading-relaxed">
                {successMessage}
              </p>
            </div>
          </div>
        )}

        {/* 에러 메시지 오버레이 */}
        {errorMessage && (
          <div className="absolute inset-0 bg-red-500/95 backdrop-blur-sm z-50 flex items-center justify-center">
            <div className="text-white text-center p-8">
              <div className="text-7xl mb-6">❌</div>
              <p className="text-3xl font-bold whitespace-pre-line leading-relaxed">
                {errorMessage}
              </p>
            </div>
          </div>
        )}

        {/* 공지사항 헤더 */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-6 shadow-lg">
          <h2 className="text-2xl font-bold mb-3">공지사항</h2>
          <div className="space-y-2 text-sm leading-relaxed">
            <p className="flex items-center gap-2">
              <span className="text-xl">✓</span> 출입체크
            </p>
            <p className="flex items-center gap-2">
              <span className="text-xl">✓</span> 휴대폰 끝 4자리 입력 후 확인
            </p>
            <div className="mt-3 text-xs bg-white/10 p-3 rounded-lg">
              <p className="font-semibold">회원님, 입력 후 확인을 눌러주세요</p>
            </div>
          </div>
        </div>

        {/* 입력 영역 */}
        <div className="p-6 bg-gradient-to-b from-gray-50 to-white border-b border-gray-200">
          <label className="block text-sm font-semibold text-gray-700 mb-3">
            회원번호를 터치하세요 (Please enter your ID)
          </label>
          
          <div className="relative">
            <input
              value={input}
              readOnly
              placeholder="휴대폰 끝 4자리"
              className="w-full px-6 py-5 text-4xl text-center font-bold bg-white border-2 border-gray-300 rounded-xl focus:outline-none focus:border-blue-500 tracking-[0.5em] shadow-inner"
            />
            {input.length > 0 && (
              <div className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 text-sm">
                {input.length}/4
              </div>
            )}
          </div>

          {/* 로딩 인디케이터 */}
          {loading && (
            <div className="mt-3 flex items-center justify-center text-blue-600">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600 mr-2"></div>
              <span className="text-sm font-semibold">처리 중...</span>
            </div>
          )}
        </div>

        {/* 키패드 영역 */}
        <div className="flex-1 p-6 flex flex-col justify-center">
          <NumericKeypad
            value={input}
            onChange={setInput}
            onEnter={handleCheckin}
            onClear={resetForm}
            disabled={loading}
            maxLength={4}
          />
        </div>

        {/* 하단 안내 */}
        <div className="p-6 bg-gradient-to-b from-yellow-50 to-yellow-100 border-t-2 border-yellow-200">
          <div className="bg-white border-2 border-yellow-300 rounded-xl p-4 shadow-sm">
            <p className="font-bold text-gray-800 mb-2 text-sm flex items-center gap-2">
              <span className="text-2xl">💡</span>
              <span>헬스장 입장할 때 꼭!!! 해주세요.</span>
            </p>
            <div className="text-xs text-gray-700 space-y-1.5 ml-8">
              <p className="flex items-center gap-2">
                <span className="w-5 h-5 bg-blue-500 text-white rounded-full flex items-center justify-center text-[10px] font-bold">1</span>
                회원님 휴대폰 끝 4자리 입력 (예: 1234)
              </p>
              <p className="flex items-center gap-2">
                <span className="w-5 h-5 bg-blue-500 text-white rounded-full flex items-center justify-center text-[10px] font-bold">2</span>
                확인 버튼 클릭 (F8 또는 Enter)
              </p>
              <p className="flex items-center gap-2">
                <span className="w-5 h-5 bg-green-500 text-white rounded-full flex items-center justify-center text-[10px] font-bold">✓</span>
                입장 완료!
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}