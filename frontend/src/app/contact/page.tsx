"use client";
import { FormEvent, useState } from "react";
import { apiFetch } from "@/lib/api";
import { useToast } from "@/contexts/app-context";

export default function ContactPage() {
  const [form, setForm] = useState({ name:"", phone_number:"", body:"" }); const [loading, setLoading] = useState(false); const [error, setError] = useState(""); const toast = useToast();
  const submit = async (event: FormEvent) => { event.preventDefault(); setLoading(true); setError(""); try { await apiFetch("/support/inquiries/", { method:"POST", body:JSON.stringify(form) }); setForm({ name:"", phone_number:"", body:"" }); toast("پیام شما ثبت شد"); } catch (caught) { setError(caught instanceof Error ? caught.message : "ارسال انجام نشد"); } finally { setLoading(false); } };
  return <div className="container section"><div className="section-head"><div><h1>تماس با ما</h1><p>برای سؤال‌های عمومی پیام بگذارید؛ مشکلات سفارش را از بخش تیکت پیگیری کنید.</p></div></div><form className="panel stack auth-card" onSubmit={submit}><div className="field"><label>نام</label><input className="input" value={form.name} onChange={(event) => setForm({ ...form, name:event.target.value })} required /></div><div className="field"><label>شماره موبایل</label><input className="input" dir="ltr" value={form.phone_number} onChange={(event) => setForm({ ...form, phone_number:event.target.value })} required /></div><div className="field"><label>پیام</label><textarea className="input" minLength={10} value={form.body} onChange={(event) => setForm({ ...form, body:event.target.value })} required /></div>{error && <div className="alert error">{error}</div>}<button className="button" disabled={loading}>{loading ? "در حال ارسال..." : "ارسال پیام"}</button></form></div>;
}
