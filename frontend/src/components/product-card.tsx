import Link from "next/link";
import Image from "next/image";
import type { Product } from "@/lib/types";
import { formatToman, mediaUrl, toPersianDigits } from "@/lib/format";

export function ProductCard({ product }: { product: Product }) {
  const available = product.variants.filter((variant) => variant.stock > 0);
  const cheapest = [...available].sort((a, b) => a.price_toman - b.price_toman)[0];
  return <article className="product-card">
    <Link href={`/products/${product.slug}`} className="product-image" aria-label={product.title_fa}>
      {mediaUrl(product.image) ? <Image src={mediaUrl(product.image)!} alt={product.title_fa} width={560} height={380} unoptimized /> : <span>Gift Card</span>}
      {product.instant_delivery && <b className="badge">تحویل آنی</b>}
    </Link>
    <div className="product-body">
      <div className="eyebrow">{product.brand?.title_fa || product.category.title_fa}</div>
      <h3><Link href={`/products/${product.slug}`}>{product.title_fa}</Link></h3>
      <div className="rating">★ {toPersianDigits(product.rating_average || "بدون امتیاز")} <small>({toPersianDigits(product.rating_count)})</small></div>
      <div className="card-footer"><span>{cheapest ? `از ${formatToman(cheapest.price_toman)}` : "ناموجود"}</span><Link href={`/products/${product.slug}`}>مشاهده</Link></div>
    </div>
  </article>;
}
