import { useState, useEffect } from "react";
import NumericKeypad from "../components/NumericKeypad";
import { kioskService } from "../services/kioskService";
import { maskName, formatErrorMessage } from "../utils/userUtils";
import logo from '../assets/logo.png';


export default function UserApp() {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
 
  // 동명이인 후보 리스트
  // Candidate 타입도 Member 구조와 일치하도록 보완
  interface Candidate {
    id: number; // member_id
    name: string;
    phone_masked: string;
    gender?: 'M' | 'F'; // 성별 추가
    locker_type?: string | null;
    // 기타 필요한 필드 추가 가능
  }
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  // 선택된 후보 id
  const [selectedCandidateId, setSelectedCandidateId] = useState<number | null>(null);

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

  // 체크인 처리 (동명이인 분기 포함)
  // 체크인 로직을 kioskService로 통일
  const handleCheckin = async (candidateId?: number) => {
    if (input.length !== 4 && !candidateId) {
      setErrorMessage("전화번호 뒷자리 4자리를 입력해주세요.");
      return;
    }
    setLoading(true);
    setErrorMessage(null);
    setSuccessMessage(null);
    try {
      // 1. 동명이인 후보가 선택된 경우: memberId로 체크인/체크아웃 반복
      if (candidateId) {
        let member: any = undefined;
        try {
          const searchRes = await kioskService.searchByPhone(input);
          member = searchRes.members.find(m => m.member_id === candidateId);
        } catch {}
        const tryCheckIn = async () => {
          try {
            const response = await kioskService.checkIn(candidateId);
            if (response.status === 'success') {
              let msg = `✅ 출입이 확인되었습니다!\n\n${response.member_info?.name ?? '회원'}님\n입장 시간: ${new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}`;
              if (response.member_info?.membership_end_date) {
                const end = new Date(response.member_info.membership_end_date);
                const today = new Date();
                end.setHours(0,0,0,0); today.setHours(0,0,0,0);
                const daysLeft = Math.ceil((end.getTime() - today.getTime()) / (1000*60*60*24));
                if (daysLeft < 0) msg += `\n\n❗ 회원권이 만료되었습니다.`;
                else msg += `\n\n회원권 남은 일수: ${daysLeft}일`;
              }
              setSuccessMessage(msg);
            }
          } catch (error: any) {
            if (error?.response?.status === 400) {
              // 400 오류는 예외가 아니라 정상 분기(입장 상태 → 퇴장 시도)
              await tryCheckout();
            } else {
              setErrorMessage('알 수 없는 오류가 발생했습니다.');
            }
          }
        };
        const tryCheckout = async () => {
          try {
            const checkoutRes = await kioskService.checkout(candidateId);
            let msg = `✅ 퇴장이 확인되었습니다!\n\n${checkoutRes.member_name ?? '회원'}님\n퇴장 시간: ${checkoutRes.checkout_time ? new Date(checkoutRes.checkout_time).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' }) : '-'} `;
            if (checkoutRes.membership_end_date) {
              const end = new Date(checkoutRes.membership_end_date);
              const today = new Date();
              end.setHours(0,0,0,0); today.setHours(0,0,0,0);
              const daysLeft = Math.ceil((end.getTime() - today.getTime()) / (1000*60*60*24));
              if (daysLeft < 0) msg += `\n\n❗ 회원권이 만료되었습니다.`;
              else msg += `\n\n회원권 남은 일수: ${daysLeft}일`;
            }
            setSuccessMessage(msg);
          } catch (error: any) {
            // 400 오류(이미 퇴장 상태)는 정상 분기이므로 무시, 그 외만 예외 처리
            if (error?.response?.status !== 400) {
              setErrorMessage('퇴장 처리에 실패했습니다.');
            }
          }
        };
        if (member) {
          if (member.is_active) {
            await tryCheckout();
          } else {
            await tryCheckIn();
          }
        } else {
          await tryCheckIn();
        }
        setCandidates([]);
        setSelectedCandidateId(null);
      } else {
        // 2. 4자리 입력 후 후보 검색
        const searchRes = await kioskService.searchByPhone(input);
        if (searchRes.status === 'not_found') {
          setErrorMessage('등록된 회원이 없습니다.');
          setCandidates([]);
          setSelectedCandidateId(null);
        } else if (searchRes.status === 'duplicate' && searchRes.members.length > 1) {
          // 동명이인 후보 선택
          const candidates = searchRes.members.map(m => ({
            id: m.member_id,
            name: m.name,
            phone_masked: m.phone_number.slice(0,3) + '-****-' + m.phone_number.slice(-4)
          }));
          setCandidates(candidates);
          setSelectedCandidateId(null);
        } else if (searchRes.status === 'success' && searchRes.members.length === 1) {
          // 단일 회원이면 상태 판별 후 입장/퇴장 처리
          const member = searchRes.members[0];
          const tryCheckIn = async () => {
            try {
              const response = await kioskService.checkIn(member.member_id);
              if (response.status === 'success') {
                let msg = `✅ 출입이 확인되었습니다!\n\n${response.member_info?.name ?? '회원'}님\n입장 시간: ${new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}`;
                if (response.member_info?.membership_end_date) {
                  const end = new Date(response.member_info.membership_end_date);
                  const today = new Date();
                  end.setHours(0,0,0,0); today.setHours(0,0,0,0);
                  const daysLeft = Math.ceil((end.getTime() - today.getTime()) / (1000*60*60*24));
                  if (daysLeft < 0) msg += `\n\n❗ 회원권이 만료되었습니다.`;
                  else msg += `\n\n회원권 남은 일수: ${daysLeft}일`;
                }
                setSuccessMessage(msg);
              }
            } catch (error: any) {
              if (error?.response?.status === 400) {
                // 400 오류는 예외가 아니라 정상 분기(입장 상태 → 퇴장 시도)
                await tryCheckout();
              } else {
                setErrorMessage('알 수 없는 오류가 발생했습니다.');
              }
            }
          };
          const tryCheckout = async () => {
            try {
              const checkoutRes = await kioskService.checkout(member.member_id);
              let msg = `✅ 퇴장이 확인되었습니다!\n\n${checkoutRes.member_name ?? '회원'}님\n퇴장 시간: ${checkoutRes.checkout_time ? new Date(checkoutRes.checkout_time).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' }) : '-'} `;
              if (checkoutRes.membership_end_date) {
                const end = new Date(checkoutRes.membership_end_date);
                const today = new Date();
                end.setHours(0,0,0,0); today.setHours(0,0,0,0);
                const daysLeft = Math.ceil((end.getTime() - today.getTime()) / (1000*60*60*24));
                if (daysLeft < 0) msg += `\n\n❗ 회원권이 만료되었습니다.`;
                else msg += `\n\n회원권 남은 일수: ${daysLeft}일`;
              }
              setSuccessMessage(msg);
            } catch (error: any) {
              // 400 오류(이미 퇴장 상태)는 정상 분기이므로 무시, 그 외만 예외 처리
              if (error?.response?.status !== 400) {
                setErrorMessage('퇴장 처리에 실패했습니다.');
              }
            }
          };
          if (member.is_active) {
            await tryCheckout();
          } else {
            await tryCheckIn();
          }
          setCandidates([]);
          setSelectedCandidateId(null);
        }
      }
    } catch (error: any) {
      // 400 오류(입장/퇴장 중복)는 정상 분기이므로 info로만 출력, 그 외만 에러 메시지
      if (error?.response?.status === 400) {
        console.info('정상 분기(입장/퇴장 중복):', error);
      } else {
        console.error('체크인 실패:', error);
        setErrorMessage(formatErrorMessage(error));
      }
      setCandidates([]);
      setSelectedCandidateId(null);
    } finally {
      setLoading(false);
    }
  };

  // 폼 초기화
  const resetForm = () => {
    setInput("");
    setCandidates([]);
    setSelectedCandidateId(null);
  };

  return (
    <div className="flex h-screen bg-gray-900 overflow-hidden">
      
       {/* 좌측: 이미지 + 유튜브 영상 */}
      <div className="w-[60%] h-full relative flex flex-col overflow-hidden">

        {/* 상단 배너 고정 */}
        <div className="w-full h-64 bg-gradient-to-r from-black via-gray-900 to-black flex items-center justify-center shrink-0 border-b-2 border-gray-800">
          <div className="text-center flex items-center justify-center gap-6">
            <img src={logo} alt="GYM Logo" className="h-500 w-auto drop-shadow-[0_0_32px_#39FF14bb] align-middle" />
          </div>
        </div>

          {/* 남는 영역에 유튜브 영상 */}
          <div className="flex-1 flex items-center justify-center bg-black">
            <iframe
              width="100%"
              height="100%"
              src="https://www.youtube.com/embed/wTc7pfHbNtQ?autoplay=1&mute=1"
              title="YouTube video player"
              frameBorder="0"
              allow="autoplay; encrypted-media"
              allowFullScreen
              style={{ borderRadius: '16px', maxWidth: 960, minHeight: 320 }}
            ></iframe>
          </div>
        <div className="absolute inset-0 bg-gradient-to-r from-black/50 to-transparent" />
        
        {/* 체육관 로고/이름 오버레이 */}
        <div className="absolute top-12 left-12 text-white">
          <h1 className="text-6xl font-bold mb-3 drop-shadow-lg">
            GYM TO PT
          </h1>
          <p className="text-2xl opacity-90 drop-shadow-md">
            완벽한 몸을 만들때까지
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
        <div className="bg-gradient-to-r from-gray-600 to-gray-700 text-white p-6 shadow-lg">
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

        {/* 입력 영역 및 동명이인 후보 선택 */}
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
          {/* 동명이인 후보 선택 모달 */}
          {candidates.length > 0 && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
              <div className="bg-white rounded-2xl shadow-2xl p-8 min-w-[340px] max-w-xs w-full flex flex-col items-center">
                <div className="mb-4 text-lg font-bold text-gray-800">여러 명의 회원이 검색되었습니다.<br/>본인 이름과 전화번호를 선택하세요.</div>
                <ul className="w-full space-y-3 mb-4">
                  {candidates.map(c => (
                    <li key={c.id}>
                      <button
                        className={`w-full px-4 py-3 rounded-lg border-2 text-lg font-bold flex items-center justify-between ${selectedCandidateId === c.id ? 'bg-blue-600 text-white border-blue-700' : 'bg-white border-gray-300 text-gray-800'} transition`}
                        onClick={() => setSelectedCandidateId(c.id)}
                        disabled={loading}
                      >
                        <span>{maskName(c.name)}</span>
                        <span className="ml-4 text-base font-mono">{c.phone_masked}</span>
                      </button>
                    </li>
                  ))}
                </ul>
                <button
                  className="w-full py-3 rounded-lg bg-blue-700 text-white font-bold text-xl disabled:opacity-50"
                  disabled={!selectedCandidateId || loading}
                  onClick={() => handleCheckin(selectedCandidateId!)}
                >
                  본인 선택 후 출입 확인
                </button>
              </div>
            </div>
          )}
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
            onEnter={() => handleCheckin()}
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
