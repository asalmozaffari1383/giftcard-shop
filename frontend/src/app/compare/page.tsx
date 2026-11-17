"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { PageIntro } from "@/components/ui";
import { apiFetch } from "@/lib/api";
import { formatToman, toPersianDigits } from "@/lib/format";
import type { Paginated, Product } from "@/lib/types";

export default function ComparePage() {
  const params = useSearchParams();
  const [options, setOptions] = useState<Product[]>([]);
  const [first, setFirst] = useState(params.get("first") || "");
  const [second, setSecond] = useState("");
  const [products, setProducts] = useState<Product[]>([]);
  const [page, setPage] = useState(1);
  const [more, setMore] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    apiFetch<Paginated<Product>>(`/catalog/products/?page=${page}`).then((data) => {
      setOptions((current) => [...current, ...data.results.filter((item) => !current.some((existing) => existing.id === item.id))]); setMore(Boolean(data.next));
    }).catch((caught) => setError(caught.message));
  }, [page]);
  useEffect(() => {
    let active = true;
    setProducts([]); setError("");
    Promise.all([first, second].filter(Boolean).map((slug) => apiFetch<Product>(`/catalog/products/${encodeURIComponent(slug)}/`)))
      .then((data) => { if (active) setProducts(data); }).catch((caught) => { if (active) setError(caught.message); });
    return () => { active = false; };
  }, [first, second]);
  const attributes = Array.from(new Set(products.flatMap((product) => Object.keys(product.attributes))));
  return <div className="container page-shell"><PageIntro eyebrow="انتخاب آگاهانه" title="مقایسه محصولات" description="قیمت، برند، موجودی و ویژگی‌های دو محصول را کنار هم ببین."/>
    <div className="panel compare-controls">{([first, second] as const).map((value, index) => <label className="field" key={index}>محصول {toPersianDigits(index + 1)}<select className="input" value={value} onChange={(event) => (index === 0 ? setFirst : setSecond)(event.target.value)}><option value="">انتخاب محصول</option>{value && !options.some((item) => item.slug === value) && <option value={value}>{products.find((item) => item.slug === value)?.title_fa || value}</option>}{options.map((item) => <option key={item.id} value={item.slug}>{item.title_fa}</option>)}</select></label>)}{more && <button className="button secondary" onClick={() => setPage(page + 1)}>بارگذاری محصولات بیشتر</button>}</div>
    {error && <div className="alert error">{error}</div>}
    {products.length ? <div className="compare-table"><table><thead><tr><th>مشخصات</th>{products.map((product, index) => <th key={`${product.id}-${index}`}><Link href={`/products/${product.slug}`}>{product.title_fa}</Link></th>)}</tr></thead><tbody>
      <tr><th>برند</th>{products.map((product, index) => <td key={index}>{product.brand?.title_fa}</td>)}</tr>
      <tr><th>قیمت نهایی</th>{products.map((product, index) => <td key={index}>{formatToman(product.final_price)}</td>)}</tr>
      <tr><th>وضعیت موجودی</th>{products.map((product, index) => <td key={index}>{product.variants.some((item) => item.stock > 0) ? "موجود" : "ناموجود"}</td>)}</tr>
      {attributes.map((attribute) => <tr key={attribute}><th>{attribute}</th>{products.map((product, index) => <td key={index}>{product.attributes[attribute] || "—"}</td>)}</tr>)}
    </tbody></table></div> : <p className="panel">دو محصول را برای مقایسه انتخاب کن.</p>}
  </div>;
}
