"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { apiFetch } from "@/lib/api";
import type { CartItem, User } from "@/lib/types";

type Toast = { id: number; text: string; kind: "success" | "error" };
type AuthContextValue = {
  user: User | null; loading: boolean; setSession: (user: User) => void;
  refreshUser: () => Promise<void>; logout: () => Promise<void>;
};
type CartContextValue = {
  items: CartItem[]; loading: boolean; count: number; total: number;
  refreshCart: () => Promise<void>; addItem: (variant: number, quantity: number) => Promise<void>;
  updateItem: (item: CartItem, quantity: number) => Promise<void>;
  removeItem: (item: CartItem) => Promise<void>; clearLocalCart: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);
const CartContext = createContext<CartContextValue | null>(null);
const ToastContext = createContext<(text: string, kind?: Toast["kind"]) => void>(() => undefined);

export function AppProviders({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [items, setItems] = useState<CartItem[]>([]);
  const [cartLoading, setCartLoading] = useState(false);
  const [toasts, setToasts] = useState<Toast[]>([]);

  const toast = useCallback((text: string, kind: Toast["kind"] = "success") => {
    const id = Date.now();
    setToasts((current) => [...current, { id, text, kind }]);
    window.setTimeout(() => setToasts((current) => current.filter((item) => item.id !== id)), 3500);
  }, []);

  const refreshUser = useCallback(async () => {
    try { setUser(await apiFetch<User>("/auth/me/")); }
    catch { setUser(null); }
    finally { setAuthLoading(false); }
  }, []);

  const refreshCart = useCallback(async () => {
    if (!user) { setItems([]); return; }
    setCartLoading(true);
    try { setItems(await apiFetch<CartItem[]>("/orders/cart/")); }
    catch { setItems([]); }
    finally { setCartLoading(false); }
  }, [user]);

  useEffect(() => { void refreshUser(); }, [refreshUser]);
  useEffect(() => { if (user) void refreshCart(); else setItems([]); }, [user, refreshCart]);

  const setSession = useCallback((nextUser: User) => {
    setUser(nextUser); setAuthLoading(false);
  }, []);

  const logout = useCallback(async () => {
    await apiFetch<void>("/auth/token/logout/", { method: "POST" }).catch(() => undefined);
    setUser(null); setItems([]); toast("از حساب خارج شدید");
  }, [toast]);

  const addItem = useCallback(async (variant: number, quantity: number) => {
    if (!user) throw new Error("برای افزودن به سبد ابتدا وارد شوید.");
    const item = await apiFetch<CartItem>("/orders/cart/", { method: "POST", body: JSON.stringify({ variant, quantity }) });
    setItems((current) => [...current.filter((entry) => entry.variant !== variant), item]);
    toast("محصول به سبد خرید اضافه شد");
  }, [toast, user]);

  const updateItem = useCallback(async (item: CartItem, quantity: number) => {
    const updated = await apiFetch<CartItem>(`/orders/cart/items/${item.id}/`, {
      method: "PATCH", body: JSON.stringify({ quantity }),
    });
    setItems((current) => current.map((entry) => entry.id === item.id ? updated : entry));
  }, []);

  const removeItem = useCallback(async (item: CartItem) => {
    await apiFetch<void>(`/orders/cart/items/${item.id}/`, { method: "DELETE" });
    setItems((current) => current.filter((entry) => entry.id !== item.id));
    toast("محصول از سبد حذف شد");
  }, [toast]);

  const clearLocalCart = useCallback(() => { setItems([]); }, []);
  const cartValue = useMemo(() => ({ items, loading: cartLoading,
    count: items.reduce((sum, item) => sum + item.quantity, 0),
    total: items.reduce((sum, item) => sum + item.price_toman * item.quantity, 0),
    refreshCart, addItem, updateItem, removeItem, clearLocalCart,
  }), [items, cartLoading, refreshCart, addItem, updateItem, removeItem, clearLocalCart]);

  return (
    <ToastContext.Provider value={toast}>
      <AuthContext.Provider value={{ user, loading: authLoading, setSession, refreshUser, logout }}>
        <CartContext.Provider value={cartValue}>{children}</CartContext.Provider>
      </AuthContext.Provider>
      <div className="toast-stack" aria-live="polite">
        {toasts.map((item) => <div className={`toast ${item.kind}`} key={item.id}>{item.text}</div>)}
      </div>
    </ToastContext.Provider>
  );
}

export function useAuth() { const value = useContext(AuthContext); if (!value) throw new Error("AuthProvider missing"); return value; }
export function useCart() { const value = useContext(CartContext); if (!value) throw new Error("CartProvider missing"); return value; }
export function useToast() { return useContext(ToastContext); }
