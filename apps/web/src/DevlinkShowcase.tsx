import { useEffect, useMemo, useState, type ReactNode } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { LucideIcon } from "lucide-react";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  BarChart3,
  Bell,
  Check,
  ChevronDown,
  Copy,
  ExternalLink,
  Eye,
  EyeOff,
  Filter,
  Home,
  Link2,
  Lock,
  LogIn,
  MoreHorizontal,
  MousePointerClick,
  Plus,
  QrCode,
  Search,
  Settings,
  Share2,
  Shield,
  Sparkles,
  Trash2,
  Users,
  Zap,
} from "lucide-react";

type Page = "landing" | "auth" | "dashboard" | "create" | "analytics" | "links" | "workspace";
type Status = "active" | "expired" | "flagged";
type Role = "Owner" | "Admin" | "Editor" | "Viewer";

type LinkRow = {
  code: string;
  destination: string;
  clicks: number;
  status: Status;
  created: string;
  workspace: string;
};

const accent = "#E8FF47";
const panelShadow =
  "0 0 0 1px rgba(255,255,255,0.06), 0 2px 4px rgba(0,0,0,0.4), 0 8px 16px rgba(0,0,0,0.3)";

const navItems: Array<{ page: Page; label: string; icon: LucideIcon; section: "workspace" | "account" }> = [
  { page: "dashboard", label: "Dashboard", icon: Home, section: "workspace" },
  { page: "create", label: "Create link", icon: Plus, section: "workspace" },
  { page: "analytics", label: "Analytics", icon: BarChart3, section: "workspace" },
  { page: "links", label: "Links", icon: Link2, section: "workspace" },
  { page: "workspace", label: "Workspace", icon: Users, section: "workspace" },
  { page: "auth", label: "Auth", icon: LogIn, section: "account" },
];

const linkRows: LinkRow[] = [
  {
    code: "gh-port",
    destination: "https://github.com/aaradhya/devlink-platform",
    clicks: 488210,
    status: "active",
    created: "Jun 15, 2026",
    workspace: "Platform",
  },
  {
    code: "launch",
    destination: "https://devlink.ai/blog/distributed-link-intelligence",
    clicks: 184902,
    status: "active",
    created: "Jun 12, 2026",
    workspace: "Growth",
  },
  {
    code: "pricing-v2",
    destination: "https://devlink.ai/pricing?experiment=v2",
    clicks: 72882,
    status: "expired",
    created: "May 28, 2026",
    workspace: "Growth",
  },
  {
    code: "risk-scan",
    destination: "https://unsafe-example.test/payload",
    clicks: 9014,
    status: "flagged",
    created: "May 21, 2026",
    workspace: "Security",
  },
];

const chartData = [
  { date: "May 17", clicks: 820 },
  { date: "May 20", clicks: 1180 },
  { date: "May 23", clicks: 1640 },
  { date: "May 26", clicks: 1490 },
  { date: "May 29", clicks: 2310 },
  { date: "Jun 01", clicks: 2840 },
  { date: "Jun 04", clicks: 3190 },
  { date: "Jun 07", clicks: 3920 },
  { date: "Jun 10", clicks: 4510 },
  { date: "Jun 13", clicks: 5220 },
  { date: "Jun 15", clicks: 6190 },
];

const countryData = [
  { country: "United States", clicks: 82400 },
  { country: "India", clicks: 68120 },
  { country: "Germany", clicks: 32904 },
  { country: "United Kingdom", clicks: 27440 },
  { country: "Brazil", clicks: 18205 },
];

const deviceData = [
  { name: "Desktop", value: 58, color: "#E8FF47" },
  { name: "Mobile", value: 31, color: "#888888" },
  { name: "Tablet", value: 11, color: "#444444" },
];

const referrers = [
  { source: "github.com", clicks: 42102, pct: 34 },
  { source: "news.ycombinator.com", clicks: 28690, pct: 23 },
  { source: "linkedin.com", clicks: 19104, pct: 16 },
  { source: "direct", clicks: 14220, pct: 11 },
];

const members: Array<{ name: string; email: string; role: Role }> = [
  { name: "Aaradhya Mehra", email: "aaradhya@devlink.ai", role: "Owner" },
  { name: "Mira Shah", email: "mira@devlink.ai", role: "Admin" },
  { name: "Theo Park", email: "theo@devlink.ai", role: "Editor" },
  { name: "Nina Vale", email: "nina@devlink.ai", role: "Viewer" },
];

