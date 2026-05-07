import { Link, useLocation } from "@tanstack/react-router";
import { Logo } from "@/components/marks/Logo";
import { LayoutDashboard, Target, PieChart, Zap, Settings, LogOut, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useState } from "react";

const navItems = [
  { to: "/dashboard", label: "Hub", icon: LayoutDashboard },
  { to: "/goals", label: "Goals", icon: Target },
  { to: "/portfolio", label: "Portfolio", icon: PieChart },
  { to: "/quick-advice", label: "Quick advice", icon: Zap },
] as const;

export function AppShell({ children }: { children: React.ReactNode }) {
  const loc = useLocation();
  const [aiOn, setAiOn] = useState(true);
  return (
    <div className="min-h-screen bg-canvas grid grid-cols-1 lg:grid-cols-[260px_1fr]">
      <aside className="border-r hairline hidden lg:flex flex-col bg-card">
        <div className="h-16 px-6 flex items-center border-b hairline"><Logo /></div>
        <nav className="flex-1 p-3 space-y-0.5">
          {navItems.map((n) => {
            const active = loc.pathname === n.to || (n.to !== "/dashboard" && loc.pathname.startsWith(n.to));
            return (
              <Link
                key={n.to}
                to={n.to}
                className={
                  "flex items-center gap-3 px-3 h-10 rounded-lg text-sm transition-colors " +
                  (active ? "bg-secondary text-foreground" : "text-muted-foreground hover:text-foreground hover:bg-secondary/60")
                }
              >
                <n.icon className="size-4" />
                {n.label}
              </Link>
            );
          })}
        </nav>
        <div className="p-4 border-t hairline space-y-3">
          <button
            onClick={() => setAiOn((v) => !v)}
            className="w-full flex items-center justify-between text-xs px-3 py-2.5 rounded-lg border hairline bg-background hover:border-foreground/30 transition-colors"
          >
            <span className="inline-flex items-center gap-2">
              <Sparkles className={"size-3.5 " + (aiOn ? "text-accent" : "text-muted-foreground")} />
              INSA narrative
            </span>
            <span className={"px-2 py-0.5 rounded-full text-[10px] uppercase tracking-wider " + (aiOn ? "bg-accent text-accent-foreground" : "bg-muted text-muted-foreground")}>
              {aiOn ? "On" : "Off"}
            </span>
          </button>
          <div className="flex items-center gap-2">
            <Button asChild variant="ghost" size="sm" className="flex-1 justify-start">
              <Link to="/dashboard"><Settings className="size-4" /> Settings</Link>
            </Button>
            <Button asChild variant="ghost" size="icon">
              <Link to="/"><LogOut className="size-4" /></Link>
            </Button>
          </div>
        </div>
      </aside>
      <div className="flex flex-col min-h-screen">
        <header className="lg:hidden h-16 border-b hairline px-4 flex items-center justify-between bg-card">
          <Logo />
          <Button asChild variant="outline" size="sm"><Link to="/">Exit</Link></Button>
        </header>
        <main className="flex-1">{children}</main>
      </div>
    </div>
  );
}