"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { LoadingState } from "@/components/states";
import { useAuth, useToast } from "@/contexts/app-context";
import { apiFetch } from "@/lib/api";
import type { Profile } from "@/lib/types";

export default function AccountPage() {
  const { user, loading, refreshUser } = useAuth(); const toast = useToast(); const router = useRouter(); const [profile, setProfile] = useState<Profile>({ first_name:"", last_name:"", email:"" }); const [saving, setSaving] = useState(false); const [error, setError] = useState("");
  useEffect(() => { if (!loading && !user) router.replace("/login?next=/account"); if (user?.profile) setProfile(user.profile); }, [loading, user, router]);
  const save = async (event: FormEvent) => { event.preventDefault(); setSaving(true); setError(""); try { await apiFetch<Profile>("/auth/profile/", { method:"PATCH", body:JSON.stringify(profile) }); await refreshUser(); toast("پروفایل ذخیره شد"); } catch (caught) { setError(caught instanceof Error ? caught.message : "ذخیره انجام نشد"); } finally { setSaving(false); } };
  if (loading || !user) return <div className="container section"><LoadingState /></div>;
  return <div className="container section"><div className="section-head"><div><h1>حساب کاربری</h1><p dir="ltr">{user.phone_number}</p></div><Link className="button secondary" href="/orders">سفارش‌های من</Link></div><form className="panel stack" onSubmit={save}><h2>اطلاعات پروفایل</h2><div className="field"><label>نام</label><input className="input" value={profile.first_name} onChange={(e) => setProfile({ ...profile, first_name:e.target.value })} /></div><div className="field"><label>نام خانوادگی</label><input className="input" value={profile.last_name} onChange={(e) => setProfile({ ...profile, last_name:e.target.value })} /></div><div className="field"><label>ایمیل</label><input className="input" type="email" dir="ltr" value={profile.email} onChange={(e) => setProfile({ ...profile, email:e.target.value })} /></div>{error && <div className="alert error">{error}</div>}<button className="button" disabled={saving}>{saving ? "در حال ذخیره..." : "ذخیره تغییرات"}</button></form></div>;
}
