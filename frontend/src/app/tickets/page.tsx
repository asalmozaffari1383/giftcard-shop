"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { EmptyState, LoadingState } from "@/components/states";
import { useAuth, useToast } from "@/contexts/app-context";
import { apiFetch, unwrapResults } from "@/lib/api";
import { ticketStatus } from "@/lib/format";
import type { Paginated, Ticket } from "@/lib/types";

export default function TicketsPage() {
  const { user, loading: authLoading } = useAuth(); const router = useRouter(); const params = useSearchParams(); const toast = useToast(); const [tickets, setTickets] = useState<Ticket[]>([]); const [subject, setSubject] = useState(""); const [order, setOrder] = useState(params.get("order") || ""); const [loading, setLoading] = useState(true); const [creating, setCreating] = useState(false); const [error, setError] = useState("");
  const load = () => apiFetch<Paginated<Ticket> | Ticket[]>("/support/tickets/").then((data) => setTickets(unwrapResults(data))).catch((caught) => setError(caught instanceof Error ? caught.message : "خطا")).finally(() => setLoading(false));
  useEffect(() => { if (!authLoading && !user) router.replace("/login?next=/tickets"); if (user) void load(); }, [user, authLoading, router]);
  const create = async (event: FormEvent) => { event.preventDefault(); setCreating(true); setError(""); try { const ticket = await apiFetch<Ticket>("/support/tickets/", { method:"POST", body:JSON.stringify({ subject, order:order || null }) }); toast("تیکت ایجاد شد"); router.push(`/tickets/${ticket.id}`); } catch (caught) { setError(caught instanceof Error ? caught.message : "ثبت تیکت انجام نشد"); } finally { setCreating(false); } };
  if (authLoading || !user) return <div className="container section"><LoadingState /></div>;
  return <div className="container section"><div className="section-head"><div><h1>پشتیبانی</h1><p>سؤال‌ها و مشکلات سفارش را مستقیم پیگیری کنید.</p></div></div><div className="checkout-layout"><div><h2>تیکت‌های من</h2>{loading ? <LoadingState /> : tickets.length ? <div className="list">{tickets.map((ticket) => <Link className="list-card" href={`/tickets/${ticket.id}`} key={ticket.id}><div><h3>{ticket.subject}</h3><p>{new Date(ticket.created_at).toLocaleDateString("fa-IR")}</p></div><span className={`status ${ticket.status}`}>{ticketStatus[ticket.status]}</span></Link>)}</div> : <EmptyState title="تیکتی ندارید" text="در صورت نیاز از فرم کناری پیام جدید بسازید." />}</div><form className="panel stack" onSubmit={create}><h2>تیکت جدید</h2><div className="field"><label>موضوع</label><input className="input" minLength={3} maxLength={200} value={subject} onChange={(e) => setSubject(e.target.value)} required /></div><div className="field"><label>شناسه سفارش (اختیاری)</label><input className="input" dir="ltr" value={order} onChange={(e) => setOrder(e.target.value)} /></div>{error && <div className="alert error">{error}</div>}<button className="button" disabled={creating}>{creating ? "در حال ثبت..." : "ایجاد تیکت"}</button></form></div></div>;
}
