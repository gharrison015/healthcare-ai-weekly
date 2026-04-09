import { AmbientBackground } from "@/components/ui/ambient-background";
import { GlassCardStyles } from "@/components/ui/glass-card";
import { getBulletins } from "@/lib/data";
import { BulletinArchiveCards } from "./bulletin-archive-cards";

export default function BulletinsPage() {
  const bulletins = getBulletins();

  return (
    <>
      <AmbientBackground />
      <GlassCardStyles />

      <div className="px-10 max-sm:px-4">
        <div style={{ padding: "48px 0 32px" }}>
          <h1
            className="font-extrabold mb-2"
            style={{ fontSize: "38px", color: "#0284C7", letterSpacing: "-0.5px" }}
          >
            Bulletins
          </h1>
          <div style={{ fontSize: "20px", lineHeight: "1.6", color: "#374151" }}>
            Breaking healthcare AI developments and urgent alerts.
          </div>
        </div>

        {bulletins.length > 0 ? (
          <BulletinArchiveCards bulletins={bulletins} />
        ) : (
          <div
            className="text-center py-16"
            style={{ color: "#94a3b8", fontSize: "16px" }}
          >
            No bulletins published yet.
          </div>
        )}

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
