"use client";

import { FormEvent, useEffect, useState } from "react";
import { EmptyState, LoadingState } from "@/components/states";
import { PageIntro } from "@/components/ui";
import { useAuth } from "@/contexts/app-context";
import { apiFetch, unwrapResults } from "@/lib/api";
import { formatToman } from "@/lib/format";
import type { Paginated } from "@/lib/types";

type SchoolList = { id: number; title: string; notes: string; status: string; quoted_total: number | null; admin_reply: string; created_at: string };
const statuses: Record<string, string> = { PENDING: "در انتظار قیمت‌گذاری", QUOTED: "پیشنهاد آماده است", CLOSED: "بسته‌شده" };

export default function SchoolListsPage() {
  const { user, loading } = useAuth();
  const [items, setItems] = useState<SchoolList[]>([]);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  useEffect(() => {
    if (user) apiFetch<Paginated<SchoolList>>("/support/school-lists/").then((data) => setItems(unwrapResults(data))).catch((caught) => setError(caught.message));
  }, [user]);
  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const file = data.get("file");
    if (!(file instanceof File) || file.size > 5 * 1024 * 1024) { setError("فایل باید حداکثر ۵ مگابایت باشد."); return; }
    setSaving(true); setError("");
    try {
      const item = await apiFetch<SchoolList>("/support/school-lists/", { method: "POST", body: data });
      setItems((current) => [item, ...current]); form.reset();
    } catch (caught) { setError(caught instanceof Error ? caught.message : "ارسال لیست انجام نشد"); }
    finally { setSaving(false); }
  };
  if (loading) return <div className="container page-shell"><LoadingState/></div>;
  if (!user) return <div className="container page-shell"><EmptyState title="لیست مدرسه‌ات را بفرست" text="با ورود به حساب، تصویر یا PDF لیست را برای قیمت‌گذاری فروشگاه ارسال کن." href="/login?next=/school-lists" action="ورود با موبایل"/></div>;
  return <div className="container page-shell"><PageIntro eyebrow="خرید راحت‌تر" title="قیمت‌گذاری لیست مدرسه" description="تصویر یا PDF را بفرست؛ پاسخ، اقلام پیشنهادی و مبلغ را همین‌جا دریافت می‌کنی."/>
    <div className="address-layout"><form className="panel stack" onSubmit={submit}>
      <label className="field">عنوان لیست<input className="input" name="title" required maxLength={200} placeholder="مثلاً لیست پایه سوم"/></label>
      <label className="field">توضیحات<textarea className="input" name="notes" maxLength={2000} placeholder="برند دلخواه، تعداد دانش‌آموز و نکات خرید"/></label>
      <label className="field">فایل لیست<input className="input" type="file" name="file" accept="image/png,image/jpeg,application/pdf" required/></label>
      <small>JPG، PNG یا PDF تا ۵ مگابایت؛ فایل فقط برای خودت و مدیریت قابل دریافت است.</small>
      {error && <div className="alert error" role="alert">{error}</div>}<button className="button" disabled={saving}>{saving ? "در حال ارسال…" : "ارسال برای قیمت‌گذاری"}</button>
    </form><section className="stack">{items.map((item) => <article className="panel stack" key={item.id}><div><span className="badge">{statuses[item.status]}</span><h2>{item.title}</h2><small>{new Date(item.created_at).toLocaleDateString("fa-IR")}</small></div><p>{item.notes}</p><a className="button secondary" href={`/api/backend/support/school-lists/${item.id}/file/`}>دریافت فایل من</a>{item.quoted_total !== null && <strong>{formatToman(item.quoted_total)}</strong>}{item.admin_reply && <p className="quote-reply">{item.admin_reply}</p>}</article>)}{!items.length && <div className="panel"><p>هنوز لیستی نفرستاده‌ای.</p></div>}</section></div>
  </div>;
}
