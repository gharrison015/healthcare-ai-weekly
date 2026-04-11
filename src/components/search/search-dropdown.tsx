"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useSearch, type RankedResult, type SearchRecordType } from "./search-provider";

const TYPE_LABELS: Record<SearchRecordType, string> = {
  issue_story: "Weekly Issues",
  bulletin: "Bulletins",
  consulting: "Consulting Intelligence",
  learn: "Learn",
};

const TYPE_BADGES: Record<SearchRecordType, { bg: string; text: string }> = {
  issue_story: { bg: "#E0F2FE", text: "#0284C7" },
  bulletin: { bg: "#FEE2E2", text: "#DC2626" },
  consulting: { bg: "#EDE9FE", text: "#6344F5" },
  learn: { bg: "#DCFCE7", text: "#16A34A" },
};

const TYPE_ORDER: SearchRecordType[] = [
  "issue_story",
  "bulletin",
  "consulting",
  "learn",
];

function highlightMatch(text: string, query: string): React.ReactNode {
  if (!query || query.length < 2) return text;
  const terms = query
    .trim()
    .split(/\s+/)
    .map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"))
    .filter(Boolean);
  if (terms.length === 0) return text;
  const re = new RegExp(`(${terms.join("|")})`, "ig");
  const parts = text.split(re);
  return parts.map((part, i) =>
    re.test(part) ? (
      <mark
        key={i}
        style={{ background: "rgba(2, 132, 199, 0.18)", color: "inherit", padding: 0 }}
      >
        {part}
      </mark>
    ) : (
      <span key={i}>{part}</span>
    ),
  );
}

