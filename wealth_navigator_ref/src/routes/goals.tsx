import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { AppShell } from "@/components/site/AppShell";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Check, Shield, Anchor, Sprout, ArrowLeft, ArrowRight, Briefcase, GraduationCap, Home, Heart, Plane, PiggyBank } from "lucide-react";

export const Route = createFileRoute("/goals")({
  head: () => ({ meta: [{ title: "Define goals — YourBestPath" }] }),
  component: Wizard,
});

const ALL_GOALS = [
  { id: "emergency", pillar: "Survival", label: "Emergency fund", icon: Shield },
  { id: "insurance", pillar: "Survival", label: "Insurance ladder", icon: Heart },
  { id: "education", pillar: "Safety", label: "Education", icon: GraduationCap },
  { id: "home", pillar: "Safety", label: "Home", icon: Home },
  { id: "retirement", pillar: "Growth", label: "Retirement", icon: PiggyBank },
  { id: "wealth", pillar: "Growth", label: "Wealth creation", icon: Briefcase },
  { id: "travel", pillar: "Growth", label: "Lifestyle / travel", icon: Plane },
] as const;

const STEPS = ["Framework", "Select goals", "Details", "Risk", "Summary"] as const;

function Wizard() {
  const [step, setStep] = useState(0);
  const [selected, setSelected] = useState<string[]>(["emergency", "retirement"]);
  const [risk, setRisk] = useState<"Conservative" | "Moderate" | "Aggressive">("Moderate");
  const nav = useNavigate();

  return (
    <AppShell>
      <div className="max-w-3xl mx-auto px-6 py-10 md:py-14">
        <Stepper step={step} />

        <div className="mt-10 min-h-[460px]">
          {step === 0 && <Framework />}
          {step === 1 && <Selection selected={selected} setSelected={setSelected} />}
          {step === 2 && <Details selected={selected} />}
          {step === 3 && <RiskStep risk={risk} setRisk={setRisk} />}
          {step === 4 && <Summary selected={selected} risk={risk} />}
        </div>

        <div className="mt-12 flex items-center justify-between border-t hairline pt-6">
          <Button
            variant="ghost"
            disabled={step === 0}
            onClick={() => setStep((s) => Math.max(0, s - 1))}
            className="rounded-full"
          >
            <ArrowLeft className="mr-1 size-4" /> Back
          </Button>
          {step < STEPS.length - 1 ? (
            <Button onClick={() => setStep((s) => s + 1)} className="rounded-full px-6 h-11">
              Continue <ArrowRight className="ml-1 size-4" />
            </Button>
          ) : (
            <Button onClick={() => nav({ to: "/portfolio" })} className="rounded-full px-6 h-11">
              Finalize plan <Check className="ml-1 size-4" />
            </Button>
          )}
        </div>
      </div>
    </AppShell>
  );
}

function Stepper({ step }: { step: number }) {
  return (
    <div>
      <div className="flex items-center justify-between text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
        <span>Step {step + 1} of {STEPS.length}</span>
        <span className="text-accent">{STEPS[step]}</span>
      </div>
      <div className="mt-3 h-px bg-border relative">
        <div
          className="absolute left-0 top-0 h-px bg-accent transition-all duration-500"
          style={{ width: `${((step + 1) / STEPS.length) * 100}%` }}
        />
      </div>
    </div>
  );
}

