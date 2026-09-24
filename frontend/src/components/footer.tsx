import Link from "next/link";

export function Footer() {
  return <footer className="site-footer"><div className="container footer-inner">
    <div><strong>گیفت‌کارت شاپ</strong><p>خرید امن محصولات دیجیتال با تحویل سریع.</p></div>
    <div className="footer-links"><Link href="/products">فروشگاه</Link><Link href="/tickets">پشتیبانی</Link><Link href="/contact">تماس</Link><Link href="/account">حساب کاربری</Link></div>
  </div></footer>;
}
