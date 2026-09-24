"use client";

import Link from "next/link";
import { useAuth, useCart } from "@/contexts/app-context";
import { EmptyState, LoadingState } from "@/components/states";
import { formatToman } from "@/lib/format";

export default function CartPage() {
  const { user, loading: authLoading } = useAuth();
  const { items, total, loading, updateItem, removeItem } = useCart();
  if (authLoading) return <div className="container section"><LoadingState /></div>;
  if (!user) return <div className="container section"><EmptyState title="برای مشاهده سبد وارد شوید" text="سبد خرید شما پس از ورود با سرور همگام می‌شود." href="/login?next=/cart" action="ورود با موبایل" /></div>;
  if (loading) return <div className="container section"><LoadingState /></div>;
  if (!items.length) return <div className="container section"><EmptyState title="سبد خرید خالی است" text="یک محصول دیجیتال انتخاب کنید." href="/products" action="رفتن به فروشگاه" /></div>;

  return <div className="container section">
    <div className="section-head"><div><h1>سبد خرید</h1><p>موجودی نهایی هنگام ثبت سفارش کنترل می‌شود.</p></div></div>
    <div className="cart-layout"><div className="cart-items">{items.map((item) => <div className="cart-item" key={item.id}>
      <div><h3><Link href={`/products/${item.product_slug}`}>{item.product_title}</Link></h3><p>{item.variant_label}</p></div>
      <div className="cart-quantity"><button onClick={() => item.quantity > 1 && void updateItem(item, item.quantity - 1)} disabled={item.quantity <= 1}>−</button><span>{item.quantity}</span><button onClick={() => item.quantity < 20 && void updateItem(item, item.quantity + 1)} disabled={item.quantity >= 20}>+</button></div>
      <strong>{formatToman(item.price_toman * item.quantity)}</strong>
      <button className="button danger small" onClick={() => void removeItem(item)}>حذف</button>
    </div>)}</div>
      <aside className="panel summary"><h2>خلاصه سبد</h2><div className="summary-row"><span>جمع محصولات</span><span>{formatToman(total)}</span></div><div className="summary-row total"><span>قابل پرداخت</span><span>{formatToman(total)}</span></div><Link className="button full" href="/checkout">ادامه و پرداخت</Link></aside>
    </div>
  </div>;
}
