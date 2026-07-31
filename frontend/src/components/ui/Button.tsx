import { forwardRef, type ButtonHTMLAttributes } from "react";

type Variant = "primary" | "secondary" | "success" | "danger" | "ghost";

const variantClasses: Record<Variant, string> = {
  primary: "bg-zinc-900 text-white hover:bg-zinc-700",
  secondary:
    "border border-zinc-300 bg-white text-zinc-700 hover:bg-zinc-50",
  success: "bg-emerald-600 text-white hover:bg-emerald-500",
  danger: "bg-red-600 text-white hover:bg-red-500",
  ghost: "text-zinc-500 hover:bg-zinc-100 hover:text-zinc-900",
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", className = "", ...props }, ref) => (
    <button
      ref={ref}
      className={`inline-flex min-h-[44px] items-center justify-center gap-1.5 rounded-lg px-3.5 py-2 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${variantClasses[variant]} ${className}`}
      {...props}
    />
  )
);
Button.displayName = "Button";
