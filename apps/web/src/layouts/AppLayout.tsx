import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { Bot, Home, LogOut, Sparkles, Users } from "lucide-react";
import { clearAuth, useAuth } from "../features/auth/useAuth";
import { friendlyRole } from "../lib/labels";
import { useToast } from "../components/toast/ToastProvider";

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `flex items-center gap-2 rounded-lg px-3 py-2.5 text-sm font-medium ${
    isActive ? "bg-sky-500/20 text-white" : "text-slate-300 hover:bg-white/10 hover:text-white"
  }`;

export function AppLayout() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const toast = useToast();

  return (
    <div className="min-h-screen flex bg-slate-100">
      <aside className="w-64 bg-navy-900 text-white flex flex-col">
        <div className="px-5 py-6 border-b border-white/10">
          <div className="flex items-center gap-2 font-display text-lg font-bold">
            <Bot className="text-sky-400" size={22} />
            Banking CRM
          </div>
          <p className="mt-1 text-xs text-slate-400">AI helper for Relationship Managers</p>
        </div>
        <nav className="p-3 space-y-1 flex-1">
          <p className="px-3 py-2 text-[11px] uppercase tracking-wide text-slate-500">Main menu</p>
          <NavLink to="/" end className={linkClass}>
            <Home size={16} /> Home
          </NavLink>
          <NavLink to="/customers" className={linkClass}>
            <Users size={16} /> Customer list
          </NavLink>
          <NavLink to="/campaigns/new" className={linkClass}>
            <Sparkles size={16} /> Start AI campaign
          </NavLink>
        </nav>
        <div className="p-4 border-t border-white/10 text-xs text-slate-400 leading-relaxed">
          Demo only · All customers are synthetic
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between">
          <div>
            <p className="text-sm text-slate-500">Signed in as</p>
            <p className="font-semibold text-slate-800">
              {user?.full_name}
              <span className="ml-2 text-xs font-medium text-slate-500">
                {friendlyRole(user?.role)}
              </span>
            </p>
          </div>
          <button
            className="btn-ghost btn-sm"
            onClick={() => {
              clearAuth();
              toast.info("You have been signed out.", "Signed out");
              navigate("/login");
            }}
          >
            <LogOut size={16} /> Sign out
          </button>
        </header>
        <main className="p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
