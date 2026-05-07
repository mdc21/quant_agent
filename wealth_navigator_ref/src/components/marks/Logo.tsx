import { Link } from "@tanstack/react-router";

export function Logo({ to = "/", invert = false }: { to?: string; invert?: boolean }) {
  return (
    <Link to={to} className="group inline-flex items-center gap-2.5">
      <RingMark className={invert ? "text-background" : "text-foreground"} />
      <span
        className={
          "font-serif text-[18px] tracking-tight " +
          (invert ? "text-background" : "text-foreground")
        }
      >
        YourBest<span className="italic">Path</span>
      </span>
    </Link>
  );
}

export function RingMark({ className = "", size = 22 }: { className?: string; size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none" className={className} aria-hidden>
      <circle cx="16" cy="16" r="14" stroke="currentColor" strokeWidth="1" opacity="0.35" />
      <circle cx="16" cy="16" r="9" stroke="currentColor" strokeWidth="1" opacity="0.6" />
      <circle cx="16" cy="16" r="4" fill="currentColor" />
    </svg>
  );
}