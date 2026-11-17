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
  { title: "دفتر و کلاسور", text: "شروع یک صفحه تازه", icon: "✦", query: "دفتر" },
  { title: "نوشت‌افزار", text: "مداد و خودکارهای رنگارنگ", icon: "✎", query: "مداد" },
  { title: "پیشنهادهای رنگی", text: "انتخابی برای هر سلیقه", icon: "♡", query: "هدیه" },
  { title: "همه محصولات", text: "مشاهده تمام موجودی فروشگاه", icon: "＋", query: "" },
];

function ProductSkeletons() { return <div className="product-grid">{Array.from({ length: 4 }).map((_, index) => <div className="product-skeleton" key={index}><div className="skeleton-stack"><span/><span/><span/></div></div>)}</div>; }

export default function Home() {
  const [products, setProducts] = useState<Product[]>([]);
  const [productCount, setProductCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => { apiFetch<Paginated<Product> | Product[]>("/catalog/products/?page=1").then((data) => { setProducts(unwrapResults(data)); setProductCount(Array.isArray(data) ? data.length : data.count); }).catch((caught) => setError(caught instanceof Error ? caught.message : "خطا در دریافت محصولات")).finally(() => setLoading(false)); }, []);
  const stats = useMemo(() => ({ stock: products.reduce((sum, product) => sum + product.variants.reduce((total, variant) => total + variant.stock, 0), 0) }), [products]);
  const cheapest = products.flatMap((product) => product.variants).filter((variant) => variant.stock > 0).sort((a, b) => a.price_toman - b.price_toman)[0];

  return <>
    <section className="hero"><div className="container hero-grid">
      <div className="hero-content"><StatusPill tone="info"><Icon name="sparkles" size={15}/> فروشگاه آنلاین آلیسان</StatusPill><h1>برای نوشتنِ فردا<br/><span>رنگ تازه‌ای</span> انتخاب کن</h1><p>دفتر، نوشت‌افزار و پک‌های مدرسه؛ همراه روزهای درس، کار و خیال‌پردازی.</p><div className="hero-actions"><Link className="button primary large" href="/products">شروع گشت‌وگذار <Icon name="arrow-left"/></Link><Link className="button secondary large" href="/school-builder"><Icon name="sparkles"/> پک مدرسه من</Link></div><div className="hero-mini-stats"><span><b>{toPersianDigits(productCount)}</b> محصول ثبت‌شده</span><i/><span><b>{toPersianDigits(stats.stock)}</b> انتخاب آماده</span><i/><span><b>۲۴/۷</b> ثبت سفارش</span></div></div>
      <div className="hero-visual" aria-hidden="true"><div className="hero-orbit orbit-one"/><div className="hero-orbit orbit-two"/><div className="floating-card card-main"><span className="notebook-spiral"/><small>ALISAN SHOP</small><strong>ALISAN<span>✦</span></strong><div><span>خرید آسان</span><b>دفترِ ایده‌های تو</b></div></div><div className="floating-note note-top"><span className="icon-box success"><Icon name="check"/></span><div><b>تحویل موفق</b><small>سفارش شما آماده است</small></div></div><div className="floating-note note-bottom"><span className="icon-box"><Icon name="shield"/></span><div><b>پرداخت امن</b><small>خرید با خیال راحت</small></div></div></div>
    </div></section>

    <section className="container section categories-section"><div className="section-title"><div><span className="eyebrow">دسترسی سریع</span><h2>دنبال چه محصولی هستی؟</h2></div><Link href="/products">همه محصولات <Icon name="arrow-left" size={17}/></Link></div><div className="category-grid">{categories.map((category) => <Link className="category-card" href={category.query ? `/products?search=${category.query}` : "/products"} key={category.title}><span>{category.icon}</span><div><b>{category.title}</b><small>{category.text}</small></div><Icon name="chevron-left" size={18}/></Link>)}</div></section>

    <section className="products-showcase"><div className="container section"><div className="section-title"><div><span className="eyebrow">کاتالوگ فروشگاه</span><h2>انتخاب‌های منتخب آلیسان</h2><p>محصولات منتخب را با اطلاعات شفاف و پشتیبانی همراه بررسی کن.</p></div><Link className="button ghost" href="/products">مشاهده همه <Icon name="arrow-left" size={17}/></Link></div>{loading ? <ProductSkeletons/> : error ? <ErrorState message={error}/> : <div className="product-grid">{products.slice(0, 8).map((product) => <ProductCard product={product} key={product.id}/>)}</div>}</div></section>

    <section className="container section"><div className="promo-panel"><div><StatusPill tone="warning">انتخاب آگاهانه</StatusPill><h2>جزئیات محصول را قبل از خرید ببین</h2><p>جزئیات هر محصول را بخوان و با خیال راحت بهترین انتخاب را انجام بده.</p><Link className="button light" href="/delivery-guide">مطالعه راهنمای خرید <Icon name="arrow-left"/></Link></div><div className="promo-price"><small>کمترین گزینه موجود</small><strong>{cheapest ? formatToman(cheapest.price_toman) : "در انتظار تأمین موجودی"}</strong><span>پشتیبانی همراه شما</span></div></div></section>
  </>;
}
