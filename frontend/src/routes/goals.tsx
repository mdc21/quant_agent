import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { AppShell } from "@/components/site/AppShell";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Check, Shield, Anchor, Sprout, ArrowLeft, ArrowRight, Briefcase, GraduationCap, Home, Heart, Plane, PiggyBank, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { toast } from "sonner";

export const Route = createFileRoute("/goals")({
  head: () => ({ meta: [{ title: "Define goals — YourBestPath" }] }),
  component: Wizard,
});

const PILLAR_ICONS: Record<string, any> = {
  survival: Shield,
  safety: Anchor,
  growth: Sprout
};

const GOAL_ICONS: Record<string, any> = {
  emergency_fund: Shield,
  medical_emergency: Heart,
  job_loss_buffer: Briefcase,
  retirement: PiggyBank,
  home_purchase: Home,
  children_education: GraduationCap,
  children_marriage: Heart,
  travel: Plane,
  real_estate: Home,
  business: Briefcase,
  wealth_creation: Briefcase
};

const STEPS = ["Framework", "Select goals", "Details", "Risk", "Summary"] as const;

function Wizard() {
  const [step, setStep] = useState(0);
  const [catalog, setCatalog] = useState<any>(null);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [goalConfigs, setGoalConfigs] = useState<Record<string, any>>({});
  const [risk, setRisk] = useState<"Conservative" | "Moderate" | "Aggressive">("Moderate");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const nav = useNavigate();

  useEffect(() => {
    const user = JSON.parse(localStorage.getItem("user") || "{}");
    
    Promise.all([
      api.goals.getCatalog(),
      user.user_key ? api.goals.getUserGoals(user.user_key) : Promise.resolve(null)
    ]).then(([cat, existing]: any) => {
      setCatalog(cat);
      if (existing && existing.goals && existing.goals.length > 0) {
        const ids = existing.goals.map((g: any) => g.id);
        setSelectedIds(ids);
        setRisk(existing.risk_tolerance || "Moderate");
        
        const configs: Record<string, any> = {};
        existing.goals.forEach((g: any) => {
          configs[g.id] = g;
        });
        setGoalConfigs(configs);
      }
    })
    .finally(() => setLoading(false));
  }, []);

  const handleFinalize = async () => {
    const user = JSON.parse(localStorage.getItem("user") || "{}");
    if (!user.user_key) {
      toast.error("Please log in first");
      nav({ to: "/auth" });
      return;
    }

    setSaving(true);
    try {
      const goals = Object.values(goalConfigs);
      await api.goals.save({
        user_key: user.user_key,
        goals: goals,
        risk_profile: risk,
        monthly_expenses: 100000,
        inflation_rate: 0.06
      });
      toast.success("Goals finalized and saved!");
      nav({ to: "/portfolio" });
    } catch (err: any) {
      toast.error(err.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="flex h-screen items-center justify-center"><Loader2 className="size-8 animate-spin text-accent" /></div>;
  }

  return (
    <AppShell>
      <div className="max-w-3xl mx-auto px-6 py-10 md:py-14">
        <Stepper step={step} />

        <div className="mt-10 min-h-[460px]">
          {step === 0 && <Framework />}
          {step === 1 && (
            <Selection 
              catalog={catalog} 
              selectedIds={selectedIds} 
              setSelectedIds={setSelectedIds} 
              setGoalConfigs={setGoalConfigs}
            />
          )}
          {step === 2 && (
            <Details 
              selectedIds={selectedIds} 
              catalog={catalog}
              goalConfigs={goalConfigs}
              setGoalConfigs={setGoalConfigs}
            />
          )}
          {step === 3 && <RiskStep risk={risk} setRisk={setRisk} />}
          {step === 4 && <Summary selectedCount={selectedIds.length} risk={risk} />}
        </div>

        <div className="mt-12 flex items-center justify-between border-t hairline pt-6">
          <Button
            variant="ghost"
            disabled={step === 0 || saving}
            onClick={() => setStep((s) => Math.max(0, s - 1))}
            className="rounded-full"
          >
            <ArrowLeft className="mr-1 size-4" /> Back
          </Button>
          {step < STEPS.length - 1 ? (
            <Button 
              onClick={() => setStep((s) => s + 1)} 
              className="rounded-full px-6 h-11"
              disabled={step === 1 && selectedIds.length === 0}
            >
              Continue <ArrowRight className="ml-1 size-4" />
            </Button>
          ) : (
            <Button 
              onClick={handleFinalize} 
              className="rounded-full px-6 h-11" 
              disabled={saving}
            >
              {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Check className="ml-1 size-4" />}
              Finalize plan
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

function Selection({ catalog, selectedIds, setSelectedIds, setGoalConfigs }: any) {
  const toggle = (goal: any) => {
    const on = selectedIds.includes(goal.id);
    if (on) {
      setSelectedIds(selectedIds.filter((x: any) => x !== goal.id));
      setGoalConfigs((prev: any) => {
        const next = { ...prev };
        delete next[goal.id];
        return next;
      });
    } else {
      setSelectedIds([...selectedIds, goal.id]);
      setGoalConfigs((prev: any) => ({
        ...prev,
        [goal.id]: {
          id: goal.id,
          name: goal.name,
          tier: goal.tier,
          icon: goal.icon,
          target: 1000000,
          horizon: 10,
          future_value: 0,
          target_value: 0,
          funded_pct: 0,
          description: goal.desc
        }
      }));
    }
  };

  const allGoals = Object.entries(catalog).flatMap(([tier, goals]: any) => 
    goals.map((g: any) => ({ ...g, tier }))
  );

  return (
    <div>
      <h1 className="font-serif text-3xl md:text-4xl">Pick what matters.</h1>
      <p className="mt-3 text-muted-foreground">Choose any combination across pillars. You can refine targets next.</p>
      <div className="mt-8 grid sm:grid-cols-2 md:grid-cols-3 gap-3">
        {allGoals.map((g: any) => {
          const on = selectedIds.includes(g.id);
          const Icon = GOAL_ICONS[g.id] || Briefcase;
          return (
            <button
              key={g.id}
              onClick={() => toggle(g)}
              className={
                "text-left rounded-xl border p-5 transition-all " +
                (on ? "border-foreground bg-foreground text-background shadow-[0_10px_40px_-20px_oklch(0.18_0.015_250/0.5)]" : "hairline bg-card hover:border-foreground/40")
              }
            >
              <div className="flex items-center justify-between">
                <Icon className={"size-5 " + (on ? "text-accent" : "text-foreground/70")} />
                {on && <Check className="size-4 text-accent" />}
              </div>
              <div className="mt-8 font-serif text-lg leading-tight">{g.name}</div>
              <div className={"text-[11px] uppercase tracking-[0.18em] mt-1 " + (on ? "text-background/60" : "text-muted-foreground")}>{g.tier}</div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function Details({ selectedIds, catalog, goalConfigs, setGoalConfigs }: any) {
  const update = (id: string, key: string, val: any) => {
    setGoalConfigs((prev: any) => {
      const config = { ...prev[id], [key]: val };
      const infl = 0.06;
      config.future_value = config.target * Math.pow(1 + infl, config.horizon);
      config.target_value = config.future_value;
      return { ...prev, [id]: config };
    });
  };

  return (
    <div>
      <h1 className="font-serif text-3xl md:text-4xl">The numbers behind each goal.</h1>
      <p className="mt-3 text-muted-foreground">Only fields for the goals you picked. Order doesn't matter — the engine sequences capital.</p>
      <div className="mt-8 space-y-4">
        {selectedIds.map((id: string) => {
          const config = goalConfigs[id];
          const Icon = GOAL_ICONS[id] || Briefcase;
          return (
            <div key={id} className="rounded-xl border hairline bg-card p-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Icon className="size-4 text-accent" />
                  <span className="font-serif text-xl">{config.name}</span>
                </div>
                <span className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">{config.tier}</span>
              </div>
              <div className="mt-5 grid sm:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label className="text-xs uppercase tracking-[0.16em] text-muted-foreground">Target amount (₹)</Label>
                  <Input 
                    type="number" 
                    value={config.target} 
                    onChange={(e) => update(id, "target", Number(e.target.value))}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs uppercase tracking-[0.16em] text-muted-foreground">Years</Label>
                  <Input 
                    type="number" 
                    value={config.horizon} 
                    onChange={(e) => update(id, "horizon", Number(e.target.value))}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
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

function Summary({ selectedCount, risk }: { selectedCount: number; risk: string }) {
  return (
    <div>
      <h1 className="font-serif text-3xl md:text-4xl">Ready to engineer.</h1>
      <p className="mt-3 text-muted-foreground">The fiduciary engine will translate this into a capital-weighted, sector-disciplined portfolio.</p>
      <div className="mt-8 rounded-xl border hairline bg-card p-6 divide-y hairline">
        <Row k="Risk mandate" v={risk} />
        <Row k="Goals selected" v={`${selectedCount} across pillars`} />
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
