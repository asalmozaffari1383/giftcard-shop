import Link from "next/link";
import { Icon, TrustItem } from "@/components/ui";

export function Footer() {
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
      <div><h3>راهنما و پشتیبانی</h3><div className="footer-links"><Link href="/tickets">ثبت تیکت</Link><Link href="/contact">تماس با ما</Link><Link href="/account">حساب کاربری</Link></div></div>
      <div className="footer-contact"><h3>همراه شما هستیم</h3><p><Icon name="headset" size={18}/> پاسخ‌گویی از طریق تیکت</p><small>تمام سفارش‌ها و کدهای تحویلی از پنل کاربری قابل پیگیری‌اند.</small></div>
    </div><div className="container footer-bottom"><span>© ۱۴۰۵ گیفت‌کارت شاپ</span><span>نسخه در حال توسعه</span></div></footer>
  </>;
}
