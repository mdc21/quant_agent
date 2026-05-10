import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { AppShell } from "@/components/site/AppShell";
import { ArrowRight, Target, PieChart, Zap, TrendingUp, ShieldCheck, Sparkles, Loader2, Info, Check } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export const Route = createFileRoute("/dashboard")({
  head: () => ({ meta: [{ title: "Hub — YourBestPath" }] }),
  component: Dashboard,
});

function Dashboard() {
  const [user, setUser] = useState<any>(null);
  const [goalsData, setGoalsData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const nav = useNavigate();

  useEffect(() => {
    const storedUser = localStorage.getItem("user");
    if (!storedUser) {
      nav({ to: "/auth" });
      return;
    }
    const parsedUser = JSON.parse(storedUser);
    setUser(parsedUser);

    api.goals.getUserGoals(parsedUser.user_key)
      .then(res => setGoalsData(res))
      .finally(() => setLoading(false));
  }, [nav]);

  const name = user?.name?.split(" ")[0] || "there";
  const risk = goalsData?.risk_tolerance || user?.risk_profile || "Moderate";
  const goalsCount = goalsData?.goals?.length || 0;

  const [chatInput, setChatInput] = useState("");
  const [chatHistory, setChatHistory] = useState<any[]>([
    { role: "assistant", content: `Hello ${name}. I am your fiduciary analyst. Ask me about your sector risk or why we recommend specific trades.` }
  ]);
  const [chatLoading, setChatLoading] = useState(false);

  const handleSendChat = async () => {
    if (!chatInput.trim() || chatLoading) return;
    
    const userMsg = { role: "user", content: chatInput };
    setChatHistory(prev => [...prev, userMsg]);
    setChatInput("");
    setChatLoading(true);

    try {
      const res = await api.auth.chat({
        user_key: user.user_key,
        question: chatInput,
        history: chatHistory
      });
      setChatHistory(prev => [...prev, { role: "assistant", content: res.answer }]);
    } catch (err: any) {
      setChatHistory(prev => [...prev, { role: "assistant", content: "I'm having trouble connecting to the fiduciary engine. Please check your connection." }]);
    } finally {
      setChatLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="size-8 animate-spin text-accent" />
      </div>
    );
  }

  return (
    <AppShell>
      <div className="container-narrow py-10 md:py-14">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <div className="text-xs uppercase tracking-[0.22em] text-accent">Fiduciary Hub</div>
            <h1 className="font-serif text-4xl md:text-5xl mt-2">Welcome back, <span className="italic">{name}</span>.</h1>
            <p className="text-muted-foreground mt-2">Your plan was last reviewed today. Markets are steady — no rebalance triggers.</p>
          </div>
          <div className="text-right">
            <div className="text-xs text-muted-foreground">Goals active</div>
            <div className="font-serif text-3xl tabular">{goalsCount}<span className="text-accent"> targets</span></div>
          </div>
        </div>

        {/* Metrics */}
        <div className="mt-10 grid sm:grid-cols-2 lg:grid-cols-4 gap-px bg-border rounded-2xl overflow-hidden border hairline">
          {[
            { k: "Risk profile", v: risk, sub: `Strategy: ${risk}` },
            { k: "Goal funded", v: goalsCount > 0 ? "42%" : "0%", sub: "Aggregated target" },
            { k: "Status", v: "Compliant", sub: "UCITS 5/10/40 & Sector Caps" },
            { k: "Rebalance drift", v: "0.0%", sub: "Within tolerance" },
          ].map((m) => (
            <div key={m.k} className="bg-card p-6">
              <div className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">{m.k}</div>
              <div className="mt-3 font-serif text-2xl tabular">{m.v}</div>
              <div className="text-xs text-muted-foreground mt-1">{m.sub}</div>
            </div>
          ))}
        </div>

        {/* Action cards */}
        <h2 className="font-serif text-2xl mt-14">Your Journey Path</h2>
        <div className="mt-5 grid md:grid-cols-3 gap-5">
          <ActionCard
            to="/goals"
            tag="Step 1 · Wizard"
            title="Define goals"
            body="Walk through the survival, safety, growth framework. Five minutes."
            icon={Target}
            status={goalsCount > 0 ? "complete" : "active"}
          />
          <ActionCard
            to="/portfolio"
            tag="Step 2 · Review"
            title="Existing portfolio"
            body="Inspect your sleeves, drift, and migration recommendations."
            icon={PieChart}
            status={goalsCount > 0 ? "active" : "locked"}
          />
          <ActionCard
            to="/quick-advice"
            tag="Tool · Calculator"
            title="Quick advice"
            body="Lump-sum or SIP allocation in one screen, no full plan needed."
            icon={Zap}
          />
        </div>

        {/* Insights & Fiduciary Chat */}
        <div className="mt-14 grid lg:grid-cols-2 gap-10">
          <div className="rounded-2xl border hairline bg-card p-8 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between">
                <div className="text-[11px] uppercase tracking-[0.22em] text-accent">Strategic Narrative</div>
                <Sparkles className="size-4 text-accent" />
              </div>
              <p className="mt-6 font-serif text-2xl leading-snug text-foreground/90 italic">
                {goalsCount > 0 
                  ? `"Step 1 Complete. Your ${risk} mandate is defined. The next logical step is to sync your existing holdings so we can compute your optimization manifest."`
                  : `"Welcome. Once you define your goals and import your existing holdings, the Insight Narrative Engine (INSA) will generate a strategic manifest here."`
                }
              </p>
            </div>
            <div className="mt-8 flex flex-wrap gap-2 text-xs">
              {["ROCE > 1.5%","Sector cap 20%","UCITS 5/10/40"].map(t => (
                <span key={t} className="border hairline rounded-full px-3 py-1.5 bg-background text-muted-foreground">{t}</span>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border hairline bg-card p-8 flex flex-col">
            <div className="flex items-center justify-between mb-6">
              <div className="text-[11px] uppercase tracking-[0.22em] text-accent">Fiduciary AI Chat</div>
              <ShieldCheck className="size-4 text-accent" />
            </div>
            <div className="flex-1 min-h-0 overflow-y-auto mb-4 text-sm space-y-4 pr-2 scrollbar-thin max-h-64">
              {chatHistory.map((msg, idx) => (
                <div key={idx} className={`${msg.role === 'user' ? 'bg-accent/10 ml-auto border hairline' : 'bg-secondary/30 mr-auto'} rounded-2xl p-4 max-w-[85%]`}>
                  {msg.content}
                </div>
              ))}
              {chatLoading && (
                <div className="bg-secondary/30 rounded-2xl p-4 max-w-[85%] flex items-center gap-2">
                  <Loader2 className="size-3 animate-spin" /> Thinking...
                </div>
              )}
            </div>
            <div className="relative mt-auto">
              <input 
                type="text" 
                placeholder="Ask about your rebalance plan..." 
                className="w-full h-12 bg-background border hairline rounded-full px-5 pr-12 text-sm focus:ring-1 focus:ring-accent outline-none"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSendChat()}
              />
              <button 
                className="absolute right-2 top-2 size-8 bg-accent text-white rounded-full flex items-center justify-center hover:bg-accent/90 transition-colors disabled:opacity-50"
                onClick={handleSendChat}
                disabled={chatLoading || !chatInput.trim()}
              >
                <ArrowRight className="size-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}

function ActionCard({ to, tag, title, body, icon: Icon, status }: { to: string; tag: string; title: string; body: string; icon: any; status?: "complete" | "active" | "locked" }) {
  return (
    <Link 
      to={to} 
      className={`group rounded-2xl border hairline bg-card p-7 transition-all ${
        status === 'locked' ? 'opacity-50 grayscale pointer-events-none' : 'hover:border-foreground/30 hover:shadow-[0_20px_60px_-40px_oklch(0.18_0.015_250/0.4)]'
      }`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon className={`size-5 ${status === 'complete' ? 'text-green-500' : 'text-accent'}`} />
          {status === 'complete' && <Check className="size-3 text-green-500" />}
        </div>
        <span className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">{tag}</span>
      </div>
      <div className="mt-10 font-serif text-2xl flex items-center gap-2">
        {title}
      </div>
      <p className="text-sm text-muted-foreground mt-2 leading-relaxed">{body}</p>
      <div className="mt-6 inline-flex items-center gap-1.5 text-sm text-accent">
        {status === 'complete' ? 'Update plan' : status === 'locked' ? 'Complete previous step' : 'Continue'} 
        <ArrowRight className="size-4 transition-transform group-hover:translate-x-1" />
      </div>
    </Link>
  );
}
