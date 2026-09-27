"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { ProductCard } from "@/components/product-card";
import { ErrorState } from "@/components/states";
import { Icon, StatusPill } from "@/components/ui";
import { apiFetch, unwrapResults } from "@/lib/api";
import { formatToman, toPersianDigits } from "@/lib/format";
import type { Paginated, Product } from "@/lib/types";

const categories = [
  { title: "گیفت کارت بازی", text: "پلی‌استیشن، استیم و ایکس‌باکس", icon: "🎮", query: "بازی" },
  { title: "اپلیکیشن و سرویس", text: "اپل، گوگل پلی و اشتراک‌ها", icon: "▦", query: "اپل" },
  { title: "سرگرمی", text: "موسیقی و سرویس‌های آنلاین", icon: "♫", query: "اشتراک" },
  { title: "همه محصولات", text: "مشاهده تمام موجودی فروشگاه", icon: "＋", query: "" },
];

function ProductSkeletons() { return <div className="product-grid">{Array.from({ length: 4 }).map((_, index) => <div className="product-skeleton" key={index}><div className="skeleton-stack"><span/><span/><span/></div></div>)}</div>; }

export default function Home() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => { apiFetch<Paginated<Product> | Product[]>("/catalog/products/?page=1").then((data) => setProducts(unwrapResults(data))).catch((caught) => setError(caught instanceof Error ? caught.message : "خطا در دریافت محصولات")).finally(() => setLoading(false)); }, []);
  const stats = useMemo(() => ({ products: products.length, stock: products.reduce((sum, product) => sum + product.variants.reduce((total, variant) => total + variant.stock, 0), 0) }), [products]);
  const cheapest = products.flatMap((product) => product.variants).filter((variant) => variant.stock > 0).sort((a, b) => a.price_toman - b.price_toman)[0];

  return <>
    <section className="hero"><div className="container hero-grid">
      <div className="hero-content"><StatusPill tone="info"><Icon name="sparkles" size={15}/> فروشگاه تخصصی محصولات دیجیتال</StatusPill><h1>کد دیجیتال را<br/><span>سریع و مطمئن</span> تحویل بگیر</h1><p>محصول مناسب را انتخاب کن، پرداخت را انجام بده و کد را مستقیم و شفاف داخل حساب کاربری دریافت کن.</p><div className="hero-actions"><Link className="button primary large" href="/products">شروع خرید <Icon name="arrow-left"/></Link><Link className="button secondary large" href="/tickets"><Icon name="headset"/> راهنمای خرید</Link></div><div className="hero-mini-stats"><span><b>{toPersianDigits(stats.products || 6)}+</b> محصول فعال</span><i/><span><b>{toPersianDigits(stats.stock || 50)}+</b> کد آماده تحویل</span><i/><span><b>۲۴/۷</b> ثبت سفارش</span></div></div>
      <div className="hero-visual" aria-hidden="true"><div className="hero-orbit orbit-one"/><div className="hero-orbit orbit-two"/><div className="floating-card card-main"><span className="digital-chip"/><small>DIGITAL GIFT CARD</small><strong>GIFT<span>+</span></strong><div><span>Instant delivery</span><b>•••• ۲۰۲۶</b></div></div><div className="floating-note note-top"><span className="icon-box success"><Icon name="check"/></span><div><b>تحویل موفق</b><small>کد در حساب شماست</small></div></div><div className="floating-note note-bottom"><span className="icon-box"><Icon name="shield"/></span><div><b>پرداخت امن</b><small>تأیید سمت سرور</small></div></div></div>
    </div></section>

    <section className="container section categories-section"><div className="section-title"><div><span className="eyebrow">دسترسی سریع</span><h2>دنبال چه محصولی هستی؟</h2></div><Link href="/products">همه محصولات <Icon name="arrow-left" size={17}/></Link></div><div className="category-grid">{categories.map((category) => <Link className="category-card" href={category.query ? `/products?search=${category.query}` : "/products"} key={category.title}><span>{category.icon}</span><div><b>{category.title}</b><small>{category.text}</small></div><Icon name="chevron-left" size={18}/></Link>)}</div></section>

    <section className="products-showcase"><div className="container section"><div className="section-title"><div><span className="eyebrow">پیشنهاد فروشگاه</span><h2>محصولات آماده تحویل</h2><p>موجودی و قیمت‌ها مستقیماً از انبار دیجیتال خوانده می‌شوند.</p></div><Link className="button ghost" href="/products">مشاهده همه <Icon name="arrow-left" size={17}/></Link></div>{loading ? <ProductSkeletons/> : error ? <ErrorState message={error}/> : <div className="product-grid">{products.slice(0, 8).map((product) => <ProductCard product={product} key={product.id}/>)}</div>}</div></section>

    <section className="container section"><div className="promo-panel"><div><StatusPill tone="warning">خرید اول</StatusPill><h2>برای شروع آماده‌ای؟</h2><p>با کد <b>WELCOME10</b> فرآیند اعمال تخفیف را در محیط آزمایشی بررسی کن.</p><Link className="button light" href="/products">انتخاب محصول <Icon name="arrow-left"/></Link></div><div className="promo-price"><small>محصولات از</small><strong>{cheapest ? formatToman(cheapest.price_toman) : "قیمت مناسب"}</strong><span>تحویل مستقیم در پنل</span></div></div></section>
  </>;
}
