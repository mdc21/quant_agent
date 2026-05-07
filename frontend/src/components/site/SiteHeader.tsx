import { Link } from "@tanstack/react-router";
import { Logo } from "@/components/marks/Logo";
import { Button } from "@/components/ui/button";

const nav = [
  { to: "/platform", label: "Platform" },
  { to: "/engine", label: "Fiduciary Engine" },
  { to: "/insights", label: "Insights" },
  { to: "/pricing", label: "Pricing" },
] as const;

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-40 border-b hairline bg-background/80 backdrop-blur">
      <div className="container-narrow flex h-16 items-center justify-between">
        <Logo />
        <nav className="hidden md:flex items-center gap-8 text-[13px] text-muted-foreground">
          {nav.map((n) => (
            <Link
              key={n.to}
              to={n.to}
              className="hover:text-foreground transition-colors"
              activeProps={{ className: "text-foreground" }}
            >
              {n.label}
            </Link>
          ))}
        </nav>
        <div className="flex items-center gap-2">
          <Button asChild variant="ghost" size="sm" className="hidden sm:inline-flex">
            <Link to="/auth">Sign in</Link>
          </Button>
          <Button asChild size="sm" className="rounded-full px-4">
            <Link to="/dashboard">Open app</Link>
          </Button>
        </div>
      </div>
    </header>
  );
}