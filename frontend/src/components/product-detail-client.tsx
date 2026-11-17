"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { Icon, StatusPill, TrustItem } from "@/components/ui";
import { useAuth, useCart, useToast } from "@/contexts/app-context";
import { apiFetch, unwrapResults } from "@/lib/api";
import { formatToman, mediaUrl, toPersianDigits } from "@/lib/format";
import { Recommendations } from "@/components/recommendations";
import type { Paginated, Product, Review, Variant, WishlistItem } from "@/lib/types";

export function ProductDetailClient({ product }: { product: Product }) {
  const [reviews, setReviews] = useState<Review[]>([]);
  const [selected, setSelected] = useState<number | null>(product.variants.find((item) => item.stock > 0)?.id || null);
  const [quantity, setQuantity] = useState(1);
  const [adding, setAdding] = useState(false);
  const [wishlistId, setWishlistId] = useState<number | null>(null);
  const { user } = useAuth();
  const { addItem } = useCart();
  const toast = useToast();
  const router = useRouter();
  useEffect(() => {
    apiFetch<Paginated<Review> | Review[]>(`/reviews/?product=${product.id}`)
      .then((data) => setReviews(unwrapResults(data)))
      .catch(() => setReviews([]));
  }, [product.id]);
  useEffect(() => { setWishlistId(null); if (user) apiFetch<WishlistItem[]>("/auth/wishlist/").then((data) => setWishlistId(data.find((item) => item.product === product.id)?.id || null)).catch(() => undefined); }, [user, product.id]);
  const variant = useMemo(() => product.variants.find((item) => item.id === selected), [product, selected]);
  const add = async () => {
    if (!user) {
      router.push(`/login?next=/products/${product.slug}`);
      return;
    }
    if (!variant) return;
    setAdding(true);
    try {
      await addItem(variant.id, quantity);
      router.push("/cart");
    } catch (caught) {
      toast(caught instanceof Error ? caught.message : "افزودن به سبد انجام نشد", "error");
    } finally {
      setAdding(false);
    }
  };
  const saveWishlist = async () => {
    if (!user) { router.push(`/login?next=/products/${product.slug}`); return; }
    try {
      if (wishlistId) { await apiFetch(`/auth/wishlist/${wishlistId}/`, { method:"DELETE" }); setWishlistId(null); toast("از علاقه‌مندی‌ها حذف شد"); }
      else { const saved = await apiFetch<WishlistItem>("/auth/wishlist/", { method: "POST", body: JSON.stringify({ product: product.id }) }); setWishlistId(saved.id); toast("به علاقه‌مندی‌ها اضافه شد"); }
    } catch (caught) { toast(caught instanceof Error ? caught.message : "ذخیره محصول انجام نشد", "error"); }
  };
  const image = mediaUrl(product.image);
  const availableCount = product.variants.filter((item) => item.stock > 0).length;
  return <div className="container page-shell"><nav className="breadcrumbs"><Link href="/">خانه</Link><Icon name="chevron-left" size={14}/><Link href="/products">فروشگاه</Link><Icon name="chevron-left" size={14}/><span>{product.title_fa}</span></nav>
    <section className="product-detail-grid"><div className="product-gallery"><div className="detail-image">{image ? <Image src={image} alt={product.title_fa} width={800} height={620} priority unoptimized/> : <div className="detail-placeholder"><span>{product.brand?.title_fa?.slice(0,1) || "A"}</span><b>{product.brand?.title_fa || "محصول آلیسان"}</b><small>ALISAN PRODUCT</small></div>}</div><div className="gallery-note"><Icon name="shield"/><span>اطلاعات سفارش شما امن نگهداری می‌شود و پشتیبانی آلیسان همراه شماست.</span></div></div>
      <div className="product-buy-box"><div className="product-detail-head"><div><span className="eyebrow">{product.brand?.title_fa || product.category.title_fa}</span><h1>{product.title_fa}</h1></div><div className="product-detail-actions"><button type="button" className={`wishlist-toggle ${wishlistId ? "active" : ""}`} onClick={() => void saveWishlist()} aria-label="افزودن به علاقه‌مندی"><Icon name="star" size={18}/></button>{product.instant_delivery && <StatusPill tone="success"><Icon name="clock" size={14}/> آماده ارسال</StatusPill>}</div></div><div className="detail-rating"><span><Icon name="star" size={17}/> {toPersianDigits(product.rating_average || "—")}</span><small>{toPersianDigits(product.rating_count)} نظر خریدار</small><i/><small>{toPersianDigits(availableCount)} انتخاب موجود</small></div><p className="description">{product.description}</p>
        {Object.keys(product.attributes || {}).length > 0 && <div className="product-attributes">{Object.entries(product.attributes).map(([key, value]) => <div key={key}><small>{key}</small><b>{value}</b></div>)}</div>}
        <div className="variant-heading"><div><h2>بسته یا نوع محصول را انتخاب کن</h2><p>گزینه‌های ناموجود غیرفعال شده‌اند.</p></div>{variant && <span className="stock-confirm"><Icon name="check" size={15}/> موجود در انبار</span>}</div>
        <div className="variant-list">{product.variants.map((item: Variant) => <button type="button" className={`variant ${selected === item.id ? "selected" : ""}`} disabled={item.stock < 1} onClick={() => { setSelected(item.id); setQuantity(1); }} key={item.id}><div><span>{item.label}</span><small>{product.kind === "PHYSICAL" ? "لوازم‌تحریر" : `${item.region} · ${item.currency}`}</small></div><div><b>{formatToman(item.price_toman)}</b><small>{item.stock > 0 ? `${toPersianDigits(item.stock)} عدد` : "ناموجود"}</small></div>{selected === item.id && <i><Icon name="check" size={14}/></i>}</button>)}</div>
        {variant ? <div className="purchase-panel"><div className="purchase-price"><small>مبلغ قابل پرداخت</small>{variant.old_price_toman && <del>{formatToman(variant.old_price_toman * quantity)}</del>}<strong>{formatToman(variant.price_toman * quantity)}</strong></div><div className="quantity-control" aria-label="انتخاب تعداد"><button type="button" onClick={() => setQuantity((value) => Math.max(1, value - 1))} disabled={quantity <= 1}><Icon name="minus" size={17}/></button><span>{toPersianDigits(quantity)}</span><button type="button" onClick={() => setQuantity((value) => Math.min(20, variant.stock, value + 1))} disabled={quantity >= Math.min(20, variant.stock)}><Icon name="plus" size={17}/></button></div><button type="button" className="button primary buy-button" onClick={() => void add()} disabled={adding}><Icon name="bag"/>{adding ? "در حال افزودن..." : user ? "افزودن و مشاهده سبد" : "ورود و ادامه خرید"}</button></div> : <div className="unavailable-box"><Icon name="clock"/><div><b>این محصول فعلاً موجود نیست</b><span>گزینه دیگری انتخاب کن یا بعداً دوباره بررسی کن.</span></div></div>}
        <div className="buy-trust"><TrustItem icon="shield" title="پرداخت کنترل‌شده" text="تأیید مبلغ سمت سرور"/><TrustItem icon="clock" title="ارسال قابل پیگیری" text="از آماده‌سازی تا تحویل"/></div>
      </div></section>
    <Recommendations slug={product.slug}/><section className="reviews-section"><div className="section-title"><div><span className="eyebrow">تجربه خریداران</span><h2>نظرهای ثبت‌شده</h2></div><Link href="/reviews">ثبت نظر <Icon name="arrow-left" size={16}/></Link></div>{reviews.length ? <div className="review-grid">{reviews.map((review) => <article className="review-card" key={review.id}><div><span className="review-avatar">خ</span><div><b>خریدار تأییدشده</b><small>{new Date(review.created_at).toLocaleDateString("fa-IR")}</small></div><span className="rating"><Icon name="star" size={14}/> {toPersianDigits(review.rating)}</span></div><p>{review.body}</p></article>)}</div> : <div className="reviews-empty"><Icon name="star" size={28}/><div><b>هنوز نظری ثبت نشده است</b><span>بعد از خرید تکمیل‌شده، امکان ثبت نظر فعال می‌شود.</span></div></div>}</section>
  </div>;
}
