"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import type { Product } from "@/lib/types";
import { ProductCard } from "./product-card";

export function Recommendations({ slug, excluded = [] }: { slug: string; excluded?: string[] }) {
  const [products, setProducts] = useState<Product[]>([]);
  useEffect(() => {
    let active = true;
    apiFetch<Product[]>(`/catalog/products/${encodeURIComponent(slug)}/related/`).then((data) => { if (active) setProducts(data); }).catch(() => { if (active) setProducts([]); });
    return () => { active = false; };
  }, [slug]);
  const visible = products.filter((product) => !excluded.includes(product.slug));
  if (!visible.length) return null;
  return <section className="feature-grid"><div className="section-title"><div><span className="eyebrow">پیشنهاد آلیسان</span><h2>انتخاب‌های مکمل خریدت</h2></div></div><div className="product-grid">{visible.map((product) => <ProductCard key={product.id} product={product}/>)}</div></section>;
}
