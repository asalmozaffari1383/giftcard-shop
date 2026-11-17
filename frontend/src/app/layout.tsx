import type { Metadata } from "next";
import "./globals.css";
import { AppProviders } from "@/contexts/app-context";
import { Header } from "@/components/header";
import { Footer } from "@/components/footer";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3001"),
  title: { default: "آلیسان | Alisan", template: "%s | آلیسان" },
  description: "خرید دفتر، نوشت‌افزار، پک مدرسه و ست هدیه از فروشگاه لوازم‌تحریر آلیسان؛ با پیگیری ارسال و پشتیبانی سفارش",
  applicationName: "آلیسان",
  alternates: { canonical: "/" },
  openGraph: { type: "website", locale: "fa_IR", siteName: "آلیسان" },
  robots: { index: true, follow: true },
  icons: { icon: "/alisan-mark.svg", shortcut: "/alisan-mark.svg", apple: "/alisan-mark.svg" },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="fa" dir="rtl"><body><AppProviders><Header />{process.env.NEXT_PUBLIC_CATALOG_ONLY === "true" && <p role="status" className="bg-amber-100 px-4 py-3 text-center text-sm text-amber-950">فروشگاه در حال آماده‌سازی است؛ فعلاً محصولات را ببینید. ورود و خرید به‌زودی فعال می‌شود.</p>}<main>{children}</main><Footer /></AppProviders></body></html>;
}
