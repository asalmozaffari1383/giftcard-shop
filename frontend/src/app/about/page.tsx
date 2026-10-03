import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = { title: "درباره فروشگاه", description: "معرفی فروشگاه تخصصی محصولات دیجیتال و گیفت کارت" };

export default function AboutPage() {
  return <div className="container page-shell legal-page"><header className="legal-hero"><span className="eyebrow">درباره ما</span><h1>فروش تخصصی محصولات دیجیتال</h1><p>هدف فروشگاه، ارائه محصول با موجودی واقعی، قیمت شفاف، پرداخت قابل پیگیری و تحویل امن در حساب کاربری است.</p></header><section className="panel legal-content"><h2>چرا این فروشگاه؟</h2><p>موجودی هر گزینه پیش از خرید کنترل و هنگام ثبت سفارش رزرو می‌شود. کدها به‌شکل رمزنگاری‌شده نگهداری می‌شوند و فقط پس از تأیید پرداخت در اختیار خریدار قرار می‌گیرند.</p><h2>پشتیبانی شفاف</h2><p>سوابق سفارش، پرداخت و پیام‌های پشتیبانی در پنل کاربر باقی می‌مانند تا پیگیری هر خرید با شناسه مشخص انجام شود.</p><div className="hero-actions"><Link className="button primary" href="/products">مشاهده محصولات</Link><Link className="button secondary" href="/contact">تماس با ما</Link></div></section></div>;
}
