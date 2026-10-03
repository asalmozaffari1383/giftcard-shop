import Link from "next/link";
import Image from "next/image";
import { TrustItem } from "@/components/ui";

export function Footer() {
  const enamadUrl = process.env.NEXT_PUBLIC_ENAMAD_URL;
  const enamadLogoUrl = process.env.NEXT_PUBLIC_ENAMAD_LOGO_URL;
  const supportPhone = process.env.NEXT_PUBLIC_SUPPORT_PHONE;
  return <>
    <section className="trust-strip"><div className="container trust-grid">
      <TrustItem icon="shield" title="خرید مطمئن" text="حفاظت از پرداخت و اطلاعات"/>
      <TrustItem icon="clock" title="تحویل سریع" text="ارسال خودکار کد دیجیتال"/>
      <TrustItem icon="headset" title="پشتیبانی سفارش" text="پیگیری مستقیم از پنل"/>
      <TrustItem icon="ticket" title="موجودی واقعی" text="کنترل لحظه‌ای پیش از خرید"/>
    </div></section>
    <footer className="site-footer"><div className="container footer-grid">
      <div className="footer-about"><Link href="/" className="brand footer-brand"><span className="brand-mark">G</span><span><b>گیفت‌کارت</b><small>فروشگاه محصولات دیجیتال</small></span></Link><p>خرید گیفت کارت و محصولات دیجیتال با موجودی واقعی، پرداخت امن و تحویل شفاف در حساب کاربری.</p></div>
      <div><h3>دسترسی سریع</h3><div className="footer-links"><Link href="/products">همه محصولات</Link><Link href="/orders">سفارش‌های من</Link><Link href="/reviews">نظرهای من</Link></div></div>
      <div><h3>راهنما و پشتیبانی</h3><div className="footer-links"><Link href="/delivery-guide">راهنمای تحویل</Link><Link href="/tickets">ثبت تیکت</Link><Link href="/contact">تماس با ما</Link><Link href="/about">درباره ما</Link></div></div>
      <div className="footer-contact"><h3>قوانین و اعتماد</h3><div className="footer-links"><Link href="/terms">قوانین استفاده</Link><Link href="/privacy">حریم خصوصی</Link><Link href="/refund-policy">شرایط بازپرداخت</Link>{supportPhone && <a href={`tel:${supportPhone}`} dir="ltr">{supportPhone}</a>}</div>{enamadUrl && enamadLogoUrl ? <a className="trust-badge" href={enamadUrl} target="_blank" rel="noopener noreferrer"><Image src={enamadLogoUrl} alt="نماد اعتماد الکترونیکی" width={72} height={78} unoptimized/></a> : <small>محل نمایش نماد اعتماد پس از صدور آماده است.</small>}</div>
    </div><div className="container footer-bottom"><span>© ۱۴۰۵ گیفت‌کارت شاپ</span><span>کلیه حقوق محفوظ است</span></div></footer>
  </>;
}
