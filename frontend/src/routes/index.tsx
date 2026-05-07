import { createFileRoute, Link } from "@tanstack/react-router";
import { SiteShell } from "@/components/site/SiteShell";
import { Button } from "@/components/ui/button";
import { ArrowRight, ArrowUpRight, ShieldCheck, Sparkles, Layers, LineChart } from "lucide-react";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "YourBestPath — Fiduciary Wealth, Engineered" },
      { name: "description", content: "Define goals. Profile risk. Receive a transparent, multi-agent fiduciary portfolio strategy." },
    ],
  }),
  component: Landing,
});

function Landing() {
  return (
    <SiteShell>
      <Hero />
      <Pillars />
      <EngineSection />
      <JourneySection />
      <ClosingCTA />
    </SiteShell>
  );
}

function Hero() {
  return (
    <section className="relative overflow-hidden">
      <BgGrid />
      <div className="container-narrow pt-20 pb-24 md:pt-28 md:pb-32 grid lg:grid-cols-12 gap-12 items-end">
        <div className="lg:col-span-7">
          <div className="inline-flex items-center gap-2 text-[11px] uppercase tracking-[0.2em] text-muted-foreground border hairline rounded-full px-3 py-1.5">
            <span className="size-1.5 rounded-full bg-accent" /> Fiduciary · Capital-weighted · Auditable
          </div>
          <h1 className="mt-7 font-serif text-[44px] sm:text-[60px] lg:text-[76px] leading-[1.02] tracking-tight">
            Wealth, designed
            <br />
            around <span className="italic text-accent">your goals</span>—
            <br />
            not a product shelf.
          </h1>
          <p className="mt-7 text-base sm:text-lg text-muted-foreground max-w-xl leading-relaxed">
            YourBestPath is a fiduciary platform that turns survival, safety, and growth goals into a defensible portfolio. Multi-agent quant engine. Transparent reasoning. Tax-aware rebalancing.
          </p>
          <div className="mt-10 flex flex-wrap gap-3">
            <Button asChild size="lg" className="rounded-full h-12 px-6">
              <Link to="/dashboard">
                Start your plan <ArrowRight className="ml-1" />
              </Link>
            </Button>
            <Button asChild size="lg" variant="outline" className="rounded-full h-12 px-6 border-foreground/20">
              <Link to="/engine">
                See the engine
              </Link>
            </Button>
          </div>
          <div className="mt-10 flex items-center gap-6 text-xs text-muted-foreground">
            <span className="inline-flex items-center gap-2"><ShieldCheck className="size-3.5" /> AES-256 · SOC2 mindset</span>
            <span className="hidden sm:inline-flex items-center gap-2"><Layers className="size-3.5" /> UCITS 5/10/40 aware</span>
          </div>
        </div>

        <div className="lg:col-span-5">
          <PortfolioCard />
        </div>
      </div>
    </section>
  );
}

function BgGrid() {
  return (
    <div aria-hidden className="pointer-events-none absolute inset-0 -z-10">
      <div className="absolute inset-0 [background-image:linear-gradient(to_right,oklch(0.9_0.008_250/_0.5)_1px,transparent_1px),linear-gradient(to_bottom,oklch(0.9_0.008_250/_0.5)_1px,transparent_1px)] [background-size:64px_64px] [mask-image:radial-gradient(ellipse_at_top,black_30%,transparent_75%)]" />
      <div className="absolute -top-40 right-[-10%] size-[520px] rounded-full bg-accent/5 blur-3xl" />
    </div>
  );
}

