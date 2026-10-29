import { createContext, useCallback, useContext, useRef, useState, type ReactNode } from "react";
import { Button } from "./Button";

interface ToastItem {
  id: number;
  kind: "success" | "error";
  message: string;
}

const ToastContext = createContext<(kind: ToastItem["kind"], message: string) => void>(() => {});

export const useToast = () => useContext(ToastContext);

/** Toasts persist until dismissed, so they are never missed and need no timing exemption. */
export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);
  const nextId = useRef(0);
  const push = useCallback((kind: ToastItem["kind"], message: string) => {
    setItems((cur) => [...cur, { id: nextId.current++, kind, message }]);
  }, []);
  return (
    <ToastContext.Provider value={push}>
      {children}
      <div className="toasts" role="status" aria-live="polite">
        {items.map((t) => (
          <div key={t.id} className={`toast toast--${t.kind}`}>
            <span aria-hidden="true">{t.kind === "success" ? "✓" : "⚠"}</span>
            <span>
              <span className="visually-hidden">{t.kind === "success" ? "Success: " : "Error: "}</span>
              {t.message}
            </span>
            <Button variant="secondary" onClick={() => setItems((cur) => cur.filter((x) => x.id !== t.id))}>
              Dismiss
            </Button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
