"use client";
import { FormEvent, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { ProductCard } from "@/components/product-card";
import { EmptyState, ErrorState } from "@/components/states";
import { Icon, PageIntro } from "@/components/ui";
import { apiFetch, unwrapResults } from "@/lib/api";
import { toPersianDigits } from "@/lib/format";
import type { Brand, Category, Paginated, Product } from "@/lib/types";

function ProductSkeletons() { return <div className="product-grid">{Array.from({ length: 8 }).map((_, index) => <div className="product-skeleton" key={index}><div className="skeleton-stack"><span/><span/><span/></div></div>)}</div>; }

export default function ProductsPage() {
  const searchParams = useSearchParams();
  const [data, setData] = useState<Paginated<Product>>({ count:0, next:null, previous:null, results:[] });
  const [categories, setCategories] = useState<Category[]>([]); const [brands, setBrands] = useState<Brand[]>([]);
  const [search, setSearch] = useState(searchParams.get("search") || ""); const [category, setCategory] = useState(""); const [brand, setBrand] = useState(""); const [ordering, setOrdering] = useState("-created_at"); const [page, setPage] = useState(1); const [loading, setLoading] = useState(true); const [error, setError] = useState("");
  const load = async (nextPage = page, filters = { search, category, brand, ordering }) => { setLoading(true); setError(""); const params = new URLSearchParams({ page:String(nextPage), ordering:filters.ordering }); if (filters.search) params.set("search", filters.search); if (filters.category) params.set("category__slug", filters.category); if (filters.brand) params.set("brand__slug", filters.brand); try { setData(await apiFetch<Paginated<Product>>(`/catalog/products/?${params}`)); setPage(nextPage); } catch (caught) { setError(caught instanceof Error ? caught.message : "خطا"); } finally { setLoading(false); } };
  useEffect(() => { void load(1); Promise.all([apiFetch<Category[] | Paginated<Category>>("/catalog/categories/"), apiFetch<Brand[] | Paginated<Brand>>("/catalog/brands/")]).then(([cats, brs]) => { setCategories(unwrapResults(cats)); setBrands(unwrapResults(brs)); }).catch(() => undefined); }, []);
  const submit = (event: FormEvent) => { event.preventDefault(); void load(1); };
  const clear = () => { const reset = { search:"", category:"", brand:"", ordering:"-created_at" }; setSearch(reset.search); setCategory(reset.category); setBrand(reset.brand); setOrdering(reset.ordering); void load(1, reset); };

  return <div className="container page-shell"><PageIntro eyebrow="فروشگاه" title="انتخاب محصول دیجیتال" description="محصول، منطقه و مبلغ مناسب را پیدا کن؛ موجودی هر انتخاب به‌صورت لحظه‌ای نمایش داده می‌شود."/>
    <form className="shop-toolbar" onSubmit={submit}><div className="search-control"><Icon name="search"/><input className="input" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="جست‌وجوی نام محصول یا برند..."/><button type="submit" aria-label="جست‌وجو">جست‌وجو</button></div><select className="input" value={category} onChange={(event) => setCategory(event.target.value)} aria-label="دسته‌بندی"><option value="">همه دسته‌ها</option>{categories.map((item) => <option value={item.slug} key={item.id}>{item.title_fa}</option>)}</select><select className="input" value={brand} onChange={(event) => setBrand(event.target.value)} aria-label="برند"><option value="">همه برندها</option>{brands.map((item) => <option value={item.slug} key={item.id}>{item.title_fa}</option>)}</select><select className="input" value={ordering} onChange={(event) => setOrdering(event.target.value)} aria-label="مرتب‌سازی"><option value="-created_at">جدیدترین</option><option value="title_fa">نام محصول</option><option value="-title_fa">نام معکوس</option></select></form>
    <div className="results-bar"><span><b>{toPersianDigits(data.count)}</b> محصول پیدا شد</span>{(search || category || brand) && <button onClick={clear}><Icon name="x" size={15}/> پاک‌کردن فیلترها</button>}</div>
    {loading ? <ProductSkeletons/> : error ? <ErrorState message={error} retry={() => void load()}/> : data.results.length ? <><div className="product-grid">{data.results.map((product) => <ProductCard product={product} key={product.id}/>)}</div><nav className="pagination" aria-label="صفحه‌بندی"><button className="button secondary" disabled={!data.previous} onClick={() => void load(page - 1)}><Icon name="chevron-left"/> صفحه قبل</button><span>صفحه <b>{toPersianDigits(page)}</b></span><button className="button secondary" disabled={!data.next} onClick={() => void load(page + 1)}>صفحه بعد <Icon name="arrow-left"/></button></nav></> : <EmptyState title="محصولی پیدا نشد" text="عبارت جست‌وجو یا فیلترها را تغییر بده."/>}
  </div>;
}
