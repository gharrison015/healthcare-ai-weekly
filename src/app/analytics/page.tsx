import { AmbientBackground } from "@/components/ui/ambient-background";
import { GlassCardStyles } from "@/components/ui/glass-card";
import {
  getDashboardSummary,
  getQuizAnalytics,
  getQuestionDifficulty,
  getAttemptsByDay,
} from "@/lib/analytics-data";

interface PageProps {
  searchParams: Promise<{ key?: string }>;
}

export default async function AnalyticsPage({ searchParams }: PageProps) {
  const params = await searchParams;
  const password = process.env.ANALYTICS_PASSWORD;

  // Password gate
  if (!password || params.key !== password) {
    return (
      <>
        <AmbientBackground />
        <GlassCardStyles />
        <div className="px-10 max-sm:px-4" style={{ paddingTop: 120, textAlign: "center" }}>
          <div
            style={{
              background: "rgba(255, 255, 255, 0.5)",
              backdropFilter: "blur(16px) saturate(1.6)",
              WebkitBackdropFilter: "blur(16px) saturate(1.6)",
              border: "1px solid rgba(255, 255, 255, 0.55)",
              boxShadow: "0 1px 2px rgba(0,0,0,0.03), 0 4px 16px rgba(0,0,0,0.04), inset 0 1px 0 rgba(255,255,255,0.6)",
              borderRadius: 16,
              padding: "48px 32px",
              maxWidth: 420,
              margin: "0 auto",
            }}
          >
            <div style={{ fontSize: 40, marginBottom: 16 }}>&#128274;</div>
            <h1 style={{ fontSize: 24, fontWeight: 800, color: "#0F1D35", marginBottom: 8 }}>
              Unauthorized
            </h1>
            <p style={{ fontSize: 16, color: "#64748b" }}>
              This dashboard requires a valid access key.
            </p>
          </div>
        </div>
      </>
    );
  }

  // Fetch all data server-side (uses service_role key)
  const [summary, quizStats, hardestQuestions, dailyAttempts] = await Promise.all([
    getDashboardSummary(),
    getQuizAnalytics(),
    getQuestionDifficulty(),
    getAttemptsByDay(30),
  ]);

  const maxDailyCount = Math.max(...dailyAttempts.map((d) => d.count), 1);

  return (
    <>
      <AmbientBackground />
      <GlassCardStyles />

      <div className="px-10 max-sm:px-4" style={{ maxWidth: 1100, margin: "0 auto" }}>
        {/* Header */}
        <div style={{ padding: "48px 0 32px" }}>
          <a
            href="/"
            className="inline-block no-underline hover:underline rounded-lg mb-5"
            style={{
              fontSize: 20,
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
            className="font-extrabold mb-2"
            style={{ fontSize: 38, color: "#0F1D35", letterSpacing: "-0.5px" }}
          >
            Quiz Analytics Dashboard
          </h1>
          <p style={{ fontSize: 18, color: "#64748b" }}>
            Anonymous aggregate quiz performance data
          </p>
        </div>

        {/* Summary Cards */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
            gap: 16,
            marginBottom: 32,
          }}
        >
          <SummaryCard label="Total Attempts" value={summary.totalAttempts} />
          <SummaryCard label="Unique Sessions" value={summary.uniqueSessions} />
          <SummaryCard label="Avg Score" value={`${summary.avgScorePct}%`} />
          <SummaryCard label="Topics Covered" value={summary.topicsCovered} />
        </div>

        {/* Quiz Completion Rates */}
        <SectionCard title="Quiz Completion Rates by Topic">
          {quizStats.length === 0 ? (
            <EmptyState text="No quiz data yet. Submissions will appear here." />
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr>
                    <Th>Topic (slug)</Th>
                    <Th align="right">Attempts</Th>
                    <Th align="right">Avg Score</Th>
                    <Th align="right">First Attempt</Th>
                    <Th align="right">Last Attempt</Th>
                  </tr>
                </thead>
                <tbody>
                  {quizStats.map((row) => (
                    <tr key={row.quiz_slug}>
                      <Td>
                        <code
                          style={{
                            background: "rgba(2, 132, 199, 0.08)",
                            padding: "2px 8px",
                            borderRadius: 6,
                            fontSize: 14,
                            color: "#0284C7",
                          }}
                        >
                          {row.quiz_slug}
                        </code>
                      </Td>
                      <Td align="right">{row.attempts}</Td>
                      <Td align="right">
                        <ScoreBadge score={row.avg_score_pct} />
                      </Td>
                      <Td align="right">{formatDate(row.first_attempt)}</Td>
                      <Td align="right">{formatDate(row.last_attempt)}</Td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </SectionCard>

        {/* Hardest Questions */}
        <SectionCard title="Hardest Questions (lowest correct rate)">
          {hardestQuestions.length === 0 ? (
            <EmptyState text="No per-question data yet." />
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr>
                    <Th>Quiz</Th>
                    <Th>Question ID</Th>
                    <Th align="right">Attempts</Th>
                    <Th align="right">Correct Rate</Th>
                  </tr>
                </thead>
                <tbody>
                  {hardestQuestions.slice(0, 15).map((row) => (
                    <tr key={`${row.quiz_slug}-${row.question_id}`}>
                      <Td>
                        <code
                          style={{
                            background: "rgba(2, 132, 199, 0.08)",
                            padding: "2px 8px",
                            borderRadius: 6,
                            fontSize: 14,
                            color: "#0284C7",
                          }}
                        >
                          {row.quiz_slug}
                        </code>
                      </Td>
                      <Td>{row.question_id}</Td>
                      <Td align="right">{row.attempts}</Td>
                      <Td align="right">
                        <ScoreBadge score={row.correct_rate_pct} />
                      </Td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </SectionCard>

        {/* Attempts Over Time */}
        <SectionCard title="Attempts Over Time (last 30 days)">
          {dailyAttempts.length === 0 ? (
            <EmptyState text="No activity in the last 30 days." />
          ) : (
            <div style={{ display: "flex", alignItems: "flex-end", gap: 4, height: 120, padding: "16px 0" }}>
              {dailyAttempts.map((d) => (
                <div
                  key={d.day}
                  title={`${d.day}: ${d.count} attempt${d.count !== 1 ? "s" : ""}`}
                  style={{
                    flex: 1,
                    minWidth: 8,
                    height: `${Math.max((d.count / maxDailyCount) * 100, 6)}%`,
                    background: "linear-gradient(180deg, #0284C7, #0ea5e9)",
                    borderRadius: "4px 4px 0 0",
                    opacity: 0.85,
                    transition: "opacity 0.2s",
                    cursor: "default",
                  }}
                />
              ))}
            </div>
          )}
        </SectionCard>

        {/* Footer */}
        <div
          className="text-center"
          style={{ fontSize: 14, color: "#94a3b8", padding: "32px 0 48px" }}
        >
          Healthcare AI Weekly by Greg Harrison, Guidehouse
        </div>
      </div>
    </>
  );
}

// --- Subcomponents ---

function SummaryCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div
      style={{
        background: "rgba(255, 255, 255, 0.5)",
        backdropFilter: "blur(16px) saturate(1.6)",
        WebkitBackdropFilter: "blur(16px) saturate(1.6)",
        border: "1px solid rgba(255, 255, 255, 0.55)",
        boxShadow:
          "0 1px 2px rgba(0,0,0,0.03), 0 4px 16px rgba(0,0,0,0.04), inset 0 1px 0 rgba(255,255,255,0.6)",
        borderRadius: 16,
        padding: "24px 20px",
      }}
    >
      <div style={{ fontSize: 13, fontWeight: 600, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 8 }}>
        {label}
      </div>
      <div style={{ fontSize: 32, fontWeight: 800, color: "#0F1D35" }}>
        {value}
      </div>
    </div>
  );
}

function SectionCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div
      style={{
        background: "rgba(255, 255, 255, 0.5)",
        backdropFilter: "blur(16px) saturate(1.6)",
        WebkitBackdropFilter: "blur(16px) saturate(1.6)",
        border: "1px solid rgba(255, 255, 255, 0.55)",
        boxShadow:
          "0 1px 2px rgba(0,0,0,0.03), 0 4px 16px rgba(0,0,0,0.04), inset 0 1px 0 rgba(255,255,255,0.6)",
        borderRadius: 16,
        padding: "24px 24px 16px",
        marginBottom: 24,
      }}
    >
      <h2 style={{ fontSize: 18, fontWeight: 700, color: "#0F1D35", marginBottom: 16 }}>
        {title}
      </h2>
      {children}
    </div>
  );
}

function Th({ children, align = "left" }: { children: React.ReactNode; align?: "left" | "right" }) {
  return (
    <th
      style={{
        textAlign: align,
        fontSize: 12,
        fontWeight: 700,
        color: "#64748b",
        textTransform: "uppercase",
        letterSpacing: "0.5px",
        padding: "8px 12px",
        borderBottom: "1px solid rgba(0,0,0,0.06)",
      }}
    >
      {children}
    </th>
  );
}

function Td({ children, align = "left" }: { children: React.ReactNode; align?: "left" | "right" }) {
  return (
    <td
      style={{
        textAlign: align,
        fontSize: 14,
        color: "#374151",
        padding: "10px 12px",
        borderBottom: "1px solid rgba(0,0,0,0.04)",
      }}
    >
      {children}
    </td>
  );
}

function ScoreBadge({ score }: { score: number }) {
  const color = score >= 75 ? "#16a34a" : score >= 50 ? "#d97706" : "#dc2626";
  const bg = score >= 75 ? "rgba(22,163,74,0.1)" : score >= 50 ? "rgba(217,119,6,0.1)" : "rgba(220,38,38,0.1)";
  return (
    <span
      style={{
        display: "inline-block",
        padding: "2px 10px",
        borderRadius: 12,
        fontSize: 13,
        fontWeight: 700,
        color,
        background: bg,
      }}
    >
      {score}%
    </span>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div style={{ textAlign: "center", padding: "32px 16px", color: "#94a3b8", fontSize: 15 }}>
      {text}
    </div>
  );
}

function formatDate(iso: string): string {
  if (!iso) return "--";
  try {
    return new Date(iso).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return iso.slice(0, 10);
  }
}
