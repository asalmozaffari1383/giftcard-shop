export type Paginated<T> = { count: number; next: string | null; previous: string | null; results: T[] };

export type Profile = { first_name: string; last_name: string; email: string };
export type User = { id: number; phone_number: string; is_verified: boolean; is_customer: boolean; profile: Profile | null };
export type Category = { id: number; parent: number | null; title_fa: string; slug: string };
export type Brand = { id: number; title_fa: string; slug: string };
export type Variant = {
  id: number; sku: string; label: string; face_value: string; currency: string; region: string;
  price_toman: number; price_rial: number; old_price_toman: number | null; stock: number;
};
export type Product = {
  id: number; sku: string; title_fa: string; slug: string; description: string; image: string | null;
  seo_title: string; seo_description: string; instant_delivery: boolean; brand: Brand | null;
  category: Category; rating_average: string | null; rating_count: number; variants: Variant[];
};
export type CartItem = { id: number; variant: number; quantity: number; price_toman: number; product_title: string; product_slug: string; variant_label: string };
export type OrderItem = { id: number; sku: string; product_title: string; product_slug: string; variant_label: string; region: string; quantity: number; unit_price_toman: number; codes: string[] };
export type OrderStatusHistory = { id: number; previous_status: string; status: string; label: string; created_at: string };
export type Order = {
  id: string; status: "PENDING" | "PROCESSING" | "COMPLETED" | "CANCELED" | "FAILED" | "REFUNDED";
  subtotal_toman: number; discount_toman: number; total_toman: number; created_at: string;
  created_at_jalali: string; expires_at: string; paid_at: string | null; items: OrderItem[]; status_history: OrderStatusHistory[];
};
export type Payment = {
  id: string; order: string; gateway: string; amount_toman: number;
  status: string; reference_id: string; verified_at: string | null;
};
export type Review = { id: number; product: number; product_title: string; product_slug: string; rating: number; body: string; status: string; created_at: string };
export type ReviewProductOption = { id: number; title_fa: string; slug: string };
export type TicketMessage = { id: number; author: number; body: string; created_at: string };
export type Ticket = {
  id: number; user: number; subject: string; status: "OPEN" | "WAITING" | "CLOSED";
  order: string | null; messages: TicketMessage[]; created_at: string;
};
