import { createFileRoute, Link } from "@tanstack/react-router";
import { SiteShell } from "@/components/site/SiteShell";
import { Button } from "@/components/ui/button";
import { ArrowRight } from "lucide-react";

export const Route = createFileRoute("/engine")({
  head: () => ({ meta: [{ title: "Engine — YourBestPath" }] }),
  component: Page,
});

const COPY = {
  platform: { eyebrow: "Platform", title: "Every screen earns its place.", body: "From onboarding to rebalance, YourBestPath is built around clarity, not feature breadth. Each surface has one job and stays out of the way otherwise." },
  engine: { eyebrow: "Fiduciary engine", title: "Capital-weighted. Auditable. Always.", body: "GENPOA enforces UCITS 5/10/40, multi-cap targets and sector caps at the rupee level — not stock count. A 4-tier AI cascade adds narrative, never overrides the math." },
  insights: { eyebrow: "Insights", title: "Notes from the engine room.", body: "Briefings on portfolio construction, sector concentration risks, and how fiduciary structures hold up across market regimes." },
  pricing: { eyebrow: "Pricing", title: "Aligned with your outcomes.", body: "Flat platform fee. No commissions. No revenue-share with product issuers. Your portfolio is built for you, not for our P&L." },
} as const;

function Page() {
  const c = COPY["engine"];
  return (
    <SiteShell>
      <section className="container-narrow py-24 md:py-32">
        <div className="text-[11px] uppercase tracking-[0.22em] text-accent">{c.eyebrow}</div>
        <h1 className="font-serif text-4xl md:text-6xl mt-4 leading-[1.05] max-w-3xl">{c.title}</h1>
        <p className="mt-6 text-lg text-muted-foreground max-w-2xl leading-relaxed">{c.body}</p>
        <div className="mt-10 flex flex-wrap gap-3">
          <Button asChild className="rounded-full h-12 px-6"><Link to="/dashboard">Open the app <ArrowRight className="ml-1" /></Link></Button>
          <Button asChild variant="outline" className="rounded-full h-12 px-6 border-foreground/20"><Link to="/">Back to home</Link></Button>
        </div>
      </section>
    </SiteShell>
  );
}