export function DevlinkShowcase() {
  const [page, setPage] = useState<Page>("landing");
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [showPassword, setShowPassword] = useState(false);
  const [copied, setCopied] = useState<string | null>(null);
  const [selected, setSelected] = useState<string[]>(["gh-port", "launch"]);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(false);
  const [alias, setAlias] = useState("gh-portfolio");
  const [longUrl, setLongUrl] = useState("https://github.com/aaradhya/devlink-platform");
  const [protectedLink, setProtectedLink] = useState(true);
  const [routing, setRouting] = useState(true);
  const [range, setRange] = useState("30d");

  useEffect(() => {
    if (!toast) return;
    const id = window.setTimeout(() => setToast(false), 2600);
    return () => window.clearTimeout(id);
  }, [toast]);

  function copy(value: string) {
    void navigator.clipboard?.writeText(value);
    setCopied(value);
    window.setTimeout(() => setCopied(null), 2000);
  }

  function createLink() {
    setLoading(true);
    window.setTimeout(() => {
      setLoading(false);
      setToast(true);
      setPage("dashboard");
    }, 900);
  }

  const shellPages: Page[] = ["dashboard", "create", "analytics", "links", "workspace"];
  const inApp = shellPages.includes(page);

  return (
    <div className="min-h-screen bg-[#080808] text-[#F5F5F5] selection:bg-[#E8FF47] selection:text-[#080808]">
      <StylePrimitive />
      {toast && <Toast />}

      {!inApp && (
        <div className="page-fade">
          {page === "landing" && <LandingPage setPage={setPage} setAuthMode={setAuthMode} />}
          {page === "auth" && (
            <AuthPage
              mode={authMode}
              setMode={setAuthMode}
              setPage={setPage}
              showPassword={showPassword}
              setShowPassword={setShowPassword}
            />
          )}
        </div>
      )}

      {inApp && (
        <div className="flex min-h-screen bg-[#080808]">
          <Sidebar page={page} setPage={setPage} />
          <main className="min-w-0 flex-1 pb-24 lg:pb-0 lg:pl-[240px]">
            <Topbar page={page} />
            <div className="mx-auto max-w-[1280px] px-4 py-8 sm:px-6 lg:px-8">
              <div key={page} className="page-fade">
                {page === "dashboard" && <DashboardPage setPage={setPage} copied={copied} copy={copy} />}
                {page === "create" && (
                  <CreatePage
                    alias={alias}
                    longUrl={longUrl}
                    loading={loading}
                    protectedLink={protectedLink}
                    routing={routing}
                    setAlias={setAlias}
                    setLongUrl={setLongUrl}
                    setProtectedLink={setProtectedLink}
                    setRouting={setRouting}
                    createLink={createLink}
                    copy={copy}
                    copied={copied}
                  />
                )}
                {page === "analytics" && <AnalyticsPage copied={copied} copy={copy} range={range} setRange={setRange} />}
                {page === "links" && (
                  <LinksPage copied={copied} copy={copy} selected={selected} setSelected={setSelected} />
                )}
                {page === "workspace" && <WorkspacePage />}
              </div>
            </div>
          </main>
          <MobileNav page={page} setPage={setPage} />
          {page === "links" && selected.length > 0 && <BulkBar count={selected.length} />}
        </div>
      )}
    </div>
  );
}

