// 이름 마스킹 함수
export function maskName(name: string): string {
  if (name.length === 2) return name[0] + '○';
  if (name.length > 2) return name[0] + '○' + name[name.length - 1];
  return name;
}

// 에러 메시지 가공 함수 (FastAPI 422 등 대응)
export function formatErrorMessage(error: any): string {
  const detail = error?.response?.data?.detail;
  if (!detail) return "체크인에 실패했습니다.\n프론트 데스크에 문의하세요.";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    // FastAPI validation error 배열 처리
    return detail.map((e: any) => `${e.loc?.join('.')}: ${e.msg}`).join('\n');
  }
  return JSON.stringify(detail);
}
