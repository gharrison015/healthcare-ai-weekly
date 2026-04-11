"use client";

import Link from "next/link";
import type { RankedResult, SearchRecordType } from "./search-provider";

const TYPE_LABELS: Record<SearchRecordType, string> = {
  issue_story: "Weekly Issue",
  bulletin: "Bulletin",
  consulting: "Consulting Intelligence",
  learn: "Learn",
};

const TYPE_BADGES: Record<SearchRecordType, { bg: string; text: string }> = {
  issue_story: { bg: "#E0F2FE", text: "#0284C7" },
  bulletin: { bg: "#FEE2E2", text: "#DC2626" },
  consulting: { bg: "#EDE9FE", text: "#6344F5" },
  learn: { bg: "#DCFCE7", text: "#16A34A" },
};

export function SearchResultCard({ result }: { result: RankedResult }) {
  const badge = TYPE_BADGES[result.type];
  return (
    <Link
      href={result.url}
      className="block no-underline group"
      style={{
        background: "rgba(255, 255, 255, 0.72)",
        backdropFilter: "blur(20px) saturate(1.6)",
        WebkitBackdropFilter: "blur(20px) saturate(1.6)",
        border: "1px solid rgba(255, 255, 255, 0.7)",
        borderRadius: "14px",
        padding: "18px 22px",
        boxShadow:
          "0 2px 12px rgba(15, 29, 53, 0.06), inset 0 1px 0 rgba(255, 255, 255, 0.8)",
        transition: "all 180ms ease",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = "translateY(-2px)";
        e.currentTarget.style.boxShadow =
          "0 10px 28px rgba(15, 29, 53, 0.12), inset 0 1px 0 rgba(255, 255, 255, 0.9)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = "translateY(0)";
        e.currentTarget.style.boxShadow =
          "0 2px 12px rgba(15, 29, 53, 0.06), inset 0 1px 0 rgba(255, 255, 255, 0.8)";
      }}
    >
      <div className="flex items-center gap-2" style={{ marginBottom: 10 }}>
        <span
          style={{
            fontSize: "10px",
            fontWeight: 700,
            textTransform: "uppercase",
            letterSpacing: "0.6px",
            padding: "3px 8px",
            borderRadius: "4px",
            background: badge.bg,
            color: badge.text,
          }}
        >
          {result.type === "consulting" && result.firm
            ? result.firm
            : TYPE_LABELS[result.type]}
        </span>
        {result.section && (
          <span style={{ fontSize: "11px", color: "#94a3b8" }}>
            {result.section}
          </span>
        )}
        {result.source && (
          <span style={{ fontSize: "11px", color: "#94a3b8" }}>
            · {result.source}
          </span>
        )}
        {result.date && (
          <span
            style={{
              fontSize: "11px",
              color: "#94a3b8",
              marginLeft: "auto",
            }}
          >
            {result.date}
          </span>
        )}
      </div>
      <div
        style={{
          fontSize: "18px",
          fontWeight: 700,
          color: "#0F1D35",
          lineHeight: 1.35,
          marginBottom: 8,
          letterSpacing: "-0.2px",
        }}
      >
        {result.title}
      </div>
      {result.body && (
        <div
          style={{
            fontSize: "14px",
            color: "#475569",
            lineHeight: 1.55,
            overflow: "hidden",
            display: "-webkit-box",
            WebkitLineClamp: 3,
            WebkitBoxOrient: "vertical",
          }}
        >
          {result.body}
        </div>
      )}
    </Link>
  );
}
