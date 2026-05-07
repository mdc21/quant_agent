import { createFileRoute, Link } from "@tanstack/react-router";
import { AppShell } from "@/components/site/AppShell";
import { ArrowRight, Target, PieChart, Zap, TrendingUp, ShieldCheck, Sparkles } from "lucide-react";

export const Route = createFileRoute("/dashboard")({
  head: () => ({ meta: [{ title: "Hub — YourBestPath" }] }),
  component: Dashboard,
});

function Dashboard() {
  return (
    <AppShell>
      <div className="container-narrow py-10 md:py-14">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <div className="text-xs uppercase tracking-[0.22em] text-accent">Fiduciary Hub</div>
            <h1 className="font-serif text-4xl md:text-5xl mt-2">Welcome back, <span className="italic">Aarav</span>.</h1>
            <p className="text-muted-foreground mt-2">Your plan was last reviewed 3 days ago. Markets moved 0.8% — no rebalance triggers.</p>
          </div>
          <div className="text-right">
            <div className="text-xs text-muted-foreground">Net worth tracked</div>
            <div className="font-serif text-3xl tabular">₹3.82<span className="text-accent">Cr</span></div>
          </div>
        </div>

        {/* Metrics */}
        <div className="mt-10 grid sm:grid-cols-2 lg:grid-cols-4 gap-px bg-border rounded-2xl overflow-hidden border hairline">
          {[
            { k: "Risk profile", v: "Aggressive", sub: "Drawdown band ±18%" },
            { k: "Goal funded", v: "62%", sub: "Of total target" },
            { k: "Expected CAGR", v: "14.2%", sub: "Net of costs" },
            { k: "Rebalance drift", v: "1.4%", sub: "Within tolerance" },
          ].map((m) => (
            <div key={m.k} className="bg-card p-6">
              <div className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">{m.k}</div>
              <div className="mt-3 font-serif text-2xl tabular">{m.v}</div>
              <div className="text-xs text-muted-foreground mt-1">{m.sub}</div>
            </div>
          ))}
        </div>

        {/* Action cards */}
        <h2 className="font-serif text-2xl mt-14">Where to next</h2>
        <div className="mt-5 grid md:grid-cols-3 gap-5">
          <ActionCard
            to="/goals"
            tag="Wizard"
            title="Define goals"
            body="Walk through the survival, safety, growth framework. Five minutes."
            icon={Target}
          />
          <ActionCard
            to="/portfolio"
            tag="Review"
            title="Existing portfolio"
            body="Inspect your sleeves, drift, and migration recommendations."
            icon={PieChart}
          />
          <ActionCard
            to="/quick-advice"
            tag="Calculator"
            title="Quick advice"
            body="Lump-sum or SIP allocation in one screen, no full plan needed."
            icon={Zap}
          />
        </div>

        {/* Insights */}
        <div className="mt-14 grid lg:grid-cols-3 gap-5">
          <div className="lg:col-span-2 rounded-2xl border hairline bg-card p-7">
            <div className="flex items-center justify-between">
              <div className="text-[11px] uppercase tracking-[0.22em] text-accent">INSA narrative · Tier 2 Groq</div>
              <Sparkles className="size-4 text-accent" />
            </div>
            <p className="mt-4 font-serif text-2xl leading-snug">
              "Your equity sleeve is overweight Industrials by 4.2%. Migrating <span className="italic">INDUSTOWER</span> to <span className="italic">HINDUNILVR</span> restores ROCE quality and frees ₹6.8L of headroom for the passive sleeve."
            </p>
            <div className="mt-6 flex flex-wrap gap-2 text-xs">
              {["ROCE > 15%","Sector cap 20%","Tax LTCG ₹0.94L"].map(t => (
                <span key={t} className="border hairline rounded-full px-3 py-1.5 bg-background">{t}</span>
              ))}
            </div>
          </div>
          <div className="rounded-2xl border hairline bg-foreground text-background p-7 relative overflow-hidden">
            <div aria-hidden className="absolute -right-16 -bottom-16 size-64 rounded-full bg-accent/30 blur-3xl" />
            <div className="relative">
              <div className="text-[11px] uppercase tracking-[0.22em] text-background/60">Compliance</div>
              <div className="mt-4 flex items-start gap-3">
                <ShieldCheck className="size-5 text-accent mt-0.5" />
                <div>
                  <div className="font-serif text-xl">UCITS 5/10/40 — Pass</div>
                  <div className="text-xs text-background/70 mt-1">All single-name and concentration tests within mandate.</div>
                </div>
              </div>
              <div className="mt-5 flex items-start gap-3">
                <TrendingUp className="size-5 text-accent mt-0.5" />
                <div>
                  <div className="font-serif text-xl">Capital weighted</div>
                  <div className="text-xs text-background/70 mt-1">60/25/15 multi-cap holds within ±2% buffer.</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}

function ActionCard({ to, tag, title, body, icon: Icon }: { to: string; tag: string; title: string; body: string; icon: any }) {
  return (
    <Link to={to} className="group rounded-2xl border hairline bg-card p-7 hover:border-foreground/30 hover:shadow-[0_20px_60px_-40px_oklch(0.18_0.015_250/0.4)] transition-all">
      <div className="flex items-center justify-between">
        <Icon className="size-5 text-accent" />
        <span className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">{tag}</span>
      </div>
      <div className="mt-10 font-serif text-2xl">{title}</div>
      <p className="text-sm text-muted-foreground mt-2 leading-relaxed">{body}</p>
      <div className="mt-6 inline-flex items-center gap-1.5 text-sm text-accent">
        Continue <ArrowRight className="size-4 transition-transform group-hover:translate-x-1" />
      </div>
    </Link>
  );
}
