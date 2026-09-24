import type { Metadata } from "next";
import type { Product } from "@/lib/types";

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await params;
  const base = (process.env.INTERNAL_API_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1").replace(/\/$/, "");
  try {
    const response = await fetch(`${base}/catalog/products/${slug}/`, { next: { revalidate: 300 } });
    if (!response.ok) return { title: "محصول" };
    const product = await response.json() as Product;
    return {
      title: product.seo_title || product.title_fa,
      description: product.seo_description || product.description.slice(0, 160),
      openGraph: { title: product.seo_title || product.title_fa, description: product.seo_description },
    };
  } catch {
    return { title: "محصول" };
  }
}

export default function ProductLayout({ children }: { children: React.ReactNode }) { return children; }
