"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ProductCard } from "@/components/product-card";
import { EmptyState, ErrorState, LoadingState } from "@/components/states";
import { PageIntro } from "@/components/ui";
import { apiFetch, unwrapResults } from "@/lib/api";
import { toPersianDigits } from "@/lib/format";
import type { Paginated, Product } from "@/lib/types";

export default function SchoolBuilderPage() {
  const [grade, setGrade] = useState("1");
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    setLoading(true); setError("");
    apiFetch<Paginated<Product>>(`/catalog/products/?is_bundle=true&school_grade=${grade}`)
      .then((data) => { if (active) setProducts(unwrapResults(data)); })
      .catch((caught) => { if (active) setError(caught instanceof Error ? caught.message : "دریافت پک‌ها انجام نشد"); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [grade]);
  return <div className="container page-shell"><PageIntro eyebrow="آماده برای مدرسه" title="پک مناسب پایه‌ات را پیدا کن" description="پایه تحصیلی را انتخاب کن تا پک‌های پیشنهادی و اقلام هر پک را ببینی."/>
    <section className="panel stack"><label className="field">پایه تحصیلی<select className="input" value={grade} onChange={(event) => setGrade(event.target.value)}>{Array.from({ length: 12 }, (_, index) => <option value={index + 1} key={index}>پایه {toPersianDigits(index + 1)}</option>)}</select></label><p>لیست مدرسه‌ها متفاوت است؛ پیش از خرید، محتویات پک را با لیست مدرسه تطبیق بده.</p><Link className="button secondary" href="/school-lists">لیست خاص داری؟ برای قیمت‌گذاری بفرست</Link></section>
    {loading ? <LoadingState/> : error ? <ErrorState message={error}/> : products.length ? <div className="product-grid feature-grid">{products.map((product) => <div key={product.id}><ProductCard product={product}/><p className="muted">اقلام: {product.bundle_items.join("، ")}</p></div>)}</div> : <EmptyState title="هنوز پک این پایه ثبت نشده" text="لیست مدرسه را بفرست تا فروشگاه پیشنهاد اختصاصی آماده کند." href="/school-lists" action="ارسال لیست مدرسه"/>}
  </div>;
}
