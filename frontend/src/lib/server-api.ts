import type { Paginated, Product } from "@/lib/types";

const API_URL = (process.env.INTERNAL_API_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1").replace(/\/$/, "");

function encodedSlug(slug: string) {
  try {
    return encodeURIComponent(decodeURIComponent(slug));
  } catch {
    return encodeURIComponent(slug);
  }
}

export async function getPublicProduct(slug: string): Promise<Product | null> {
  const response = await fetch(`${API_URL}/catalog/products/${encodedSlug(slug)}/`, {
    cache: "no-store",
  });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error(`Product API returned ${response.status}`);
  return response.json() as Promise<Product>;
}

export async function getAllPublicProducts(): Promise<Product[]> {
  const products: Product[] = [];
  for (let page = 1; page <= 100; page += 1) {
    const response = await fetch(`${API_URL}/catalog/products/?page=${page}`, {
      next: { revalidate: 3600 },
    });
    if (!response.ok) break;
    const data = await response.json() as Paginated<Product>;
    products.push(...data.results);
    if (!data.next) break;
  }
  return products;
}
