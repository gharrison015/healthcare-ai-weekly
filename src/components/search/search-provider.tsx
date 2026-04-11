"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import MiniSearch, { type SearchResult } from "minisearch";

export type SearchRecordType =
  | "issue_story"
  | "bulletin"
  | "consulting"
  | "learn";

export interface SearchRecord {
  id: string;
  type: SearchRecordType;
  title: string;
  body: string;
  url: string;
  date: string;
  tags: string[];
  section?: string;
  source?: string;
  firm?: string;
}

export interface RankedResult extends SearchRecord {
  score: number;
}

interface SearchFilters {
  types?: SearchRecordType[];
  firms?: string[];
  dateFrom?: string;
  dateTo?: string;
  sort?: "relevance" | "newest" | "oldest";
}

interface SearchContextValue {
  isReady: boolean;
  isLoading: boolean;
  recordCount: number;
  records: SearchRecord[];
  search: (query: string, filters?: SearchFilters) => RankedResult[];
  ensureLoaded: () => void;
  isOpen: boolean;
  openSearch: () => void;
  closeSearch: () => void;
}

const SearchContext = createContext<SearchContextValue | null>(null);

export function SearchProvider({ children }: { children: React.ReactNode }) {
  const [records, setRecords] = useState<SearchRecord[]>([]);
  const [isReady, setIsReady] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const indexRef = useRef<MiniSearch<SearchRecord> | null>(null);
  const loadTriggered = useRef(false);

  const loadIndex = useCallback(async () => {
    if (loadTriggered.current) return;
    loadTriggered.current = true;
    setIsLoading(true);
    try {
      const res = await fetch("/search-index.json", { cache: "force-cache" });
      if (!res.ok) throw new Error(`Failed to load search index: ${res.status}`);
      const data: SearchRecord[] = await res.json();

      const mini = new MiniSearch<SearchRecord>({
        fields: ["title", "body", "tags", "firm", "source"],
        storeFields: [
          "id",
          "type",
          "title",
          "body",
          "url",
          "date",
          "tags",
          "section",
          "source",
          "firm",
        ],
        extractField: (document, fieldName) => {
          const v = (document as unknown as Record<string, unknown>)[fieldName];
          if (Array.isArray(v)) return v.join(" ");
          return (v ?? "") as string;
        },
        searchOptions: {
          boost: { title: 3, tags: 2, firm: 2, body: 1 },
          prefix: true,
          fuzzy: 0.2,
          combineWith: "AND",
        },
      });

      mini.addAll(data);

      indexRef.current = mini;
      setRecords(data);
      setIsReady(true);
    } catch (err) {
      console.error("[search] Failed to load index:", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Global keyboard shortcut (⌘K / Ctrl+K)
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const isModK = (e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k";
      if (isModK) {
        e.preventDefault();
        loadIndex();
        setIsOpen(true);
      }
      if (e.key === "Escape" && isOpen) setIsOpen(false);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [isOpen, loadIndex]);

  const search = useCallback(
    (query: string, filters: SearchFilters = {}): RankedResult[] => {
      if (!indexRef.current) return [];
      const trimmed = query.trim();

      let base: RankedResult[];
      if (trimmed.length < 2) {
        // Empty/short query: return recent items across everything.
        base = [...records]
          .sort((a, b) => (b.date || "").localeCompare(a.date || ""))
          .slice(0, 20)
          .map((r) => ({ ...r, score: 0 }));
      } else {
        const hits = indexRef.current.search(trimmed) as (SearchResult &
          SearchRecord)[];
        base = hits.map((h) => ({
          id: h.id,
          type: h.type,
          title: h.title,
          body: h.body,
          url: h.url,
          date: h.date,
          tags: Array.isArray(h.tags) ? h.tags : [],
          section: h.section,
          source: h.source,
          firm: h.firm,
          score: h.score,
        }));
      }

      let filtered = base;
      if (filters.types && filters.types.length > 0) {
        const set = new Set(filters.types);
        filtered = filtered.filter((r) => set.has(r.type));
      }
      if (filters.firms && filters.firms.length > 0) {
        const set = new Set(filters.firms.map((f) => f.toLowerCase()));
        filtered = filtered.filter(
          (r) => r.firm && set.has(r.firm.toLowerCase()),
        );
      }
      if (filters.dateFrom) {
        filtered = filtered.filter((r) => (r.date || "") >= filters.dateFrom!);
      }
      if (filters.dateTo) {
        filtered = filtered.filter((r) => (r.date || "") <= filters.dateTo!);
      }

      if (filters.sort === "newest") {
        filtered.sort((a, b) => (b.date || "").localeCompare(a.date || ""));
      } else if (filters.sort === "oldest") {
        filtered.sort((a, b) => (a.date || "").localeCompare(b.date || ""));
      }
      // else: keep MiniSearch relevance order

      return filtered;
    },
    [records],
  );

  const value = useMemo<SearchContextValue>(
    () => ({
      isReady,
      isLoading,
      recordCount: records.length,
      records,
      search,
      ensureLoaded: loadIndex,
      isOpen,
      openSearch: () => {
        loadIndex();
        setIsOpen(true);
      },
      closeSearch: () => setIsOpen(false),
    }),
    [isReady, isLoading, records, search, loadIndex, isOpen],
  );

  return (
    <SearchContext.Provider value={value}>{children}</SearchContext.Provider>
  );
}

export function useSearch(): SearchContextValue {
  const ctx = useContext(SearchContext);
  if (!ctx) throw new Error("useSearch must be used inside <SearchProvider>");
  return ctx;
}
