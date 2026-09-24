"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { EmptyState, LoadingState } from "@/components/states";
import { useAuth, useCart } from "@/contexts/app-context";
import { apiFetch } from "@/lib/api";
import { formatToman } from "@/lib/format";
import type { Order, Payment } from "@/lib/types";

function stableKey(name: string) { const saved = sessionStorage.getItem(name); if (saved) return saved; const key = `${name}-${crypto.randomUUID()}`; sessionStorage.setItem(name, key); return key; }

export default function CheckoutPage() {
  const { user, loading: authLoading } = useAuth(); const { items, total, clearLocalCart } = useCart(); const [coupon, setCoupon] = useState(""); const [loading, setLoading] = useState(false); const [error, setError] = useState(""); const router = useRouter();
  useEffect(() => { if (!authLoading && !user) router.replace("/login?next=/checkout"); }, [authLoading, user, router]);
  const submit = async (event: FormEvent) => { event.preventDefault(); setLoading(true); setError(""); try { const order = await apiFetch<Order>("/orders/checkout/", { method:"POST", headers:{ "Idempotency-Key":stableKey("checkout") }, body:JSON.stringify({ coupon_code:coupon }) }); const payment = await apiFetch<{ payment:Payment; payment_url:string }>("/payments/initiate/", { method:"POST", body:JSON.stringify({ order_id:order.id, idempotency_key:stableKey(`payment-${order.id}`) }) }); clearLocalCart(); sessionStorage.removeItem("checkout"); window.location.assign(payment.payment_url); } catch (caught) { setError(caught instanceof Error ? caught.message : "ثبت سفارش انجام نشد"); } finally { setLoading(false); } };
  if (authLoading || !user) return <div className="container section"><LoadingState /></div>; if (!items.length) return <div className="container section"><EmptyState title="سبد خالی است" text="برای پرداخت ابتدا محصولی به سبد اضافه کنید." href="/products" action="مشاهده محصولات" /></div>;
  return <div className="container section"><div className="section-head"><div><h1>ثبت سفارش و پرداخت</h1><p>پس از پرداخت موفق، کدها در جزئیات سفارش نمایش داده می‌شوند.</p></div></div><form className="checkout-layout" onSubmit={submit}><div className="panel stack"><h2>اطلاعات سفارش</h2><div className="alert success">تحویل این سفارش دیجیتال است و نیاز به آدرس پستی ندارد.</div><div className="field"><label>کد تخفیف (اختیاری)</label><input className="input" value={coupon} onChange={(e) => setCoupon(e.target.value.trim().toUpperCase())} placeholder="مثلاً WELCOME" /></div>{error && <div className="alert error">{error}</div>}</div><aside className="panel summary"><h2>مبلغ پرداخت</h2><div className="summary-row"><span>تعداد ردیف‌ها</span><span>{items.length}</span></div><div className="summary-row total"><span>جمع فعلی</span><span>{formatToman(total)}</span></div><button className="button full" disabled={loading}>{loading ? "در حال ساخت پرداخت..." : "انتقال به درگاه"}</button><p className="muted text-center">مبلغ نهایی پس از اعتبارسنجی کد تخفیف مشخص می‌شود.</p></aside></form></div>;
}
