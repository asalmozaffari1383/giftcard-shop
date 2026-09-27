"use client";
import { use, useEffect, useState } from "react";
import Link from "next/link";
import { ErrorState, LoadingState } from "@/components/states";
import { Icon, StatusPill } from "@/components/ui";
import { useToast } from "@/contexts/app-context";
import { apiFetch } from "@/lib/api";
import { formatToman, orderStatus, toPersianDigits } from "@/lib/format";
import type { Order } from "@/lib/types";

const toneFor = (status:string) => status === "COMPLETED" ? "success" : status === "FAILED" || status === "REFUNDED" ? "danger" : "warning";
export default function OrderDetailPage({ params }: { params: Promise<{ id:string }> }) {
  const { id } = use(params); const [order, setOrder] = useState<Order | null>(null); const [loading, setLoading] = useState(true); const [error, setError] = useState(""); const toast = useToast();
  const load = () => { setLoading(true); setError(""); apiFetch<Order>(`/orders/${id}/`).then(setOrder).catch((caught) => setError(caught instanceof Error ? caught.message : "خطا")).finally(() => setLoading(false)); };
  useEffect(load, [id]); const copy = async (code:string) => { await navigator.clipboard.writeText(code); toast("کد با موفقیت کپی شد"); };
  if (loading) return <div className="container page-shell"><LoadingState text="در حال دریافت جزئیات سفارش..."/></div>; if (error || !order) return <div className="container page-shell"><ErrorState message={error || "سفارش یافت نشد"} retry={load}/></div>;
  const codes = order.items.flatMap((item) => item.codes);
  return <div className="container page-shell"><nav className="breadcrumbs"><Link href="/orders">سفارش‌ها</Link><Icon name="chevron-left" size={14}/><span>#{order.id.slice(0,8).toUpperCase()}</span></nav><section className={`order-hero ${order.status.toLowerCase()}`}><div className="result-icon"><Icon name={order.status === "COMPLETED" ? "check" : order.status === "FAILED" ? "x" : "clock"} size={32}/></div><div><StatusPill tone={toneFor(order.status)}>{orderStatus[order.status]}</StatusPill><h1>{order.status === "COMPLETED" ? "سفارش آماده استفاده است" : order.status === "PENDING" ? "در انتظار تکمیل پرداخت" : "وضعیت سفارش در حال پیگیری است"}</h1><p>سفارش #{order.id.slice(0,8).toUpperCase()} · ثبت در {order.created_at_jalali}</p></div></section>
    <div className="order-detail-layout"><main><section className="order-section"><div className="order-section-head"><div><span className="icon-box"><Icon name="bag"/></span><h2>اقلام سفارش</h2></div><span>{toPersianDigits(order.items.length)} ردیف</span></div>{order.items.map((item) => <article className="order-product" key={item.id}><span className="cart-thumb">{item.sku.slice(0,1)}</span><div><b>{item.sku}</b><small>تعداد {toPersianDigits(item.quantity)}</small></div><strong>{formatToman(item.unit_price_toman * item.quantity)}</strong></article>)}</section>
      {order.status === "COMPLETED" && <section className="order-section delivered-section"><div className="order-section-head"><div><span className="icon-box success"><Icon name="ticket"/></span><h2>کدهای تحویل‌شده</h2></div><StatusPill tone="success"><Icon name="shield" size={14}/> نمایش امن</StatusPill></div><p className="section-caption">این کدها را در محل امن نگهداری کن و در اختیار دیگران قرار نده.</p>{codes.length ? <div className="delivered-codes">{order.items.flatMap((item) => item.codes.map((code,index) => <div className="code-card" key={`${item.id}-${index}`}><div><small>{item.sku}</small><code>{code}</code></div><button onClick={() => void copy(code)} aria-label="کپی کد"><Icon name="copy"/><span>کپی</span></button></div>))}</div> : <div className="processing-code"><span className="button-spinner"/><div><b>کد در حال آماده‌سازی است</b><small>چند لحظه دیگر وضعیت را به‌روزرسانی کن.</small></div></div>}</section>}</main>
      <aside className="order-summary"><h2>صورتحساب</h2><div className="summary-row"><span>جمع اولیه</span><b>{formatToman(order.subtotal_toman)}</b></div><div className="summary-row"><span>تخفیف</span><b className="success-text">{order.discount_toman ? `− ${formatToman(order.discount_toman)}` : "بدون تخفیف"}</b></div><div className="summary-row"><span>تحویل دیجیتال</span><b className="success-text">رایگان</b></div><div className="summary-total"><span>مبلغ نهایی</span><strong>{formatToman(order.total_toman)}</strong></div><button className="button secondary full" onClick={load}><Icon name="clock"/> به‌روزرسانی وضعیت</button><Link className="button ghost full" href={`/tickets?order=${order.id}`}><Icon name="headset"/> پشتیبانی این سفارش</Link></aside></div>
  </div>;
}
