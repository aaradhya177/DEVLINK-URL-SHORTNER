import { BarChart3, Layers, Link2, LogOut } from "lucide-react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { logout } from "../api/auth";
import { useAuth } from "../features/auth/useAuth";
import { Button } from "../components/Button";

export function AppLayout() {
  const auth = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    const refreshToken = auth.refreshToken;
    auth.clearTokens();
    navigate("/login");
    if (refreshToken) {
      await logout(refreshToken).catch(() => undefined);
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <Link2 size={22} />
          <strong>DEVLINK</strong>
        </div>
        <nav className="nav">
          <NavLink to="/links">
            <Layers size={18} /> Links
          </NavLink>
          <NavLink to="/bulk">
            <Link2 size={18} /> Bulk
          </NavLink>
          <NavLink to="/links">
            <BarChart3 size={18} /> Analytics
          </NavLink>
        </nav>
        <Button variant="ghost" onClick={handleLogout}>
          <LogOut size={16} /> Sign out
        </Button>
      </aside>
      <main className="main-panel">
        <Outlet />
      </main>
    </div>
  );
}
