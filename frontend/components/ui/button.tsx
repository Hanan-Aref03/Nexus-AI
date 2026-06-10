import Link from "next/link";
import type { AnchorHTMLAttributes, ButtonHTMLAttributes, ReactNode } from "react";

import { cn } from "@/lib/utils";

type ButtonVariant = "primary" | "secondary" | "ghost" | "outline" | "danger";
type ButtonSize = "sm" | "md" | "lg";

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    "bg-primary text-primary-foreground shadow-lg shadow-primary/20 hover:bg-primary/90 hover:shadow-primary/30",
  secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
  ghost: "bg-transparent text-foreground hover:bg-white/5",
  outline: "border border-border bg-transparent text-foreground hover:bg-white/5",
  danger: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
};

const sizeClasses: Record<ButtonSize, string> = {
  sm: "h-9 px-3 text-sm",
  md: "h-11 px-4 text-sm",
  lg: "h-12 px-5 text-base",
};

interface SharedProps {
  children: ReactNode;
  className?: string;
  variant?: ButtonVariant;
  size?: ButtonSize;
}

type AnchorButtonProps = SharedProps & AnchorHTMLAttributes<HTMLAnchorElement> & { href: string };
type NativeButtonProps = SharedProps & ButtonHTMLAttributes<HTMLButtonElement> & { href?: never };

export function Button(props: AnchorButtonProps): any;
export function Button(props: NativeButtonProps): any;
export function Button({
  children,
  className,
  variant = "primary",
  size = "md",
  href,
  ...rest
}: AnchorButtonProps | NativeButtonProps) {
  const classes = cn(
    "inline-flex items-center justify-center gap-2 rounded-full border font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-ring/60 focus:ring-offset-0",
    variantClasses[variant],
    sizeClasses[size],
    className,
  );

  if (href) {
    const { href: _ignored, ...anchorProps } = rest as AnchorButtonProps;
    if (href.startsWith("/")) {
      return (
        <Link className={classes} href={href as any} {...anchorProps}>
          {children}
        </Link>
      );
    }

    return (
      <a className={classes} href={href} {...anchorProps}>
        {children}
      </a>
    );
  }

  return (
    <button className={classes} type="button" {...(rest as ButtonHTMLAttributes<HTMLButtonElement>)}>
      {children}
    </button>
  );
}
