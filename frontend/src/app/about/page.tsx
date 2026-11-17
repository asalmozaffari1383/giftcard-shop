import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = { title: "درباره فروشگاه", description: "معرفی فروشگاه آنلاین آلیسان" };

export default function AboutPage() {
  return <div className="container page-shell legal-page"><header className="legal-hero"><span className="eyebrow">درباره ما</span><h1>آلیسان؛ فروشگاهی برای انتخاب‌های دوست‌داشتنی</h1><p>هدف آلیسان، ارائه انتخاب‌های متنوع، قیمت شفاف، پرداخت قابل پیگیری و پشتیبانی همراه برای هر سفارش است.</p></header><section className="panel legal-content"><h2>چرا این فروشگاه؟</h2><p>اطلاعات هر گزینه پیش از خرید بررسی می‌شود و سفارش‌ها با فرایندی شفاف و قابل پیگیری ثبت می‌شوند.</p><h2>پشتیبانی شفاف</h2><p>سوابق سفارش، پرداخت و پیام‌های پشتیبانی در پنل کاربر باقی می‌مانند تا پیگیری هر خرید با شناسه مشخص انجام شود.</p><div className="hero-actions"><Link className="button primary" href="/products">مشاهده محصولات</Link><Link className="button secondary" href="/contact">تماس با ما</Link></div></section></div>;
}
