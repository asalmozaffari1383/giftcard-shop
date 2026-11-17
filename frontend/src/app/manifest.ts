import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "آلیسان | Alisan",
    short_name: "آلیسان",
    description: "فروشگاه لوازم‌تحریر و پک‌های مدرسه آلیسان",
    icons: [{ src: "/alisan-mark.svg", sizes: "any", type: "image/svg+xml", purpose: "any" }],
    start_url: "/",
    display: "standalone",
    background_color: "#fffaf5",
    theme_color: "#ef7898",
    lang: "fa",
    dir: "rtl",
  };
}