function PortfolioCard() {
  const sleeves = [
    { label: "Equity (Multi-Cap)", weight: 58, color: "bg-foreground" },
    { label: "Passive Index", weight: 18, color: "bg-accent" },
    { label: "Fixed Income", weight: 16, color: "bg-[oklch(0.55_0.08_240)]" },
    { label: "Commodities", weight: 5, color: "bg-[var(--gold)]" },
    { label: "Cash", weight: 3, color: "bg-muted-foreground/40" },
  ];
  return (
    <div className="relative">
      <div className="absolute -inset-4 bg-gradient-to-br from-accent/10 via-transparent to-transparent rounded-3xl -z-10" />
      <div className="rounded-2xl border hairline bg-card p-6 shadow-[0_30px_80px_-40px_oklch(0.18_0.015_250/0.4)]">
        <div className="flex items-center justify-between text-xs">
          <span className="uppercase tracking-[0.18em] text-muted-foreground">Proposed portfolio</span>
          <span className="font-mono text-foreground/70">v.2026.05</span>
        </div>
        <div className="mt-5 flex items-baseline justify-between">
          <div>
            <div className="font-serif text-4xl tabular">₹3.82<span className="text-accent">Cr</span></div>
            <div className="text-xs text-muted-foreground mt-1">Aggressive · 12y horizon</div>
          </div>
          <div className="text-right">
            <div className="text-xs text-muted-foreground">Expected CAGR</div>
            <div className="font-serif text-2xl tabular">14.2<span className="text-base">%</span></div>
          </div>
        </div>

        <div className="mt-6 h-2.5 w-full overflow-hidden rounded-full flex">
          {sleeves.map((s) => (
            <div key={s.label} className={s.color} style={{ width: `${s.weight}%` }} />
          ))}
        </div>

        <ul className="mt-6 space-y-3 text-sm">
          {sleeves.map((s) => (
            <li key={s.label} className="flex items-center justify-between">
              <span className="inline-flex items-center gap-2.5">
                <span className={"size-2 rounded-full " + s.color} />
                <span className="text-foreground/85">{s.label}</span>
              </span>
              <span className="tabular text-foreground/70">{s.weight}%</span>
            </li>
          ))}
        </ul>

        <div className="mt-6 pt-5 border-t hairline flex items-center justify-between text-xs text-muted-foreground">
          <span>4-layer agent cascade · GENPOA</span>
          <span className="inline-flex items-center gap-1 text-accent">Audit ledger <ArrowUpRight className="size-3" /></span>
        </div>
      </div>
    </div>
  );
}

