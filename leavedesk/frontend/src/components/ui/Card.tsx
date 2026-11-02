import { useId, type ReactNode } from "react";

export function Card({ className, children }: { className?: string; children: ReactNode }) {
  return <div className={`card ${className ?? ""}`.trim()}>{children}</div>;
}

/** A labelled region: heading plus content, optionally in a Card. */
export function Section({
  title,
  action,
  card = false,
  children,
}: {
  title: string;
  action?: ReactNode;
  card?: boolean;
  children: ReactNode;
}) {
  const id = useId();
  const body = (
    <>
      <div className="section__head">
        <h2 id={id} className="section__title">
          {title}
        </h2>
        {action}
      </div>
      {children}
    </>
  );
  return (
    <section aria-labelledby={id} className={card ? "card" : "section"}>
      {body}
    </section>
  );
}

/** Page title, muted subtitle and at most one primary action on the right. */
export function PageHeader({
  title,
  subtitle,
  action,
  titleId,
}: {
  title: string;
  titleId?: string;
  subtitle?: ReactNode;
  action?: ReactNode;
}) {
  return (
    <header className="page-header">
      <div>
        <h1 id={titleId} className="page-header__title">{title}</h1>
        {subtitle && <p className="page-header__subtitle">{subtitle}</p>}
      </div>
      {action && <div className="page-header__action">{action}</div>}
    </header>
  );
}
