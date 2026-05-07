import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RingMark } from "@/components/marks/Logo";
import { ShieldCheck, Lock } from "lucide-react";

export const Route = createFileRoute("/auth")({
  head: () => ({ meta: [{ title: "Sign in — YourBestPath" }, { name: "description", content: "Secure access to your fiduciary plan." }]}),
  component: AuthPage,
});

function AuthPage() {
  const [tab, setTab] = useState<"signin" | "signup">("signin");
  const nav = useNavigate();
  return (
    <div className="min-h-screen grid lg:grid-cols-2 bg-background">
      {/* Brand panel */}
      <aside className="relative hidden lg:flex flex-col justify-between p-12 text-background overflow-hidden bg-foreground">
        <div aria-hidden className="absolute inset-0">
          <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2">
            {[480, 360, 240, 140, 70].map((d, i) => (
              <div
                key={d}
                className="absolute rounded-full border"
                style={{
                  width: d, height: d, left: -d/2, top: -d/2,
                  borderColor: i === 0 ? "oklch(0.6 0.12 165 / 0.25)" : i === 1 ? "oklch(0.55 0.08 240 / 0.25)" : i === 2 ? "oklch(0.72 0.12 80 / 0.25)" : "oklch(1 0 0 / 0.08)",
                  boxShadow: i < 3 ? "0 0 80px -20px currentColor" : undefined,
                }}
              />
            ))}
          </div>
          <div className="absolute inset-0 bg-gradient-to-t from-foreground via-transparent to-transparent" />
        </div>
        <div className="relative">
          <Link to="/" className="inline-flex items-center gap-2.5">
            <RingMark className="text-background" />
            <span className="font-serif text-lg">YourBest<span className="italic">Path</span></span>
          </Link>
        </div>
        <div className="relative">
          <p className="font-serif text-3xl leading-tight max-w-md">
            "A fiduciary plan is not a product — it's a <span className="italic text-accent">covenant</span> with your future self."
          </p>
          <p className="mt-6 text-xs uppercase tracking-[0.22em] text-background/60">Fiduciary Charter · Section 1</p>
        </div>
      </aside>

      {/* Action panel */}
      <section className="flex items-center justify-center p-6 sm:p-12">
        <div className="w-full max-w-md">
          <div className="lg:hidden mb-8">
            <Link to="/" className="inline-flex items-center gap-2.5">
              <RingMark />
              <span className="font-serif text-lg">YourBest<span className="italic">Path</span></span>
            </Link>
          </div>

          <div className="rounded-2xl border hairline bg-card p-8 shadow-[0_30px_80px_-50px_oklch(0.18_0.015_250/0.4)]">
            <h1 className="font-serif text-3xl">{tab === "signin" ? "Welcome back." : "Begin your plan."}</h1>
            <p className="text-sm text-muted-foreground mt-2">{tab === "signin" ? "Continue to your fiduciary dashboard." : "Set up your secure account in under a minute."}</p>

            <div className="mt-6 grid grid-cols-2 p-1 bg-secondary rounded-full text-sm">
              {(["signin","signup"] as const).map((t) => (
                <button
                  key={t}
                  onClick={() => setTab(t)}
                  className={"h-9 rounded-full transition-all " + (tab === t ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground")}
                >
                  {t === "signin" ? "Sign in" : "Create account"}
                </button>
              ))}
            </div>

            <form
              className="mt-6 space-y-4"
              onSubmit={(e) => { e.preventDefault(); nav({ to: "/dashboard" }); }}
            >
              {tab === "signup" && (
                <Field label="Full name"><Input placeholder="Aarav Mehta" required /></Field>
              )}
              <Field label="Email"><Input type="email" placeholder="you@firm.com" required /></Field>
              <Field label="Password"><Input type="password" placeholder="••••••••" required /></Field>

              <Button type="submit" className="w-full h-11 rounded-full mt-2">
                {tab === "signin" ? "Sign in securely" : "Create account"}
              </Button>
            </form>

            <div className="mt-6 flex items-center gap-2 text-[11px] text-muted-foreground justify-center">
              <Lock className="size-3" /> 256-bit AES · session-bound · audit-logged
            </div>
          </div>

          <div className="mt-6 flex items-center justify-center gap-2 text-xs text-muted-foreground">
            <ShieldCheck className="size-3.5 text-accent" /> Held to a fiduciary standard.
          </div>
        </div>
      </section>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <Label className="text-xs uppercase tracking-[0.16em] text-muted-foreground">{label}</Label>
      {children}
    </div>
  );
}
