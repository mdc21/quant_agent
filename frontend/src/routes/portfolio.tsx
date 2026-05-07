import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { AppShell } from "@/components/site/AppShell";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { 
  ShieldCheck, 
  ArrowRight, 
  Upload, 
  PieChart, 
  TrendingUp, 
  AlertCircle,
  Loader2,
  Check,
  Briefcase,
  Layers,
  Zap,
  Info,
  Plus,
  Trash2
} from "lucide-react";
import { api } from "@/lib/api";
import { toast } from "sonner";

export const Route = createFileRoute("/portfolio")({
  head: () => ({ meta: [{ title: "Portfolio Review — YourBestPath" }] }),
  component: PortfolioPage,
});

function PortfolioPage() {
  const [user, setUser] = useState<any>(null);
  const [isReviewLoading, setIsReviewLoading] = useState(true);
  const [reviewData, setReviewData] = useState<any>(null);
  const [uploading, setUploading] = useState(false);
  const [showUpload, setShowUpload] = useState(false);
  const [csvContent, setCsvContent] = useState("");
  const [currentHoldings, setCurrentHoldings] = useState<any[]>([]);
  const [stagedHoldings, setStagedHoldings] = useState<any[]>([]);
  const [hasChanges, setHasChanges] = useState(false);
  const nav = useNavigate();

  const fetchReview = async (userKey: string) => {
    setIsReviewLoading(true);
    try {
      // 1. Fetch raw holdings first so we always have a baseline
      const raw = await api.portfolio.get(userKey);
      const holdings = raw.holdings || [];
      setCurrentHoldings(holdings);
      setStagedHoldings(holdings);

      // 2. Attempt the full review/optimization
      const res = await api.portfolio.review(userKey);
      setReviewData(res);
      setHasChanges(false);
      setShowUpload(false);
    } catch (err: any) {
      console.error("Review fetch failed:", err);
      if (err.message.includes("No goals")) {
        toast.error("Please define your goals first");
        nav({ to: "/goals" });
      } else {
        // If review fails but we have holdings, stay on page but show upload option
        setShowUpload(currentHoldings.length === 0);
        if (currentHoldings.length > 0) {
          toast.warning("Optimization engine is busy. Showing baseline portfolio.");
        }
      }
    } finally {
      setIsReviewLoading(false);
    }
  };

  const handleStageRemove = (symbol: string) => {
    setStagedHoldings(prev => prev.filter(h => h.symbol !== symbol));
    setHasChanges(true);
  };

  const handleApplyChanges = async () => {
    setUploading(true);
    try {
      await api.portfolio.upload({ user_key: user.user_key, holdings: stagedHoldings });
      toast.success("Portfolio synchronized successfully");
      fetchReview(user.user_key);
    } catch (err: any) {
      toast.error(err.message);
    } finally {
      setUploading(false);
    }
  };


  useEffect(() => {
    const storedUser = localStorage.getItem("user");
    if (!storedUser) {
      nav({ to: "/auth" });
      return;
    }
    const parsedUser = JSON.parse(storedUser);
    setUser(parsedUser);
    if (parsedUser && parsedUser.user_key) {
      fetchReview(parsedUser.user_key);
    } else {
      nav({ to: "/auth" });
    }
  }, []);

  const handleUpload = async () => {
    if (!csvContent) return;
    try {
      const lines = csvContent.split("\n").filter(l => l.trim());
      const headers = lines[0].toLowerCase().split(",");
      const symIdx = headers.indexOf("symbol") !== -1 ? headers.indexOf("symbol") : headers.indexOf("ticker");
      const qtyIdx = headers.indexOf("quantity") !== -1 ? headers.indexOf("quantity") : headers.indexOf("qty");
      const prcIdx = headers.indexOf("avg_price") !== -1 ? headers.indexOf("avg_price") : headers.indexOf("price");

      if (symIdx === -1 || qtyIdx === -1) {
        throw new Error("CSV must have Symbol and Quantity columns");
      }

      const newHoldings = lines.slice(1).map(line => {
        const parts = line.split(",");
        return {
          symbol: parts[symIdx].trim().toUpperCase(),
          quantity: parseFloat(parts[qtyIdx]),
          avg_price: prcIdx !== -1 ? parseFloat(parts[prcIdx]) : 0
        };
      });

      // Merge into staged
      const merged = [...stagedHoldings];
      newHoldings.forEach(nh => {
        const existingIdx = merged.findIndex(eh => eh.symbol === nh.symbol);
        if (existingIdx !== -1) {
          merged[existingIdx] = nh; 
        } else {
          merged.push(nh);
        }
      });

      setStagedHoldings(merged);
      setHasChanges(true);
      setCsvContent("");
      toast.info("Holdings staged. Click 'Apply Changes' to save.");
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  if (isReviewLoading) {
    return <div className="flex h-screen items-center justify-center"><Loader2 className="size-8 animate-spin text-accent" /></div>;
  }

  if (showUpload) {
    return (
      <AppShell>
        <div className="max-w-3xl mx-auto py-14 px-6">
          <div className="flex items-center justify-between mb-10">
            <div>
              <h1 className="font-serif text-4xl">Manage Portfolio.</h1>
              <p className="text-sm text-muted-foreground mt-1">Stage your additions and removals below.</p>
            </div>
            <div className="flex gap-3">
              <Button variant="ghost" onClick={() => setShowUpload(false)}>Cancel</Button>
              <Button 
                onClick={handleApplyChanges} 
                disabled={!hasChanges || uploading}
                className="rounded-full px-6"
              >
                {uploading ? <Loader2 className="mr-2 size-4 animate-spin" /> : <ShieldCheck className="mr-2 size-4" />}
                Synchronize Changes
              </Button>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            {/* Left: CSV Upload */}
            <div className="rounded-2xl border hairline bg-card p-8 h-fit">
              <div className="flex items-center gap-2 mb-4">
                 <Upload className="size-4 text-accent" />
                 <h2 className="font-serif text-xl">Bulk Stage</h2>
              </div>
              <Label htmlFor="csv-upload" className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Paste CSV Content</Label>
              <textarea 
                id="csv-upload"
                className="w-full h-32 mt-2 bg-background border hairline rounded-xl p-4 text-xs font-mono focus:ring-1 focus:ring-accent outline-none transition-all"
                placeholder="Symbol, Qty, AvgPrice"
                value={csvContent}
                onChange={(e) => setCsvContent(e.target.value)}
              />
              <Button 
                variant="outline"
                className="w-full mt-4 h-10 rounded-full text-xs" 
                onClick={handleUpload}
                disabled={!csvContent}
              >
                <Plus className="mr-2 size-3" />
                Stage for Addition
              </Button>
            </div>

            {/* Right: Manual Removal */}
            <div className="rounded-2xl border hairline bg-card p-8">
              <div className="flex items-center gap-2 mb-4">
                 <Briefcase className="size-4 text-accent" />
                 <h2 className="font-serif text-xl">Review Changes</h2>
              </div>
              <div className="space-y-2 max-h-[400px] overflow-y-auto pr-2 scrollbar-thin">
                {stagedHoldings.length === 0 ? (
                  <p className="text-sm text-muted-foreground italic">No holdings staged.</p>
                ) : (
                  stagedHoldings.map((h) => (
                    <div key={h.symbol} className="flex items-center justify-between p-3 rounded-xl bg-secondary/30 border hairline">
                      <div>
                        <div className="font-medium text-sm">{h.symbol}</div>
                        <div className="text-[10px] text-muted-foreground">{h.quantity} units @ ₹{h.avg_price}</div>
                      </div>
                      <Button 
                        variant="ghost" 
                        size="icon" 
                        className="size-8 rounded-full text-orange-500 hover:text-orange-600 hover:bg-orange-50"
                        onClick={() => handleStageRemove(h.symbol)}
                      >
                        <Trash2 className="size-4" />
                      </Button>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          {hasChanges && (
            <div className="mt-8 p-4 rounded-xl bg-accent/10 border border-accent/20 flex items-center justify-between">
              <div className="text-xs text-accent font-medium">You have uncommitted changes in your staged portfolio.</div>
              <Button size="sm" className="rounded-full h-8 px-4 text-xs" onClick={handleApplyChanges}>Sync Now</Button>
            </div>
          )}
          
          <div className="mt-12 flex items-start gap-3 p-4 rounded-xl bg-secondary/50 border hairline">
            <p className="text-xs text-muted-foreground leading-relaxed">
              Updating your portfolio will trigger a full fiduciary review. The engine will recalculate drift, tax-loss harvesting opportunities, and rebalance actions against your target mandate.
            </p>
          </div>
        </div>
      </AppShell>
    );
  }

  if (isReviewLoading || !reviewData) {
    return <div className="flex h-screen items-center justify-center"><Loader2 className="size-8 animate-spin text-accent" /></div>;
  }

  const { equity_sleeve, passive_sleeve, rebalance_plan, metrics, narrative } = reviewData;

  return (
    <AppShell>
      <div className="container-narrow py-10 md:py-14">
        <header className="flex flex-wrap items-end justify-between gap-6">
          <div>
            <div className="text-xs uppercase tracking-[0.22em] text-accent font-semibold">Fiduciary Review</div>
            <h1 className="font-serif text-4xl md:text-5xl mt-2">Optimization <span className="italic text-foreground/70">Manifest</span>.</h1>
            <p className="text-muted-foreground mt-3 max-w-xl">Based on your {metrics.risk_profile} profile and {fmtInr(metrics.total_capital)} capital.</p>
          </div>
          <div className="flex gap-3">
             <Button variant="ghost" className="rounded-full" onClick={() => nav({ to: "/" })}>Back</Button>
             <Button variant="outline" className="rounded-full" onClick={() => setShowUpload(true)}>Update Portfolio</Button>
             <Button className="rounded-full px-6">Seal Decision</Button>
          </div>
        </header>

        {/* Narrative Box */}
        <div className="mt-10 rounded-2xl border hairline bg-card p-8 border-l-4 border-l-accent shadow-[0_20px_50px_-30px_oklch(0.18_0.015_250/0.3)]">
          <div className="flex items-center justify-between">
            <div className="text-[11px] uppercase tracking-[0.22em] text-accent">Insight Narrative engine</div>
            <Zap className="size-4 text-accent" />
          </div>
          <p className="mt-5 font-serif text-2xl leading-snug text-foreground/90 italic">
            "{narrative}"
          </p>
        </div>

        {/* Metrics Grid */}
        <div className="mt-10 grid sm:grid-cols-2 lg:grid-cols-4 gap-px bg-border rounded-2xl overflow-hidden border hairline">
          {[
            { k: "Total Equity", v: fmtInr(metrics.equity_cap), sub: "Target Allocation" },
            { k: "Action Count", v: rebalance_plan.length, sub: "Trades required" },
            { k: "Est. Tax Cost", v: fmtInr(reviewData.total_est_tax), sub: "Rebalance Tax Manifest" },
            { k: "Status", v: "Compliant", sub: "UCITS 5/10/40 & Sector Caps" },
          ].map((m) => (
            <div key={m.k} className="bg-card p-6">
              <div className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">{m.k}</div>
              <div className="mt-3 font-serif text-2xl">{m.v}</div>
              <div className="text-xs text-muted-foreground mt-1">{m.sub}</div>
            </div>
          ))}
        </div>

        {/* Existing Portfolio Baseline */}
        <div className="mt-14">
          <div className="flex items-center gap-3 mb-6">
             <Briefcase className="size-5 text-accent" />
             <h2 className="font-serif text-2xl">Current Positions <span className="text-muted-foreground/50 font-sans text-sm font-normal ml-2">(Baseline)</span></h2>
          </div>
          <div className="rounded-2xl border hairline bg-card overflow-hidden">
             <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 p-6">
                {currentHoldings.length === 0 ? (
                  <p className="text-sm text-muted-foreground italic col-span-full">No existing holdings found. Please use 'Update Portfolio' to add assets.</p>
                ) : (
                  currentHoldings.map((h: any) => (
                    <div key={h.symbol} className="p-4 rounded-xl border hairline bg-secondary/10 flex flex-col justify-between">
                       <div className="flex items-center justify-between">
                          <span className="font-serif text-lg">{h.symbol}</span>
                          <span className="text-[10px] uppercase tracking-wider text-muted-foreground">{h.quantity} units</span>
                       </div>
                       <div className="mt-4 flex items-end justify-between">
                          <div className="text-xs text-muted-foreground">Market Value</div>
                          <div className="font-medium text-sm">{fmtInr(h.market_value)}</div>
                       </div>
                    </div>
                  ))
                )}
             </div>
          </div>
        </div>

        {/* Comparison Charts */}
        <div className="mt-14 grid lg:grid-cols-2 gap-10">
          <div className="rounded-2xl border hairline bg-card p-8">
            <div className="flex items-center gap-2 mb-6">
              <PieChart className="size-4 text-accent" />
              <h2 className="font-serif text-xl">Asset Class Mix</h2>
            </div>
            <div className="space-y-6">
              {(reviewData.comparison?.asset_classes || []).map((ac: any) => (
                <div key={ac.label}>
                  <div className="flex justify-between text-xs mb-2">
                    <span className="font-medium">{ac.label}</span>
                    <span className="text-muted-foreground">
                      {((ac.current / (reviewData.metrics.total_capital || 1)) * 100).toFixed(0)}% 
                      <span className="mx-1">→</span>
                      <span className="text-accent font-bold">{((ac.proposed / (reviewData.metrics.total_capital || 1)) * 100).toFixed(0)}%</span>
                    </span>
                  </div>
                  <div className="space-y-1.5">
                    <div className="h-1.5 bg-secondary rounded-full overflow-hidden">
                      <div className="h-full bg-muted-foreground/30" style={{ width: `${(ac.current / (reviewData.metrics.total_capital || 1)) * 100}%` }} />
                    </div>
                    <div className="h-1.5 bg-secondary rounded-full overflow-hidden">
                      <div className="h-full bg-accent" style={{ width: `${(ac.proposed / (reviewData.metrics.total_capital || 1)) * 100}%` }} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border hairline bg-card p-8">
            <div className="flex items-center gap-2 mb-6">
              <TrendingUp className="size-4 text-accent" />
              <h2 className="font-serif text-xl">Sector Drift Analysis</h2>
            </div>
            <div className="space-y-4 max-h-64 overflow-y-auto pr-2 scrollbar-thin">
              {(reviewData.comparison?.sectors || []).map((sec: any) => (
                <div key={sec.name}>
                  <div className="flex justify-between text-[10px] mb-1.5 uppercase tracking-wider">
                    <span>{sec.name}</span>
                    <span className={sec.proposed > sec.current ? 'text-accent' : 'text-orange-500'}>
                      {sec.proposed > sec.current ? 'Increasing' : 'Trimming'}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-1 bg-secondary rounded-full overflow-hidden relative">
                       <div className="absolute inset-y-0 left-0 bg-muted-foreground/20" style={{ width: `${Math.min(100, (sec.current / (reviewData.metrics.total_capital || 1)) * 100)}%` }} />
                       <div className="absolute inset-y-0 left-0 bg-accent" style={{ width: `${Math.min(100, (sec.proposed / (reviewData.metrics.total_capital || 1)) * 100)}%` }} />
                    </div>
                    <span className="text-[10px] font-mono w-8 text-right">{((sec.proposed / (reviewData.metrics.total_capital || 1)) * 100).toFixed(0)}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Rebalance Plan */}
        <div className="mt-14">
          <div className="flex items-center gap-3 mb-6">
             <TrendingUp className="size-5 text-accent" />
             <h2 className="font-serif text-2xl">Rebalance Action Plan</h2>
          </div>
          <div className="rounded-2xl border hairline bg-card overflow-hidden">
            <table className="w-full text-left border-collapse">
               <thead>
                 <tr className="bg-secondary/50 text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                   <th className="px-6 py-4 font-semibold">Asset</th>
                   <th className="px-6 py-4 font-semibold">Action</th>
                   <th className="px-6 py-4 font-semibold text-right">Amount</th>
                   <th className="px-6 py-4 font-semibold text-center">Tax Harvest</th>
                 </tr>
               </thead>
               <tbody className="divide-y hairline">
                  {rebalance_plan.map((a: any, i: number) => (
                    <tr key={i} className="hover:bg-secondary/20 transition-colors">
                      <td className="px-6 py-4 font-serif text-lg">{a.symbol}</td>
                      <td className="px-6 py-4">
                         <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                           a.action === 'EXIT' ? 'bg-destructive/10 text-destructive' :
                           a.action === 'BUY' ? 'bg-accent/10 text-accent' :
                           a.action === 'TRIM' ? 'bg-orange-500/10 text-orange-600' :
                           'bg-blue-500/10 text-blue-600'
                         }`}>
                           {a.action}
                         </span>
                      </td>
                      <td className={`px-6 py-4 text-right font-mono text-sm ${a.diff < 0 ? 'text-destructive' : 'text-accent'}`}>
                         {a.diff > 0 ? '+' : ''}{fmtInr(Math.abs(a.diff))}
                      </td>
                      <td className="px-6 py-4 text-center">
                         <div className="flex flex-col items-center">
                            <span className={a.is_harvest ? 'text-accent font-bold text-xs' : 'text-muted-foreground text-xs'}>
                              {a.is_harvest ? '✅ HARVEST' : '—'}
                            </span>
                            {a.est_tax > 0 && (
                              <span className="text-[10px] text-destructive mt-1">Tax: {fmtInr(a.est_tax)}</span>
                            )}
                         </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
            </table>
          </div>
        </div>

        <div className="mt-14 grid lg:grid-cols-2 gap-10">
          {/* Alpha Sleeve */}
          <div>
            <div className="flex items-center gap-3 mb-6">
               <Briefcase className="size-5 text-accent" />
               <h2 className="font-serif text-2xl">Alpha Sleeve (Direct)</h2>
            </div>
            <div className="space-y-3">
              {equity_sleeve.map((s: any) => (
                <div key={s.symbol} className="rounded-xl border hairline bg-card p-5 hover:border-accent/40 transition-all group">
                   <div className="flex items-center justify-between">
                      <div className="font-serif text-xl group-hover:text-accent transition-colors">{s.symbol}</div>
                      <div className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">{s.sector}</div>
                   </div>
                   <div className="mt-4 flex items-center justify-between">
                      <div className="text-sm text-muted-foreground">Allocation: <span className="text-foreground font-medium">{fmtInr(s.target_capital)}</span></div>
                      <div className="text-sm text-muted-foreground">Weight: <span className="text-accent font-bold">{(s.target_weight * 100).toFixed(1)}%</span></div>
                   </div>
                   <div className="mt-3 h-1.5 w-full bg-secondary rounded-full overflow-hidden">
                      <div className="h-full bg-accent transition-all duration-1000" style={{ width: `${s.target_weight * 100 * 10}%` }} />
                   </div>
                </div>
              ))}
            </div>
          </div>

          {/* Passive Sleeve */}
          <div>
            <div className="flex items-center gap-3 mb-6">
               <Layers className="size-5 text-accent" />
               <h2 className="font-serif text-2xl">Beta & Defensive</h2>
            </div>
            <div className="space-y-3">
              {passive_sleeve.map((s: any) => (
                <div key={s.ticker} className="rounded-xl border hairline bg-card p-5">
                   <div className="flex items-center justify-between">
                      <div className="font-serif text-xl">{s.name || s.ticker}</div>
                      <div className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">{s.category}</div>
                   </div>
                   <p className="text-xs text-muted-foreground mt-2 italic">"{s.rationale}"</p>
                   <div className="mt-4 flex items-center justify-between">
                      <div className="text-sm text-muted-foreground">Value: <span className="text-foreground font-medium">{fmtInr(s.target_capital)}</span></div>
                      <div className="text-sm text-muted-foreground">TER: <span className="text-foreground font-medium">{(s.expense_ratio * 100).toFixed(2)}%</span></div>
                   </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}

function fmtInr(val: number) {
  if (val >= 10000000) return `₹${(val / 10000000).toFixed(2)} Cr`;
  if (val >= 100000) return `₹${(val / 100000).toFixed(2)} L`;
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0
  }).format(val);
}
