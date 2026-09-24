"use client";
import { ErrorState } from "@/components/states";
export default function ErrorPage({ reset }: { reset: () => void }) { return <div className="container section"><ErrorState message="نمایش این صفحه با خطا مواجه شد." retry={reset} /></div>; }
