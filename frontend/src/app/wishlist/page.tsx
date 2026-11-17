"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { EmptyState, ErrorState, LoadingState } from "@/components/states";
import { PageIntro, Icon } from "@/components/ui";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/contexts/app-context";
import type { WishlistItem } from "@/lib/types";

export default function WishlistPage() {
  const { user, loading: authLoading } = useAuth();
  const [items, setItems] = useState<WishlistItem[]>([]); const [loading, setLoading] = useState(true); const [error, setError] = useState("");
  const load = () => { if (!user) return; setLoading(true); setError(""); apiFetch<WishlistItem[]>("/auth/wishlist/").then(setItems).catch((e) => setError(e instanceof Error ? e.message : "خطا در دریافت علاقه‌مندی‌ها")).finally(() => setLoading(false)); };
  useEffect(load, [user]);
  if (authLoading || (user && loading)) return <div className="container page-shell"><LoadingState text="در حال دریافت علاقه‌مندی‌ها..."/></div>;
  if (!user) return <div className="container page-shell"><EmptyState title="برای دیدن علاقه‌مندی‌ها وارد شوید" text="محصولات دلخواهت را برای خرید بعدی ذخیره کن." href="/login?next=/wishlist" action="ورود با موبایل"/></div>;
  if (error) return <div className="container page-shell"><ErrorState message={error} retry={load}/></div>;
  if (!items.length) return <div className="container page-shell"><EmptyState title="هنوز محصولی ذخیره نکرده‌ای" text="روی ستاره‌ی محصول‌های دوست‌داشتنی بزن." href="/products" action="مشاهده محصولات"/></div>;
  return <div className="container page-shell"><PageIntro eyebrow="حساب کاربری" title="علاقه‌مندی‌های من" description="محصول‌هایی که برای خرید بعدی نشان کرده‌ای اینجا هستند."/><div className="wishlist-grid">{items.map((item) => <article className="panel wishlist-card" key={item.id}><div className="wishlist-card-icon"><Icon name="star"/></div><div><h2><Link href={`/products/${item.product_slug}`}>{item.product_title}</Link></h2><small>ذخیره‌شده در آلیسان</small></div><button className="button danger small" onClick={() => apiFetch(`/auth/wishlist/${item.id}/`, { method: "DELETE" }).then(() => setItems((current) => current.filter((entry) => entry.id !== item.id))).catch((caught) => setError(caught.message))}>حذف</button></article>)}</div></div>;
}
