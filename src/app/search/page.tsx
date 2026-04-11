"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { AmbientBackground } from "@/components/ui/ambient-background";
import { GlassCardStyles } from "@/components/ui/glass-card";
import {
  useSearch,
  type SearchRecordType,
} from "@/components/search/search-provider";
import { SearchResultCard } from "@/components/search/search-result-card";

const TYPE_OPTIONS: { value: SearchRecordType; label: string }[] = [
  { value: "issue_story", label: "Weekly Issues" },
  { value: "bulletin", label: "Bulletins" },
  { value: "consulting", label: "Consulting Intelligence" },
  { value: "learn", label: "Learn" },
];

const DATE_PRESETS: { value: string; label: string; days: number | null }[] = [
  { value: "all", label: "All time", days: null },
  { value: "week", label: "Last week", days: 7 },
  { value: "month", label: "Last month", days: 30 },
  { value: "quarter", label: "Last 3 months", days: 90 },
];

const SORT_OPTIONS = [
  { value: "relevance", label: "Relevance" },
  { value: "newest", label: "Newest" },
  { value: "oldest", label: "Oldest" },
] as const;

function isoDaysAgo(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toISOString().slice(0, 10);
}

function SearchPageInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { search, isReady, ensureLoaded, records } = useSearch();

  const initialQuery = searchParams.get("q") || "";
  const [query, setQuery] = useState(initialQuery);
  const [types, setTypes] = useState<SearchRecordType[]>(() => {
    const t = searchParams.getAll("type") as SearchRecordType[];
    return t.length > 0 ? t : [];
  });
  const [datePreset, setDatePreset] = useState<string>(
    searchParams.get("date") || "all",
  );
  const [firm, setFirm] = useState<string>(searchParams.get("firm") || "");
  const [sort, setSort] = useState<"relevance" | "newest" | "oldest">(
    (searchParams.get("sort") as "relevance" | "newest" | "oldest") ||
      "relevance",
  );

  useEffect(() => {
    ensureLoaded();
  }, [ensureLoaded]);

  // Keep URL in sync with filter state
  useEffect(() => {
    const params = new URLSearchParams();
    if (query) params.set("q", query);
    for (const t of types) params.append("type", t);
    if (datePreset && datePreset !== "all") params.set("date", datePreset);
    if (firm) params.set("firm", firm);
    if (sort !== "relevance") params.set("sort", sort);
    const qs = params.toString();
    router.replace(`/search${qs ? `?${qs}` : ""}`, { scroll: false });
  }, [query, types, datePreset, firm, sort, router]);

  const firms = useMemo(() => {
    const set = new Set<string>();
    for (const r of records) if (r.firm) set.add(r.firm);
    return Array.from(set).sort();
  }, [records]);

  const dateFrom = useMemo(() => {
    const preset = DATE_PRESETS.find((p) => p.value === datePreset);
    return preset?.days ? isoDaysAgo(preset.days) : undefined;
  }, [datePreset]);

  const results = useMemo(() => {
    if (!isReady) return [];
    return search(query, {
      types: types.length > 0 ? types : undefined,
      firms: firm ? [firm] : undefined,
      dateFrom,
      sort,
    });
  }, [query, types, firm, dateFrom, sort, isReady, search]);

  function toggleType(t: SearchRecordType) {
    setTypes((prev) =>
      prev.includes(t) ? prev.filter((x) => x !== t) : [...prev, t],
    );
  }

  return (
    <>
      <AmbientBackground />
      <GlassCardStyles />

      <div className="px-10 max-sm:px-4">
        <div className="pt-16 pb-6 max-w-[1100px] mx-auto">
          <h1
            className="font-extrabold mb-2"
            style={{
              color: "#0F1D35",
              letterSpacing: "-1px",
              fontSize: "38px",
            }}
          >
            Search
          </h1>
          <p
            style={{
              color: "#6b7280",
              fontSize: "15px",
              marginBottom: 24,
            }}
          >
            Across weekly issues, bulletins, consulting intelligence, and learn
            topics.
          </p>

          <div
            className="flex items-center gap-3 mb-6"
            style={{
              background: "rgba(255, 255, 255, 0.82)",
              backdropFilter: "blur(20px) saturate(1.8)",
              WebkitBackdropFilter: "blur(20px) saturate(1.8)",
              border: "1px solid rgba(255, 255, 255, 0.7)",
              borderRadius: "14px",
              padding: "14px 18px",
              boxShadow:
                "0 8px 24px rgba(15, 29, 53, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.85)",
            }}
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#6b7280"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <circle cx="11" cy="11" r="7" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search..."
              autoFocus
              className="flex-1 bg-transparent outline-none"
              style={{ fontSize: "16px", color: "#0F1D35" }}
            />
          </div>

          <div className="grid gap-6" style={{ gridTemplateColumns: "240px 1fr" }}>
            {/* Filter sidebar */}
            <aside className="max-md:hidden">
              <div
                style={{
                  background: "rgba(255, 255, 255, 0.72)",
                  backdropFilter: "blur(20px) saturate(1.6)",
                  WebkitBackdropFilter: "blur(20px) saturate(1.6)",
                  border: "1px solid rgba(255, 255, 255, 0.7)",
                  borderRadius: "14px",
                  padding: "18px 20px",
                }}
              >
                <div
                  style={{
                    fontSize: "11px",
                    fontWeight: 800,
                    textTransform: "uppercase",
                    letterSpacing: "0.8px",
                    color: "#94a3b8",
                    marginBottom: 10,
                  }}
                >
                  Content Type
                </div>
                <div className="flex flex-col gap-2 mb-5">
                  {TYPE_OPTIONS.map((opt) => (
                    <label
                      key={opt.value}
                      className="flex items-center gap-2 cursor-pointer"
                      style={{ fontSize: "13px", color: "#0F1D35" }}
                    >
                      <input
                        type="checkbox"
                        checked={types.includes(opt.value)}
                        onChange={() => toggleType(opt.value)}
                      />
                      {opt.label}
                    </label>
                  ))}
                </div>

                <div
                  style={{
                    fontSize: "11px",
                    fontWeight: 800,
                    textTransform: "uppercase",
                    letterSpacing: "0.8px",
                    color: "#94a3b8",
                    marginBottom: 10,
                  }}
                >
                  Date Range
                </div>
                <div className="flex flex-col gap-2 mb-5">
                  {DATE_PRESETS.map((opt) => (
                    <label
                      key={opt.value}
                      className="flex items-center gap-2 cursor-pointer"
                      style={{ fontSize: "13px", color: "#0F1D35" }}
                    >
                      <input
                        type="radio"
                        name="date-preset"
                        checked={datePreset === opt.value}
                        onChange={() => setDatePreset(opt.value)}
                      />
                      {opt.label}
                    </label>
                  ))}
                </div>

                {firms.length > 0 && (
                  <>
                    <div
                      style={{
                        fontSize: "11px",
                        fontWeight: 800,
                        textTransform: "uppercase",
                        letterSpacing: "0.8px",
                        color: "#94a3b8",
                        marginBottom: 10,
                      }}
                    >
                      Consulting Firm
                    </div>
                    <select
                      value={firm}
                      onChange={(e) => setFirm(e.target.value)}
                      className="w-full mb-5"
                      style={{
                        fontSize: "13px",
                        padding: "6px 8px",
                        borderRadius: "6px",
                        border: "1px solid rgba(15, 29, 53, 0.12)",
                        background: "rgba(255,255,255,0.7)",
                      }}
                    >
                      <option value="">All firms</option>
                      {firms.map((f) => (
                        <option key={f} value={f}>
                          {f}
                        </option>
                      ))}
                    </select>
                  </>
                )}

                <div
                  style={{
                    fontSize: "11px",
                    fontWeight: 800,
                    textTransform: "uppercase",
                    letterSpacing: "0.8px",
                    color: "#94a3b8",
                    marginBottom: 10,
                  }}
                >
                  Sort By
                </div>
                <select
                  value={sort}
                  onChange={(e) =>
                    setSort(e.target.value as typeof sort)
                  }
                  className="w-full"
                  style={{
                    fontSize: "13px",
                    padding: "6px 8px",
                    borderRadius: "6px",
                    border: "1px solid rgba(15, 29, 53, 0.12)",
                    background: "rgba(255,255,255,0.7)",
                  }}
                >
                  {SORT_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
            </aside>

            {/* Results column */}
            <div>
              <div
                style={{
                  fontSize: "13px",
                  color: "#6b7280",
                  marginBottom: 14,
                }}
              >
                {!isReady
                  ? "Loading..."
                  : `${results.length} result${results.length === 1 ? "" : "s"}`}
                {query ? ` for "${query}"` : ""}
              </div>

              {isReady && results.length === 0 && query && (
                <div
                  style={{
                    background: "rgba(255, 255, 255, 0.72)",
                    border: "1px solid rgba(255, 255, 255, 0.7)",
                    borderRadius: "14px",
                    padding: "28px 24px",
                    color: "#6b7280",
                    fontSize: "14px",
                  }}
                >
                  No matches for &ldquo;{query}&rdquo;. Try different keywords,
                  clear filters, or check spelling.
                </div>
              )}

              <div className="flex flex-col gap-4">
                {results.map((r) => (
                  <SearchResultCard key={r.id} result={r} />
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<div style={{ padding: 40 }}>Loading...</div>}>
      <SearchPageInner />
    </Suspense>
  );
}
