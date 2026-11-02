import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { ArrowRight, ChevronLeft, ChevronRight, Search } from "lucide-react";
import { api } from "../api/client";
import { EmptyState, PageLoader } from "../components/PageLoader";
import { RmJourneyWizard } from "../components/RmJourneyWizard";
import { friendlyStatus } from "../lib/labels";
import { useEmptyDataToast, useQueryErrorToast } from "../hooks/useQueryToasts";

type CustomerRow = {
  customerId: string;
  customerCode: string;
  fullName: string;
  age: number;
  city: string;
  occupation: string;
  segment: string;
  monthlyIncome: number;
  riskCategory: string;
  scenarioTag?: string | null;
  hasSalaryAccount: boolean;
  maskedAccountNumber?: string | null;
};

function buildPageItems(current: number, total: number): Array<number | "ellipsis"> {
  if (total <= 9) {
    return Array.from({ length: total }, (_, i) => i + 1);
  }

  const pages = new Set<number>();
  pages.add(1);
  pages.add(total);
  for (let p = current - 2; p <= current + 2; p += 1) {
    if (p >= 1 && p <= total) pages.add(p);
  }

  const sorted = Array.from(pages).sort((a, b) => a - b);
  const items: Array<number | "ellipsis"> = [];
  for (let i = 0; i < sorted.length; i += 1) {
    const pageNum = sorted[i];
    if (i > 0 && pageNum - sorted[i - 1] > 1) {
      items.push("ellipsis");
    }
    items.push(pageNum);
  }
  return items;
}

