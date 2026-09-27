"use client";

import { FormEvent, use, useEffect, useState } from "react";
import { ErrorState, LoadingState } from "@/components/states";
import { useAuth, useToast } from "@/contexts/app-context";
import { apiFetch } from "@/lib/api";
import { ticketStatus } from "@/lib/format";
import type { Ticket, TicketMessage } from "@/lib/types";

export default function TicketDetailPage({ params }: { params: Promise<{ id:string }> }) {
  const { id } = use(params); const { user } = useAuth(); const toast = useToast(); const [ticket, setTicket] = useState<Ticket | null>(null); const [body, setBody] = useState(""); const [loading, setLoading] = useState(true); const [sending, setSending] = useState(false); const [error, setError] = useState("");
  useEffect(() => {
    void apiFetch<Ticket>(`/support/tickets/${id}/`)
      .then(setTicket)
      .catch((caught) => setError(caught instanceof Error ? caught.message : "خطا"))
      .finally(() => setLoading(false));
  }, [id]);
  const send = async (event: FormEvent) => { event.preventDefault(); setSending(true); try { const message = await apiFetch<TicketMessage>(`/support/tickets/${id}/messages/`, { method:"POST", body:JSON.stringify({ body }) }); setTicket((current) => current ? { ...current, status:"WAITING", messages:[...current.messages, message] } : current); setBody(""); toast("پیام ارسال شد"); } catch (caught) { setError(caught instanceof Error ? caught.message : "ارسال انجام نشد"); } finally { setSending(false); } };
  const close = async () => { try { const data = await apiFetch<Ticket>(`/support/tickets/${id}/close/`, { method:"POST" }); setTicket(data); toast("تیکت بسته شد"); } catch (caught) { setError(caught instanceof Error ? caught.message : "بستن تیکت انجام نشد"); } };
  if (loading) return <div className="container section"><LoadingState /></div>; if (error && !ticket) return <div className="container section"><ErrorState message={error} /></div>; if (!ticket) return null;
  return <div className="container section"><div className="section-head"><div><h1>{ticket.subject}</h1><p>{ticket.order ? `سفارش: ${ticket.order}` : "تیکت عمومی"}</p></div><span className={`status ${ticket.status}`}>{ticketStatus[ticket.status]}</span></div><div className="panel"><div className="messages">{ticket.messages.length ? ticket.messages.map((message) => <div className={`message ${message.author === user?.id ? "mine" : ""}`} key={message.id}><p>{message.body}</p><time>{message.author === user?.id ? "شما" : "پشتیبانی"} · {new Date(message.created_at).toLocaleString("fa-IR")}</time></div>) : <p className="muted">هنوز پیامی ثبت نشده است.</p>}</div>{error && <div className="alert error">{error}</div>}{ticket.status !== "CLOSED" && <form className="stack" onSubmit={send}><textarea className="input" aria-label="متن پیام" minLength={2} value={body} onChange={(e) => setBody(e.target.value)} placeholder="پیام خود را بنویسید..." required /><div className="hero-actions"><button className="button" disabled={sending}>{sending ? "در حال ارسال..." : "ارسال پیام"}</button><button type="button" className="button danger" onClick={() => void close()}>بستن تیکت</button></div></form>}</div></div>;
}
