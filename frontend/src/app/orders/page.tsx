"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { EmptyState, ErrorState, LoadingState } from "@/components/states";
import { Icon, PageIntro } from "@/components/ui";
import { useAuth } from "@/contexts/app-context";
import { apiFetch, unwrapResults } from "@/lib/api";
import { formatToman, orderStatus, toPersianDigits } from "@/lib/format";
import type { Order, Paginated } from "@/lib/types";

export default function OrdersPage() {
  const { user, loading: authLoading } = useAuth(); const router = useRouter(); const [orders, setOrders] = useState<Order[]>([]); const [loading, setLoading] = useState(true); const [error, setError] = useState("");
  useEffect(() => { if (!authLoading && !user) { router.replace("/login?next=/orders"); return; } if (user) apiFetch<Paginated<Order> | Order[]>("/orders/").then((data) => setOrders(unwrapResults(data))).catch((caught) => setError(caught instanceof Error ? caught.message : "خطا")).finally(() => setLoading(false)); }, [user, authLoading, router]);
  if (authLoading || loading) return <div className="container page-shell"><LoadingState text="در حال دریافت سفارش‌ها..."/></div>; if (error) return <div className="container page-shell"><ErrorState message={error}/></div>; if (!orders.length) return <div className="container page-shell"><EmptyState title="هنوز سفارشی نداری" text="بعد از اولین خرید، وضعیت سفارش و کد دیجیتال اینجا نمایش داده می‌شود." href="/products" action="شروع خرید"/></div>;
  return <div className="container page-shell"><PageIntro eyebrow="حساب کاربری" title="سفارش‌های من" description="وضعیت پرداخت، تحویل و کدهای دیجیتال را از یک جا پیگیری کن."/><div className="order-stats"><div><span className="icon-box"><Icon name="bag"/></span><p><b>{toPersianDigits(orders.length)}</b><small>کل سفارش‌ها</small></p></div><div><span className="icon-box success"><Icon name="check"/></span><p><b>{toPersianDigits(orders.filter((order) => order.status === "COMPLETED").length)}</b><small>تکمیل‌شده</small></p></div><div><span className="icon-box warning"><Icon name="clock"/></span><p><b>{toPersianDigits(orders.filter((order) => order.status === "PENDING" || order.status === "PROCESSING").length)}</b><small>در حال پیگیری</small></p></div></div><div className="orders-table"><div className="orders-head"><span>شناسه و تاریخ</span><span>اقلام</span><span>مبلغ</span><span>وضعیت</span><span/></div>{orders.map((order) => <Link className="order-row" href={`/orders/${order.id}`} key={order.id}><span><b>#{order.id.slice(0,8).toUpperCase()}</b><small>{order.created_at_jalali}</small></span><span>{toPersianDigits(order.items.reduce((sum,item) => sum + item.quantity, 0))} محصول</span><strong>{formatToman(order.total_toman)}</strong><span className={`status ${order.status}`}>{orderStatus[order.status]}</span><Icon name="chevron-left"/></Link>)}</div></div>;
}
