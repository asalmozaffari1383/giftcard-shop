"use client";

import { FormEvent, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth, useToast } from "@/contexts/app-context";
import { apiFetch } from "@/lib/api";
import { normalizeIranianPhone } from "@/lib/format";
import type { User } from "@/lib/types";

export default function LoginPage() {
  const [step, setStep] = useState<"phone" | "code">("phone");
  const [phone, setPhone] = useState("");
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const { setSession } = useAuth();
  const toast = useToast();
  const router = useRouter();
  const params = useSearchParams();

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    const normalized = normalizeIranianPhone(phone);
    try {
      if (step === "phone") {
        await apiFetch("/auth/otp/request/", { method: "POST", body: JSON.stringify({ phone_number: normalized }) });
        setPhone(normalized);
        setStep("code");
        toast("کد ورود ایجاد شد");
      } else {
        const data = await apiFetch<{ user: User }>("/auth/otp/verify/", {
          method: "POST", body: JSON.stringify({ phone_number: normalized, code }),
        });
        setSession(data.user);
        toast("با موفقیت وارد شدید");
        router.replace(params.get("next") || "/account");
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "ورود انجام نشد");
    } finally {
      setLoading(false);
    }
  };

  return <div className="container section"><div className="panel auth-card">
    <div className="eyebrow">ورود امن با موبایل</div>
    <h1>{step === "phone" ? "ورود یا ثبت‌نام" : "تأیید کد یک‌بارمصرف"}</h1>
    <p className="muted">{step === "phone" ? "شماره موبایل ایران را وارد کنید." : `کد ایجادشده برای ${phone} را وارد کنید.`}</p>
    {step === "code" && <div className="alert success">کد تست محیط توسعه: ۱۲۳۴۵۶</div>}
    {error && <div className="alert error">{error}</div>}
    <form className="stack" onSubmit={submit}>
      {step === "phone" ? <div className="field"><label>شماره موبایل</label><input className="input" inputMode="tel" dir="ltr" placeholder="09123456789" value={phone} onChange={(event) => setPhone(event.target.value)} required /></div> : <div className="field"><label>کد ۶ رقمی</label><input className="input" inputMode="numeric" dir="ltr" maxLength={6} value={code} onChange={(event) => setCode(event.target.value)} required autoFocus /></div>}
      <button className="button full" disabled={loading}>{loading ? "لطفاً صبر کنید..." : step === "phone" ? "دریافت کد" : "ورود"}</button>
      {step === "code" && <button type="button" className="link-button" onClick={() => setStep("phone")}>تغییر شماره</button>}
    </form>
  </div></div>;
}
