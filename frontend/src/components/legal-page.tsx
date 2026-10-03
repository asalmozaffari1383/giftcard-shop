type Section = { title: string; paragraphs: string[] };

export function LegalPage({ eyebrow, title, intro, sections }: {
  eyebrow: string;
  title: string;
  intro: string;
  sections: Section[];
}) {
  return <div className="container page-shell legal-page">
    <header className="legal-hero"><span className="eyebrow">{eyebrow}</span><h1>{title}</h1><p>{intro}</p></header>
    <div className="legal-grid">
      <article className="panel legal-content">{sections.map((section) => <section key={section.title}><h2>{section.title}</h2>{section.paragraphs.map((paragraph) => <p key={paragraph}>{paragraph}</p>)}</section>)}</article>
      <aside className="panel legal-aside"><h2>اطلاعات فروشگاه</h2><dl><dt>نام کسب‌وکار</dt><dd>{process.env.NEXT_PUBLIC_BUSINESS_NAME || "در حال تکمیل"}</dd><dt>شماره پشتیبانی</dt><dd dir="ltr">{process.env.NEXT_PUBLIC_SUPPORT_PHONE || "در حال تکمیل"}</dd><dt>ساعات پاسخ‌گویی</dt><dd>{process.env.NEXT_PUBLIC_SUPPORT_HOURS || "در حال تکمیل"}</dd><dt>نشانی</dt><dd>{process.env.NEXT_PUBLIC_BUSINESS_ADDRESS || "در حال تکمیل"}</dd></dl><p>برای پیگیری سفارش، ثبت تیکت از داخل حساب کاربری سریع‌ترین مسیر است.</p></aside>
    </div>
  </div>;
}
