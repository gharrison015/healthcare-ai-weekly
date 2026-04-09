import { AmbientBackground } from "@/components/ui/ambient-background";
import { GlassCardStyles } from "@/components/ui/glass-card";

export default function AnalyticsPage() {
  return (
    <>
      <AmbientBackground />
      <GlassCardStyles />

      <div className="px-10 max-sm:px-4">
        <div style={{ padding: "48px 0 32px" }}>
          <a
            href="/"
            className="inline-block no-underline hover:underline rounded-lg mb-5"
            style={{
              fontSize: "20px",
              color: "#0284C7",
              fontWeight: 700,
              padding: "8px 16px",
              background: "rgba(2, 132, 199, 0.08)",
              border: "1px solid rgba(2, 132, 199, 0.15)",
            }}
          >
            &larr; Home
          </a>
          <h1
            className="font-extrabold mb-4"
            style={{ fontSize: "38px", color: "#0F1D35", letterSpacing: "-0.5px" }}
          >
            Analytics Dashboard
          </h1>
          <div style={{ fontSize: "20px", lineHeight: "1.6", color: "#374151" }}>
            Newsletter performance metrics and reader analytics. Coming soon.
          </div>
        </div>

        <div
          className="text-center py-16"
          style={{ color: "#94a3b8", fontSize: "16px" }}
        >
          Analytics dashboard coming soon.
        </div>

        <div
          className="text-center"
          style={{ fontSize: "14px", color: "#94a3b8", padding: "32px 0 48px" }}
        >
          Healthcare AI Weekly by Greg Harrison, Guidehouse
        </div>
      </div>
    </>
  );
}
