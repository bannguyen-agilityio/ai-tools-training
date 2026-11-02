import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMarkAllRead, useMarkRead, useNotifications } from "../../features/notifications/api";
import { Button } from "./Button";
import { useDismiss } from "./useDismiss";

/** Bell with unread count; the count is part of the accessible name (R35). */
export function NotificationBell() {
  const { data } = useNotifications(true);
  const markRead = useMarkRead();
  const markAll = useMarkAllRead();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  useDismiss(open, ref, () => setOpen(false));
  const unread = data?.unread_count ?? 0;
  const name = unread > 0 ? `Notifications, ${unread} unread` : "Notifications, none unread";

  return (
    <div className="menu" ref={ref}>
      <button
        type="button"
        data-menu-button
        className="icon-btn bell"
        aria-label={name}
        aria-expanded={open}
        aria-controls={open ? "notif-panel" : undefined}
        onClick={() => setOpen((o) => !o)}
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
          <path d="M6 9a6 6 0 0 1 12 0c0 6 2 7 2 7H4s2-1 2-7Z" />
          <path d="M10 20a2 2 0 0 0 4 0" />
        </svg>
        {unread > 0 && (
          <span className="bell__badge num" aria-hidden="true">
            {unread > 99 ? "99+" : unread}
          </span>
        )}
      </button>
      {open && (
        <div id="notif-panel" className="menu__panel menu__panel--wide" role="region" aria-label="Notifications">
          {!data || data.items.length === 0 ? (
            <p className="menu__empty">No notifications</p>
          ) : (
            <>
              <ul className="notif-list">
                {data.items.map((n) => (
                  <li key={n.id}>
                    <button
                      type="button"
                      className="notif"
                      onClick={() => {
                        if (!n.read_at) markRead.mutate(n.id);
                        setOpen(false);
                        navigate(n.link);
                      }}
                    >
                      <span className="notif__title">
                        {!n.read_at && <span className="visually-hidden">Unread: </span>}
                        {n.title}
                      </span>
                      <span className="notif__body">{n.body}</span>
                    </button>
                  </li>
                ))}
              </ul>
              {unread > 0 && (
                <Button variant="ghost" size="sm" onClick={() => markAll.mutate()}>
                  Mark all as read
                </Button>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
