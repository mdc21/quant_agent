import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { AppShell } from "@/components/site/AppShell";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Sparkles, Zap, Loader2, Briefcase, Layers, Info } from "lucide-react";
import { api } from "@/lib/api";
import { toast } from "sonner";

export const Route = createFileRoute("/quick-advice")({
  head: () => ({ meta: [{ title: "Quick advice — YourBestPath" }] }),
  component: Quick,
});

function Quick() {
  const navigate = useNavigate();
  const [mode, setMode] = useState<"Lump-sum" | "SIP">("Lump-sum");
  const [amount, setAmount] = useState(500000);
  const [horizon, setHorizon] = useState<"short" | "medium" | "long">("long");
  const [risk, setRisk] = useState<"Conservative" | "Balanced" | "Growth">("Growth");
  const [loading, setLoading] = useState(false);
  const [advice, setAdvice] = useState<any>(null);

  const getAdvice = async () => {
    setLoading(true);
    try {
      const user = JSON.parse(localStorage.getItem("user") || "{}");
      const res = await api.portfolio.getQuickAdvice({
        user_key: user.user_key || "guest",
        investment_type: mode,
        amount: amount,
        horizon: horizon,
        purpose: "Wealth Creation",
        risk_profile: risk
      });
      setAdvice(res);
    } catch (err: any) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    getAdvice();
  }, [mode, risk, horizon]); // Refresh on parameter change

  return (
    <AppShell>
      <div className="container-narrow py-10 md:py-14 grid lg:grid-cols-12 gap-10">
        <div className="lg:col-span-4">
          <div className="text-xs uppercase tracking-[0.22em] text-accent font-semibold">Quick advice</div>
          <h1 className="font-serif text-4xl mt-2">One screen. One answer.</h1>
          <p className="mt-3 text-muted-foreground">Skip the full plan. Get institutional-grade instrument selection in seconds.</p>

          <div className="mt-8 rounded-2xl border hairline bg-card p-6 space-y-5 shadow-sm">
            <div className="grid grid-cols-2 p-1 bg-secondary rounded-full text-sm">
              {(["Lump-sum", "SIP"] as const).map(m => (
                <button key={m} onClick={() => setMode(m)} className={"h-9 rounded-full transition-all " + (mode === m ? "bg-background text-foreground shadow-sm" : "text-muted-foreground")}>
                  {m}
                </button>
              ))}
            </div>

            <div className="space-y-1.5">
              <Label className="text-xs uppercase tracking-[0.16em] text-muted-foreground">{mode === "Lump-sum" ? "Capital (₹)" : "Monthly SIP (₹)"}</Label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">₹</span>
                <Input type="number" className="pl-7" value={amount} onChange={(e) => setAmount(Number(e.target.value))} />
              </div>
            </div>

            <Choice label="Horizon" value={horizon} setValue={setHorizon as any} options={[["short","< 3y"],["medium","3–7y"],["long","7y+"]]} />
            <Choice label="Risk" value={risk} setValue={setRisk as any} options={[["Conservative","Conservative"],["Balanced","Balanced"],["Growth","Growth"]]} />

            <Button className="w-full h-11 rounded-full mt-2" onClick={getAdvice} disabled={loading}>
              {loading ? <Loader2 className="mr-2 size-4 animate-spin" /> : <Zap className="mr-2 size-4" />}
              Recalculate Optimization
            </Button>
          </div>
        </div>

        <div className="lg:col-span-8">
          {loading && !advice ? (
             <div className="h-96 flex flex-col items-center justify-center text-muted-foreground">
                <Loader2 className="size-8 animate-spin mb-4 text-accent" />
                <p className="font-serif">Scanning market for {risk} {mode}...</p>
             </div>
          ) : advice ? (
            <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
               <div className="rounded-2xl border hairline bg-card p-8 relative overflow-hidden">
                  <div aria-hidden className="absolute -right-20 -top-20 size-64 rounded-full bg-accent/5 blur-3xl" />
                  
                  <div className="relative flex items-center justify-between">
                    <div>
                      <div className="text-[11px] uppercase tracking-[0.22em] text-accent">Strategic recommendation</div>
                      <h2 className="font-serif text-3xl mt-2">{risk} · {mode}</h2>
                    </div>
                    <Sparkles className="size-6 text-accent" />
                  </div>

                  <div className="mt-8 rounded-xl bg-secondary/50 p-6 border hairline">
                    <p className="font-serif text-xl leading-snug italic text-foreground/80">
                      "{advice.narrative}"
                    </p>
                  </div>

                  <div className="mt-10 grid sm:grid-cols-3 gap-6">
                     <Stat k="Equity Cap" v={fmtInr(advice.metrics.equity_cap)} />
                     <Stat k="Defensive Cap" v={fmtInr(advice.metrics.defensive_cap)} />
                     <Stat k="Instrument Count" v={advice.equity_sleeve.length + advice.passive_sleeve.length} />
                  </div>

                  {/* 🔬 Selection Funnel (Recruitment Analogy) */}
                  <div className="mt-10 p-6 rounded-xl border hairline bg-accent/5 border-accent/20">
                    <h3 className="font-serif text-lg flex items-center gap-2 text-accent">
                      <Zap className="size-4" /> The Selection Funnel
                    </h3>
                    <p className="mt-2 text-xs text-muted-foreground leading-relaxed">
                      Our fiduciary engine evaluates the entire market, but only a few make it into your portfolio. 
                      Think of it as a strict corporate recruitment process.
                    </p>
                    
                    <div className="mt-6 grid grid-cols-1 sm:grid-cols-3 gap-4">
                      <div className="p-3 rounded-lg bg-background/60 border hairline">
                        <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold">1. Universe</div>
                        <div className="text-sm font-medium mt-1">The Applicants</div>
                        <div className="text-[10px] text-muted-foreground mt-1">~117 companies screened for ROCE & Governance.</div>
                      </div>
                      <div className="p-3 rounded-lg bg-background/60 border hairline">
                        <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold">2. Sieve</div>
                        <div className="text-sm font-medium mt-1">The Interview</div>
                        <div className="text-[10px] text-muted-foreground mt-1">Deep-dive into NIM, GNPA & Culture.</div>
                      </div>
                      <div className="p-3 rounded-lg bg-accent/10 border border-accent/30 shadow-sm">
                        <div className="text-[10px] uppercase tracking-wider text-accent font-semibold">3. Recruited</div>
                        <div className="text-sm font-medium mt-1">The Dream Team</div>
                        <div className="text-[10px] text-accent/80 mt-1">Final {advice.equity_sleeve.length} stocks optimized for your risk profile.</div>
                      </div>
                    </div>
                  </div>

                  <div className="mt-12 grid md:grid-cols-2 gap-8">
                     <div>
                        <div className="flex items-center gap-2 mb-4">
                           <Briefcase className="size-4 text-accent" />
                           <h3 className="font-serif text-xl">Recruited Equities</h3>
                        </div>
                        <div className="space-y-2">
                           {advice.equity_sleeve.slice(0, 8).map((s: any) => (
                             <div key={s.symbol} className="flex items-center justify-between p-3 rounded-lg border hairline bg-background/50 hover:border-accent/40 transition-colors group">
                                <div>
                                  <div className="font-medium">{s.symbol}</div>
                                  <div className="text-[10px] text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity">Recruited for: {s.cap}</div>
                                </div>
                                <span className="text-xs text-muted-foreground">{fmtInr(s.target_capital)}</span>
                             </div>
                           ))}
                        </div>
                     </div>
                     <div>
                        <div className="flex items-center gap-2 mb-4">
                           <Layers className="size-4 text-accent" />
                           <h3 className="font-serif text-xl">Passive Sleeve</h3>
                        </div>
                        <div className="space-y-2">
                           {advice.passive_sleeve.map((s: any) => (
                             <div key={s.ticker} className="flex items-center justify-between p-3 rounded-lg border hairline bg-background/50">
                                <span className="font-medium truncate mr-2">{s.name || s.ticker}</span>
                                <span className="text-xs text-muted-foreground whitespace-nowrap">{fmtInr(s.target_capital)}</span>
                             </div>
                           ))}
                        </div>
                     </div>
                  </div>

                  {/* 📡 The Applicants (Research Universe) */}
                  <div className="mt-14 pt-8 border-t hairline">
                     <div className="flex items-center justify-between mb-4">
                        <h3 className="font-serif text-lg">Shortlisted Applicants</h3>
                        <span className="text-[10px] text-muted-foreground uppercase tracking-widest">Active Watchlist</span>
                     </div>
                     <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                        {advice.research_universe
                           .filter((s: any) => !advice.equity_sleeve.some((es: any) => es.symbol === s.symbol))
                           .slice(0, 8)
                           .map((s: any) => (
                              <div key={s.symbol} className="px-3 py-2 rounded-lg border hairline bg-secondary/5 text-xs flex items-center justify-between">
                                 <span className="text-muted-foreground font-medium">{s.symbol}</span>
                                 <span className="text-[9px] font-bold text-accent/60">{(s.conviction * 10).toFixed(1)}</span>
                              </div>
                           ))}
                     </div>
                  </div>

                  <div className="mt-10 pt-8 border-t hairline flex items-center justify-between">
                     <p className="text-[11px] text-muted-foreground flex items-center gap-1.5">
                        <Info className="size-3" /> Fiduciary mandate: UCITS 5/10/40 · ROCE {'>'} 1.5% · Sector Cap {advice.metrics.risk_profile === "Aggressive" || advice.metrics.risk_profile === "Growth" ? "25%" : advice.metrics.risk_profile === "Conservative" ? "15%" : "20%"}
                     </p>
                     <Button 
                        variant="ghost" 
                        className="rounded-full text-accent"
                        onClick={() => navigate({ to: "/portfolio" })}
                     >
                        View full plan manifest →
                     </Button>
                  </div>
               </div>
            </div>
          ) : null}
        </div>
      </div>
    </AppShell>
  );
}

function Choice<T extends string>({ label, value, setValue, options }: { label: string; value: T; setValue: (v: T) => void; options: Array<[T, string]> }) {
  return (
    <div className="space-y-1.5">
      <Label className="text-xs uppercase tracking-[0.16em] text-muted-foreground">{label}</Label>
      <div className="grid grid-cols-3 gap-2">
        {options.map(([v, l]) => (
          <button
            key={v}
            onClick={() => setValue(v)}
            className={"h-10 rounded-lg border text-sm transition-colors " + (value === v ? "border-foreground bg-foreground text-background" : "hairline bg-background hover:border-foreground/40")}
          >
            {l}
          </button>
        ))}
      </div>
    </div>
  );
}

function Stat({ k, v }: { k: string; v: string | number }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground">{k}</div>
      <div className="font-serif text-2xl mt-1">{v}</div>
    </div>
  );
}

function fmtInr(val: number) {
  if (val >= 10000000) return `₹${(val / 10000000).toFixed(1)}Cr`;
  if (val >= 100000) return `₹${(val / 100000).toFixed(1)}L`;
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0
  }).format(val);
}