function Pillars() {
  const items = [
    { tag: "01 · Survival", title: "Protect what you've built", body: "Emergency reserves, insurance ladders, and short-tenor liquidity sleeves before any growth bet." },
    { tag: "02 · Safety", title: "Fund the non-negotiables", body: "Education, home, healthcare. Goal-funded with capital-protected instruments and risk-matched horizons." },
    { tag: "03 · Growth", title: "Compound with conviction", body: "Multi-cap 60/25/15, sector ceilings, ROCE & FCF quality screens — concentrated, not crowded." },
  ];
  return (
    <section className="border-t hairline">
      <div className="container-narrow py-20 md:py-28">
        <SectionHeader eyebrow="Three pillars" title={<>A framework before a portfolio.</>} />
        <div className="mt-14 grid md:grid-cols-3 gap-px bg-border rounded-2xl overflow-hidden border hairline">
          {items.map((it) => (
            <div key={it.tag} className="bg-background p-8 md:p-10">
              <div className="text-[11px] uppercase tracking-[0.22em] text-accent">{it.tag}</div>
              <h3 className="mt-5 font-serif text-2xl leading-tight">{it.title}</h3>
              <p className="mt-3 text-sm text-muted-foreground leading-relaxed">{it.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function EngineSection() {
  const tiers = [
    { n: "T1", name: "GPT-4o", role: "High-reasoning · cross-portfolio narrative" },
    { n: "T2", name: "Groq · Llama 3.1", role: "High-speed standard chat fallback" },
    { n: "T3", name: "Gemini 1.5 Flash", role: "Long-context manifest parsing" },
    { n: "T4", name: "Local Engine", role: "Deterministic guardrail — no hallucination by silence" },
  ];
  return (
    <section className="border-t hairline bg-secondary/40">
      <div className="container-narrow py-20 md:py-28 grid lg:grid-cols-12 gap-12">
        <div className="lg:col-span-5">
          <SectionHeader eyebrow="Fiduciary engine" title={<>Four layers. <br/>One <span className="italic text-accent">defensible</span> answer.</>} />
          <p className="mt-6 text-muted-foreground leading-relaxed max-w-md">
            Every recommendation is generated against an immutable Decision Manifest — your existing book, the proposed book, and the reason for every migration.
          </p>
          <div className="mt-8 flex flex-wrap gap-2 text-xs">
            {["ROCE > 15%","FCF Quality","UCITS 5/10/40","20% Sector cap","Tax-aware rebalance"].map(t => (
              <span key={t} className="border hairline rounded-full px-3 py-1.5 bg-background">{t}</span>
            ))}
          </div>
        </div>
        <div className="lg:col-span-7">
          <ol className="space-y-px rounded-2xl overflow-hidden border hairline bg-border">
            {tiers.map((t) => (
              <li key={t.n} className="bg-background p-6 flex items-start gap-6 group">
                <span className="font-mono text-xs text-accent w-8 pt-1">{t.n}</span>
                <div className="flex-1">
                  <div className="font-serif text-xl">{t.name}</div>
                  <div className="text-sm text-muted-foreground mt-1">{t.role}</div>
                </div>
                <Sparkles className="size-4 text-muted-foreground/50 group-hover:text-accent transition-colors" />
              </li>
            ))}
          </ol>
        </div>
      </div>
    </section>
  );
}

function JourneySection() {
  const steps = [
    { k: "Define", body: "A guided wizard distils survival, safety and growth goals into capital-tagged horizons." , icon: Layers},
    { k: "Profile", body: "Risk mandate translates directly into solver constraints — sector ceilings, drawdown bands.", icon: ShieldCheck },
    { k: "Optimise", body: "GENPOA produces a capital-weighted proposed book with migration attribution per holding.", icon: LineChart },
    { k: "Rebalance", body: "Tax-aware action list — what to sell, what to fund, in what order, with cost trade-offs surfaced.", icon: Sparkles },
  ];
  return (
    <section className="border-t hairline">
      <div className="container-narrow py-20 md:py-28">
        <SectionHeader eyebrow="The journey" title={<>From a blank page to a board-ready plan.</>} />
        <div className="mt-14 grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {steps.map((s, i) => (
            <div key={s.k} className="border hairline rounded-2xl p-6 bg-card hover:border-foreground/30 transition-colors">
              <div className="flex items-center justify-between">
                <s.icon className="size-5 text-accent" />
                <span className="font-mono text-[11px] text-muted-foreground">0{i+1}</span>
              </div>
              <div className="mt-8 font-serif text-2xl">{s.k}</div>
              <p className="mt-2 text-sm text-muted-foreground leading-relaxed">{s.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function ClosingCTA() {
  return (
    <section className="border-t hairline">
      <div className="container-narrow py-24">
        <div className="rounded-3xl border hairline bg-foreground text-background p-10 md:p-16 relative overflow-hidden">
          <div aria-hidden className="absolute -right-24 -bottom-24 size-[420px] rounded-full bg-accent/30 blur-3xl" />
          <div className="relative max-w-2xl">
            <h2 className="font-serif text-4xl md:text-5xl leading-[1.05]">
              Build a portfolio your <span className="italic text-accent">future self</span> would sign off on.
            </h2>
            <p className="mt-5 text-background/70 max-w-xl">
              Open the platform, define your goals, and see a fiduciary-grade proposed portfolio in under five minutes.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Button asChild size="lg" variant="secondary" className="rounded-full h-12 px-6 bg-background text-foreground hover:bg-background/90">
                <Link to="/dashboard">Open the dashboard <ArrowRight className="ml-1" /></Link>
              </Button>
              <Button asChild size="lg" variant="ghost" className="rounded-full h-12 px-6 text-background hover:bg-background/10">
                <Link to="/quick-advice">Try quick advice</Link>
              </Button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function SectionHeader({ eyebrow, title }: { eyebrow: string; title: React.ReactNode }) {
  return (
    <div className="max-w-3xl">
      <div className="text-[11px] uppercase tracking-[0.22em] text-accent">{eyebrow}</div>
      <h2 className="mt-4 font-serif text-3xl md:text-5xl leading-[1.05] tracking-tight">{title}</h2>
    </div>
  );
}
