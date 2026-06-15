import { useEffect, useMemo, useState, type ReactNode } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { LucideIcon } from "lucide-react";
import {
  AlertCircle,
  BarChart2,
  Bell,
  Check,
  CheckCircle,
  Copy,
  Eye,
  EyeOff,
  LayoutDashboard,
  Link2,
  LogOut,
  Search,
  Settings,
  Trash2,
  Users,
  X,
  Zap,
} from "lucide-react";

type Page = "landing" | "login" | "register" | "dashboard" | "create" | "analytics" | "links" | "workspace";
type LinkItem = {
  id: number;
  shortCode: string;
  longUrl: string;
  isActive: boolean;
  clicks: number;
  createdAt: Date;
};
type User = { name: string; email: string };
type ToastState = { title: string; message: string; type: "success" | "error" } | null;

const reservedCodes = new Set(["test", "api", "admin"]);
const navItems: Array<{ page: Page; label: string; icon: LucideIcon }> = [
  { page: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { page: "links", label: "Links", icon: Link2 },
  { page: "analytics", label: "Analytics", icon: BarChart2 },
  { page: "workspace", label: "Workspace", icon: Users },
  { page: "dashboard", label: "Settings", icon: Settings },
];

export function DevlinkShowcase() {
  const [currentPage, setCurrentPage] = useState<Page>("landing");
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState<User>({ name: "Aaradhya", email: "aaradhya@example.com" });
  const [links, setLinks] = useState<LinkItem[]>([]);
  const [selectedLinkId, setSelectedLinkId] = useState<number | null>(null);
  const [copied, setCopied] = useState<string | null>(null);
  const [toast, setToast] = useState<ToastState>(null);

  function navigate(page: Page) {
    if (["dashboard", "create", "analytics", "links", "workspace"].includes(page) && !isAuthenticated) {
      setCurrentPage("login");
      return;
    }
    setCurrentPage(page);
  }

  function login(user: User) {
    setCurrentUser(user);
    setIsAuthenticated(true);
    setCurrentPage("dashboard");
  }

  function logout() {
    setIsAuthenticated(false);
    setCurrentPage("landing");
  }

  function createLink(input: { shortCode: string; longUrl: string }) {
    const link: LinkItem = {
      id: Date.now(),
      shortCode: input.shortCode || randomCode(),
      longUrl: input.longUrl,
      isActive: true,
      clicks: 0,
      createdAt: new Date(),
    };
    setLinks((items) => [link, ...items]);
    setSelectedLinkId(link.id);
    setToast({ title: "Link created", message: `lnk.ai/${link.shortCode}`, type: "success" });
    setCurrentPage("dashboard");
  }

  function deleteLink(id: number) {
    setLinks((items) => items.filter((item) => item.id !== id));
    if (selectedLinkId === id) setSelectedLinkId(null);
    setToast({ title: "Link removed", message: "The short link was deleted from this session.", type: "success" });
  }

  function copy(value: string) {
    void navigator.clipboard?.writeText(value);
    setCopied(value);
    window.setTimeout(() => setCopied(null), 2000);
  }

  const appPages: Page[] = ["dashboard", "create", "analytics", "links", "workspace"];
  const inApp = appPages.includes(currentPage);

  return (
    <div className="min-h-screen bg-[#080808] text-[#F0F0F0]">
      <DesignPrimitives />
      {toast && <Toast toast={toast} onClose={() => setToast(null)} />}
      {!inApp && (
        <div className="page-fade">
          {currentPage === "landing" && <LandingPage navigate={navigate} />}
          {(currentPage === "login" || currentPage === "register") && (
            <AuthPage mode={currentPage} navigate={navigate} onSubmit={login} />
          )}
        </div>
      )}
      {inApp && (
        <div className="min-h-screen lg:pl-[240px]">
          <Sidebar page={currentPage} user={currentUser} navigate={navigate} logout={logout} />
          <Topbar page={currentPage} user={currentUser} />
          <main className="page-fade px-4 py-8 sm:px-8 lg:px-10">
            <div className="mx-auto max-w-[1280px]">
              {currentPage === "dashboard" && (
                <DashboardPage
                  user={currentUser}
                  links={links}
                  navigate={navigate}
                  copied={copied}
                  copy={copy}
                  deleteLink={deleteLink}
                  openAnalytics={(id) => {
                    setSelectedLinkId(id);
                    navigate("analytics");
                  }}
                />
              )}
              {currentPage === "create" && <CreatePage links={links} createLink={createLink} copy={copy} copied={copied} />}
              {currentPage === "analytics" && (
                <AnalyticsPage
                  link={links.find((item) => item.id === selectedLinkId) ?? links[0]}
                  navigate={navigate}
                  copy={copy}
                  copied={copied}
                />
              )}
              {currentPage === "links" && (
                <LinksPage
                  links={links}
                  navigate={navigate}
                  copied={copied}
                  copy={copy}
                  deleteLink={deleteLink}
                  openAnalytics={(id) => {
                    setSelectedLinkId(id);
                    navigate("analytics");
                  }}
                />
              )}
              {currentPage === "workspace" && <WorkspacePage user={currentUser} />}
            </div>
          </main>
          <MobileNav page={currentPage} navigate={navigate} />
        </div>
      )}
    </div>
  );
}

function LandingPage({ navigate }: { navigate: (page: Page) => void }) {
  return (
    <div className="dot-grid relative min-h-screen overflow-hidden bg-[#080808]">
      <div className="pointer-events-none absolute right-[-200px] top-[-200px] h-[600px] w-[600px] bg-[radial-gradient(circle,rgba(232,255,71,0.06),transparent_70%)]" />
      <header className="fixed inset-x-0 top-0 z-30 h-14 border-b border-white/[0.06] bg-[#080808]/80 backdrop-blur">
        <nav className="mx-auto flex h-full max-w-[1280px] items-center justify-between px-6">
          <Wordmark />
          <div className="hidden items-center gap-8 text-[13px] text-[#888888] md:flex">
            {["Features", "Docs", "Pricing"].map((item) => (
              <button key={item} className="transition-ui hover:text-[#F0F0F0] focus-ring">{item}</button>
            ))}
          </div>
          <div className="flex items-center gap-4">
            <button className="text-[13px] text-[#888888] transition-ui hover:text-[#F0F0F0] focus-ring" onClick={() => navigate("login")}>
              Log in
            </button>
            <button className="accent-button px-4 py-2" onClick={() => navigate("register")}>
              Get started
            </button>
          </div>
        </nav>
      </header>
      <main className="relative mx-auto min-h-screen max-w-[1280px] px-6 pt-[30vh]">
        <section className="max-w-[560px]">
          <span className="rounded-[4px] border border-[#444444] px-2 py-1 text-[11px] font-medium uppercase tracking-widest text-[#888888]">
            Link Intelligence
          </span>
          <h1 className="mt-6 text-[40px] font-bold leading-[1.1] tracking-[-0.04em] text-[#F0F0F0] sm:text-[48px]">
            Short links that
            <span className="block font-light text-[#888888]">think for you.</span>
          </h1>
          <p className="mt-6 max-w-[420px] text-[15px] leading-[1.7] text-[#888888]">
            Redirect at sub-50ms. Track every click without storing a single raw IP. Built on the architecture that scales.
          </p>
          <div className="mt-10 flex flex-col gap-4 sm:flex-row sm:items-center">
            <button className="accent-button px-5 py-2.5" onClick={() => navigate("register")}>
              Create free account
            </button>
            <button className="text-[13px] text-[#888888] transition-ui hover:text-[#F0F0F0] focus-ring">
              See how it works →
            </button>
          </div>
          <div className="mt-8 flex items-center gap-3">
            <div className="flex -space-x-2">
              {["AM", "RS", "KP", "NV"].map((initials) => (
                <span key={initials} className="grid h-7 w-7 place-items-center rounded-[50%] border border-[#080808] bg-[#1C1C1C] text-[10px] text-[#888888]">
                  {initials}
                </span>
              ))}
            </div>
            <p className="text-xs text-[#444444]">Built by engineers, used by engineers</p>
          </div>
        </section>
        <TerminalWindow />
      </main>
      <section className="mx-auto grid max-w-[1280px] gap-8 px-6 py-20 md:grid-cols-4">
        <Feature icon={Zap} title="Sub-50ms Redirects" copy="Redis-cached hot path with graceful DB fallback." />
        <Feature icon={AlertCircle} title="Zero Raw IPs" copy="SHA-256 hashed with daily salt before any storage layer." />
        <Feature icon={Link2} title="Conditional Routing" copy="Geo, device, and time-based rules evaluated at redirect time." />
        <Feature icon={Bell} title="Dead Link Radar" copy="Async health monitoring with instant alerts." last />
      </section>
      <section className="border-y border-white/[0.06] px-6 py-8">
        <div className="mx-auto flex max-w-[1280px] flex-col gap-4 sm:flex-row sm:items-center sm:justify-center">
          <p className="text-[15px] text-[#888888]">Start with 0 setup. No credit card.</p>
          <button className="accent-button px-4 py-2" onClick={() => navigate("register")}>Create account</button>
        </div>
      </section>
    </div>
  );
}

function AuthPage({
  mode,
  navigate,
  onSubmit,
}: {
  mode: "login" | "register";
  navigate: (page: Page) => void;
  onSubmit: (user: User) => void;
}) {
  const [tab, setTab] = useState<"login" | "register">(mode);
  const [name, setName] = useState("Aaradhya Mehra");
  const [email, setEmail] = useState("aaradhya@example.com");
  const [password, setPassword] = useState("devlink-preview");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  function submit() {
    setLoading(true);
    window.setTimeout(() => onSubmit({ name: tab === "register" ? name : nameFromEmail(email), email }), 650);
  }

  return (
    <div className="dot-grid grid min-h-screen place-items-center bg-[#080808] px-6">
      <div className="w-full max-w-[400px] rounded-[8px] border border-white/[0.06] bg-[#111111] p-10 shadow-card">
        <button className="mb-8 focus-ring" onClick={() => navigate("landing")}><Wordmark /></button>
        <div className="grid grid-cols-2 border-b border-white/[0.06]">
          {(["login", "register"] as const).map((item) => (
            <button
              key={item}
              className={`pb-3 text-[11px] font-medium uppercase tracking-widest transition-ui focus-ring ${
                tab === item ? "border-b border-[#E8FF47] text-[#F0F0F0]" : "text-[#444444] hover:text-[#888888]"
              }`}
              onClick={() => setTab(item)}
            >
              {item}
            </button>
          ))}
        </div>
        <div key={tab} className="page-fade mt-8 space-y-4">
          {tab === "register" && <TextField label="Name" value={name} onChange={setName} />}
          <TextField label="Email" value={email} onChange={setEmail} />
          <TextField
            label="Password"
            value={showPassword ? password : "••••••••••••••"}
            onChange={showPassword ? setPassword : undefined}
            right={
              <button className="text-[#444444] transition-ui hover:text-[#F0F0F0] focus-ring" onClick={() => setShowPassword(!showPassword)}>
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            }
          />
          <button className="accent-button w-full py-3" onClick={submit}>
            {loading ? <span className="h-4 w-4 animate-spin rounded-[50%] border-2 border-[#080808]/30 border-t-[#080808]" /> : "Continue"}
          </button>
          <p className="text-center text-xs text-[#888888]">
            {tab === "login" ? "Don't have an account?" : "Already have an account?"}{" "}
            <button className="text-[#F0F0F0] underline underline-offset-4 focus-ring" onClick={() => setTab(tab === "login" ? "register" : "login")}>
              {tab === "login" ? "Sign up" : "Log in"}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}

function DashboardPage({
  user,
  links,
  navigate,
  copied,
  copy,
  deleteLink,
  openAnalytics,
}: {
  user: User;
  links: LinkItem[];
  navigate: (page: Page) => void;
  copied: string | null;
  copy: (value: string) => void;
  deleteLink: (id: number) => void;
  openAnalytics: (id: number) => void;
}) {
  const totalClicks = links.reduce((sum, link) => sum + link.clicks, 0);
  return (
    <div>
      <PageHeading title="Dashboard" subtitle={`Good morning, ${firstName(user.name)}`} />
      <div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Total Links" value={links.length ? String(links.length) : "—"} icon={Link2} empty={!links.length} />
        <StatCard label="Active Links" value={links.length ? String(links.filter((link) => link.isActive).length) : "—"} icon={CheckCircle} empty={!links.length} />
        <StatCard label="Clicks" value={links.length ? String(totalClicks) : "—"} icon={BarChart2} empty={!links.length} />
        <StatCard label="Avg CTR" value="—" icon={Zap} empty />
      </div>
      <section className="mt-10">
        <div className="mb-4 flex items-center justify-between">
          <SectionLabel>Your Links</SectionLabel>
          <button className="secondary-button px-3.5 py-1.5" onClick={() => navigate("create")}>+ New link</button>
        </div>
        {links.length === 0 ? (
          <EmptyLinks navigate={navigate} />
        ) : (
          <LinksTable links={links} copied={copied} copy={copy} deleteLink={deleteLink} openAnalytics={openAnalytics} />
        )}
      </section>
    </div>
  );
}

function CreatePage({
  links,
  createLink,
  copy,
  copied,
}: {
  links: LinkItem[];
  createLink: (input: { shortCode: string; longUrl: string }) => void;
  copy: (value: string) => void;
  copied: string | null;
}) {
  const [url, setUrl] = useState("");
  const [alias, setAlias] = useState("");
  const [expires, setExpires] = useState(false);
  const [password, setPassword] = useState(false);
  const [routing, setRouting] = useState(false);
  const [loading, setLoading] = useState(false);
  const validUrl = url.length === 0 ? null : /^https?:\/\/[^\s]+\.[^\s]+/.test(url);
  const aliasTaken = reservedCodes.has(alias) || links.some((link) => link.shortCode === alias);
  const aliasAvailable = alias.length > 2 && !aliasTaken;
  const shortPreview = `lnk.ai/${alias || "—"}`;

  function submit() {
    if (!validUrl || aliasTaken) return;
    setLoading(true);
    window.setTimeout(() => {
      createLink({ longUrl: url, shortCode: alias || randomCode() });
      setLoading(false);
    }, 800);
  }

  return (
    <div className="grid gap-10 xl:grid-cols-[0.58fr_0.42fr]">
      <section>
        <PageHeading title="New Link" subtitle="Create a short link. Metrics appear only after real session activity." />
        <div className="mt-8 space-y-6">
          <TextField label="Destination URL" value={url} onChange={setUrl} placeholder="https://..." indicator={validUrl} />
          <AliasField value={alias} onChange={setAlias} taken={aliasTaken} available={aliasAvailable} />
          <SwitchBlock label="Expires" checked={expires} onChange={setExpires}>
            <TextField label="Expiration Date" value="2026-12-31" onChange={() => undefined} />
          </SwitchBlock>
          <SwitchBlock label="Password Protection" checked={password} onChange={setPassword}>
            <TextField label="Password" value="launch-room" onChange={() => undefined} />
          </SwitchBlock>
          <SwitchBlock label="Conditional Routing" checked={routing} onChange={setRouting}>
            <div className="grid gap-3 md:grid-cols-[1fr_0.7fr_1fr]">
              <SelectLike label="Condition" value="Geo equals" />
              <TextField label="Value" value="IN" onChange={() => undefined} />
              <TextField label="Destination" value="https://..." onChange={() => undefined} />
            </div>
            <button className="mt-3 text-[13px] text-[#888888] transition-ui hover:text-[#F0F0F0]">Add rule</button>
          </SwitchBlock>
          <button className="accent-button w-full py-3" disabled={!validUrl || aliasTaken || loading} onClick={submit}>
            {loading ? (
              <>
                <span className="mr-2 h-4 w-4 animate-spin rounded-[50%] border-2 border-[#080808]/30 border-t-[#080808]" />
                Creating...
              </>
            ) : (
              "Shorten link"
            )}
          </button>
        </div>
      </section>
      <aside className="sticky top-32 h-fit rounded-[6px] border border-white/[0.06] bg-[#111111] p-6 shadow-card">
        <SectionLabel muted>Preview</SectionLabel>
        <p className="mt-5 font-mono text-xl text-[#F0F0F0]">{shortPreview}</p>
        <button className="secondary-button mt-4 w-full justify-center py-3 disabled:text-[#444444]" disabled={!alias} onClick={() => copy(shortPreview)}>
          {copied === shortPreview ? <Check className="mr-2 h-4 w-4 text-[#E8FF47]" /> : <Copy className="mr-2 h-4 w-4" />}
          Copy link
        </button>
        <div className="my-5 h-px bg-white/[0.06]" />
        <SectionLabel muted>QR Code</SectionLabel>
        {url ? <QrPattern seed={alias || url} /> : <div className="mt-4 grid h-[120px] w-[120px] place-items-center border border-dashed border-white/[0.08] text-[#444444]">—</div>}
        {url && <button className="mt-3 text-[13px] text-[#888888] transition-ui hover:text-[#F0F0F0]">Download PNG</button>}
      </aside>
    </div>
  );
}

function AnalyticsPage({
  link,
  navigate,
  copy,
  copied,
}: {
  link?: LinkItem;
  navigate: (page: Page) => void;
  copy: (value: string) => void;
  copied: string | null;
}) {
  if (!link) {
    return (
      <EmptyPanel
        icon={BarChart2}
        title="No links to analyze"
        copy="Create a link first to see analytics here."
        action="Create link"
        onAction={() => navigate("create")}
      />
    );
  }
  const shortUrl = `lnk.ai/${link.shortCode}`;
  const data = useMemo(() => makeClickSeries(link.clicks), [link.clicks]);
  return (
    <div>
      <div className="flex flex-col gap-4 border-b border-white/[0.06] pb-6 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <p className="font-mono text-2xl text-[#F0F0F0]">{link.shortCode}</p>
          <p className="mt-2 truncate text-[13px] text-[#888888]">{link.longUrl}</p>
        </div>
        <div className="flex gap-2">
          <StatusBadge link={link} />
          <button className="secondary-button px-3 py-2" onClick={() => copy(shortUrl)}>
            {copied === shortUrl ? <Check className="mr-2 h-4 w-4 text-[#E8FF47]" /> : <Copy className="mr-2 h-4 w-4" />}
            Copy
          </button>
          <button className="text-[13px] text-[#888888] transition-ui hover:text-[#F0F0F0]">Open link ↗</button>
        </div>
      </div>
      <div className="mt-6 inline-flex rounded-[4px] border border-white/[0.06] p-1">
        {["7D", "30D", "90D"].map((range) => (
          <button key={range} className={`rounded-[2px] px-3 py-1.5 text-[13px] ${range === "30D" ? "bg-[#1C1C1C] text-[#F0F0F0]" : "text-[#444444]"}`}>
            {range}
          </button>
        ))}
      </div>
      <div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Total Clicks" value={String(link.clicks)} icon={BarChart2} empty={link.clicks === 0} />
        <StatCard label="Countries" value="—" icon={Search} empty />
        <StatCard label="Top Device" value="—" icon={Settings} empty />
        <StatCard label="Peak Day" value="—" icon={Bell} empty />
      </div>
      <p className="mt-4 text-xs text-[#444444]">Analytics populate as your link receives real traffic.</p>
      <section className="mt-10">
        <SectionLabel>Clicks over time</SectionLabel>
        {link.clicks === 0 ? (
          <div className="mt-4 grid h-[200px] place-items-center border-b border-white/[0.06] text-[13px] text-[#444444]">
            No clicks recorded yet.
          </div>
        ) : (
          <div className="mt-4 h-[260px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data}>
                <defs>
                  <linearGradient id="clickFill" x1="0" x2="0" y1="0" y2="1">
                    <stop offset="0%" stopColor="#E8FF47" stopOpacity={0.15} />
                    <stop offset="100%" stopColor="#E8FF47" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="rgba(255,255,255,0.04)" vertical={false} />
                <XAxis dataKey="day" stroke="#444444" tickLine={false} axisLine={false} fontSize={12} />
                <YAxis stroke="#444444" tickLine={false} axisLine={false} fontSize={12} />
                <Tooltip contentStyle={tooltipStyle} />
                <Area dataKey="clicks" type="monotone" stroke="#E8FF47" strokeWidth={2} fill="url(#clickFill)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </section>
      <div className="mt-10 grid gap-6 xl:grid-cols-2">
        <DashedEmpty label="Traffic data appears here" />
        <DashedEmpty label="Traffic data appears here" />
      </div>
    </div>
  );
}

function LinksPage({
  links,
  navigate,
  copied,
  copy,
  deleteLink,
  openAnalytics,
}: {
  links: LinkItem[];
  navigate: (page: Page) => void;
  copied: string | null;
  copy: (value: string) => void;
  deleteLink: (id: number) => void;
  openAnalytics: (id: number) => void;
}) {
  const [selected, setSelected] = useState<number[]>([]);
  return (
    <div>
      <div className="flex items-center justify-between">
        <PageHeading title="Links" subtitle="Every row is created in this session." />
        <button className="accent-button px-4 py-2.5" onClick={() => navigate("create")}>+ New link</button>
      </div>
      <div className="mt-6 flex flex-col gap-3 sm:flex-row">
        <div className="flex w-full max-w-[280px] items-center gap-2 rounded-[4px] border border-white/[0.06] bg-[#111111] px-3 py-3 focus-within:border-[#E8FF47] focus-within:shadow-[0_0_0_3px_rgba(232,255,71,0.08)]">
          <Search className="h-4 w-4 text-[#444444]" />
          <input className="min-w-0 bg-transparent text-[13px] text-[#F0F0F0] outline-none placeholder:text-[#444444]" placeholder="Search by URL or code..." />
        </div>
        <SelectLike label="" value="All status" />
      </div>
      <div className="mt-8">
        {links.length === 0 ? (
          <EmptyLinks navigate={navigate} />
        ) : (
          <LinksTable links={links} copied={copied} copy={copy} deleteLink={deleteLink} openAnalytics={openAnalytics} selectable selected={selected} setSelected={setSelected} />
        )}
      </div>
      {selected.length > 0 && <BulkBar count={selected.length} />}
    </div>
  );
}

function WorkspacePage({ user }: { user: User }) {
  return (
    <div>
      <PageHeading title="Personal Workspace" subtitle="Manage members and permissions" />
      <div className="mt-8 grid gap-10 xl:grid-cols-[0.6fr_0.4fr]">
        <section>
          <SectionLabel>Members</SectionLabel>
          <div className="mt-4 border-y border-white/[0.06]">
            <div className="flex items-center justify-between py-4">
              <div className="flex items-center gap-3">
                <Avatar user={user} />
                <div>
                  <p className="text-[13px] text-[#F0F0F0]">{user.name}</p>
                  <p className="text-[11px] text-[#888888]">{user.email}</p>
                </div>
              </div>
              <span className="rounded-[2px] bg-[#E8FF47]/[0.08] px-2 py-1 text-[11px] font-medium uppercase tracking-widest text-[#E8FF47]">Owner</span>
            </div>
          </div>
          <p className="mt-4 text-[13px] text-[#444444]">No other members.</p>
        </section>
        <section>
          <SectionLabel>Invite Member</SectionLabel>
          <div className="mt-4 rounded-[6px] border border-white/[0.06] bg-[#111111] p-6 shadow-card">
            <TextField label="Email" value="" onChange={() => undefined} placeholder="colleague@company.com" />
            <div className="mt-4"><SelectLike label="Role" value="Editor" full /></div>
            <button className="secondary-button mt-4 w-full justify-center py-3">Send invite</button>
          </div>
          <div className="mt-8">
            <SectionLabel>Pending Invites</SectionLabel>
            <p className="mt-4 text-[13px] text-[#444444]">No pending invites.</p>
          </div>
        </section>
      </div>
    </div>
  );
}

function Sidebar({ page, user, navigate, logout }: { page: Page; user: User; navigate: (page: Page) => void; logout: () => void }) {
  return (
    <aside className="fixed inset-y-0 left-0 z-40 hidden w-[240px] border-r border-white/[0.06] bg-[#080808] lg:block">
      <div className="flex h-full flex-col p-6">
        <div className="flex items-center gap-3">
          <Wordmark />
          <span className="rounded-[4px] border border-white/[0.06] px-1.5 py-0.5 text-[10px] text-[#444444]">v1.0</span>
        </div>
        <nav className="mt-8 space-y-1">
          {navItems.slice(0, 3).map((item) => <NavItem key={item.label} item={item} active={page === item.page} navigate={navigate} />)}
          <p className="px-4 pt-8 text-[10px] font-medium uppercase tracking-widest text-[#444444]">Account</p>
          {navItems.slice(3).map((item) => <NavItem key={item.label} item={item} active={page === item.page} navigate={navigate} />)}
        </nav>
        <div className="mt-auto flex items-center gap-3 border-t border-white/[0.06] pt-4">
          <Avatar user={user} />
          <div className="min-w-0 flex-1">
            <p className="truncate text-[13px] text-[#F0F0F0]">{user.name}</p>
            <p className="truncate text-[11px] text-[#888888]">{user.email}</p>
          </div>
          <button className="text-[#444444] transition-ui hover:text-[#EF4444] focus-ring" onClick={logout}>
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </aside>
  );
}

function NavItem({ item, active, navigate }: { item: { page: Page; label: string; icon: LucideIcon }; active: boolean; navigate: (page: Page) => void }) {
  return (
    <button
      className={`flex h-12 w-full items-center gap-3 border-l-2 px-4 text-[13px] transition-ui focus-ring ${
        active ? "border-[#E8FF47] bg-[#E8FF47]/[0.04] text-[#F0F0F0]" : "border-transparent text-[#888888] hover:text-[#F0F0F0]"
      }`}
      onClick={() => navigate(item.page)}
    >
      <item.icon className="h-4 w-4" />
      {item.label}
    </button>
  );
}

function Topbar({ page, user }: { page: Page; user: User }) {
  return (
    <header className="sticky top-0 z-30 h-14 border-b border-white/[0.06] bg-[#080808] px-4 sm:px-8 lg:px-10">
      <div className="mx-auto flex h-full max-w-[1280px] items-center justify-between">
        <p className="text-[15px] font-medium text-[#F0F0F0]">{titleFor(page)}</p>
        <div className="flex items-center gap-4">
          <button className="text-[#888888] transition-ui hover:text-[#F0F0F0] focus-ring"><Bell className="h-4 w-4" /></button>
          <Avatar user={user} />
        </div>
      </div>
    </header>
  );
}

function MobileNav({ page, navigate }: { page: Page; navigate: (page: Page) => void }) {
  return (
    <nav className="fixed inset-x-0 bottom-0 z-40 grid grid-cols-4 border-t border-white/[0.06] bg-[#080808] lg:hidden">
      {navItems.slice(0, 4).map((item) => (
        <button key={item.label} className={`py-3 text-[11px] ${page === item.page ? "text-[#E8FF47]" : "text-[#888888]"}`} onClick={() => navigate(item.page)}>
          <item.icon className="mx-auto mb-1 h-4 w-4" />
          {item.label}
        </button>
      ))}
    </nav>
  );
}

function LinksTable({
  links,
  copied,
  copy,
  deleteLink,
  openAnalytics,
  selectable,
  selected = [],
  setSelected,
}: {
  links: LinkItem[];
  copied: string | null;
  copy: (value: string) => void;
  deleteLink: (id: number) => void;
  openAnalytics: (id: number) => void;
  selectable?: boolean;
  selected?: number[];
  setSelected?: (ids: number[]) => void;
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[760px]">
        <thead>
          <tr className="text-left text-[13px] font-medium uppercase tracking-wide text-[#444444]">
            {selectable && <th className="w-10 py-3" />}
            <th className="py-3">Code</th>
            <th className="py-3">Destination</th>
            <th className="py-3">Status</th>
            <th className="py-3">Created</th>
            <th className="py-3 text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          {links.map((link) => {
            const shortUrl = `lnk.ai/${link.shortCode}`;
            return (
              <tr key={link.id} className="group h-12 border-b border-white/[0.04] transition-ui hover:bg-white/[0.02]">
                {selectable && (
                  <td>
                    <input
                      type="checkbox"
                      className="h-4 w-4 accent-[#E8FF47]"
                      checked={selected.includes(link.id)}
                      onChange={(event) => setSelected?.(event.target.checked ? [...selected, link.id] : selected.filter((id) => id !== link.id))}
                    />
                  </td>
                )}
                <td className="font-mono text-[13px] text-[#F0F0F0]">{link.shortCode}</td>
                <td className="max-w-[240px] truncate text-[13px] text-[#888888]">{link.longUrl}</td>
                <td><StatusBadge link={link} /></td>
                <td className="text-[13px] text-[#444444]">{relativeTime(link.createdAt)}</td>
                <td>
                  <div className="flex justify-end gap-2 opacity-0 transition-ui group-hover:opacity-100">
                    <IconButton onClick={() => copy(shortUrl)}>{copied === shortUrl ? <Check className="h-4 w-4 text-[#E8FF47]" /> : <Copy className="h-4 w-4" />}</IconButton>
                    <IconButton onClick={() => openAnalytics(link.id)}><BarChart2 className="h-4 w-4" /></IconButton>
                    <IconButton onClick={() => window.confirm("Delete this link?") && deleteLink(link.id)}><Trash2 className="h-4 w-4" /></IconButton>
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

function StatCard({ label, value, icon: Icon, empty }: { label: string; value: string; icon: LucideIcon; empty?: boolean }) {
  return (
    <div className="rounded-[6px] border border-white/[0.06] bg-[#111111] p-6 shadow-card">
      <div className="flex items-center justify-between">
        <SectionLabel>{label}</SectionLabel>
        <Icon className="h-4 w-4 text-[#444444]" />
      </div>
      <p className={`mt-5 font-mono text-[32px] font-bold tabular-nums text-[#F0F0F0] ${empty ? "text-[#444444]" : ""}`}>{value}</p>
      {empty && <p className="mt-2 text-xs text-[#444444]">No data yet</p>}
    </div>
  );
}

function EmptyLinks({ navigate }: { navigate: (page: Page) => void }) {
  return (
    <div className="grid place-items-center rounded-[6px] border border-dashed border-white/[0.08] px-6 py-16 text-center">
      <Link2 className="h-8 w-8 text-[#444444]" />
      <p className="mt-4 text-[15px] text-[#888888]">No links yet</p>
      <p className="mt-2 text-[13px] text-[#444444]">Create your first short link to see it here.</p>
      <button className="accent-button mt-6 px-4 py-2.5" onClick={() => navigate("create")}>Create link</button>
    </div>
  );
}

function EmptyPanel({ icon: Icon, title, copy, action, onAction }: { icon: LucideIcon; title: string; copy: string; action: string; onAction: () => void }) {
  return (
    <div className="grid min-h-[420px] place-items-center text-center">
      <div>
        <Icon className="mx-auto h-12 w-12 text-[#444444]" />
        <p className="mt-5 text-xl text-[#888888]">{title}</p>
        <p className="mt-2 text-[13px] text-[#444444]">{copy}</p>
        <button className="accent-button mt-6 px-4 py-2.5" onClick={onAction}>{action}</button>
      </div>
    </div>
  );
}

function TextField({ label, value, onChange, placeholder, right, indicator }: { label: string; value: string; onChange?: (value: string) => void; placeholder?: string; right?: ReactNode; indicator?: boolean | null }) {
  return (
    <label className="block">
      <span className="mb-2 block text-[11px] font-medium uppercase tracking-widest text-[#888888]">{label}</span>
      <div className="flex items-center rounded-[4px] border border-white/[0.06] bg-[#080808] px-3 transition-ui focus-within:border-[#E8FF47] focus-within:shadow-[0_0_0_3px_rgba(232,255,71,0.08)]">
        <input className="min-w-0 flex-1 bg-transparent py-3 text-[13px] text-[#F0F0F0] outline-none placeholder:text-[#444444]" value={value} placeholder={placeholder} onChange={(event) => onChange?.(event.target.value)} />
        {indicator !== undefined && indicator !== null && <span className={`h-2 w-2 rounded-[50%] ${indicator ? "bg-[#22C55E]" : "bg-[#EF4444]"}`} />}
        {indicator === null && value && <span className="h-2 w-2 rounded-[50%] bg-[#444444]" />}
        {right}
      </div>
    </label>
  );
}

function AliasField({ value, onChange, taken, available }: { value: string; onChange: (value: string) => void; taken: boolean; available: boolean }) {
  return (
    <label className="block">
      <span className="mb-2 block text-[11px] font-medium uppercase tracking-widest text-[#888888]">Short Code</span>
      <div className="flex rounded-[4px] border border-white/[0.06] bg-[#080808] transition-ui focus-within:border-[#E8FF47] focus-within:shadow-[0_0_0_3px_rgba(232,255,71,0.08)]">
        <span className="border-r border-white/[0.06] bg-[#1C1C1C] px-3 py-3 text-[13px] text-[#444444]">lnk.ai/</span>
        <input className="min-w-0 flex-1 bg-transparent px-3 py-3 text-[13px] text-[#F0F0F0] outline-none" value={value} onChange={(event) => onChange(event.target.value)} />
        {available && <span className="px-3 py-3 text-[11px] text-[#22C55E]">available</span>}
        {taken && value && <span className="px-3 py-3 text-[11px] text-[#EF4444]">taken</span>}
      </div>
    </label>
  );
}

function SwitchBlock({ label, checked, onChange, children }: { label: string; checked: boolean; onChange: (value: boolean) => void; children: ReactNode }) {
  return (
    <div>
      <div className="flex items-center justify-between">
        <SectionLabel>{label}</SectionLabel>
        <button className={`h-6 w-11 rounded-[4px] border p-1 transition-ui ${checked ? "border-[#E8FF47] bg-[#E8FF47]/20" : "border-white/[0.12] bg-[#1C1C1C]"}`} onClick={() => onChange(!checked)}>
          <span className={`block h-4 w-4 rounded-[3px] transition-ui ${checked ? "translate-x-5 bg-[#E8FF47]" : "bg-[#F0F0F0]"}`} />
        </button>
      </div>
      {checked && <div className="page-fade mt-4">{children}</div>}
    </div>
  );
}

function SelectLike({ label, value, full }: { label: string; value: string; full?: boolean }) {
  return (
    <label className={`block ${full ? "w-full" : "w-full sm:w-auto"}`}>
      {label && <span className="mb-2 block text-[11px] font-medium uppercase tracking-widest text-[#888888]">{label}</span>}
      <button className="w-full rounded-[4px] border border-white/[0.06] bg-[#111111] px-3 py-3 text-left text-[13px] text-[#F0F0F0] transition-ui hover:border-white/[0.12] focus-ring">
        {value}
      </button>
    </label>
  );
}

function StatusBadge({ link }: { link: LinkItem }) {
  const className = link.isActive ? "bg-[#22C55E]/[0.08] text-[#22C55E]" : "bg-white/[0.04] text-[#888888]";
  return <span className={`rounded-[2px] px-2 py-1 text-xs ${className}`}>{link.isActive ? "Active" : "Expired"}</span>;
}

function IconButton({ children, onClick }: { children: ReactNode; onClick: () => void }) {
  return <button className="text-[#444444] transition-ui hover:text-[#F0F0F0] focus-ring" onClick={onClick}>{children}</button>;
}

function Toast({ toast, onClose }: { toast: NonNullable<ToastState>; onClose: () => void }) {
  useEffect(() => {
    const id = window.setTimeout(onClose, 3000);
    return () => window.clearTimeout(id);
  }, [onClose]);
  const Icon = toast.type === "success" ? CheckCircle : AlertCircle;
  return (
    <div className="toast-enter fixed right-4 top-4 z-50 flex w-[320px] gap-3 rounded-[6px] border border-white/[0.12] bg-[#111111] p-4 shadow-modal">
      <Icon className={`mt-0.5 h-4 w-4 ${toast.type === "success" ? "text-[#22C55E]" : "text-[#EF4444]"}`} />
      <div className="min-w-0 flex-1">
        <p className="text-[13px] text-[#F0F0F0]">{toast.title}</p>
        <p className="mt-1 truncate text-xs text-[#888888]">{toast.message}</p>
      </div>
      <button className="text-[#444444] transition-ui hover:text-[#F0F0F0]" onClick={onClose}><X className="h-4 w-4" /></button>
    </div>
  );
}

function Feature({ icon: Icon, title, copy, last }: { icon: LucideIcon; title: string; copy: string; last?: boolean }) {
  return (
    <div className={`pr-6 ${last ? "" : "md:border-r md:border-white/[0.06]"}`}>
      <Icon className="h-5 w-5 text-[#888888]" />
      <h2 className="mt-4 text-[15px] text-[#F0F0F0]">{title}</h2>
      <p className="mt-2 text-[13px] leading-6 text-[#888888]">{copy}</p>
    </div>
  );
}

function TerminalWindow() {
  return (
    <div className="mt-16 w-full max-w-[380px] overflow-hidden rounded-[6px] border border-white/[0.06] bg-[#111111] shadow-card lg:absolute lg:right-20 lg:top-1/2 lg:mt-0 lg:-translate-y-1/2">
      <div className="relative flex h-9 items-center bg-[#1C1C1C] px-4">
        <div className="flex gap-1.5">
          <span className="h-1.5 w-1.5 rounded-[50%] bg-[#FF5F57]" />
          <span className="h-1.5 w-1.5 rounded-[50%] bg-[#FEBC2E]" />
          <span className="h-1.5 w-1.5 rounded-[50%] bg-[#28C840]" />
        </div>
        <span className="absolute left-1/2 -translate-x-1/2 text-[11px] text-[#444444]">bash</span>
      </div>
      <pre className="p-5 font-mono text-xs leading-[1.8] text-[#888888]">
        <span className="text-[#E8FF47]">$</span>{` curl -X POST lnk.ai/api/v1/links \\
  -H "Authorization: Bearer sk_..." \\
  -d '{
    "url": "github.com/aaradhya/...",
    "alias": "my-portfolio"
  }'

{
  "short_url": "lnk.ai/my-portfolio",
  "created_at": "just now",
  "analytics": "lnk.ai/analytics/..."
}`}
        <span className="ml-1 inline-block h-3.5 w-0.5 animate-pulse bg-[#E8FF47]" />
      </pre>
    </div>
  );
}

function QrPattern({ seed }: { seed: string }) {
  const cells = useMemo(() => Array.from({ length: 36 }, (_, index) => (index * 7 + seed.length * 3) % 5 !== 0), [seed]);
  return (
    <div className="mt-4 grid h-[120px] w-[120px] grid-cols-6 gap-1 bg-[#111111] p-2">
      {cells.map((filled, index) => <span key={index} className={filled ? "bg-[#F0F0F0]" : "bg-[#111111]"} />)}
    </div>
  );
}

function BulkBar({ count }: { count: number }) {
  return (
    <div className="fixed inset-x-0 bottom-0 z-40 border-t border-white/[0.06] bg-[#111111] px-6 py-3 shadow-modal lg:left-[240px]">
      <div className="mx-auto flex max-w-[1280px] items-center justify-between">
        <p className="text-[13px] text-[#F0F0F0]">{count} selected</p>
        <div className="flex gap-3">
          <button className="secondary-button px-3 py-2">Deactivate</button>
          <button className="rounded-[4px] px-3 py-2 text-[13px] text-[#EF4444] transition-ui hover:bg-[#EF4444]/[0.08]">Delete</button>
        </div>
      </div>
    </div>
  );
}

function Avatar({ user }: { user: User }) {
  return <span className="grid h-8 w-8 place-items-center rounded-[50%] bg-[#1C1C1C] text-xs text-[#F0F0F0]">{initials(user.name)}</span>;
}

function Wordmark() {
  return <span className="text-[15px] font-semibold text-[#F0F0F0]">lnk<span className="text-[#E8FF47]">.ai</span></span>;
}

function PageHeading({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div>
      <h1 className="text-2xl font-medium tracking-[-0.03em] text-[#F0F0F0]">{title}</h1>
      <p className="mt-2 text-[13px] text-[#888888]">{subtitle}</p>
    </div>
  );
}

function SectionLabel({ children, muted }: { children: ReactNode; muted?: boolean }) {
  return <p className={`text-[11px] font-medium uppercase tracking-widest ${muted ? "text-[#444444]" : "text-[#888888]"}`}>{children}</p>;
}

function DashedEmpty({ label }: { label: string }) {
  return <div className="grid h-40 place-items-center rounded-[6px] border border-dashed border-white/[0.08] text-[13px] text-[#444444]">{label}</div>;
}

function DesignPrimitives() {
  return (
    <style>{`
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
      * { font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
      .dot-grid {
        background-image: radial-gradient(rgba(255,255,255,0.07) 1px, transparent 1px);
        background-size: 24px 24px;
      }
      .transition-ui {
        transition: opacity 150ms cubic-bezier(0.16,1,0.3,1), transform 150ms cubic-bezier(0.16,1,0.3,1), border-color 150ms cubic-bezier(0.16,1,0.3,1), color 150ms cubic-bezier(0.16,1,0.3,1), background-color 150ms cubic-bezier(0.16,1,0.3,1);
      }
      .focus-ring:focus-visible {
        outline: none;
        box-shadow: 0 0 0 3px rgba(232,255,71,0.08);
        border-color: #E8FF47;
      }
      .accent-button {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border-radius: 4px;
        background: #E8FF47;
        color: #080808;
        font-size: 13px;
        font-weight: 600;
        transition: transform 150ms cubic-bezier(0.16,1,0.3,1), opacity 150ms cubic-bezier(0.16,1,0.3,1);
      }
      .accent-button:hover { transform: translateY(-1px); }
      .accent-button:active { transform: translateY(0); }
      .accent-button:disabled { opacity: 0.45; transform: none; }
      .secondary-button {
        display: inline-flex;
        align-items: center;
        border-radius: 4px;
        border: 1px solid rgba(255,255,255,0.12);
        color: #F0F0F0;
        font-size: 13px;
        transition: background-color 150ms cubic-bezier(0.16,1,0.3,1), border-color 150ms cubic-bezier(0.16,1,0.3,1);
      }
      .secondary-button:hover { background: #1C1C1C; }
      .shadow-card { box-shadow: 0 0 0 1px rgba(255,255,255,0.06), 0 2px 4px rgba(0,0,0,0.4); }
      .shadow-modal { box-shadow: 0 0 0 1px rgba(255,255,255,0.08), 0 8px 32px rgba(0,0,0,0.6); }
      .page-fade { animation: pageFade 150ms cubic-bezier(0.16,1,0.3,1); }
      .toast-enter { animation: toastIn 200ms cubic-bezier(0.16,1,0.3,1); }
      .skeleton {
        background: linear-gradient(90deg, #111111 25%, #1C1C1C 50%, #111111 75%);
        background-size: 200% 100%;
        animation: shimmer 1.5s linear infinite;
      }
      @keyframes shimmer { 0% { background-position: 200% 0 } 100% { background-position: -200% 0 } }
      @keyframes pageFade { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
      @keyframes toastIn { from { transform: translateX(calc(100% + 16px)); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
    `}</style>
  );
}

function randomCode() {
  return Math.random().toString(36).slice(2, 8);
}

function initials(name: string) {
  return name.split(" ").map((part) => part[0]).join("").slice(0, 2).toUpperCase();
}

function firstName(name: string) {
  return name.split(" ")[0] || "there";
}

function nameFromEmail(email: string) {
  return email.split("@")[0]?.replace(/[._-]/g, " ") || "User";
}

function relativeTime(date: Date) {
  const seconds = Math.max(0, Math.floor((Date.now() - date.getTime()) / 1000));
  if (seconds < 10) return "just now";
  if (seconds < 60) return `${seconds} seconds ago`;
  const minutes = Math.floor(seconds / 60);
  return `${minutes} minute${minutes === 1 ? "" : "s"} ago`;
}

function makeClickSeries(clicks: number) {
  if (clicks <= 0) return [];
  const days = ["D-6", "D-5", "D-4", "D-3", "D-2", "D-1", "Today"];
  let remaining = clicks;
  return days.map((day, index) => {
    const value = index === days.length - 1 ? remaining : Math.floor(clicks / days.length);
    remaining -= value;
    return { day, clicks: value };
  });
}

function titleFor(page: Page) {
  return page === "create" ? "New Link" : page[0].toUpperCase() + page.slice(1);
}

const tooltipStyle = {
  background: "#111111",
  border: "1px solid rgba(255,255,255,0.06)",
  borderRadius: "4px",
  color: "#F0F0F0",
};