export function CustomersPage() {
  const [search, setSearch] = useState("");
  const [segment, setSegment] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);

  const query = useMemo(() => {
    const params = new URLSearchParams();
    params.set("page", String(page));
    params.set("page_size", String(pageSize));
    if (search) params.set("search", search);
    if (segment) params.set("segment", segment);
    return `/customers?${params.toString()}`;
  }, [search, segment, page, pageSize]);

  const { data, isLoading, error, isSuccess } = useQuery({
    queryKey: ["customers", query],
    queryFn: () =>
      api<{
        total: number;
        page: number;
        totalPages: number;
        items: CustomerRow[];
        disclaimer: string;
      }>(query),
  });

  useQueryErrorToast(error, "Could not load customers");
  useEmptyDataToast(
    isSuccess && !search && !segment,
    Boolean(data && data.total === 0),
    "No customers found in the database. Please seed data before browsing or running campaigns.",
    "customers-db-empty",
  );
  useEmptyDataToast(
    isSuccess && Boolean(search || segment),
    Boolean(data && data.total === 0),
    "No customers match your search filters.",
    `customers-filter-empty-${search}-${segment}`,
  );

  return (
    <div className="space-y-4">
      <RmJourneyWizard current="dashboard" />
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl font-bold">Customer list</h1>
          <p className="text-sm text-amber-700">
            {data?.disclaimer || "POC Environment - Synthetic Data"} ·{" "}
            {data ? `${data.total.toLocaleString("en-IN")} customers` : "Loading..."}
          </p>
          <p className="text-sm text-slate-500 mt-1">
            Browse profiles anytime. To score and message someone, start an AI campaign.
          </p>
        </div>
        <Link to="/campaigns/new" className="btn-primary">
          Start AI campaign <ArrowRight size={16} />
        </Link>
      </div>

      <div className="card p-4 grid md:grid-cols-3 gap-3">
        <label className="text-sm md:col-span-1">
          <span className="font-medium text-slate-600">Search</span>
          <div className="relative">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              className="field pl-8"
              placeholder="Name or customer code"
              value={search}
              onChange={(e) => {
                setPage(1);
                setSearch(e.target.value);
              }}
            />
          </div>
        </label>
        <label className="text-sm">
          <span className="font-medium text-slate-600">Segment</span>
          <select
            className="field"
            value={segment}
            onChange={(e) => {
              setPage(1);
              setSegment(e.target.value);
            }}
          >
            <option value="">All segments</option>
            <option value="STANDARD">Standard</option>
            <option value="GOLD">Gold</option>
            <option value="PREMIUM">Premium</option>
            <option value="PRIVATE">Private</option>
          </select>
        </label>
        <label className="text-sm">
          <span className="font-medium text-slate-600">Rows per page</span>
          <select
            className="field"
            value={pageSize}
            onChange={(e) => {
              setPage(1);
              setPageSize(Number(e.target.value));
            }}
          >
            <option value={10}>10</option>
            <option value={25}>25</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
        </label>
      </div>

      {isLoading ? (
        <PageLoader label="Loading customers..." />
      ) : error ? (
        <p className="text-red-600">{(error as Error).message}</p>
      ) : data && data.total === 0 ? (
        <EmptyState
          title="No data found"
          message={
            search || segment
              ? "No customers match your filters."
              : "No customers found in the database."
          }
        />
      ) : (
      <div className="card overflow-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 text-left text-slate-600">
            <tr>
              <th className="px-3 py-3">Code</th>
              <th className="px-3 py-3">Customer</th>
              <th className="px-3 py-3">Account number</th>
              <th className="px-3 py-3">City</th>
              <th className="px-3 py-3">Segment</th>
              <th className="px-3 py-3">Monthly income</th>
              <th className="px-3 py-3">Risk</th>
              <th className="px-3 py-3">Action</th>
            </tr>
          </thead>
          <tbody>
            {(data?.items || []).map((c) => (
              <tr key={c.customerId} className="border-t border-slate-100">
                <td className="px-3 py-3 font-mono text-xs">{c.customerCode}</td>
                <td className="px-3 py-3 font-medium">
                  {c.fullName}
                  {c.scenarioTag ? (
                    <span className="ml-2 badge bg-violet-50 text-violet-700">
                      Demo case {c.scenarioTag}
                    </span>
                  ) : null}
                </td>
                <td className="px-3 py-3 font-mono text-xs">
                  {c.maskedAccountNumber || "—"}
                </td>
                <td className="px-3 py-3">{c.city}</td>
                <td className="px-3 py-3">{friendlyStatus(c.segment)}</td>
                <td className="px-3 py-3">₹{Number(c.monthlyIncome).toLocaleString("en-IN")}</td>
                <td className="px-3 py-3">{friendlyStatus(c.riskCategory)}</td>
                <td className="px-3 py-3">
                  <Link className="btn-secondary btn-sm" to={`/customers/${c.customerId}`}>
                    View profile
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      )}

      {!isLoading && data && data.total > 0 ? (
        <PaginationBar
          page={data.page || page}
          totalPages={data.totalPages || 1}
          total={data.total || 0}
          pageSize={pageSize}
          onChange={setPage}
        />
      ) : null}
    </div>
  );
}

function PaginationBar({
  page,
  totalPages,
  total,
  pageSize,
  onChange,
}: {
  page: number;
  totalPages: number;
  total: number;
  pageSize: number;
  onChange: (page: number) => void;
}) {
  const items = buildPageItems(page, totalPages);
  const from = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const to = Math.min(page * pageSize, total);

  return (
    <div className="card px-4 py-3 flex flex-wrap items-center justify-between gap-3">
      <p className="text-sm text-slate-600">
        Showing{" "}
        <span className="font-semibold text-slate-800">
          {from.toLocaleString("en-IN")}–{to.toLocaleString("en-IN")}
        </span>{" "}
        of <span className="font-semibold text-slate-800">{total.toLocaleString("en-IN")}</span>
      </p>

      <div className="flex flex-wrap items-center gap-1">
        <button
          type="button"
          className="btn-secondary btn-sm"
          disabled={page <= 1}
          onClick={() => onChange(1)}
          aria-label="First page"
        >
          First
        </button>
        <button
          type="button"
          className="btn-secondary btn-sm"
          disabled={page <= 1}
          onClick={() => onChange(Math.max(1, page - 1))}
          aria-label="Previous page"
        >
          <ChevronLeft size={14} /> Prev
        </button>

        {items.map((item, idx) =>
          item === "ellipsis" ? (
            <span key={`e-${idx}`} className="px-2 text-slate-400 select-none">
              …
            </span>
          ) : (
            <button
              key={item}
              type="button"
              className={`min-w-9 rounded-lg px-2.5 py-1.5 text-sm font-semibold transition ${
                item === page
                  ? "bg-sky-600 text-white"
                  : "border border-slate-300 bg-white text-slate-700 hover:bg-slate-50"
              }`}
              onClick={() => onChange(item)}
              aria-current={item === page ? "page" : undefined}
            >
              {item}
            </button>
          ),
        )}

        <button
          type="button"
          className="btn-secondary btn-sm"
          disabled={page >= totalPages}
          onClick={() => onChange(Math.min(totalPages, page + 1))}
          aria-label="Next page"
        >
          Next <ChevronRight size={14} />
        </button>
        <button
          type="button"
          className="btn-secondary btn-sm"
          disabled={page >= totalPages}
          onClick={() => onChange(totalPages)}
          aria-label="Last page"
        >
          Last
        </button>
      </div>
    </div>
  );
}
