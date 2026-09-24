import Link from "next/link";

export function LoadingState({ text = "در حال دریافت اطلاعات..." }: { text?: string }) {
  return <div className="state"><div className="spinner" /> <p>{text}</p></div>;
}
export function EmptyState({ title, text, href, action }: { title: string; text: string; href?: string; action?: string }) {
  return <div className="state empty"><div className="empty-icon">◇</div><h2>{title}</h2><p>{text}</p>{href && <Link className="button" href={href}>{action}</Link>}</div>;
}
export function ErrorState({ message, retry }: { message: string; retry?: () => void }) {
  return <div className="alert error"><span>{message}</span>{retry && <button onClick={retry}>تلاش دوباره</button>}</div>;
}
