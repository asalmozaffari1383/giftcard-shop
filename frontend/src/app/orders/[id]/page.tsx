"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { ErrorState, LoadingState } from "@/components/states";
import { useToast } from "@/contexts/app-context";
import { apiFetch } from "@/lib/api";
import { formatToman, orderStatus } from "@/lib/format";
import type { Order } from "@/lib/types";

export default function OrderDetailPage({ params }: { params: Promise<{ id:string }> }) {
  const { id } = use(params); const [order, setOrder] = useState<Order | null>(null); const [loading, setLoading] = useState(true); const [error, setError] = useState(""); const toast = useToast();
  const load = () => { setLoading(true); apiFetch<Order>(`/orders/${id}/`).then(setOrder).catch((caught) => setError(caught instanceof Error ? caught.message : "خطا")).finally(() => setLoading(false)); };
  useEffect(load, [id]); const copy = async (code:string) => { await navigator.clipboard.writeText(code); toast("کد کپی شد"); };
  if (loading) return <div className="container section"><LoadingState /></div>; if (error || !order) return <div className="container section"><ErrorState message={error || "سفارش یافت نشد"} /></div>;
  return <div className="container section"><div className="section-head"><div><h1>جزئیات سفارش</h1><p dir="ltr">{order.id}</p></div><span className={`status ${order.status}`}>{orderStatus[order.status]}</span></div><div className="panel"><div className="summary-row"><span>تاریخ ثبت</span><b>{order.created_at_jalali}</b></div><div className="summary-row"><span>جمع اولیه</span><b>{formatToman(order.subtotal_toman)}</b></div><div className="summary-row"><span>تخفیف</span><b>{formatToman(order.discount_toman)}</b></div><div className="summary-row total"><span>مبلغ سفارش</span><b>{formatToman(order.total_toman)}</b></div></div>{order.status === "PENDING" && <div className="alert error">پرداخت این سفارش هنوز تأیید نشده است.</div>}<div className="order-items">{order.items.map((item) => <div className="panel" key={item.id}><div className="list-card"><div><h3>{item.sku}</h3><p>تعداد {item.quantity}</p></div><strong>{formatToman(item.unit_price_toman * item.quantity)}</strong></div>{item.codes.map((code, index) => <div className="code-box" key={`${item.id}-${index}`}><code>{code}</code><button className="button small" onClick={() => void copy(code)}>کپی</button></div>)}{order.status === "COMPLETED" && !item.codes.length && <p className="muted">کد در حال آماده‌سازی است؛ چند لحظه دیگر صفحه را تازه کنید.</p>}</div>)}</div><div className="hero-actions"><button className="button secondary" onClick={load}>به‌روزرسانی وضعیت</button><Link className="button secondary" href={`/tickets?order=${order.id}`}>پشتیبانی این سفارش</Link></div></div>;
}
