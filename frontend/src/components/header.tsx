"use client";

import Link from "next/link";
import { useState } from "react";
import { usePathname } from "next/navigation";
import { useAuth, useCart } from "@/contexts/app-context";
import { toPersianDigits } from "@/lib/format";

const links = [{ href: "/products", label: "محصولات" }, { href: "/orders", label: "سفارش‌ها" }, { href: "/tickets", label: "پشتیبانی" }, { href: "/contact", label: "تماس" }];

export function Header() {
  const pathname = usePathname();
  const { user, loading, logout } = useAuth();
  const { count } = useCart();
  const [open, setOpen] = useState(false);
  return (
    <header className="site-header">
      <div className="container header-inner">
        <Link href="/" className="brand">گیفت‌کارت شاپ</Link>
        <button className="menu-toggle" onClick={() => setOpen((value) => !value)} aria-expanded={open} aria-label="نمایش منو">☰</button>
        <nav className={`main-nav ${open ? "open" : ""}`} aria-label="منوی اصلی">
          {links.map((link) => <Link onClick={() => setOpen(false)} className={pathname.startsWith(link.href) ? "active" : ""} href={link.href} key={link.href}>{link.label}</Link>)}
        </nav>
        <div className="header-actions">
          <Link href="/cart" className="cart-link">سبد <span>{toPersianDigits(count)}</span></Link>
          {!loading && (user ? <button className="link-button" onClick={() => void logout()}>خروج</button> : <Link className="button small" href="/login">ورود</Link>)}
        </div>
      </div>
    </header>
  );
}
