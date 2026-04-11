"use client";

const SOURCES = [
  "Fierce Healthcare",
  "Becker's Hospital Review",
  "STAT News",
  "Healthcare IT News",
  "Healthcare Dive",
  "Modern Healthcare",
  "Health Affairs",
  "MobiHealthNews",
  "HIT Consultant",
  "CMS Newsroom",
  "HHS.gov",
  "AMA",
  "Rock Health",
  "McKinsey Healthcare",
  "Deloitte Health Insights",
  "Google Health",
  "Microsoft Health",
  "NVIDIA Healthcare",
  "AWS Health",
  "OpenAI",
  "Anthropic",
  "Google AI",
  "Newsdata.io",
  "Hacker News",
  "Reddit",
];

export function SourceTicker() {
  // Duplicate for seamless loop
  const allItems = [...SOURCES, ...SOURCES];

  return (
    <div className="pt-0 pb-1 text-center">
      <div
        className="text-xs font-extrabold uppercase tracking-widest"
        style={{ color: "#94a3b8", letterSpacing: "2px", fontSize: "12px", marginBottom: "1px" }}
      >
        Curated from Credible Sources
      </div>
      <div className="relative overflow-hidden py-1">
        {/* Left fade */}
        <div
          className="absolute top-0 bottom-0 left-0 w-[120px] z-[2] pointer-events-none"
          style={{
            background: "linear-gradient(to right, #f0f2f5, transparent)",
          }}
        />
        {/* Track */}
        <div
          className="flex items-center gap-12"
          style={{
            width: "max-content",
            animation: "ticker-scroll 40s linear infinite",
          }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLElement).style.animationPlayState =
              "paused";
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLElement).style.animationPlayState =
              "running";
          }}
        >
          {allItems.map((source, i) => (
            <span
              key={`${source}-${i}`}
              className="whitespace-nowrap transition-opacity duration-200 hover:opacity-100"
              style={{
                fontSize: "15px",
                fontWeight: 600,
                color: "#6b7280",
                opacity: 0.7,
              }}
            >
              {source}
            </span>
          ))}
        </div>
        {/* Right fade */}
        <div
          className="absolute top-0 bottom-0 right-0 w-[120px] z-[2] pointer-events-none"
          style={{
            background: "linear-gradient(to left, #f0f2f5, transparent)",
          }}
        />
      </div>
    </div>
  );
}
