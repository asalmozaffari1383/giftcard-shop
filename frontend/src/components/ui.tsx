import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode, TextareaHTMLAttributes } from "react";

type IconName = "arrow-left" | "bag" | "check" | "chevron-left" | "clock" | "copy" | "headset" | "menu" | "minus" | "phone" | "plus" | "search" | "shield" | "sparkles" | "star" | "ticket" | "user" | "wallet" | "x";

export function Icon({ name, size = 20 }: { name: IconName; size?: number }) {
  const paths: Record<IconName, ReactNode> = {
    "arrow-left": <><path d="M19 12H5"/><path d="m12 19-7-7 7-7"/></>,
    bag: <><path d="M6 8h12l1 12H5L6 8Z"/><path d="M9 9V6a3 3 0 0 1 6 0v3"/></>,
    check: <path d="m5 12 4 4L19 6"/>,
    "chevron-left": <path d="m15 18-6-6 6-6"/>,
    clock: <><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></>,
    copy: <><rect x="8" y="8" width="11" height="11" rx="2"/><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"/></>,
    headset: <><path d="M4 14v-2a8 8 0 0 1 16 0v2"/><path d="M4 14h3v5H5a1 1 0 0 1-1-1v-4Zm16 0h-3v5h2a1 1 0 0 0 1-1v-4Z"/><path d="M17 19c0 1-1 2-3 2h-2"/></>,
    menu: <><path d="M4 7h16M4 12h16M4 17h16"/></>,
    minus: <path d="M5 12h14"/>,
    phone: <><path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 2 .7 2.9a2 2 0 0 1-.4 2.1L8.1 10a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.9.6 2.9.7a2 2 0 0 1 1.6 1.9Z"/></>,
    plus: <path d="M12 5v14M5 12h14"/>,
    search: <><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></>,
    shield: <><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/><path d="m9 12 2 2 4-4"/></>,
    sparkles: <><path d="m12 3-1 3-3 1 3 1 1 3 1-3 3-1-3-1-1-3Z"/><path d="m19 13-1 2-2 1 2 1 1 2 1-2 2-1-2-1-1-2Z"/><path d="m5 15-1 2-2 1 2 1 1 2 1-2 2-1-2-1-1-2Z"/></>,
    star: <path d="m12 2 3 6 7 .9-5 4.8 1.4 6.8L12 17l-6.4 3.5L7 13.7 2 9l7-.9L12 2Z"/>,
    ticket: <><path d="M3 8a2 2 0 0 0 0 4v5h18v-5a2 2 0 0 0 0-4V3H3v5Z"/><path d="M13 5v2m0 4v2m0 4v-1"/></>,
    user: <><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/></>,
    wallet: <><path d="M3 6h16a2 2 0 0 1 2 2v11H5a2 2 0 0 1-2-2V6Z"/><path d="M3 7V5a2 2 0 0 1 2-2h12"/><path d="M16 12h5v4h-5a2 2 0 0 1 0-4Z"/></>,
    x: <path d="m6 6 12 12M18 6 6 18"/>,
  };
  return <svg aria-hidden="true" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">{paths[name]}</svg>;
}

export function Button({ children, variant = "primary", icon, className = "", ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" | "ghost" | "danger"; icon?: IconName }) {
  return <button className={`button ${variant} ${className}`.trim()} {...props}>{icon && <Icon name={icon} size={18}/>}<span>{children}</span></button>;
}

export function Field({ label, hint, children }: { label: string; hint?: string; children: ReactNode }) {
  return <label className="field"><span className="field-label">{label}</span>{children}{hint && <small className="field-hint">{hint}</small>}</label>;
}

export function Input(props: InputHTMLAttributes<HTMLInputElement>) { return <input className={`input ${props.className || ""}`} {...props}/>; }
export function Textarea(props: TextareaHTMLAttributes<HTMLTextAreaElement>) { return <textarea className={`input textarea ${props.className || ""}`} {...props}/>; }

export function StatusPill({ children, tone = "neutral" }: { children: ReactNode; tone?: "success" | "warning" | "danger" | "info" | "neutral" }) {
  return <span className={`status-pill ${tone}`}>{children}</span>;
}

export function PageIntro({ eyebrow, title, description, action }: { eyebrow?: string; title: string; description?: string; action?: ReactNode }) {
  return <div className="page-intro"><div>{eyebrow && <span className="eyebrow">{eyebrow}</span>}<h1>{title}</h1>{description && <p>{description}</p>}</div>{action}</div>;
}

export function TrustItem({ icon, title, text }: { icon: IconName; title: string; text: string }) {
  return <div className="trust-item"><span className="icon-box"><Icon name={icon}/></span><div><strong>{title}</strong><small>{text}</small></div></div>;
}
