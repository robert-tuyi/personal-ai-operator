import { forwardRef, type ButtonHTMLAttributes } from "react";

export type ButtonVariant = "primary" | "secondary" | "success" | "danger" | "ghost";

export const buttonVariantClasses: Record<ButtonVariant, string> = {
  primary: "bg-zinc-900 text-white hover:bg-zinc-700",
  secondary:
    "border border-zinc-300 bg-white text-zinc-700 hover:bg-zinc-50",
  success: "bg-emerald-600 text-white hover:bg-emerald-500",
  danger: "bg-red-600 text-white hover:bg-red-500",
  ghost: "text-zinc-500 hover:bg-zinc-100 hover:text-zinc-900",
};

// Shared with LinkButton so a navigation link can look identical to a real <button>.
export function buttonClasses(variant: ButtonVariant, className = ""): string {
  return `inline-flex min-h-[44px] items-center justify-center gap-1.5 rounded-lg px-3.5 py-2 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${buttonVariantClasses[variant]} ${className}`;
}

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", className = "", ...props }, ref) => (
    <button ref={ref} className={buttonClasses(variant, className)} {...props} />
  )
);
Button.displayName = "Button";
