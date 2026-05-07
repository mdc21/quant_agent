import { Link } from "@tanstack/react-router";
import { RingMark } from "@/components/marks/Logo";

export function SiteFooter() {
  return (
    <footer className="border-t hairline mt-24">
      <div className="container-narrow py-14 grid gap-10 md:grid-cols-4 text-sm">
        <div className="md:col-span-2">
          <div className="flex items-center gap-2.5">
            <RingMark />
            <span className="font-serif text-lg">YourBest<span className="italic">Path</span></span>
          </div>
          <p className="mt-4 max-w-md text-muted-foreground leading-relaxed">
            A fiduciary wealth platform. We answer to your goals — not to a product shelf.
            Decisions are auditable, capital-weighted, and explainable end-to-end.
          </p>
          <p className="mt-6 text-xs text-muted-foreground">
            © {new Date().getFullYear()} YourBestPath. For demonstration purposes only. Not investment advice.
          </p>
        </div>
        <FooterCol title="Platform" links={[["/platform","Overview"],["/engine","Fiduciary Engine"],["/dashboard","Dashboard"],["/quick-advice","Quick advice"]]}/>
        <FooterCol title="Company" links={[["/insights","Insights"],["/pricing","Pricing"],["/auth","Sign in"]]}/>
      </div>
    </footer>
  );
}

function FooterCol({ title, links }: { title: string; links: Array<[string, string]> }) {
  return (
    <div>
      <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground mb-4">{title}</div>
      <ul className="space-y-2.5">
        {links.map(([to, label]) => (
          <li key={to}>
            <Link to={to} className="hover:text-foreground text-foreground/80 transition-colors">
              {label}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}