import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "گیفت‌کارت شاپ",
    short_name: "گیفت‌کارت",
    description: "فروشگاه محصولات دیجیتال و گیفت کارت",
    start_url: "/",
    display: "standalone",
    background_color: "#f7f5fb",
    theme_color: "#6d28d9",
    lang: "fa",
    dir: "rtl",
  };
}
