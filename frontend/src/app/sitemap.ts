import type { MetadataRoute } from "next";
import { getAllPublicProducts } from "@/lib/server-api";

export const dynamic = "force-dynamic";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const siteUrl = (process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000").replace(/\/$/, "");
  const staticPages = ["", "/products", "/about", "/contact", "/delivery-guide", "/refund-policy", "/terms", "/privacy"];
  const products = await getAllPublicProducts().catch(() => []);
  return [
    ...staticPages.map((path, index) => ({
      url: `${siteUrl}${path}`,
      changeFrequency: index < 2 ? "daily" as const : "monthly" as const,
      priority: index === 0 ? 1 : index === 1 ? 0.9 : 0.6,
    })),
    ...products.map((product) => ({
      url: `${siteUrl}/products/${encodeURIComponent(product.slug)}`,
      changeFrequency: "daily" as const,
      priority: 0.8,
    })),
  ];
}
