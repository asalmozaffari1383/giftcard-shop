import type { Metadata } from "next";
import { getPublicProduct } from "@/lib/server-api";

const siteUrl = (process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000").replace(/\/$/, "");

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await params;
  const product = await getPublicProduct(slug).catch(() => null);
  if (!product) return { title: "محصول یافت نشد", robots: { index: false, follow: false } };
  const canonical = `${siteUrl}/products/${encodeURIComponent(product.slug)}`;
  const title = product.seo_title || product.title_fa;
  const description = product.seo_description || product.description.slice(0, 160);
  return {
    title,
    description,
    alternates: { canonical },
    openGraph: {
      type: "website",
      locale: "fa_IR",
      url: canonical,
      title,
      description,
      images: product.image ? [{ url: product.image, alt: product.title_fa }] : undefined,
    },
  };
}

export default function ProductLayout({ children }: Readonly<{
  children: React.ReactNode;
}>) {
  return children;
}
