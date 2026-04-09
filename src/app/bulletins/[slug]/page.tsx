import { notFound } from "next/navigation";
import Link from "next/link";
import { AmbientBackground } from "@/components/ui/ambient-background";
import { GlassCardStyles } from "@/components/ui/glass-card";
import { getBulletin, getBulletinSlugs } from "@/lib/data";

export async function generateStaticParams() {
  const slugs = getBulletinSlugs();
  return slugs.map((slug) => ({ slug }));
}

interface PageProps {
  params: Promise<{ slug: string }>;
}

export default async function BulletinPage({ params }: PageProps) {
  const { slug } = await params;
  const bulletin = getBulletin(slug);

  if (!bulletin) {
    notFound();
  }

  const date = new Date(bulletin.timestamp);
  const formattedDate = date.toLocaleDateString("en-US", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });
  const formattedTime = date.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
  });

  return (
    <>
      <AmbientBackground />
      <GlassCardStyles />

      <div className="px-10 max-sm:px-4">
        <div style={{ padding: "48px 0 32px" }}>
          <Link
            href="/bulletins"
            className="inline-block no-underline hover:underline rounded-lg mb-5"
            style={{
              fontSize: "16px",
              color: "#0284C7",
              fontWeight: 700,
              padding: "8px 16px",
              background: "rgba(2, 132, 199, 0.06)",
              border: "1px solid rgba(2, 132, 199, 0.15)",
            }}
          >
            &larr; All Bulletins
          </Link>

          <div className="flex items-center gap-3 mb-4">
            <span
              className="text-xs font-bold uppercase tracking-wider px-2.5 py-1 rounded-md"
              style={{
                background: "rgba(2, 132, 199, 0.1)",
                color: "#0284C7",
                border: "1px solid rgba(2, 132, 199, 0.2)",
                letterSpacing: "0.8px",
              }}
            >
              Bulletin
            </span>
            <span
              className="text-xs font-semibold px-2 py-0.5 rounded-full"
              style={{
                background:
                  bulletin.verification === "confirmed"
                    ? "rgba(5, 150, 105, 0.08)"
                    : "rgba(245, 158, 11, 0.08)",
                color:
                  bulletin.verification === "confirmed" ? "#059669" : "#d97706",
                border: `1px solid ${
                  bulletin.verification === "confirmed"
                    ? "rgba(5, 150, 105, 0.2)"
                    : "rgba(245, 158, 11, 0.2)"
                }`,
              }}
            >
              {bulletin.verification}
            </span>
            <span
              className="text-xs font-semibold px-2 py-0.5 rounded-full"
              style={{
                background: "rgba(2, 132, 199, 0.08)",
                color: "#0284C7",
                border: "1px solid rgba(2, 132, 199, 0.2)",
              }}
            >
              Velocity: {bulletin.velocity_score}
            </span>
          </div>

          <h1
            className="font-extrabold mb-3"
            style={{
              fontSize: "34px",
              color: "#0F1D35",
              letterSpacing: "-0.5px",
              lineHeight: "1.2",
            }}
          >
            {bulletin.headline}
          </h1>

          <div className="flex items-center gap-2 mb-6" style={{ fontSize: "14px", color: "#94a3b8" }}>
            <span>{formattedDate} at {formattedTime}</span>
            <span style={{ color: "#d1d5db" }}>|</span>
            <a
              href={bulletin.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="no-underline hover:underline font-semibold"
              style={{ color: "#0284C7" }}
            >
              {bulletin.source_name}
            </a>
          </div>
        </div>

        <div className="mb-6">
          <div
            style={{
              fontSize: "18px",
              lineHeight: "1.7",
              color: "#374151",
            }}
          >
            {bulletin.body}
          </div>
        </div>

        <div className="flex flex-wrap gap-1.5 mb-6">
          {bulletin.tags.map((tag) => (
            <span
              key={tag}
              className="text-xs font-medium px-2.5 py-1 rounded-full"
              style={{
                background: "rgba(2, 132, 199, 0.06)",
                color: "#0369a1",
                border: "1px solid rgba(2, 132, 199, 0.12)",
              }}
            >
              {tag}
            </span>
          ))}
        </div>

        <div className="mb-8">
          <a
            href={bulletin.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block no-underline hover:underline rounded-lg font-bold"
            style={{
              fontSize: "16px",
              color: "#0284C7",
              padding: "10px 20px",
              background: "rgba(2, 132, 199, 0.06)",
              border: "1px solid rgba(2, 132, 199, 0.15)",
            }}
          >
            Read original source &rarr;
          </a>
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
