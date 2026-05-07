import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/site/AppShell";
import { ArrowDown, ArrowUp, Sparkles } from "lucide-react";

export const Route = createFileRoute("/portfolio")({
  head: () => ({ meta: [{ title: "Portfolio — YourBestPath" }] }),
  component: Portfolio,
});

const sleeves = [
  { label: "Equity · Multi-Cap", current: 62, proposed: 58, color: "bg-foreground" },
  { label: "Passive Index", current: 12, proposed: 18, color: "bg-accent" },
  { label: "Fixed Income", current: 18, proposed: 16, color: "bg-[oklch(0.55_0.08_240)]" },
  { label: "Commodities", current: 4, proposed: 5, color: "bg-[var(--gold)]" },
  { label: "Cash", current: 4, proposed: 3, color: "bg-muted-foreground/40" },
];

const actions = [
  { side: "sell", sym: "INDUSTOWER", qty: "120", reason: "Sector concentration · Telecom > 22%", tax: "LTCG ₹0.94L" },
  { side: "buy", sym: "HINDUNILVR", qty: "85", reason: "ROCE 92% · FCF quality A", tax: "—" },
  { side: "buy", sym: "CPSEETF", qty: "1,400", reason: "Passive sleeve under-allocated", tax: "—" },
  { side: "sell", sym: "HDFC GILT 2031", qty: "30", reason: "Duration risk · rebalance to short-tenor", tax: "STCG ₹0.12L" },
];

function Portfolio() {
  return (
    <AppShell>
      <div className="container-narrow py-10 md:py-14">
        <div className="flex items-end justify-between flex-wrap gap-4">
          <div>
            <div className="text-xs uppercase tracking-[0.22em] text-accent">Existing vs proposed</div>
            <h1 className="font-serif text-4xl md:text-5xl mt-2">Portfolio review.</h1>
            <p className="text-muted-foreground mt-2">Capital-weighted comparison with migration attribution per holding.</p>
          </div>
          <div className="text-right text-xs text-muted-foreground">
            <div>Manifest hash · 0x7c1f…a9</div>
            <div className="font-mono mt-1">GENPOA · v.2026.05</div>
          </div>
        </div>

        {/* Sleeve compare */}
        <div className="mt-10 rounded-2xl border hairline bg-card p-7">
          <div className="grid grid-cols-12 text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
            <div className="col-span-4">Sleeve</div>
            <div className="col-span-3">Current</div>
            <div className="col-span-3">Proposed</div>
            <div className="col-span-2 text-right">Delta</div>
          </div>
          <div className="mt-3 divide-y hairline">
            {sleeves.map((s) => {
              const delta = s.proposed - s.current;
              return (
                <div key={s.label} className="grid grid-cols-12 items-center py-4 text-sm">
                  <div className="col-span-4 inline-flex items-center gap-2.5">
                    <span className={"size-2 rounded-full " + s.color} /> {s.label}
                  </div>
                  <div className="col-span-3"><Bar pct={s.current} /></div>
                  <div className="col-span-3"><Bar pct={s.proposed} accent /></div>
                  <div className={"col-span-2 text-right tabular font-mono " + (delta > 0 ? "text-accent" : delta < 0 ? "text-destructive" : "text-muted-foreground")}>
                    {delta > 0 ? "+" : ""}{delta}%
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Actions */}
        <div className="mt-10 grid lg:grid-cols-3 gap-5">
          <div className="lg:col-span-2 rounded-2xl border hairline bg-card overflow-hidden">
            <div className="px-7 py-5 border-b hairline flex items-center justify-between">
              <div>
                <div className="text-[11px] uppercase tracking-[0.22em] text-accent">Tax-aware action list</div>
                <div className="font-serif text-xl mt-1">4 actions · Net tax impact ₹1.06L</div>
              </div>
            </div>
            <div className="divide-y hairline">
              {actions.map((a) => (
                <div key={a.sym + a.side} className="px-7 py-5 flex items-center gap-5">
                  <div className={"size-9 rounded-full inline-flex items-center justify-center " + (a.side === "buy" ? "bg-accent/15 text-accent" : "bg-destructive/10 text-destructive")}>
                    {a.side === "buy" ? <ArrowDown className="size-4" /> : <ArrowUp className="size-4" />}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-baseline gap-3">
                      <span className="font-serif text-lg">{a.sym}</span>
                      <span className="text-xs text-muted-foreground uppercase tracking-[0.16em]">{a.side} · {a.qty}</span>
                    </div>
                    <div className="text-sm text-muted-foreground mt-0.5">{a.reason}</div>
                  </div>
                  <div className="font-mono text-xs text-muted-foreground">{a.tax}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border hairline bg-foreground text-background p-7 relative overflow-hidden">
            <div aria-hidden className="absolute -right-16 -bottom-16 size-64 rounded-full bg-accent/30 blur-3xl" />
            <div className="relative">
              <div className="inline-flex items-center gap-2 text-[11px] uppercase tracking-[0.22em] text-background/60">
                <Sparkles className="size-3.5 text-accent" /> INSA narrative
              </div>
              <p className="mt-4 font-serif text-xl leading-snug">
                Migrating Industrials concentration into FMCG quality lifts portfolio ROCE from <span className="text-accent">14.1%</span> to <span className="text-accent">17.6%</span> with no incremental drawdown band.
              </p>
              <div className="mt-6 text-xs text-background/60">Source · Tier 1 GPT-4o · manifest 0x7c1f…a9</div>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}

function Bar({ pct, accent }: { pct: number; accent?: boolean }) {
  return (
    <div className="flex items-center gap-3">
      <div className="h-1.5 flex-1 bg-secondary rounded-full overflow-hidden">
        <div className={(accent ? "bg-accent" : "bg-foreground") + " h-full rounded-full"} style={{ width: pct + "%" }} />
      </div>
      <span className="tabular text-xs text-muted-foreground w-9 text-right">{pct}%</span>
    </div>
  );
}
