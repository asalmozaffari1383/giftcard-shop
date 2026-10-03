import Link from "next/link";
import Image from "next/image";
import type { Product } from "@/lib/types";
import { formatToman, mediaUrl, toPersianDigits } from "@/lib/format";
import { Icon, StatusPill } from "@/components/ui";

export function ProductCard({ product }: { product: Product }) {
  const available = product.variants.filter((variant) => variant.stock > 0);
  const priced = [...product.variants].sort((a, b) => a.price_toman - b.price_toman);
  const cheapest = [...available].sort((a, b) => a.price_toman - b.price_toman)[0] || priced[0];
  const inStock = available.length > 0;
  const oldPrice = cheapest?.old_price_toman;
  const discount = oldPrice && cheapest ? Math.round((1 - cheapest.price_toman / oldPrice) * 100) : 0;
  const image = mediaUrl(product.image);

  return <article className={`product-card ${!inStock ? "out-of-stock" : ""}`}>
    <Link href={`/products/${product.slug}`} className="product-image" aria-label={`مشاهده ${product.title_fa}`}>
      <span className="product-glow"/>
      {image ? <Image src={image} alt={product.title_fa} width={560} height={380} unoptimized /> : <div className="product-placeholder"><span>{product.brand?.title_fa?.slice(0, 1) || "G"}</span><small>{product.brand?.title_fa || product.category.title_fa}</small></div>}
      <div className="product-badges">{product.instant_delivery && <StatusPill tone="success"><Icon name="clock" size={14}/> تحویل آنی</StatusPill>}{discount > 0 && <StatusPill tone="danger">٪{toPersianDigits(discount)} تخفیف</StatusPill>}</div>
      {!inStock && <span className="unavailable-overlay">در انتظار موجودی</span>}
    </Link>
    <div className="product-body">
      <div className="product-meta"><span>{product.brand?.title_fa || product.category.title_fa}</span><span className="rating"><Icon name="star" size={14}/> {toPersianDigits(product.rating_average || "—")} <small>({toPersianDigits(product.rating_count)})</small></span></div>
      <h3><Link href={`/products/${product.slug}`}>{product.title_fa}</Link></h3>
      <div className="stock-line"><span className={inStock ? "stock-dot available" : "stock-dot"}/>{inStock ? `${toPersianDigits(available.length)} انتخاب موجود` : "فعلاً غیرقابل خرید"}</div>
      <div className="card-footer"><div className="price-block">{oldPrice && <del>{formatToman(oldPrice)}</del>}<strong>{cheapest ? formatToman(cheapest.price_toman) : "در انتظار قیمت"}</strong>{cheapest && <small>{inStock ? "شروع قیمت" : "آخرین قیمت ثبت‌شده"}</small>}</div><Link className="card-action" href={`/products/${product.slug}`} aria-label={`مشاهده ${product.title_fa}`}><Icon name="chevron-left"/></Link></div>
    </div>
  </article>;
}
