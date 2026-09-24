"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { ErrorState, LoadingState } from "@/components/states";
import { apiFetch } from "@/lib/api";
import { formatToman } from "@/lib/format";
import type { Payment } from "@/lib/types";

export default function PaymentResultPage() {
  const params = useSearchParams(); const paymentId = params.get("payment_id"); const [payment, setPayment] = useState<Payment | null>(null); const [loading, setLoading] = useState(Boolean(paymentId)); const [error, setError] = useState(paymentId ? "" : "شناسه پرداخت در آدرس وجود ندارد.");
  useEffect(() => { if (!paymentId) return; apiFetch<Payment>(`/payments/${paymentId}/`).then(setPayment).catch((caught) => setError(caught instanceof Error ? caught.message : "وضعیت پرداخت دریافت نشد")).finally(() => setLoading(false)); }, [paymentId]);
  if (loading) return <div className="container section"><LoadingState text="در حال بررسی نتیجه پرداخت..." /></div>; if (error || !payment) return <div className="container section"><ErrorState message={error || "پرداخت یافت نشد"} /></div>;
  const successful = payment.status === "VERIFIED" || payment.status === "SUCCESS";
  return <div className="container section"><div className="panel auth-card text-center"><div className={`empty-icon ${successful ? "" : "muted"}`}>{successful ? "✓" : "!"}</div><h1>{successful ? "پرداخت موفق بود" : "پرداخت هنوز تأیید نشده"}</h1><p>{formatToman(payment.amount_toman)}</p>{payment.reference_id && <p>شماره پیگیری: <b>{payment.reference_id}</b></p>}<div className="hero-actions"><Link className="button" href={`/orders/${payment.order}`}>مشاهده سفارش و کدها</Link><Link className="button secondary" href="/orders">همه سفارش‌ها</Link></div></div></div>;
}
