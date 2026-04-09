export function AmbientBackground() {
  return (
    <div
      className="fixed inset-0 overflow-hidden pointer-events-none"
      style={{
        zIndex: -1,
        background:
          "linear-gradient(135deg, #e8edf5 0%, #dfe6f0 30%, #eae4f0 60%, #e0eaf5 100%)",
      }}
    >
      {/* Sky blue circle - top right */}
      <div
        className="absolute rounded-full"
        style={{
          width: 600,
          height: 600,
          background:
            "radial-gradient(circle, rgba(14, 165, 233, 0.25), transparent 70%)",
          top: "-10%",
          right: "-5%",
          filter: "blur(100px)",
          opacity: 0.4,
          animation: "ambient-drift 20s ease-in-out infinite alternate",
        }}
      />
      {/* Purple circle - bottom left */}
      <div
        className="absolute rounded-full"
        style={{
          width: 500,
          height: 500,
          background:
            "radial-gradient(circle, rgba(139, 92, 246, 0.2), transparent 70%)",
          bottom: "-10%",
          left: "-5%",
          filter: "blur(100px)",
          opacity: 0.4,
          animation: "ambient-drift 20s ease-in-out infinite alternate",
          animationDelay: "-10s",
        }}
      />
    </div>
  );
}
