import type { ReactNode } from "react";

interface WorkflowCardProps {
  eyebrow: string;
  title: string;
  description: string;
  children: ReactNode;
}

export function WorkflowCard({
  eyebrow,
  title,
  description,
  children,
}: WorkflowCardProps) {
  return (
    <section className="workflow-card">
      <div className="section-label">{eyebrow}</div>
      <h2>{title}</h2>
      <p className="workflow-card__description">{description}</p>
      {children}
    </section>
  );
}