function Framework() {
  const bands = [
    { tag: "Survival", icon: Shield, body: "Liquidity, insurance, and emergency runway. Capital you cannot afford to lose.", tone: "border-l-[var(--gold)]" },
    { tag: "Safety", icon: Anchor, body: "Funded life milestones — education, home, healthcare. Risk-matched, time-bound.", tone: "border-l-[oklch(0.55_0.08_240)]" },
    { tag: "Growth", icon: Sprout, body: "Long-horizon compounding. Multi-cap, sector-disciplined, ROCE-screened.", tone: "border-l-accent" },
  ];
  return (
    <div>
      <h1 className="font-serif text-3xl md:text-4xl">A framework before a portfolio.</h1>
      <p className="mt-3 text-muted-foreground">Every goal you'll set lives in one of three pillars. Capital flows in this order — never the reverse.</p>
      <div className="mt-8 space-y-3">
        {bands.map((b) => (
          <div key={b.tag} className={"rounded-xl border hairline border-l-4 bg-card p-5 flex items-start gap-4 " + b.tone}>
            <b.icon className="size-5 text-foreground/70 mt-1" />
            <div>
              <div className="font-serif text-xl">{b.tag}</div>
              <div className="text-sm text-muted-foreground mt-1">{b.body}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function Selection({ selected, setSelected }: { selected: string[]; setSelected: (s: string[]) => void }) {
  const toggle = (id: string) => setSelected(selected.includes(id) ? selected.filter((x) => x !== id) : [...selected, id]);
  return (
    <div>
      <h1 className="font-serif text-3xl md:text-4xl">Pick what matters.</h1>
      <p className="mt-3 text-muted-foreground">Choose any combination across pillars. You can refine targets next.</p>
      <div className="mt-8 grid sm:grid-cols-2 md:grid-cols-3 gap-3">
        {ALL_GOALS.map((g) => {
          const on = selected.includes(g.id);
          return (
            <button
              key={g.id}
              onClick={() => toggle(g.id)}
              className={
                "text-left rounded-xl border p-5 transition-all " +
                (on ? "border-foreground bg-foreground text-background shadow-[0_10px_40px_-20px_oklch(0.18_0.015_250/0.5)]" : "hairline bg-card hover:border-foreground/40")
              }
            >
              <div className="flex items-center justify-between">
                <g.icon className={"size-5 " + (on ? "text-accent" : "text-foreground/70")} />
                {on && <Check className="size-4 text-accent" />}
              </div>
              <div className="mt-8 font-serif text-lg">{g.label}</div>
              <div className={"text-[11px] uppercase tracking-[0.18em] mt-1 " + (on ? "text-background/60" : "text-muted-foreground")}>{g.pillar}</div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function Details({ selected }: { selected: string[] }) {
  return (
    <div>
      <h1 className="font-serif text-3xl md:text-4xl">The numbers behind each goal.</h1>
      <p className="mt-3 text-muted-foreground">Only fields for the goals you picked. Order doesn't matter — the engine sequences capital.</p>
      <div className="mt-8 space-y-4">
        {selected.length === 0 && (
          <div className="text-sm text-muted-foreground border hairline rounded-xl p-6">
            No goals selected — go back and pick at least one.
          </div>
        )}
        {selected.map((id) => {
          const g = ALL_GOALS.find((x) => x.id === id)!;
          return (
            <div key={id} className="rounded-xl border hairline bg-card p-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <g.icon className="size-4 text-accent" />
                  <span className="font-serif text-xl">{g.label}</span>
                </div>
                <span className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">{g.pillar}</span>
              </div>
              <div className="mt-5 grid sm:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label className="text-xs uppercase tracking-[0.16em] text-muted-foreground">Target amount (₹)</Label>
                  <Input type="number" defaultValue={defaultAmount(id)} />
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs uppercase tracking-[0.16em] text-muted-foreground">Years</Label>
                  <Input type="number" defaultValue={defaultYears(id)} />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function defaultAmount(id: string) {
  return ({ emergency: 600000, insurance: 250000, education: 5000000, home: 12000000, retirement: 50000000, wealth: 20000000, travel: 1500000 } as Record<string, number>)[id] ?? 1000000;
}
function defaultYears(id: string) {
  return ({ emergency: 1, insurance: 1, education: 12, home: 7, retirement: 22, wealth: 15, travel: 3 } as Record<string, number>)[id] ?? 5;
}

function RiskStep({ risk, setRisk }: { risk: string; setRisk: (r: any) => void }) {
  const [score, setScore] = useState([60]);
  const profiles = [
    { key: "Conservative", body: "Capital protection · 15% sector cap · low drawdown band" },
    { key: "Moderate", body: "Balanced · 20% sector cap · ±12% drawdown band" },
    { key: "Aggressive", body: "Compounding · 25% sector cap · ±18% drawdown band" },
  ] as const;
  return (
    <div>
      <h1 className="font-serif text-3xl md:text-4xl">Your risk mandate.</h1>
      <p className="mt-3 text-muted-foreground">This becomes a hard constraint inside the optimiser.</p>

      <div className="mt-8">
        <Slider value={score} onValueChange={(v) => { setScore(v); setRisk(v[0] < 33 ? "Conservative" : v[0] < 66 ? "Moderate" : "Aggressive"); }} max={100} step={1} />
        <div className="mt-2 flex justify-between text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
          <span>Capital first</span><span>Balanced</span><span>Compound first</span>
        </div>
      </div>

      <div className="mt-8 grid md:grid-cols-3 gap-3">
        {profiles.map((p) => {
          const on = risk === p.key;
          return (
            <button
              key={p.key}
              onClick={() => setRisk(p.key)}
              className={"text-left rounded-xl border p-5 transition-all " + (on ? "border-foreground bg-foreground text-background" : "hairline bg-card hover:border-foreground/40")}
            >
              <div className="font-serif text-xl">{p.key}</div>
              <div className={"text-xs mt-2 " + (on ? "text-background/70" : "text-muted-foreground")}>{p.body}</div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function Summary({ selected, risk }: { selected: string[]; risk: string }) {
  return (
    <div>
      <h1 className="font-serif text-3xl md:text-4xl">Ready to engineer.</h1>
      <p className="mt-3 text-muted-foreground">The fiduciary engine will translate this into a capital-weighted, sector-disciplined portfolio.</p>
      <div className="mt-8 rounded-xl border hairline bg-card p-6 divide-y hairline">
        <Row k="Risk mandate" v={risk} />
        <Row k="Goals selected" v={`${selected.length} across pillars`} />
        <Row k="Engine" v="GENPOA · 4-tier cascade · INSA narrative on" />
        <Row k="Compliance" v="UCITS 5/10/40 · ±2% multi-cap buffer" />
      </div>
      <p className="mt-6 text-xs text-muted-foreground">By finalising, you authorise the system to compute a proposed portfolio and migration plan. No trades are executed.</p>
    </div>
  );
}
function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex items-center justify-between py-3 first:pt-0 last:pb-0">
      <span className="text-xs uppercase tracking-[0.16em] text-muted-foreground">{k}</span>
      <span className="font-serif text-base">{v}</span>
    </div>
  );
}
