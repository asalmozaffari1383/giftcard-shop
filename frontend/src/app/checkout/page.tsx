"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { EmptyState, LoadingState } from "@/components/states";
import { PageIntro } from "@/components/ui";
import { useAuth, useCart } from "@/contexts/app-context";
import { ApiError, apiFetch, unwrapResults } from "@/lib/api";
import { formatToman, toPersianDigits } from "@/lib/format";
import type { Address, Order, Paginated, Payment, ShippingMethod } from "@/lib/types";

function stableKey(name: string) {
  const saved = sessionStorage.getItem(name);
  if (saved && saved.length <= 80) return saved;
  const key = crypto.randomUUID();
  sessionStorage.setItem(name, key);
  return key;
}

export default function CheckoutPage() {
  const { user, loading: authLoading } = useAuth();
  const { items, total, clearLocalCart, refreshCart } = useCart();
  const [coupon, setCoupon] = useState("");
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [shipping, setShipping] = useState<ShippingMethod[]>([]);
  const [addressId, setAddressId] = useState<number | null>(null);
  const [shippingId, setShippingId] = useState<number | null>(null);
  const [pending, setPending] = useState<Order | null>(null);
  const [initializing, setInitializing] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();
  useEffect(() => { if (!authLoading && !user) router.replace("/login?next=/checkout"); }, [authLoading, user, router]);
  useEffect(() => {
    if (!user) return;
    const load = async () => {
      try {
        const saved = sessionStorage.getItem(`checkout-order-${user.id}`);
        if (saved) {
          const order = await apiFetch<Order>(`/orders/${saved}/`).catch(() => null);
          if (order?.status === "PENDING" && new Date(order.expires_at) > new Date()) setPending(order);
          else { sessionStorage.removeItem(`checkout-order-${user.id}`); sessionStorage.removeItem(`checkout-${user.id}`); }
        }
        const [addressData, methods] = await Promise.all([
          apiFetch<Address[]>("/auth/addresses/"), apiFetch<ShippingMethod[] | Paginated<ShippingMethod>>("/orders/shipping-methods/"),
        ]);
        const shippingMethods = unwrapResults(methods);
        setAddresses(addressData); setShipping(shippingMethods);
        setAddressId(addressData.find((item) => item.is_default)?.id || addressData[0]?.id || null);
        setShippingId(shippingMethods[0]?.id || null);
      } catch (caught) { setError(caught instanceof Error ? caught.message : "دریافت روش ارسال انجام نشد"); }
      finally { setInitializing(false); }
    };
    void load();
  }, [user]);
  const needsShipping = items.some((item) => item.product_kind === "PHYSICAL");
  const method = shipping.find((item) => item.id === shippingId);
  const shippingCost = pending?.shipping_toman ?? (needsShipping && method ? (method.free_above_toman > 0 && total >= method.free_above_toman ? 0 : method.price_toman) : 0);
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!user) return;
    setLoading(true); setError("");
    let currentOrder = pending;
    try {
      if (!currentOrder) {
        currentOrder = await apiFetch<Order>("/orders/checkout/", {
          method: "POST", headers: { "Idempotency-Key": stableKey(`checkout-${user.id}`) },
          body: JSON.stringify({ coupon_code: coupon, address_id: needsShipping ? addressId : null, shipping_method_id: needsShipping ? shippingId : null }),
        });
        sessionStorage.setItem(`checkout-order-${user.id}`, currentOrder.id);
        setPending(currentOrder); clearLocalCart();
      }
      const payment = await apiFetch<{ payment: Payment; payment_url: string }>("/payments/initiate/", {
        method: "POST", body: JSON.stringify({ order_id: currentOrder.id, idempotency_key: stableKey(`payment-${currentOrder.id}`) }),
      });
      sessionStorage.removeItem(`checkout-${user.id}`);
      sessionStorage.removeItem(`checkout-order-${user.id}`);
      window.location.assign(payment.payment_url);
    } catch (caught) {
      if (currentOrder && caught instanceof ApiError && caught.status === 500) sessionStorage.removeItem(`payment-${currentOrder.id}`);
      setError(caught instanceof Error ? caught.message : "ثبت سفارش انجام نشد");
      void refreshCart();
    } finally { setLoading(false); }
  };
  if (authLoading || !user || initializing) return <div className="container page-shell"><LoadingState/></div>;
  if (!items.length && !pending) return <div className="container page-shell"><EmptyState title="سبد خالی است" text="برای پرداخت ابتدا محصولی به سبد اضافه کن." href="/products" action="مشاهده محصولات"/></div>;
  const lines = pending ? pending.items.map((item) => ({ ...item, price_toman: item.unit_price_toman })) : items;
  return <div className="container page-shell"><PageIntro eyebrow="تکمیل خرید" title="ثبت سفارش و پرداخت" description="آدرس، هزینه ارسال و جزئیات خریدت را بررسی کن."/>
    <form className="checkout-layout" onSubmit={submit}><section className="checkout-content">
      <div className="checkout-card"><h2>خریدار</h2><p dir="ltr">{user.phone_number}</p></div>
      {pending ? <div className="checkout-card"><h2>سفارش برای پرداخت آماده است</h2><p>اقلام و تخفیف ثبت شده‌اند. برای ادامه، پرداخت را دوباره انجام بده.</p><Link href={`/orders/${pending.id}`}>مشاهده یا لغو سفارش</Link></div> : <>
        {needsShipping && <div className="checkout-card stack"><h2>آدرس و ارسال</h2>
          {addresses.length ? <label>آدرس تحویل<select className="input" required value={addressId || ""} onChange={(event) => setAddressId(Number(event.target.value))}>{addresses.map((item) => <option value={item.id} key={item.id}>{item.title} — {item.city}، {item.address}</option>)}</select></label> : <p>ابتدا یک آدرس تحویل ثبت کن.</p>}
          <Link href="/addresses" className="button secondary">مدیریت آدرس‌ها</Link>
          <label>روش ارسال<select className="input" required value={shippingId || ""} onChange={(event) => setShippingId(Number(event.target.value))}><option value="" disabled>روش ارسال را انتخاب کن</option>{shipping.map((item) => <option value={item.id} key={item.id}>{item.title} — {formatToman(item.price_toman)}</option>)}</select></label>
          {method && method.free_above_toman > 0 && <p>ارسال رایگان برای خرید بالای {formatToman(method.free_above_toman)} پیش از اعمال کوپن.</p>}
          {!shipping.length && <p>روش ارسال هنوز توسط فروشگاه تنظیم نشده است.</p>}
        </div>}
        <div className="checkout-card"><label><h2>کد تخفیف</h2><input className="input" value={coupon} onChange={(event) => setCoupon(event.target.value.trim().toUpperCase())} placeholder="کد تخفیف"/></label><p>مبلغ قطعی با تخفیف پیش از ورود به درگاه محاسبه می‌شود.</p></div>
      </>}
      <div className="checkout-card"><h2>پرداخت آنلاین</h2><p>پس از تأیید پرداخت، سفارش برای آماده‌سازی ثبت می‌شود.</p></div>
      {error && <div className="alert error" role="alert">{error}</div>}
    </section><aside className="order-summary"><h2>خلاصه خرید</h2><div className="checkout-products">{lines.map((item) => <div key={item.id}><span>{item.product_title}<small>تعداد {toPersianDigits(item.quantity)}</small></span><b>{formatToman(item.price_toman * item.quantity)}</b></div>)}</div>
      <div className="summary-row"><span>جمع محصولات</span><b>{formatToman(pending?.subtotal_toman ?? total)}</b></div>
      {pending && <div className="summary-row"><span>تخفیف</span><b>{formatToman(pending.discount_toman)}</b></div>}
      <div className="summary-row"><span>ارسال</span><b>{formatToman(shippingCost)}</b></div>
      <div className="summary-total"><span>{pending ? "مبلغ قطعی" : "مبلغ قبل از کوپن"}</span><strong>{formatToman(pending?.total_toman ?? total + shippingCost)}</strong></div>
      <button className="button primary full large" disabled={loading || (!pending && needsShipping && (!addressId || !shippingId))}>{loading ? "در حال آماده‌سازی پرداخت…" : "ادامه و پرداخت"}</button>
      <p className="summary-caption">موجودی سفارش برای ۱۵ دقیقه رزرو می‌شود.</p>
    </aside></form></div>;
}
