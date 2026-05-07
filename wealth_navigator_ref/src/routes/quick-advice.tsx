import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/site/AppShell";
import { useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Sparkles, Zap } from "lucide-react";

export const Route = createFileRoute("/quick-advice")({
  head: () => ({ meta: [{ title: "Quick advice — YourBestPath" }] }),
  component: Quick,
});

function Quick() {
  const [mode, setMode] = useState<"lump" | "sip">("lump");
  const [amount, setAmount] = useState(500000);
  const [horizon, setHorizon] = useState<"short" | "medium" | "long">("long");
  const [risk, setRisk] = useState<"Conservative" | "Balanced" | "Growth">("Growth");
  const [aiOn, setAiOn] = useState(true);

  const allocation = useMemo(() => allocate(risk, horizon), [risk, horizon]);

  return (
    <AppShell>
      <div className="container-narrow py-10 md:py-14 grid lg:grid-cols-12 gap-8">
        <div className="lg:col-span-5">
          <div className="text-xs uppercase tracking-[0.22em] text-accent">Quick advice</div>
          <h1 className="font-serif text-4xl mt-2">One screen. One answer.</h1>
          <p className="mt-3 text-muted-foreground">Skip the full plan. Get a deterministic allocation, with optional INSA narrative.</p>

          <div className="mt-8 rounded-2xl border hairline bg-card p-6 space-y-5">
            <div className="grid grid-cols-2 p-1 bg-secondary rounded-full text-sm">
              {(["lump","sip"] as const).map(m => (
                <button key={m} onClick={() => setMode(m)} className={"h-9 rounded-full transition-all " + (mode === m ? "bg-background shadow-sm" : "text-muted-foreground")}>
                  {m === "lump" ? "Lump-sum" : "Monthly SIP"}
                </button>
              ))}
            </div>

            <div className="space-y-1.5">
              <Label className="text-xs uppercase tracking-[0.16em] text-muted-foreground">{mode === "lump" ? "Capital (₹)" : "Monthly contribution (₹)"}</Label>
              <Input type="number" value={amount} onChange={(e) => setAmount(Number(e.target.value))} />
            </div>

            <Choice label="Horizon" value={horizon} setValue={setHorizon as any} options={[["short","< 3y"],["medium","3–7y"],["long","7y+"]]} />
            <Choice label="Risk" value={risk} setValue={setRisk as any} options={[["Conservative","Conservative"],["Balanced","Balanced"],["Growth","Growth"]]} />

            <div className="flex items-center justify-between border-t hairline pt-4">
              <span className="text-xs text-muted-foreground inline-flex items-center gap-2"><Sparkles className={"size-3.5 " + (aiOn ? "text-accent" : "")} /> INSA narrative</span>
              <button onClick={() => setAiOn(v => !v)} className={"h-6 w-11 rounded-full relative transition-colors " + (aiOn ? "bg-accent" : "bg-secondary border hairline")}>
                <span className={"absolute top-0.5 size-5 rounded-full bg-background transition-all " + (aiOn ? "left-[calc(100%-22px)]" : "left-0.5")} />
              </button>
            </div>
          </div>
        </div>

        <div className="lg:col-span-7">
          <div className="rounded-2xl border hairline bg-card p-7">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-[11px] uppercase tracking-[0.22em] text-accent">Recommendation</div>
                <div className="font-serif text-2xl mt-2">{risk} · {horizon === "long" ? "Long horizon" : horizon === "medium" ? "Medium horizon" : "Short horizon"}</div>
              </div>
              <Zap className="size-5 text-accent" />
            </div>

            {/* Donut-style stacked bar */}
            <div className="mt-7 h-3 rounded-full overflow-hidden flex">
              {allocation.map(a => (
                <div key={a.label} className={a.color} style={{ width: a.pct + "%" }} />
              ))}
            </div>

            <ul className="mt-6 grid sm:grid-cols-2 gap-x-6 gap-y-3 text-sm">
              {allocation.map(a => (
                <li key={a.label} className="flex items-center justify-between border-b hairline pb-2.5">
                  <span className="inline-flex items-center gap-2.5">
                    <span className={"size-2 rounded-full " + a.color} /> {a.label}
                  </span>
                  <span className="tabular font-mono">{a.pct}% · ₹{Math.round(amount * a.pct / 100).toLocaleString("en-IN")}</span>
                </li>
              ))}
            </ul>

            {aiOn && (
              <div className="mt-7 rounded-xl border hairline bg-secondary/50 p-5">
                <div className="text-[11px] uppercase tracking-[0.22em] text-accent inline-flex items-center gap-2"><Sparkles className="size-3.5" /> INSA</div>
                <p className="mt-3 font-serif text-lg leading-snug">
                  At this horizon and mandate, the equity sleeve compounds harder than fixed income drag — but only if you stay through one full drawdown cycle. Hold conviction.
                </p>
              </div>
            )}

            <div className="mt-7 flex items-center gap-3">
              <Button className="rounded-full px-6 h-11">Save as plan</Button>
              <Button variant="outline" className="rounded-full px-6 h-11">Export PDF</Button>
            </div>
          </div>
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

function allocate(risk: string, horizon: string) {
  const base: Record<string, number[]> = {
    Conservative: [25, 15, 45, 5, 10],
    Balanced: [45, 20, 25, 5, 5],
    Growth: [60, 22, 10, 5, 3],
  };
  let v = base[risk];
  if (horizon === "short") v = v.map((x, i) => (i >= 2 ? x + 8 : x - 4)); // shift to defensive
  if (horizon === "long") v = v.map((x, i) => (i <= 1 ? x + 4 : x - 2));
  // normalize
  const sum = v.reduce((a, b) => a + b, 0);
  v = v.map((x) => Math.max(0, Math.round((x / sum) * 100)));
  return [
    { label: "Equity multi-cap", pct: v[0], color: "bg-foreground" },
    { label: "Passive index", pct: v[1], color: "bg-accent" },
    { label: "Fixed income", pct: v[2], color: "bg-[oklch(0.55_0.08_240)]" },
    { label: "Commodities", pct: v[3], color: "bg-[var(--gold)]" },
    { label: "Cash", pct: v[4], color: "bg-muted-foreground/40" },
  ];
}
