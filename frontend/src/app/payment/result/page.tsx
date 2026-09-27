"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { ErrorState, LoadingState } from "@/components/states";
import { Icon, StatusPill } from "@/components/ui";
import { apiFetch } from "@/lib/api";
import { formatToman } from "@/lib/format";
import type { Payment } from "@/lib/types";

const paymentConfig: Record<string, { title:string; text:string; tone:"success"|"warning"|"danger"; icon:"check"|"clock"|"x" }> = {
  VERIFIED: { title:"پرداخت با موفقیت تأیید شد", text:"سفارش تکمیل شده و کد دیجیتال در جزئیات سفارش قابل مشاهده است.", tone:"success", icon:"check" },
  READY: { title:"پرداخت هنوز تکمیل نشده", text:"اگر از درگاه بازگشته‌ای، چند لحظه صبر کن و وضعیت را دوباره بررسی کن.", tone:"warning", icon:"clock" },
  INITIATING: { title:"در حال آماده‌سازی پرداخت", text:"درخواست پرداخت هنوز نهایی نشده است.", tone:"warning", icon:"clock" },
  FAILED: { title:"پرداخت ناموفق یا لغوشده", text:"مبلغی تأیید نشده است. می‌توانی از سفارش‌ها دوباره وضعیت را بررسی کنی.", tone:"danger", icon:"x" },
  RECONCILIATION: { title:"پرداخت نیازمند بررسی است", text:"تراکنش ثبت شده و تیم پشتیبانی باید وضعیت آن را بررسی کند.", tone:"warning", icon:"clock" },
};

export default function PaymentResultPage() {
  const params = useSearchParams(); const paymentId = params.get("payment_id"); const [payment, setPayment] = useState<Payment | null>(null); const [loading, setLoading] = useState(Boolean(paymentId)); const [error, setError] = useState(paymentId ? "" : "شناسه پرداخت در آدرس وجود ندارد.");
  const load = () => { if (!paymentId) return; setLoading(true); apiFetch<Payment>(`/payments/${paymentId}/`).then(setPayment).catch((caught) => setError(caught instanceof Error ? caught.message : "وضعیت پرداخت دریافت نشد")).finally(() => setLoading(false)); };
  useEffect(load, [paymentId]);
  if (loading) return <div className="container page-shell"><LoadingState text="در حال بررسی نتیجه پرداخت..."/></div>; if (error || !payment) return <div className="container page-shell"><ErrorState message={error || "پرداخت یافت نشد"} retry={paymentId ? load : undefined}/></div>;
  const config = paymentConfig[payment.status] || paymentConfig.READY;
  return <div className="container page-shell result-shell"><div className={`result-card ${config.tone}`}><div className="result-icon"><Icon name={config.icon} size={38}/></div><StatusPill tone={config.tone}>{payment.status === "VERIFIED" ? "تأییدشده" : payment.status === "FAILED" ? "ناموفق" : "در حال بررسی"}</StatusPill><h1>{config.title}</h1><p>{config.text}</p><div className="result-details"><div><span>مبلغ تراکنش</span><b>{formatToman(payment.amount_toman)}</b></div><div><span>شماره پیگیری</span><b>{payment.reference_id || "هنوز صادر نشده"}</b></div><div><span>درگاه</span><b>{payment.gateway}</b></div></div><div className="result-actions"><Link className="button primary large" href={`/orders/${payment.order}`}>مشاهده سفارش {payment.status === "VERIFIED" && "و دریافت کد"}<Icon name="arrow-left"/></Link>{payment.status !== "VERIFIED" && <button className="button secondary large" onClick={load}><Icon name="clock"/> بررسی دوباره</button>}<Link className="button ghost" href="/orders">همه سفارش‌ها</Link></div></div></div>;
}
