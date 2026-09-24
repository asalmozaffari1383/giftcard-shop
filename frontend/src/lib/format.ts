const persianDigits = "۰۱۲۳۴۵۶۷۸۹";

export function toPersianDigits(value: string | number) {
  return String(value).replace(/\d/g, (digit) => persianDigits[Number(digit)]);
}

export function formatToman(value: number) {
  return `${new Intl.NumberFormat("fa-IR").format(value)} تومان`;
}

export function normalizeIranianPhone(value: string) {
  const latin = value.replace(/[۰-۹]/g, (digit) => String(persianDigits.indexOf(digit))).replace(/\s|-/g, "");
  if (latin.startsWith("09")) return `+98${latin.slice(1)}`;
  if (latin.startsWith("989")) return `+${latin}`;
  return latin;
}

export const orderStatus: Record<string, string> = {
  PENDING: "در انتظار پرداخت", PROCESSING: "در حال پردازش", COMPLETED: "تکمیل‌شده",
  FAILED: "ناموفق", REFUNDED: "بازپرداخت‌شده",
};

export const ticketStatus: Record<string, string> = { OPEN: "باز", WAITING: "در انتظار پاسخ", CLOSED: "بسته" };

export function mediaUrl(value: string | null) {
  if (!value || value.startsWith("http://") || value.startsWith("https://")) return value;
  const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
  return `${new URL(api).origin}${value.startsWith("/") ? value : `/${value}`}`;
}
