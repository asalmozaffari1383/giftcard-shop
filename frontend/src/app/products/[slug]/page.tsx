import { notFound } from "next/navigation";
import { ProductDetailClient } from "@/components/product-detail-client";
import { getPublicProduct } from "@/lib/server-api";

export const dynamic = "force-dynamic";

export default async function ProductDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const product = await getPublicProduct(slug).catch(() => null);
  if (!product) notFound();
  const siteUrl = (process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000").replace(/\/$/, "");
  const canonical = `${siteUrl}/products/${encodeURIComponent(product.slug)}`;
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Product",
    name: product.title_fa,
    description: product.seo_description || product.description,
    image: product.image ? [product.image] : undefined,
    sku: product.sku,
    brand: product.brand ? { "@type": "Brand", name: product.brand.title_fa } : undefined,
    aggregateRating: product.rating_count > 0 ? {
      "@type": "AggregateRating",
      ratingValue: product.rating_average,
      reviewCount: product.rating_count,
    } : undefined,
    offers: product.variants.map((variant) => ({
      "@type": "Offer",
      sku: variant.sku,
      url: `${canonical}?variant=${variant.id}`,
      priceCurrency: "IRR",
      price: variant.price_rial,
      availability: variant.stock > 0 ? "https://schema.org/InStock" : "https://schema.org/OutOfStock",
      itemCondition: "https://schema.org/NewCondition",
    })),
  };
  return <>
    <script type="application/ld+json" dangerouslySetInnerHTML={{
      __html: JSON.stringify(jsonLd).replace(/</g, "\\u003c"),
    }}/>
    <ProductDetailClient product={product}/>
  </>;
}
