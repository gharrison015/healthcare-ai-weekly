"use client";

import { useEffect, useState } from "react";
import { useSearch } from "./search-provider";

export function SearchButton() {
  const { openSearch } = useSearch();
  const [isMac, setIsMac] = useState(false);

  useEffect(() => {
    setIsMac(
      typeof navigator !== "undefined" &&
        /Mac|iPhone|iPad|iPod/.test(navigator.platform),
    );
  }, []);

  return (
    <button
      type="button"
      onClick={openSearch}
      aria-label="Search"
      className="group flex items-center gap-2 rounded-full transition-all"
      style={{
        padding: "6px 10px 6px 12px",
        background: "rgba(255,255,255,0.55)",
        border: "1px solid rgba(15,29,53,0.12)",
        color: "#0F1D35",
        fontSize: "13px",
        fontWeight: 600,
        backdropFilter: "blur(12px)",
        WebkitBackdropFilter: "blur(12px)",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = "rgba(255,255,255,0.85)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = "rgba(255,255,255,0.55)";
      }}
    >
      <svg
        width="14"
        height="14"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <circle cx="11" cy="11" r="7" />
        <line x1="21" y1="21" x2="16.65" y2="16.65" />
      </svg>
      <span className="max-sm:hidden">Search</span>
      <kbd
        className="max-sm:hidden"
        style={{
          fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
          fontSize: "11px",
          padding: "1px 6px",
          borderRadius: "4px",
          background: "rgba(15,29,53,0.08)",
          color: "#6b7280",
          border: "1px solid rgba(15,29,53,0.08)",
          marginLeft: "4px",
        }}
      >
        {isMac ? "⌘K" : "Ctrl K"}
      </kbd>
    </button>
  );
}
