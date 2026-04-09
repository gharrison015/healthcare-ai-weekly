import { clsx } from "clsx";
import type { ReactNode } from "react";

interface GlassCardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
  as?: "div" | "a";
  href?: string;
  style?: React.CSSProperties;
}

export function GlassCard({
  children,
  className,
  hover = true,
  as: Tag = "div",
  href,
  style,
}: GlassCardProps) {
  const baseStyles: React.CSSProperties = {
    background: "rgba(255, 255, 255, 0.5)",
    backdropFilter: "blur(16px) saturate(1.6)",
    WebkitBackdropFilter: "blur(16px) saturate(1.6)",
    border: "1px solid rgba(255, 255, 255, 0.55)",
    boxShadow:
      "0 1px 2px rgba(0, 0, 0, 0.03), 0 4px 16px rgba(0, 0, 0, 0.04), inset 0 1px 0 rgba(255, 255, 255, 0.6)",
    transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
    ...style,
  };

  const hoverClass = hover ? "glass-card-hover" : "";

  const props: Record<string, unknown> = {
    className: clsx("rounded-2xl", hoverClass, className),
    style: baseStyles,
  };

  if (Tag === "a" && href) {
    props.href = href;
  }

  return <Tag {...(props as React.HTMLAttributes<HTMLElement> & { href?: string })}>{children}</Tag>;
}

/* Inject hover styles via a style tag in the component */
export function GlassCardStyles() {
  return (
    <style
      dangerouslySetInnerHTML={{
        __html: `
          .glass-card-hover:hover {
            background: rgba(255, 255, 255, 0.65) !important;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04), 0 8px 32px rgba(0, 0, 0, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.7) !important;
            transform: translateY(-2px);
          }
        `,
      }}
    />
  );
}
