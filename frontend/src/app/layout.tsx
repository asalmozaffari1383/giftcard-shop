import type { Metadata } from "next";
import "./globals.css";
import { AppProviders } from "@/contexts/app-context";
import { Header } from "@/components/header";
import { Footer } from "@/components/footer";

export const metadata: Metadata = {
  title: { default: "گیفت‌کارت شاپ", template: "%s | گیفت‌کارت شاپ" },
  description: "خرید آنلاین گیفت کارت و محصولات دیجیتال با تحویل سریع و امن",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="fa" dir="rtl"><body><AppProviders><Header /><main>{children}</main><Footer /></AppProviders></body></html>;
}
