import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Bot } from "lucide-react";
import { api, setAuthToken } from "../api/client";
import { InlineLoader } from "../components/PageLoader";
import { persistAuth } from "../features/auth/useAuth";
import { useToast } from "../components/toast/ToastProvider";

const demos = [
  { email: "rm@demo.bank", label: "Login as RM", hint: "Day-to-day outreach" },
  { email: "supervisor@demo.bank", label: "Login as Supervisor", hint: "Oversight view" },
  { email: "admin@demo.bank", label: "Login as Admin", hint: "Full access" },
];

export function LoginPage() {
  const navigate = useNavigate();
  const toast = useToast();
  const [email, setEmail] = useState("rm@demo.bank");
  const [password, setPassword] = useState("Demo@123");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const data = await api<{
        access_token: string;
        user: { id: string; email: string; full_name: string; role: string };
      }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      setAuthToken(data.access_token);
      persistAuth(data.access_token, data.user);
      toast.success(`Signed in as ${data.user.full_name}`, "Welcome");
      navigate("/");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Login failed";
      setError(message);
      toast.error(message, "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen grid lg:grid-cols-2">
      <div className="relative hidden lg:flex flex-col justify-between p-10 text-white bg-gradient-to-br from-navy-900 via-navy-800 to-sky-700">
        <div className="absolute inset-0 opacity-30 bg-[radial-gradient(circle_at_20%_20%,#38bdf8,transparent_35%),radial-gradient(circle_at_80%_60%,#0284c7,transparent_40%)]" />
        <div className="relative">
          <div className="inline-flex items-center gap-2 text-sky-200 text-sm font-semibold">
            <Bot size={18} /> Banking CRM
          </div>
          <h1 className="mt-6 font-display text-4xl font-bold leading-tight max-w-md">
            Find the right customers. Draft the right message.
          </h1>
          <p className="mt-4 text-slate-200 max-w-md">
            Built for Relationship Managers: ask in plain English, let AI score customers, then
            approve before any mock WhatsApp send.
          </p>
          <ol className="mt-8 space-y-2 text-sm text-sky-50/90 max-w-md">
            <li>1. Start an AI campaign</li>
            <li>2. Review scored customers</li>
            <li>3. Approve and send a mock message</li>
          </ol>
        </div>
        <p className="relative text-sm text-sky-100/80">
          Demonstration environment. Synthetic customer data only.
        </p>
      </div>

      <div className="flex items-center justify-center p-8">
        <form onSubmit={onSubmit} className="w-full max-w-md card p-8 space-y-5">
          <div>
            <h2 className="font-display text-2xl font-bold text-slate-900">Welcome back</h2>
            <p className="text-sm text-slate-500 mt-1">
              Use a demo account below, or enter email and password.
            </p>
          </div>

          <label className="block text-sm">
            <span className="text-slate-600 font-medium">Work email</span>
            <input
              className="field"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="username"
            />
          </label>
          <label className="block text-sm">
            <span className="text-slate-600 font-medium">Password</span>
            <input
              type="password"
              className="field"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />
          </label>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <button disabled={loading} className="btn-primary w-full">
            {loading ? <InlineLoader label="Signing you in..." /> : "Continue to Home"}
          </button>

          <div className="space-y-2">
            <p className="text-xs text-slate-500">Quick demo logins · password is Demo@123</p>
            <div className="grid gap-2">
              {demos.map((d) => (
                <button
                  type="button"
                  key={d.email}
                  className="btn-secondary w-full justify-between"
                  onClick={() => {
                    setEmail(d.email);
                    setPassword("Demo@123");
                  }}
                >
                  <span>{d.label}</span>
                  <span className="text-xs font-normal text-slate-500">{d.hint}</span>
                </button>
              ))}
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