export function SearchDropdown() {
  const { isOpen, closeSearch, search, isReady } = useSearch();
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [activeIdx, setActiveIdx] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  useEffect(() => {
    if (isOpen) {
      setQuery("");
      setDebouncedQuery("");
      setActiveIdx(0);
      requestAnimationFrame(() => inputRef.current?.focus());
    }
  }, [isOpen]);

  useEffect(() => {
    const t = setTimeout(() => setDebouncedQuery(query), 120);
    return () => clearTimeout(t);
  }, [query]);

  const results: RankedResult[] = useMemo(() => {
    if (!isReady) return [];
    return search(debouncedQuery).slice(0, 8);
  }, [debouncedQuery, isReady, search]);

  const grouped = useMemo(() => {
    const g: Record<SearchRecordType, RankedResult[]> = {
      issue_story: [],
      bulletin: [],
      consulting: [],
      learn: [],
    };
    for (const r of results) g[r.type].push(r);
    return g;
  }, [results]);

  const flatResults = useMemo(
    () => TYPE_ORDER.flatMap((t) => grouped[t]),
    [grouped],
  );

  function navigateTo(r: RankedResult) {
    closeSearch();
    router.push(r.url);
  }

  function onKey(e: React.KeyboardEvent) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIdx((i) => Math.min(flatResults.length - 1, i + 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIdx((i) => Math.max(0, i - 1));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (flatResults[activeIdx]) {
        navigateTo(flatResults[activeIdx]);
      } else if (query.trim()) {
        closeSearch();
        router.push(`/search?q=${encodeURIComponent(query.trim())}`);
      }
    }
  }

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Search"
      className="fixed inset-0 z-[100] flex items-start justify-center"
      style={{
        background: "rgba(15, 29, 53, 0.35)",
        backdropFilter: "blur(6px)",
        WebkitBackdropFilter: "blur(6px)",
      }}
      onClick={closeSearch}
    >
      <div
        className="mt-20 w-full max-w-[640px] mx-4 overflow-hidden"
        style={{
          background: "rgba(255, 255, 255, 0.92)",
          backdropFilter: "blur(24px) saturate(1.8)",
          WebkitBackdropFilter: "blur(24px) saturate(1.8)",
          border: "1px solid rgba(255, 255, 255, 0.7)",
          borderRadius: "16px",
          boxShadow:
            "0 20px 60px rgba(15, 29, 53, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.8)",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div
          className="flex items-center gap-3 px-5"
          style={{ borderBottom: "1px solid rgba(15, 29, 53, 0.08)", height: 56 }}
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
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setActiveIdx(0);
            }}
            onKeyDown={onKey}
            placeholder="Search issues, bulletins, consulting, learn..."
            className="flex-1 bg-transparent outline-none"
            style={{
              fontSize: "16px",
              color: "#0F1D35",
              fontFamily: "inherit",
            }}
          />
          <button
            type="button"
            onClick={closeSearch}
            aria-label="Close search"
            style={{
              fontSize: "11px",
              padding: "2px 8px",
              borderRadius: "4px",
              background: "rgba(15,29,53,0.08)",
              color: "#6b7280",
              border: "1px solid rgba(15,29,53,0.08)",
              fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
            }}
          >
            Esc
          </button>
        </div>

        <div
          className="max-h-[60vh] overflow-y-auto"
          style={{ padding: "8px 0" }}
        >
          {!isReady && (
            <div
              className="px-5 py-8 text-center"
              style={{ color: "#6b7280", fontSize: "14px" }}
            >
              Loading search index...
            </div>
          )}

          {isReady && results.length === 0 && debouncedQuery.length >= 2 && (
            <div
              className="px-5 py-8 text-center"
              style={{ color: "#6b7280", fontSize: "14px" }}
            >
              No matches for &ldquo;{debouncedQuery}&rdquo;. Try different
              keywords or check spelling.
            </div>
          )}

          {isReady && results.length === 0 && debouncedQuery.length < 2 && (
            <div
              className="px-5 py-6 text-center"
              style={{ color: "#94a3b8", fontSize: "13px" }}
            >
              Start typing to search. Recent items show as you begin.
            </div>
          )}

          {isReady &&
            results.length > 0 &&
            TYPE_ORDER.map((type) => {
              const items = grouped[type];
              if (items.length === 0) return null;
              return (
                <div key={type} style={{ padding: "4px 0" }}>
                  <div
                    style={{
                      fontSize: "11px",
                      textTransform: "uppercase",
                      letterSpacing: "0.8px",
                      fontWeight: 700,
                      color: "#94a3b8",
                      padding: "6px 20px 4px",
                    }}
                  >
                    {TYPE_LABELS[type]}
                  </div>
                  {items.map((r) => {
                    const idx = flatResults.indexOf(r);
                    const isActive = idx === activeIdx;
                    return (
                      <button
                        key={r.id}
                        type="button"
                        onClick={() => navigateTo(r)}
                        onMouseEnter={() => setActiveIdx(idx)}
                        className="w-full text-left block"
                        style={{
                          padding: "10px 20px",
                          background: isActive
                            ? "rgba(2, 132, 199, 0.08)"
                            : "transparent",
                          borderLeft: isActive
                            ? "3px solid #0284C7"
                            : "3px solid transparent",
                        }}
                      >
                        <div className="flex items-start gap-2">
                          <span
                            style={{
                              fontSize: "10px",
                              fontWeight: 700,
                              textTransform: "uppercase",
                              letterSpacing: "0.5px",
                              padding: "2px 6px",
                              borderRadius: "4px",
                              background: TYPE_BADGES[type].bg,
                              color: TYPE_BADGES[type].text,
                              flexShrink: 0,
                              marginTop: "2px",
                            }}
                          >
                            {type === "issue_story" ? "Issue" : type === "consulting" ? r.firm || "Consulting" : TYPE_LABELS[type]}
                          </span>
                          <div className="flex-1 min-w-0">
                            <div
                              style={{
                                fontSize: "14px",
                                fontWeight: 600,
                                color: "#0F1D35",
                                lineHeight: 1.35,
                                marginBottom: "2px",
                              }}
                            >
                              {highlightMatch(r.title, debouncedQuery)}
                            </div>
                            {r.body && (
                              <div
                                style={{
                                  fontSize: "12px",
                                  color: "#6b7280",
                                  lineHeight: 1.4,
                                  overflow: "hidden",
                                  textOverflow: "ellipsis",
                                  display: "-webkit-box",
                                  WebkitLineClamp: 1,
                                  WebkitBoxOrient: "vertical",
                                }}
                              >
                                {highlightMatch(r.body.slice(0, 140), debouncedQuery)}
                              </div>
                            )}
                          </div>
                          {r.date && (
                            <span
                              style={{
                                fontSize: "11px",
                                color: "#94a3b8",
                                flexShrink: 0,
                                marginTop: "3px",
                              }}
                            >
                              {r.date}
                            </span>
                          )}
                        </div>
                      </button>
                    );
                  })}
                </div>
              );
            })}

          {isReady && debouncedQuery.trim().length >= 2 && results.length > 0 && (
            <div
              style={{
                borderTop: "1px solid rgba(15, 29, 53, 0.08)",
                padding: "10px 20px",
              }}
            >
              <button
                type="button"
                onClick={() => {
                  closeSearch();
                  router.push(`/search?q=${encodeURIComponent(debouncedQuery)}`);
                }}
                style={{
                  fontSize: "13px",
                  fontWeight: 600,
                  color: "#0284C7",
                  background: "transparent",
                  border: "none",
                  cursor: "pointer",
                }}
              >
                See all results for &ldquo;{debouncedQuery}&rdquo; →
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
