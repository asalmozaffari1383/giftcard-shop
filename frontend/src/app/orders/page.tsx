"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { EmptyState, ErrorState, LoadingState } from "@/components/states";
import { useAuth } from "@/contexts/app-context";
import { apiFetch, unwrapResults } from "@/lib/api";
import { formatToman, orderStatus } from "@/lib/format";
import type { Order, Paginated } from "@/lib/types";

export default function OrdersPage() {
  const { user, loading: authLoading } = useAuth(); const router = useRouter(); const [orders, setOrders] = useState<Order[]>([]); const [loading, setLoading] = useState(true); const [error, setError] = useState("");
  useEffect(() => { if (!authLoading && !user) { router.replace("/login?next=/orders"); return; } if (user) apiFetch<Paginated<Order> | Order[]>("/orders/").then((data) => setOrders(unwrapResults(data))).catch((caught) => setError(caught instanceof Error ? caught.message : "خطا")).finally(() => setLoading(false)); }, [user, authLoading, router]);
  if (authLoading || loading) return <div className="container section"><LoadingState /></div>; if (error) return <div className="container section"><ErrorState message={error} /></div>; if (!orders.length) return <div className="container section"><EmptyState title="هنوز سفارشی ندارید" text="اولین محصول دیجیتال خود را انتخاب کنید." href="/products" action="رفتن به فروشگاه" /></div>;
  return <div className="container section"><div className="section-head"><div><h1>سفارش‌های من</h1><p>سوابق خرید و وضعیت تحویل</p></div></div><div className="list">{orders.map((order) => <Link className="list-card" href={`/orders/${order.id}`} key={order.id}><div><h3>سفارش {order.id.slice(0,8)}</h3><p>{order.created_at_jalali} · {order.items.length} ردیف</p></div><strong>{formatToman(order.total_toman)}</strong><span className={`status ${order.status}`}>{orderStatus[order.status]}</span></Link>)}</div></div>;
}
