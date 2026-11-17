"use client";

import Link from "next/link";
import Image from "next/image";
import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { useAuth, useCart } from "@/contexts/app-context";
import { toPersianDigits } from "@/lib/format";
import { Icon } from "@/components/ui";

const links = [
  { href: "/products", label: "فروشگاه" },
  { href: "/school-builder", label: "پک مدرسه" },
  { href: "/school-lists", label: "لیست مدرسه" },
  { href: "/orders", label: "سفارش‌ها" },
  { href: "/tickets", label: "پشتیبانی" },
  { href: "/contact", label: "تماس با ما" },
];

export function Header() {
  const pathname = usePathname();
  const { user, loading, logout } = useAuth();
  const { count } = useCart();
  const [open, setOpen] = useState(false);
  useEffect(() => setOpen(false), [pathname]);

  return <>
    <div className="announcement"><div className="container"><span><Icon name="sparkles" size={16}/> خرید مطمئن و تجربه‌ای رنگارنگ</span><span className="announcement-secondary">پشتیبانی آلیسان</span></div></div>
    <header className="site-header">
      <div className="container header-inner">
        <Link href="/" className="brand" aria-label="صفحه اصلی آلیسان"><Image src="/alisan-mark.svg" alt="" width={44} height={44}/><span><b>آلیسان</b><small>دنیای لوازم‌تحریر</small></span></Link>
        <nav className={`main-nav ${open ? "open" : ""}`} aria-label="منوی اصلی">
          {links.map((link) => <Link className={pathname.startsWith(link.href) ? "active" : ""} href={link.href} key={link.href}>{link.label}</Link>)}
        </nav>
        <div className="header-actions">
          <Link href={user ? "/account" : "/login"} className="header-icon-link" aria-label={user ? "حساب کاربری" : "ورود"}><Icon name="user"/><span>{loading ? "..." : user ? "حساب من" : "ورود"}</span></Link>
          <Link href="/cart" className="header-icon-link cart-action" aria-label={`سبد خرید، ${count} کالا`}><Icon name="bag"/><span>سبد خرید</span>{count > 0 && <b>{toPersianDigits(count)}</b>}</Link>
          {user && <button className="logout-action" onClick={() => void logout()}>خروج</button>}
          <button className="menu-toggle" onClick={() => setOpen((value) => !value)} aria-expanded={open} aria-label={open ? "بستن منو" : "نمایش منو"}><Icon name={open ? "x" : "menu"}/></button>
        </div>
      </div>
    </header>
  </>;
}