/* Page 1: Landing */
function LandingPage({
  setPage,
  setAuthMode,
}: {
  setPage: (page: Page) => void;
  setAuthMode: (mode: "login" | "register") => void;
}) {
  return (
    <div className="dot-grid relative min-h-screen overflow-hidden bg-[#080808]">
      <div className="pointer-events-none absolute right-[-120px] top-[-120px] h-[420px] w-[420px] rounded-full bg-[#E8FF47] opacity-[0.15] blur-[200px]" />
      <nav className="relative z-10 mx-auto flex h-20 max-w-[1280px] items-center justify-between px-6">
        <button className="flex items-center gap-3 text-left" onClick={() => setPage("landing")}>
          <LogoMark />
          <span className="text-sm font-semibold tracking-[0.18em]">DEVLINK</span>
        </button>
        <div className="hidden items-center gap-8 text-sm text-[#888888] md:flex">
          {["Features", "Docs", "Pricing"].map((item) => (
            <button key={item} className="transition-snap hover:text-[#F5F5F5]">{item}</button>
          ))}
        </div>
        <div className="flex items-center gap-3">
          <button
            className="hidden text-sm text-[#888888] transition-snap hover:text-[#F5F5F5] sm:block"
            onClick={() => {
              setAuthMode("login");
              setPage("auth");
            }}
          >
            Login
          </button>
          <button
            className="button-accent"
            onClick={() => {
              setAuthMode("register");
              setPage("auth");
            }}
          >
            Get Started
          </button>
        </div>
      </nav>

      <section className="relative z-10 mx-auto grid min-h-[calc(100vh-80px)] max-w-[1280px] items-center gap-12 px-6 py-16 lg:grid-cols-[0.6fr_0.4fr]">
        <div>
          <p className="mb-6 text-[11px] font-medium tracking-[0.24em] text-[#888888]">LINK INTELLIGENCE PLATFORM</p>
          <h1 className="max-w-3xl text-[48px] font-bold leading-[0.98] tracking-[-0.04em] text-[#F5F5F5] sm:text-[64px]">
            Every link tells
            <span className="block font-light text-[#888888]">a story.</span>
          </h1>
          <p className="mt-6 max-w-[480px] text-base leading-[1.6] text-[#888888]">
            Short links with the analytics depth of a full intelligence platform. Built for developers who care about performance.
          </p>
          <div className="mt-8 flex flex-col gap-4 sm:flex-row sm:items-center">
            <button
              className="button-accent px-6 py-3"
              onClick={() => {
                setAuthMode("register");
                setPage("auth");
              }}
            >
              Start for free
            </button>
            <button className="text-sm text-[#888888] underline-offset-4 transition-snap hover:text-[#F5F5F5] hover:underline">
              View architecture <ArrowRight className="inline h-4 w-4" />
            </button>
          </div>
          <p className="mt-8 text-xs text-[#444444]">Trusted by engineers at 40+ companies</p>
        </div>

        <TerminalWindow />
      </section>

      <section className="mx-auto max-w-[1280px] px-6 py-24">
        <div className="grid gap-14">
          {[
            ["01", "Sub-50ms Redirects", "Redis-first short code lookups with measured fallback paths and hot route instrumentation."],
            ["02", "Privacy-First Analytics", "Daily salted IP hashes, aggregate dashboards, and no raw visitor IP persistence."],
            ["03", "Conditional Routing", "Geo, device, and time-aware routing rules without turning the interface into a rule engine maze."],
            ["04", "Dead Link Radar", "Expiration workers, malicious URL scans, and flagged-state handling for public redirects."],
          ].map(([num, title, copy]) => (
            <div key={num} className="grid items-center gap-6 border-t border-white/[0.06] pt-10 md:grid-cols-[220px_1fr]">
              <span className="text-[96px] font-bold leading-none tracking-[-0.08em] text-[#1A1A1A] sm:text-[120px]">{num}</span>
              <div>
                <h2 className="text-2xl font-semibold tracking-[-0.03em] text-[#F5F5F5]">{title}</h2>
                <p className="mt-3 max-w-2xl text-sm leading-6 text-[#888888]">{copy}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-[1280px] px-6 py-20">
        <div className="relative grid gap-8 md:grid-cols-3">
          <div className="absolute left-[16%] right-[16%] top-5 hidden border-t border-dashed border-white/10 md:block" />
          {[
            ["1", "Create", "Normalize, hash, dedupe, and encode."],
            ["2", "Redirect", "Cache hit first, database only when needed."],
            ["3", "Aggregate", "Publish events and roll up daily intelligence."],
          ].map(([step, title, copy]) => (
            <div key={step} className="relative">
              <span className="grid h-10 w-10 place-items-center rounded-[4px] border border-white/[0.06] bg-[#111111] text-sm font-semibold text-[#E8FF47] shadow-panel">
                {step}
              </span>
              <h3 className="mt-5 text-lg font-semibold text-[#F5F5F5]">{title}</h3>
              <p className="mt-2 text-sm text-[#888888]">{copy}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="border-y border-white/[0.06] bg-[#0D0D0D]">
        <div className="mx-auto grid max-w-[1280px] gap-8 px-6 py-14 md:grid-cols-3">
          <MetricStrip value="10M+" label="links shortened" />
          <MetricStrip value="99.9%" label="uptime" />
          <MetricStrip value="<50ms" label="redirect latency" />
        </div>
      </section>
    </div>
  );
}

/* Page 2: Auth */
function AuthPage({
  mode,
  setMode,
  setPage,
  showPassword,
  setShowPassword,
}: {
  mode: "login" | "register";
  setMode: (mode: "login" | "register") => void;
  setPage: (page: Page) => void;
  showPassword: boolean;
  setShowPassword: (value: boolean) => void;
}) {
  const isRegister = mode === "register";
  return (
    <div className="dot-grid grid min-h-screen place-items-center bg-[#080808] px-6">
      <div className="w-full max-w-[400px] rounded-[8px] border border-white/[0.06] bg-[#111111] p-10 shadow-panel">
        <button className="mb-8 flex items-center gap-3" onClick={() => setPage("landing")}>
          <LogoMark />
          <span className="text-sm font-semibold tracking-[0.18em]">DEVLINK</span>
        </button>
        <div className="transition-snap">
          <h1 className="text-2xl font-semibold tracking-[-0.03em] text-[#F5F5F5]">
            {isRegister ? "Create account" : "Welcome back"}
          </h1>
          <p className="mt-2 text-sm leading-6 text-[#888888]">
            {isRegister ? "Set up your first workspace and start shipping traceable links." : "Continue to your link intelligence workspace."}
          </p>
        </div>
        <div className="mt-8 space-y-4">
          {isRegister && <Field label="Name" value="Aaradhya Mehra" />}
          <Field label="Email" value="aaradhya@devlink.ai" />
          <Field
            label="Password"
            value={showPassword ? "correct-horse-battery" : "••••••••••••••••••••"}
            right={
              <button className="text-[#444444] transition-snap hover:text-[#F5F5F5]" onClick={() => setShowPassword(!showPassword)}>
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            }
          />
          <button className="button-accent w-full py-3" onClick={() => setPage("dashboard")}>
            {isRegister ? "Create workspace" : "Sign in"}
          </button>
        </div>
        <p className="mt-6 text-center text-sm text-[#888888]">
          {isRegister ? "Already have an account?" : "Do not have an account?"}{" "}
          <button className="text-[#F5F5F5] underline-offset-4 transition-snap hover:underline" onClick={() => setMode(isRegister ? "login" : "register")}>
            {isRegister ? "Sign in" : "Sign up"}
          </button>
        </p>
      </div>
    </div>
  );
}

/* Page 3: Dashboard */
function DashboardPage({
  setPage,
  copied,
  copy,
}: {
  setPage: (page: Page) => void;
  copied: string | null;
  copy: (value: string) => void;
}) {
  return (
    <div className="space-y-8">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <Heading eyebrow="HOME" title="Dashboard" copy="A precise view of link health, traffic, and operational state." />
        <button className="button-accent w-fit px-4 py-2.5" onClick={() => setPage("create")}>
          <Plus className="mr-2 h-4 w-4" />
          Quick create
        </button>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Total Links" value="2,847" trend="+12.4% vs last week" icon={Link2} />
        <StatCard label="Total Clicks" value="1.2M" trend="+18.9% vs last week" icon={MousePointerClick} critical />
        <StatCard label="Active Links" value="2,391" trend="+8.1% vs last week" icon={Activity} />
        <StatCard label="Avg CTR" value="3.8%" trend="-1.2% vs last week" icon={Zap} negative />
      </div>
      <section>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold tracking-[-0.02em] text-[#F5F5F5]">Recent Links</h2>
          <button className="text-sm text-[#888888] transition-snap hover:text-[#F5F5F5]" onClick={() => setPage("links")}>
            View all <ArrowRight className="inline h-4 w-4" />
          </button>
        </div>
        <LinksTable rows={linkRows} copied={copied} copy={copy} />
      </section>
    </div>
  );
}

/* Page 4: Create Link */
function CreatePage({
  alias,
  longUrl,
  loading,
  protectedLink,
  routing,
  setAlias,
  setLongUrl,
  setProtectedLink,
  setRouting,
  createLink,
  copy,
  copied,
}: {
  alias: string;
  longUrl: string;
  loading: boolean;
  protectedLink: boolean;
  routing: boolean;
  setAlias: (value: string) => void;
  setLongUrl: (value: string) => void;
  setProtectedLink: (value: boolean) => void;
  setRouting: (value: boolean) => void;
  createLink: () => void;
  copy: (value: string) => void;
  copied: string | null;
}) {
  const shortUrl = `lnk.ai/${alias || "alias"}`;
  const validUrl = longUrl.startsWith("https://") && longUrl.includes(".");
  return (
    <div className="grid gap-8 xl:grid-cols-[0.6fr_0.4fr]">
      <div>
        <Heading eyebrow="CREATE LINK" title="Configure the redirect once. Trust it everywhere." copy="Validation, alias checks, expiration, and routing rules are designed to feel operational, not decorative." />
        <div className="mt-8 space-y-6">
          <Field label="Long URL" value={longUrl} onChange={setLongUrl} indicator={validUrl ? "good" : "bad"} large />
          <div>
            <label className="mb-2 block text-[11px] font-medium tracking-[0.18em] text-[#888888]">CUSTOM ALIAS</label>
            <div className="flex rounded-[4px] border border-white/[0.06] bg-[#080808] transition-snap focus-within:border-[#E8FF47] focus-within:shadow-[0_0_0_3px_rgba(232,255,71,0.1)]">
              <span className="border-r border-white/[0.06] px-3 py-3 text-sm text-[#444444]">lnk.ai/</span>
              <input className="min-w-0 flex-1 bg-transparent px-3 py-3 text-sm text-[#F5F5F5] outline-none" value={alias} onChange={(event) => setAlias(event.target.value)} />
              <span className="px-3 py-3 text-xs text-[#22C55E]">AVAILABLE</span>
            </div>
          </div>
          <Field label="Expiration" value="2026-12-31 23:59 UTC" />
          <Toggle label="Password protection" description="Require verification before redirect." checked={protectedLink} onChange={setProtectedLink} />
          <Toggle label="Conditional routing" description="Route by country, device, and time window." checked={routing} onChange={setRouting} />
          {routing && (
            <div className="grid gap-4 rounded-[8px] border border-white/[0.06] bg-[#111111] p-4 shadow-panel md:grid-cols-3">
              <Field label="Geo rule" value="US, IN -> /launch" />
              <Field label="Device rule" value="Mobile -> /m" />
              <Field label="Time rule" value="09:00-18:00 UTC" />
            </div>
          )}
          <button className="button-accent px-5 py-3 disabled:opacity-50" disabled={loading || !validUrl} onClick={createLink}>
            {loading && <span className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-[#080808]/30 border-t-[#080808]" />}
            {loading ? "Creating..." : "Create link"}
          </button>
        </div>
      </div>
      <aside className="h-fit rounded-[8px] border border-white/[0.06] bg-[#111111] p-6 shadow-panel">
        <p className="text-[11px] font-medium tracking-[0.18em] text-[#888888]">LIVE PREVIEW</p>
        <div className="mt-6 border-y border-white/[0.06] py-6">
          <p className="font-mono text-2xl tracking-[-0.04em] text-[#F5F5F5]">{shortUrl}</p>
          <p className="mt-2 truncate text-sm text-[#888888]">{longUrl}</p>
        </div>
        <QrPattern seed={alias} />
        <button className="mt-6 w-full rounded-[4px] border border-white/[0.06] bg-[#080808] px-4 py-3 text-sm text-[#F5F5F5] transition-snap hover:border-white/[0.12]" onClick={() => copy(shortUrl)}>
          {copied === shortUrl ? <Check className="mr-2 inline h-4 w-4 scale-110 text-[#E8FF47]" /> : <Copy className="mr-2 inline h-4 w-4" />}
          Copy link
        </button>
      </aside>
    </div>
  );
}

/* Page 5: Analytics */
function AnalyticsPage({
  copied,
  copy,
  range,
  setRange,
}: {
  copied: string | null;
  copy: (value: string) => void;
  range: string;
  setRange: (value: string) => void;
}) {
  const url = "lnk.ai/gh-port";
  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-5 border-b border-white/[0.06] pb-6 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <div className="mb-3 flex items-center gap-3">
            <StatusBadge status="active" />
            <span className="text-xs text-[#444444]">Last processed event 41ms ago</span>
          </div>
          <h1 className="font-mono text-2xl tracking-[-0.04em] text-[#F5F5F5]">gh-port</h1>
          <p className="mt-2 max-w-2xl truncate text-sm text-[#888888]">https://github.com/aaradhya/devlink-platform</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Segmented options={["7d", "30d", "90d", "Custom"]} value={range} onChange={setRange} />
          <button className="icon-button" onClick={() => copy(url)}>{copied === url ? <Check className="h-4 w-4 text-[#E8FF47]" /> : <Copy className="h-4 w-4" />}</button>
          <button className="icon-button"><Share2 className="h-4 w-4" /></button>
        </div>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Total Clicks" value="488,210" trend="+22.6% vs last week" icon={MousePointerClick} critical />
        <StatCard label="Countries" value="42" trend="+6 new" icon={Activity} />
        <StatCard label="Top Device" value="Desktop" trend="58% of traffic" icon={ExternalLink} />
        <StatCard label="Peak Day" value="Jun 15" trend="6,190 clicks" icon={Sparkles} />
      </div>
      <section>
        <h2 className="mb-4 text-lg font-semibold text-[#F5F5F5]">Traffic over time</h2>
        <div className="h-[360px]">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="acidFill" x1="0" x2="0" y1="0" y2="1">
                  <stop offset="0%" stopColor={accent} stopOpacity={0.15} />
                  <stop offset="100%" stopColor={accent} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="rgba(255,255,255,0.04)" vertical={false} />
              <XAxis dataKey="date" stroke="#444444" tickLine={false} axisLine={false} fontSize={12} />
              <YAxis stroke="#444444" tickLine={false} axisLine={false} fontSize={12} />
              <Tooltip contentStyle={tooltipStyle} />
              <Area type="monotone" dataKey="clicks" stroke={accent} strokeWidth={2} fill="url(#acidFill)" isAnimationActive />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </section>
      <div className="grid gap-8 xl:grid-cols-2">
        <ChartPanel title="Top Countries">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={countryData} layout="vertical">
              <XAxis type="number" hide />
              <YAxis dataKey="country" type="category" width={120} stroke="#888888" tickLine={false} axisLine={false} fontSize={12} />
              <Tooltip contentStyle={tooltipStyle} />
              <Bar dataKey="clicks" fill="rgba(232,255,71,0.6)" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartPanel>
        <ChartPanel title="Devices">
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie data={deviceData} dataKey="value" innerRadius={70} outerRadius={105} paddingAngle={3}>
                {deviceData.map((entry) => <Cell key={entry.name} fill={entry.color} />)}
              </Pie>
              <Tooltip contentStyle={tooltipStyle} />
            </PieChart>
          </ResponsiveContainer>
          <div className="grid grid-cols-3 gap-2">
            {deviceData.map((device) => (
              <div key={device.name} className="border-t border-white/[0.06] pt-3">
                <p className="text-xs text-[#888888]">{device.name}</p>
                <p className="font-mono text-lg text-[#F5F5F5]">{device.value}%</p>
              </div>
            ))}
          </div>
        </ChartPanel>
      </div>
      <ReferrersTable />
    </div>
  );
}

/* Page 6: Link Management */
function LinksPage({
  copied,
  copy,
  selected,
  setSelected,
}: {
  copied: string | null;
  copy: (value: string) => void;
  selected: string[];
  setSelected: (value: string[]) => void;
}) {
  return (
    <div className="space-y-6">
      <Heading eyebrow="LINK MANAGEMENT" title="Operate across every redirect." copy="Search, filter, sort, and bulk-manage links without leaving the keyboard." />
      <div className="grid gap-3 lg:grid-cols-[1fr_auto_auto_auto]">
        <SearchInput />
        <FilterButton label="Status" />
        <FilterButton label="Date range" />
        <FilterButton label="Workspace" />
      </div>
      <LinksTable rows={linkRows} copied={copied} copy={copy} selectable selected={selected} setSelected={setSelected} />
      <div className="flex justify-end gap-2 text-sm">
        {["Prev", "1", "2", "3", "Next"].map((item) => (
          <button key={item} className={`rounded-[4px] border border-white/[0.06] px-3 py-2 transition-snap hover:border-white/[0.12] ${item === "1" ? "text-[#E8FF47]" : "text-[#888888]"}`}>
            {item}
          </button>
        ))}
      </div>
    </div>
  );
}

/* Page 7: Workspace */
function WorkspacePage() {
  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <Heading eyebrow="WORKSPACE" title="Growth" copy="Invite members, assign roles, and govern shared link surfaces." />
        <button className="rounded-[4px] border border-white/[0.06] bg-[#111111] px-4 py-2 text-sm text-[#F5F5F5] shadow-panel transition-snap hover:border-white/[0.12]">
          Growth <ChevronDown className="ml-2 inline h-4 w-4" />
        </button>
      </div>
      <div className="grid gap-8 xl:grid-cols-[0.58fr_0.42fr]">
        <section>
          <h2 className="mb-4 text-lg font-semibold text-[#F5F5F5]">Members</h2>
          <div className="divide-y divide-white/[0.06] border-y border-white/[0.06]">
            {members.map((member) => (
              <div key={member.email} className="grid gap-4 py-4 sm:grid-cols-[1fr_auto_auto] sm:items-center">
                <div className="flex items-center gap-3">
                  <span className="grid h-9 w-9 place-items-center rounded-[4px] bg-[#111111] text-xs font-semibold text-[#F5F5F5] shadow-panel">
                    {member.name.split(" ").map((part) => part[0]).join("")}
                  </span>
                  <div>
                    <p className="text-sm font-medium text-[#F5F5F5]">{member.name}</p>
                    <p className="text-xs text-[#888888]">{member.email}</p>
                  </div>
                </div>
                <RoleBadge role={member.role} />
                <button className="text-left text-xs text-[#444444] transition-snap hover:text-[#EF4444] sm:text-right">Remove</button>
              </div>
            ))}
          </div>
        </section>
        <aside className="space-y-6">
          <div className="rounded-[8px] border border-white/[0.06] bg-[#111111] p-6 shadow-panel">
            <h2 className="text-lg font-semibold text-[#F5F5F5]">Invite member</h2>
            <div className="mt-5 space-y-4">
              <Field label="Email" value="new.engineer@company.com" />
              <FilterButton label="Role: Editor" full />
              <button className="button-accent w-full py-3">Send invite</button>
            </div>
          </div>
          <div className="rounded-[8px] border border-white/[0.06] bg-[#111111] p-6 shadow-panel">
            <h2 className="text-lg font-semibold text-[#F5F5F5]">Pending invites</h2>
            <div className="mt-4 space-y-3 text-sm">
              {["rhea@company.com", "samir@company.com"].map((email) => (
                <div key={email} className="flex items-center justify-between border-b border-white/[0.06] pb-3 last:border-0 last:pb-0">
                  <span className="text-[#888888]">{email}</span>
                  <span className="text-xs text-[#444444]">Sent today</span>
                </div>
              ))}
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}

function Sidebar({ page, setPage }: { page: Page; setPage: (page: Page) => void }) {
  return (
    <aside className="fixed inset-y-0 left-0 z-40 hidden w-[240px] border-r border-white/[0.06] bg-[#080808] lg:block">
      <div className="flex h-full flex-col p-6">
        <button className="mb-8 flex items-center gap-3" onClick={() => setPage("landing")}>
          <LogoMark />
          <span className="text-sm font-semibold tracking-[0.18em]">DEVLINK</span>
        </button>
        {["workspace", "account"].map((section) => (
          <div key={section} className="mb-8">
            <p className="mb-2 mt-8 text-[10px] font-medium uppercase tracking-[0.24em] text-[#444444] first:mt-0">{section}</p>
            <div className="space-y-1">
              {navItems.filter((item) => item.section === section).map((item) => {
                const active = page === item.page;
                return (
                  <button
                    key={item.page}
                    className={`transition-snap flex h-12 w-full items-center gap-3 border-l-2 px-4 text-sm ${
                      active
                        ? "border-[#E8FF47] bg-[rgba(232,255,71,0.04)] text-[#F5F5F5]"
                        : "border-transparent text-[#888888] hover:text-[#F5F5F5]"
                    }`}
                    onClick={() => setPage(item.page)}
                  >
                    <item.icon className={`h-4 w-4 ${active ? "text-[#E8FF47]" : ""}`} />
                    {item.label}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
        <div className="mt-auto flex items-center gap-3 border-t border-white/[0.06] pt-4">
          <span className="grid h-9 w-9 place-items-center rounded-[4px] bg-[#111111] text-xs font-semibold shadow-panel">AM</span>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm text-[#F5F5F5]">Aaradhya</p>
            <p className="truncate text-xs text-[#888888]">founder@devlink.ai</p>
          </div>
          <Settings className="h-4 w-4 text-[#444444]" />
        </div>
      </div>
    </aside>
  );
}

function Topbar({ page }: { page: Page }) {
  return (
    <header className="sticky top-0 z-30 flex h-14 items-center border-b border-white/[0.06] bg-[#080808]/90 px-4 backdrop-blur sm:px-6 lg:px-8">
      <div className="mx-auto flex w-full max-w-[1280px] items-center gap-4">
        <h1 className="hidden min-w-[160px] text-sm font-medium text-[#F5F5F5] sm:block">{titleFor(page)}</h1>
        <div className="mx-auto hidden w-[320px] items-center gap-2 rounded-[4px] border border-white/[0.06] bg-[#111111] px-3 py-2 md:flex">
          <Search className="h-4 w-4 text-[#444444]" />
          <span className="flex-1 text-sm text-[#444444]">Search links...</span>
          <span className="text-[11px] text-[#444444]">CMD K</span>
        </div>
        <button className="relative ml-auto rounded-[4px] p-2 text-[#888888] transition-snap hover:bg-[#1A1A1A] hover:text-[#F5F5F5]">
          <Bell className="h-4 w-4" />
          <span className="absolute right-1 top-1 h-1.5 w-1.5 rounded-full bg-[#EF4444]" />
        </button>
        <span className="grid h-8 w-8 place-items-center rounded-[4px] bg-[#111111] text-xs font-semibold shadow-panel">AM</span>
      </div>
    </header>
  );
}

function MobileNav({ page, setPage }: { page: Page; setPage: (page: Page) => void }) {
  return (
    <nav className="fixed inset-x-0 bottom-0 z-40 grid grid-cols-5 border-t border-white/[0.06] bg-[#080808]/95 backdrop-blur lg:hidden">
      {navItems.slice(0, 5).map((item) => (
        <button key={item.page} className={`py-3 text-xs ${page === item.page ? "text-[#E8FF47]" : "text-[#888888]"}`} onClick={() => setPage(item.page)}>
          <item.icon className="mx-auto mb-1 h-4 w-4" />
          {item.label.split(" ")[0]}
        </button>
      ))}
    </nav>
  );
}

function LinksTable({
  rows,
  copied,
  copy,
  selectable,
  selected = [],
  setSelected,
}: {
  rows: LinkRow[];
  copied: string | null;
  copy: (value: string) => void;
  selectable?: boolean;
  selected?: string[];
  setSelected?: (value: string[]) => void;
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[860px]">
        <thead>
          <tr className="text-left text-[11px] uppercase tracking-[0.18em] text-[#888888]">
            {selectable && <th className="w-12 py-3" />}
            <th className="py-3">Short Code</th>
            <th className="py-3">Destination</th>
            <th className="py-3 text-right">Clicks</th>
            <th className="py-3">Status</th>
            <th className="py-3">Created</th>
            <th className="py-3 text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => {
            const url = `lnk.ai/${row.code}`;
            return (
              <tr
                key={row.code}
                className="group border-b border-white/[0.04] transition-snap hover:border-transparent hover:bg-white/[0.02]"
                style={{ animationDelay: `${index * 30}ms` }}
              >
                {selectable && (
                  <td className="py-4">
                    <input
                      className="h-4 w-4 accent-[#E8FF47]"
                      type="checkbox"
                      checked={selected.includes(row.code)}
                      onChange={(event) => setSelected?.(event.target.checked ? [...selected, row.code] : selected.filter((code) => code !== row.code))}
                    />
                  </td>
                )}
                <td className="py-4 font-mono text-sm text-[#F5F5F5]">{row.code}</td>
                <td className="max-w-[360px] py-4">
                  <p className="truncate text-sm text-[#888888]">{row.destination}</p>
                  <p className="mt-1 text-xs text-[#444444]">{row.workspace}</p>
                </td>
                <td className="py-4 text-right font-mono text-sm tabular-nums text-[#F5F5F5]">{row.clicks.toLocaleString()}</td>
                <td className="py-4"><StatusBadge status={row.status} /></td>
                <td className="py-4 text-sm text-[#888888]">{row.created}</td>
                <td className="py-4">
                  <div className="flex justify-end gap-1 opacity-0 transition-snap group-hover:opacity-100">
                    <button className="icon-button" onClick={() => copy(url)}>
                      {copied === url ? <Check className="h-4 w-4 scale-110 text-[#E8FF47]" /> : <Copy className="h-4 w-4" />}
                    </button>
                    <button className="icon-button"><BarChart3 className="h-4 w-4" /></button>
                    <button className="icon-button"><Trash2 className="h-4 w-4" /></button>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function StatCard({ label, value, trend, icon: Icon, critical, negative }: { label: string; value: string; trend: string; icon: LucideIcon; critical?: boolean; negative?: boolean }) {
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const id = window.setTimeout(() => setVisible(true), 80);
    return () => window.clearTimeout(id);
  }, []);
  return (
    <div className="rounded-[8px] border border-white/[0.06] bg-[#111111] p-6 shadow-panel transition-snap hover:border-white/[0.12]">
      <div className="flex items-center justify-between">
        <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-[#888888]">{label}</p>
        <Icon className="h-4 w-4 text-[#444444]" />
      </div>
      <p className={`mt-5 font-mono text-3xl font-bold tabular-nums tracking-[-0.04em] transition-snap ${visible ? "translate-y-0 opacity-100" : "translate-y-2 opacity-0"} ${critical ? "text-[#E8FF47]" : "text-[#F5F5F5]"}`}>
        {value}
      </p>
      <span className={`mt-4 inline-flex rounded-[2px] bg-[#888888]/10 px-2 py-1 text-xs ${negative ? "text-[#EF4444]" : "text-[#22C55E]"}`}>
        {trend}
      </span>
    </div>
  );
}

function Field({ label, value, onChange, right, indicator, large }: { label: string; value: string; onChange?: (value: string) => void; right?: ReactNode; indicator?: "good" | "bad"; large?: boolean }) {
  return (
    <label className="block">
      <span className="mb-2 block text-[11px] font-medium uppercase tracking-[0.18em] text-[#888888]">{label}</span>
      <div className="flex items-center rounded-[4px] border border-white/[0.06] bg-[#080808] px-3 transition-snap focus-within:border-[#E8FF47] focus-within:shadow-[0_0_0_3px_rgba(232,255,71,0.1)]">
        {indicator && <span className={`mr-3 h-2 w-2 rounded-full ${indicator === "good" ? "bg-[#22C55E]" : "bg-[#EF4444]"}`} />}
        <input className={`min-w-0 flex-1 bg-transparent py-3 text-sm text-[#F5F5F5] outline-none placeholder:text-[#444444] ${large ? "text-base" : ""}`} value={value} onChange={(event) => onChange?.(event.target.value)} />
        {right}
      </div>
    </label>
  );
}

function Toggle({ label, description, checked, onChange }: { label: string; description: string; checked: boolean; onChange: (checked: boolean) => void }) {
  return (
    <button className="flex w-full items-center justify-between border-y border-white/[0.06] py-4 text-left transition-snap hover:bg-white/[0.02]" onClick={() => onChange(!checked)}>
      <span>
        <span className="block text-sm font-medium text-[#F5F5F5]">{label}</span>
        <span className="text-sm text-[#888888]">{description}</span>
      </span>
      <span className={`relative h-6 w-10 rounded-[4px] border transition-snap ${checked ? "border-[#E8FF47] bg-[#E8FF47]" : "border-white/[0.06] bg-[#111111]"}`}>
        <span className={`absolute top-1 h-4 w-4 rounded-[2px] bg-[#080808] transition-snap ${checked ? "left-5" : "left-1 bg-[#444444]"}`} />
      </span>
    </button>
  );
}

function StatusBadge({ status }: { status: Status }) {
  const styles: Record<Status, string> = {
    active: "bg-[#22C55E]/15 text-[#22C55E]",
    flagged: "bg-[#EF4444]/15 text-[#EF4444]",
    expired: "bg-[#888888]/15 text-[#888888]",
  };
  return <span className={`inline-flex rounded-[2px] px-2 py-1 text-xs capitalize ${styles[status]}`}>{status}</span>;
}

function RoleBadge({ role }: { role: Role }) {
  const styles: Record<Role, string> = {
    Owner: "bg-[#E8FF47] text-[#080808]",
    Admin: "bg-blue-500/15 text-blue-300",
    Editor: "bg-purple-500/15 text-purple-300",
    Viewer: "bg-[#888888]/15 text-[#888888]",
  };
  return <span className={`w-fit rounded-[2px] px-2 py-1 text-xs ${styles[role]}`}>{role}</span>;
}

function Heading({ eyebrow, title, copy }: { eyebrow: string; title: string; copy: string }) {
  return (
    <div>
      <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-[#888888]">{eyebrow}</p>
      <h1 className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-[#F5F5F5] sm:text-4xl">{title}</h1>
      <p className="mt-3 max-w-2xl text-sm leading-6 text-[#888888]">{copy}</p>
    </div>
  );
}

function SearchInput() {
  return (
    <div className="flex items-center gap-2 rounded-[4px] border border-white/[0.06] bg-[#111111] px-3 py-3 transition-snap focus-within:border-[#E8FF47]">
      <Search className="h-4 w-4 text-[#444444]" />
      <input className="min-w-0 flex-1 bg-transparent text-sm text-[#F5F5F5] outline-none placeholder:text-[#444444]" placeholder="Search short code or destination..." />
    </div>
  );
}

function FilterButton({ label, full }: { label: string; full?: boolean }) {
  return (
    <button className={`rounded-[4px] border border-white/[0.06] bg-[#111111] px-4 py-3 text-left text-sm text-[#888888] shadow-panel transition-snap hover:border-white/[0.12] hover:text-[#F5F5F5] ${full ? "w-full" : ""}`}>
      <Filter className="mr-2 inline h-4 w-4" />
      {label}
      <ChevronDown className="ml-2 inline h-4 w-4" />
    </button>
  );
}

function Segmented({ options, value, onChange }: { options: string[]; value: string; onChange: (value: string) => void }) {
  return (
    <div className="flex rounded-[4px] border border-white/[0.06] bg-[#111111] p-1">
      {options.map((option) => (
        <button key={option} className={`rounded-[3px] px-3 py-1.5 text-sm transition-snap ${value === option ? "bg-[#E8FF47] text-[#080808]" : "text-[#888888] hover:text-[#F5F5F5]"}`} onClick={() => onChange(option)}>
          {option}
        </button>
      ))}
    </div>
  );
}

function ChartPanel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section>
      <h2 className="mb-4 text-lg font-semibold text-[#F5F5F5]">{title}</h2>
      {children}
    </section>
  );
}

function ReferrersTable() {
  return (
    <section>
      <h2 className="mb-4 text-lg font-semibold text-[#F5F5F5]">Referrers</h2>
      <div className="divide-y divide-white/[0.06] border-y border-white/[0.06]">
        {referrers.map((row) => (
          <div key={row.source} className="grid gap-3 py-4 text-sm sm:grid-cols-[1fr_120px_220px] sm:items-center">
            <span className="font-medium text-[#F5F5F5]">{row.source}</span>
            <span className="font-mono tabular-nums text-[#888888]">{row.clicks.toLocaleString()}</span>
            <span className="flex items-center gap-3">
              <span className="h-1.5 flex-1 bg-[#1A1A1A]">
                <span className="block h-full bg-[#E8FF47]" style={{ width: `${row.pct}%` }} />
              </span>
              <span className="w-10 text-right font-mono text-[#888888]">{row.pct}%</span>
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}

function TerminalWindow() {
  return (
    <div className="rounded-[8px] border border-white/[0.06] bg-[#111111] p-5 font-mono text-sm shadow-panel">
      <div className="mb-5 flex gap-2">
        <span className="h-2.5 w-2.5 rounded-full bg-[#444444]" />
        <span className="h-2.5 w-2.5 rounded-full bg-[#444444]" />
        <span className="h-2.5 w-2.5 rounded-full bg-[#E8FF47]" />
      </div>
      <pre className="whitespace-pre-wrap leading-6 text-[#888888]">
        <span className="text-[#E8FF47]">POST</span> <span className="text-[#F5F5F5]">/api/v1/links</span>
        {`\n{\n  "long_url": `}
        <span className="text-[#F5F5F5]">"https://github.com/aaradhya/..."</span>
        {`,\n  "custom_alias": `}
        <span className="text-[#F5F5F5]">"gh-portfolio"</span>
        {`,\n  "expires_at": `}
        <span className="text-[#F5F5F5]">"2026-12-31"</span>
        {`\n}\n\n`}
        <span className="text-[#444444]">Response</span>
        {`\n{\n  "short_code": `}
        <span className="text-[#F5F5F5]">"gh-port"</span>
        {`,\n  "short_url": `}
        <span className="text-[#F5F5F5]">"lnk.ai/gh-port"</span>
        {`,\n  "created_at": `}
        <span className="text-[#F5F5F5]">"2026-06-15T09:41:00Z"</span>
        {`\n}`}
        <span className="ml-1 inline-block h-4 w-2 animate-pulse bg-[#E8FF47]" />
      </pre>
    </div>
  );
}

function QrPattern({ seed }: { seed: string }) {
  const cells = useMemo(() => Array.from({ length: 121 }, (_, index) => (index * 11 + seed.length * 7) % 4 !== 0), [seed]);
  return (
    <div className="mx-auto mt-6 grid w-48 grid-cols-11 gap-1 bg-[#F5F5F5] p-4">
      {cells.map((cell, index) => (
        <span key={`${seed}-${index}`} className={`aspect-square ${cell ? "bg-[#080808]" : "bg-[#F5F5F5]"}`} />
      ))}
    </div>
  );
}

function MetricStrip({ value, label }: { value: string; label: string }) {
  return (
    <div>
      <p className="font-mono text-5xl font-bold tabular-nums tracking-[-0.05em] text-[#F5F5F5]">{value}</p>
      <p className="mt-2 text-xs uppercase tracking-[0.18em] text-[#888888]">{label}</p>
    </div>
  );
}

function LogoMark() {
  return (
    <span className="grid h-8 w-8 place-items-center rounded-[4px] bg-[#E8FF47] text-[#080808]">
      <Link2 className="h-4 w-4" />
    </span>
  );
}

function Toast() {
  return (
    <div className="fixed right-4 top-4 z-50 flex items-center gap-3 rounded-[4px] border border-white/[0.06] bg-[#111111] px-4 py-3 text-sm text-[#F5F5F5] shadow-panel">
      <Check className="h-4 w-4 text-[#E8FF47]" />
      Link created, cached, and ready to route.
    </div>
  );
}

function BulkBar({ count }: { count: number }) {
  return (
    <div className="fixed bottom-20 left-4 right-4 z-40 rounded-[8px] border border-white/[0.06] bg-[#111111] p-4 shadow-panel lg:bottom-6 lg:left-[calc(240px+24px)]">
      <div className="mx-auto flex max-w-[960px] flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm text-[#F5F5F5]">{count} links selected</p>
        <div className="flex gap-2">
          <button className="rounded-[4px] border border-white/[0.06] px-3 py-2 text-sm text-[#888888] transition-snap hover:text-[#F5F5F5]">Deactivate</button>
          <button className="rounded-[4px] bg-[#EF4444]/15 px-3 py-2 text-sm text-[#EF4444] transition-snap hover:bg-[#EF4444]/25">Delete</button>
        </div>
      </div>
    </div>
  );
}

function titleFor(page: Page) {
  const titles: Record<Page, string> = {
    landing: "Landing",
    auth: "Authentication",
    dashboard: "Dashboard",
    create: "Create Link",
    analytics: "Analytics",
    links: "Links",
    workspace: "Workspace",
  };
  return titles[page];
}

function StylePrimitive() {
  return (
    <style>{`
      .transition-snap {
        transition: opacity 120ms cubic-bezier(0.16, 1, 0.3, 1),
          transform 120ms cubic-bezier(0.16, 1, 0.3, 1),
          border-color 120ms cubic-bezier(0.16, 1, 0.3, 1),
          background-color 120ms cubic-bezier(0.16, 1, 0.3, 1),
          color 120ms cubic-bezier(0.16, 1, 0.3, 1);
      }
      .shadow-panel {
        box-shadow: ${panelShadow};
      }
      .button-accent {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border-radius: 4px;
        background: #E8FF47;
        color: #080808;
        font-size: 14px;
        font-weight: 500;
        transition: transform 120ms cubic-bezier(0.16, 1, 0.3, 1),
          background-color 120ms cubic-bezier(0.16, 1, 0.3, 1);
      }
      .button-accent:hover { transform: translateY(-1px); }
      .button-accent:active { transform: translateY(0); }
      .icon-button {
        display: inline-grid;
        height: 32px;
        width: 32px;
        place-items: center;
        border-radius: 4px;
        border: 1px solid rgba(255,255,255,0.06);
        color: #888888;
        transition: color 120ms cubic-bezier(0.16, 1, 0.3, 1),
          border-color 120ms cubic-bezier(0.16, 1, 0.3, 1),
          background-color 120ms cubic-bezier(0.16, 1, 0.3, 1);
      }
      .icon-button:hover {
        color: #F5F5F5;
        border-color: rgba(255,255,255,0.12);
        background: #1A1A1A;
      }
      .dot-grid {
        background-image: radial-gradient(rgba(255,255,255,0.08) 1px, transparent 1px);
        background-size: 24px 24px;
      }
      .page-fade {
        animation: pageFade 150ms cubic-bezier(0.16, 1, 0.3, 1);
      }
      @keyframes pageFade {
        from { opacity: 0; transform: translateY(4px); }
        to { opacity: 1; transform: translateY(0); }
      }
    `}</style>
  );
}

const tooltipStyle = {
  background: "#111111",
  border: "1px solid rgba(255,255,255,0.06)",
  borderRadius: "4px",
  color: "#F5F5F5",
};
