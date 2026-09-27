import Link from "next/link";
import { Icon } from "@/components/ui";

export function LoadingState({ text = "در حال دریافت اطلاعات..." }: { text?: string }) {
  return <div className="state"><div className="skeleton-stack"><span/><span/><span/></div><p>{text}</p></div>;
}
export function EmptyState({ title, text, href, action }: { title: string; text: string; href?: string; action?: string }) {
  return <div className="state empty"><div className="empty-icon"><Icon name="bag" size={30}/></div><h2>{title}</h2><p>{text}</p>{href && <Link className="button primary" href={href}>{action}<Icon name="arrow-left" size={18}/></Link>}</div>;
}
export function ErrorState({ message, retry }: { message: string; retry?: () => void }) {
  return <div className="state error-state"><div className="empty-icon danger"><Icon name="x" size={30}/></div><h2>مشکلی پیش آمد</h2><p>{message}</p>{retry && <button className="button secondary" onClick={retry}>تلاش دوباره</button>}</div>;
}
