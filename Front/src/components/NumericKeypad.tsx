import { useState, useEffect } from "react";

type Props = {
  value: string;
  onChange: (v: string) => void;
  onEnter: () => void;
  onClear: () => void;
  disabled?: boolean;
  maxLength?: number;
};

export default function NumericKeypad({ 
  value, 
  onChange, 
  onEnter, 
  onClear,
  disabled = false,
  maxLength = 10 
}: Props) {
  const push = (k: string) => {
    if (!disabled && value.length < maxLength) {
      onChange(value + k);
    }
  };
  
  const back = () => {
    if (!disabled) {
      onChange(value.slice(0, -1));
    }
  };

  // 키보드 이벤트 처리
  const handleKeyDown = (e: KeyboardEvent) => {
    if (disabled) return;

    if (e.key >= '0' && e.key <= '9') {
      push(e.key);
    } else if (e.key === 'Backspace') {
      back();
    } else if (e.key === 'Enter' || e.key === 'F8') {
      e.preventDefault();
      onEnter();
    } else if (e.key === 'Escape') {
      onClear();
    }
  };

  // 키보드 이벤트 리스너 등록
  useState(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  });

  return (
    <div className="grid grid-cols-3 gap-3">
      {/* 숫자 버튼 1-9 */}
      {["1", "2", "3", "4", "5", "6", "7", "8", "9"].map((k) => (
        <button
          key={k}
          onClick={() => push(k)}
          disabled={disabled}
          className="keypad-btn h-20 text-3xl font-bold bg-white hover:bg-gray-50 text-gray-800 
                     rounded-xl border-2 border-gray-300 transition-all transform active:scale-95 
                     shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {k}
        </button>
      ))}

      {/* 확인 버튼 (F8) */}
      <button
        onClick={onEnter}
        disabled={disabled}
        className="keypad-btn keypad-btn-action h-20 flex flex-col items-center justify-center
                   bg-gradient-to-b from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700
                   text-white rounded-xl font-bold transition-all transform active:scale-95 
                   shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <span className="text-xl">확인</span>
        <span className="text-xs opacity-90 mt-1">(F8)</span>
      </button>

      {/* 0 버튼 */}
      <button
        onClick={() => push("0")}
        disabled={disabled}
        className="keypad-btn h-20 text-3xl font-bold bg-white hover:bg-gray-50 text-gray-800 
                   rounded-xl border-2 border-gray-300 transition-all transform active:scale-95 
                   shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
      >
        0
      </button>

      {/* 취소 버튼 (Esc) */}
      <button
        onClick={onClear}
        disabled={disabled}
        className="keypad-btn keypad-btn-action h-20 flex flex-col items-center justify-center
                   bg-gradient-to-b from-red-500 to-red-600 hover:from-red-600 hover:to-red-700
                   text-white rounded-xl font-bold transition-all transform active:scale-95 
                   shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <span className="text-xl">취소</span>
        <span className="text-xs opacity-90 mt-1">(Esc)</span>
      </button>

      {/* 지우기 버튼 (전체 너비) */}
      <button
        onClick={back}
        disabled={disabled}
        className="col-span-3 keypad-btn h-16 text-xl font-semibold
                   bg-gradient-to-r from-gray-400 to-gray-500 hover:from-gray-500 hover:to-gray-600
                   text-white rounded-xl transition-all transform active:scale-95 
                   shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed
                   flex items-center justify-center gap-2"
      >
        <span className="text-2xl">←</span>
        <span>지우기 (Backspace)</span>
      </button>
    </div>
  );
}