"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ProductCard } from "@/components/product-card";
import { ErrorState, LoadingState } from "@/components/states";
import { apiFetch, unwrapResults } from "@/lib/api";
import type { Paginated, Product } from "@/lib/types";

export default function Home() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const load = async () => {
    setLoading(true); setError("");
    try { setProducts(unwrapResults(await apiFetch<Paginated<Product> | Product[]>("/catalog/products/?page=1"))); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "خطا در دریافت محصولات"); }
    finally { setLoading(false); }
  };
  useEffect(() => { void load(); }, []);
  return <>
    <section className="hero"><div className="container hero-grid"><div>
      <div className="eyebrow">مارکت محصولات دیجیتال</div><h1>خرید سریع، امن و بی‌دردسر گیفت کارت</h1>
      <p>محصول موردنظرتان را انتخاب کنید، آنلاین پرداخت کنید و کد را مستقیم در حساب کاربری تحویل بگیرید.</p>
      <div className="hero-actions"><Link className="button" href="/products">مشاهده محصولات</Link><Link className="button secondary" href="/tickets">راهنمای خرید</Link></div>
    </div><div className="hero-card"><strong>چرا گیفت‌کارت شاپ؟</strong><div className="hero-points"><span>✓ تحویل خودکار کد</span><span>✓ موجودی واقعی و لحظه‌ای</span><span>✓ پشتیبانی سفارش</span></div></div></div></section>
    <section className="container section"><div className="feature-grid"><div className="feature"><b>تحویل سریع</b><p>کد محصولات موجود پس از تأیید پرداخت تحویل می‌شود.</p></div><div className="feature"><b>پرداخت امن</b><p>تراکنش‌ها سمت سرور تأیید و به‌صورت idempotent پردازش می‌شوند.</p></div><div className="feature"><b>پشتیبانی واقعی</b><p>برای هر سفارش می‌توانید تیکت مستقیم ثبت کنید.</p></div></div></section>
    <section className="container section-sm"><div className="section-head"><div><h2>محصولات تازه</h2><p>انتخاب‌های محبوب و موجود فروشگاه</p></div><Link href="/products">مشاهده همه ←</Link></div>
      {loading ? <LoadingState /> : error ? <ErrorState message={error} retry={() => void load()} /> : <div className="product-grid">{products.slice(0,8).map((product) => <ProductCard product={product} key={product.id} />)}</div>}
    </section>
  </>;
}
