import Link from "next/link";

export function Nav() {
  return (
    <nav
      className="sticky top-0 z-50"
      style={{
        background: "rgba(240, 242, 245, 0.7)",
        backdropFilter: "blur(20px) saturate(1.8)",
        WebkitBackdropFilter: "blur(20px) saturate(1.8)",
        borderBottom: "1px solid rgba(255, 255, 255, 0.5)",
      }}
    >
      <div className="px-10 max-sm:px-4 flex items-center justify-between h-14">
        <Link
          href="/"
          className="font-extrabold no-underline"
          style={{ fontSize: "16px", color: "#0F1D35", letterSpacing: "-0.3px" }}
        >
          Healthcare AI Weekly
        </Link>
        <div className="flex items-center gap-6">
          <Link
            href="/"
            className="no-underline font-semibold transition-colors duration-200"
            style={{ fontSize: "14px", color: "#6b7280" }}
          >
            Home
          </Link>
          <Link
            href="/bulletins"
            className="no-underline font-semibold transition-colors duration-200"
            style={{ fontSize: "14px", color: "#6b7280" }}
          >
            Bulletins
          </Link>
          <Link
            href="/learn"
            className="no-underline font-semibold transition-colors duration-200"
            style={{ fontSize: "14px", color: "#6b7280" }}
          >
            Learn
          </Link>
        </div>
      </div>
    </nav>
  );
}
