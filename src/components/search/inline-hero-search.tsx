"use client";

import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent,
} from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  useSearch,
  type RankedResult,
  type SearchRecordType,
} from "./search-provider";

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
        style={{
          background: "rgba(2, 132, 199, 0.22)",
          color: "inherit",
          padding: "0 2px",
          borderRadius: "3px",
        }}
      >
        {part}
      </mark>
    ) : (
      <span key={i}>{part}</span>
    ),
  );
}

export function InlineHeroSearch() {
  const { search, isReady, ensureLoaded } = useSearch();
  const [query, setQuery] = useState("");
  const [debounced, setDebounced] = useState("");
  const [activeIdx, setActiveIdx] = useState(0);
  const [isFocused, setIsFocused] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  // Preload the index on mount so results appear instantly on first keystroke.
  useEffect(() => {
    ensureLoaded();
  }, [ensureLoaded]);

  // Debounce the query for search.
  useEffect(() => {
    const t = setTimeout(() => setDebounced(query), 80);
    return () => clearTimeout(t);
  }, [query]);

  // Close the panel when clicking outside.
  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (
        panelRef.current &&
        !panelRef.current.contains(e.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(e.target as Node)
      ) {
        setIsFocused(false);
      }
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  const results: RankedResult[] = useMemo(() => {
    if (!isReady || debounced.trim().length < 2) return [];
    return search(debounced).slice(0, 8);
  }, [debounced, isReady, search]);

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

  // Ghost-completion: find the first result whose title starts with the query.
  const ghostCompletion = useMemo(() => {
    const q = query.trim();
    if (q.length < 2 || flatResults.length === 0) return "";
    const match = flatResults.find((r) =>
      r.title.toLowerCase().startsWith(q.toLowerCase()),
    );
    if (!match) return "";
    // Return only the part after what the user has typed, preserving the
    // original casing from the matched title.
    return match.title.slice(q.length);
  }, [query, flatResults]);

  function acceptGhost() {
    if (!ghostCompletion) return;
    setQuery((q) => q + ghostCompletion);
  }

  function navigateTo(r: RankedResult) {
    setIsFocused(false);
    router.push(r.url);
  }

  function onKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIdx((i) => Math.min(flatResults.length - 1, i + 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIdx((i) => Math.max(0, i - 1));
    } else if (e.key === "Tab" || e.key === "ArrowRight") {
      if (ghostCompletion && e.currentTarget.selectionStart === query.length) {
        e.preventDefault();
        acceptGhost();
      }
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (flatResults[activeIdx]) {
        navigateTo(flatResults[activeIdx]);
      } else if (query.trim()) {
        router.push(`/search?q=${encodeURIComponent(query.trim())}`);
      }
    } else if (e.key === "Escape") {
      setIsFocused(false);
      inputRef.current?.blur();
    }
  }

  const showPanel = isFocused && debounced.trim().length >= 2;

  return (
    <div className="relative" style={{ maxWidth: "640px", margin: "0 auto" }}>
      {/* Search input shell — matches liquid-glass cards across the site */}
      <div
        className="flex items-center gap-2"
        style={{
          background: "rgba(255, 255, 255, 0.72)",
          backdropFilter: "blur(20px) saturate(1.8)",
          WebkitBackdropFilter: "blur(20px) saturate(1.8)",
          border: `1px solid ${
            isFocused ? "rgba(2, 132, 199, 0.38)" : "rgba(255, 255, 255, 0.7)"
          }`,
          borderRadius: "14px",
          padding: "8px 14px",
          boxShadow: isFocused
            ? "0 8px 24px rgba(2, 132, 199, 0.10), 0 0 0 3px rgba(2, 132, 199, 0.06), inset 0 1px 0 rgba(255, 255, 255, 0.9)"
            : "0 2px 12px rgba(15, 29, 53, 0.06), inset 0 1px 0 rgba(255, 255, 255, 0.8)",
          transition: "all 180ms ease",
        }}
      >
        <svg
          width="13"
          height="13"
          viewBox="0 0 24 24"
          fill="none"
          stroke={isFocused ? "#0284C7" : "#6b7280"}
          strokeWidth="2.4"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
          style={{ flexShrink: 0, transition: "stroke 180ms ease" }}
        >
          <circle cx="11" cy="11" r="7" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
        {/* Relative wrapper for the ghost-completion layer */}
        <div className="relative flex-1">
          {/* Ghost completion (absolutely positioned behind the input) */}
          {ghostCompletion && (
            <div
              aria-hidden="true"
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                right: 0,
                pointerEvents: "none",
                fontSize: "13px",
                fontFamily: "inherit",
                color: "transparent",
                whiteSpace: "pre",
                overflow: "hidden",
              }}
            >
              <span style={{ color: "transparent" }}>{query}</span>
              <span style={{ color: "#94a3b8" }}>{ghostCompletion}</span>
            </div>
          )}
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setActiveIdx(0);
              setIsFocused(true);
            }}
            onFocus={() => setIsFocused(true)}
            onKeyDown={onKeyDown}
            placeholder="Search news, consulting intelligence, AI learning, etc."
            spellCheck={false}
            autoComplete="off"
            className="w-full bg-transparent outline-none relative"
            style={{
              fontSize: "13px",
              color: "#0F1D35",
              fontFamily: "inherit",
              padding: 0,
              border: "none",
              position: "relative",
              zIndex: 1,
            }}
          />
        </div>
        {query && (
          <button
            type="button"
            onClick={() => {
              setQuery("");
              inputRef.current?.focus();
            }}
            aria-label="Clear search"
            style={{
              fontSize: "9px",
              color: "#6b7280",
              background: "rgba(15, 29, 53, 0.06)",
              border: "none",
              borderRadius: "50%",
              width: "15px",
              height: "15px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              cursor: "pointer",
              flexShrink: 0,
            }}
          >
            ✕
          </button>
        )}
      </div>

      {/* Inline results panel */}
      {showPanel && (
        <div
          ref={panelRef}
          className="absolute left-0 right-0"
          style={{
            top: "calc(100% + 10px)",
            background: "rgba(255, 255, 255, 0.95)",
            backdropFilter: "blur(28px) saturate(1.8)",
            WebkitBackdropFilter: "blur(28px) saturate(1.8)",
            border: "1px solid rgba(255, 255, 255, 0.7)",
            borderRadius: "16px",
            boxShadow:
              "0 24px 60px rgba(15, 29, 53, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.85)",
            zIndex: 40,
            maxHeight: "min(60vh, 540px)",
            overflowY: "auto",
          }}
        >
          {!isReady && (
            <div
              className="px-5 py-7 text-center"
              style={{ color: "#6b7280", fontSize: "14px" }}
            >
              Loading search index...
            </div>
          )}

          {isReady && results.length === 0 && (
            <div
              className="px-5 py-7 text-center"
              style={{ color: "#6b7280", fontSize: "14px" }}
            >
              No matches for &ldquo;{debounced}&rdquo;. Try different keywords
              or check spelling.
            </div>
          )}

          {isReady &&
            results.length > 0 &&
            TYPE_ORDER.map((type) => {
              const items = grouped[type];
              if (items.length === 0) return null;
              return (
                <div key={type} style={{ padding: "6px 0" }}>
                  <div
                    style={{
                      fontSize: "11px",
                      textTransform: "uppercase",
                      letterSpacing: "0.9px",
                      fontWeight: 800,
                      color: "#94a3b8",
                      padding: "8px 22px 4px",
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
                        onMouseDown={(e) => {
                          e.preventDefault();
                          navigateTo(r);
                        }}
                        onMouseEnter={() => setActiveIdx(idx)}
                        className="w-full text-left block"
                        style={{
                          padding: "12px 22px",
                          background: isActive
                            ? "rgba(2, 132, 199, 0.08)"
                            : "transparent",
                          borderLeft: isActive
                            ? "3px solid #0284C7"
                            : "3px solid transparent",
                          cursor: "pointer",
                        }}
                      >
                        <div className="flex items-start gap-2">
                          <span
                            style={{
                              fontSize: "10px",
                              fontWeight: 700,
                              textTransform: "uppercase",
                              letterSpacing: "0.5px",
                              padding: "3px 7px",
                              borderRadius: "4px",
                              background: TYPE_BADGES[type].bg,
                              color: TYPE_BADGES[type].text,
                              flexShrink: 0,
                              marginTop: "2px",
                              whiteSpace: "nowrap",
                            }}
                          >
                            {type === "issue_story"
                              ? "Issue"
                              : type === "consulting"
                              ? r.firm || "Consulting"
                              : TYPE_LABELS[type]}
                          </span>
                          <div className="flex-1 min-w-0">
                            <div
                              style={{
                                fontSize: "15px",
                                fontWeight: 600,
                                color: "#0F1D35",
                                lineHeight: 1.35,
                                marginBottom: "3px",
                              }}
                            >
                              {highlightMatch(r.title, debounced)}
                            </div>
                            {r.body && (
                              <div
                                style={{
                                  fontSize: "13px",
                                  color: "#6b7280",
                                  lineHeight: 1.45,
                                  overflow: "hidden",
                                  textOverflow: "ellipsis",
                                  display: "-webkit-box",
                                  WebkitLineClamp: 1,
                                  WebkitBoxOrient: "vertical",
                                }}
                              >
                                {highlightMatch(
                                  r.body.slice(0, 160),
                                  debounced,
                                )}
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
                                whiteSpace: "nowrap",
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

          {isReady && results.length > 0 && (
            <div
              style={{
                borderTop: "1px solid rgba(15, 29, 53, 0.08)",
                padding: "12px 22px",
              }}
            >
              <Link
                href={`/search?q=${encodeURIComponent(debounced)}`}
                onClick={() => setIsFocused(false)}
                className="no-underline"
                style={{
                  fontSize: "13px",
                  fontWeight: 700,
                  color: "#0284C7",
                }}
              >
                See all results for &ldquo;{debounced}&rdquo; →
              </Link>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
