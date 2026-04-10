"use client";

import { useRef, useState, useEffect, useCallback, type ReactNode } from "react";

interface HorizontalScrollerProps {
  children: ReactNode;
  className?: string;
}

export function HorizontalScroller({ children, className }: HorizontalScrollerProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(false);

  const checkScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    setCanScrollLeft(el.scrollLeft > 2);
    setCanScrollRight(el.scrollLeft < el.scrollWidth - el.clientWidth - 2);
  }, []);

  useEffect(() => {
    checkScroll();
    const el = scrollRef.current;
    if (!el) return;
    el.addEventListener("scroll", checkScroll, { passive: true });
    window.addEventListener("resize", checkScroll);
    return () => {
      el.removeEventListener("scroll", checkScroll);
      window.removeEventListener("resize", checkScroll);
    };
  }, [checkScroll]);

  const scroll = (direction: "left" | "right") => {
    const el = scrollRef.current;
    if (!el) return;
    const scrollAmount = el.clientWidth * 0.8;
    el.scrollBy({
      left: direction === "left" ? -scrollAmount : scrollAmount,
      behavior: "smooth",
    });
  };

  return (
    <div className={`relative ${className || ""}`}>
      {/* Left fade + arrow */}
      {canScrollLeft && (
        <>
          <div
            className="absolute top-0 bottom-0 left-0 w-16 z-[2] pointer-events-none"
            style={{
              background: "linear-gradient(to right, #f0f2f5, transparent)",
            }}
          />
          <button
            onClick={() => scroll("left")}
            className="absolute left-2 top-1/2 -translate-y-1/2 z-[3] w-10 h-10 rounded-full flex items-center justify-center cursor-pointer border-none"
            style={{
              background: "rgba(255, 255, 255, 0.8)",
              backdropFilter: "blur(12px)",
              boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
              transition: "all 0.2s",
            }}
            aria-label="Scroll left"
          >
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M12 4L6 10L12 16" stroke="#0F1D35" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        </>
      )}

      {/* Scroll container */}
      <div
        ref={scrollRef}
        className="horizontal-scroller flex gap-4 overflow-x-auto pt-2 pb-6"
        style={{
          scrollbarWidth: "none",
          msOverflowStyle: "none",
          WebkitOverflowScrolling: "touch",
          overscrollBehaviorX: "contain",
        }}
      >
        <style dangerouslySetInnerHTML={{ __html: `
          .horizontal-scroller::-webkit-scrollbar { display: none; }
        `}} />
        {children}
      </div>

      {/* Right fade + arrow */}
      {canScrollRight && (
        <>
          <div
            className="absolute top-0 bottom-0 right-0 w-16 z-[2] pointer-events-none"
            style={{
              background: "linear-gradient(to left, #f0f2f5, transparent)",
            }}
          />
          <button
            onClick={() => scroll("right")}
            className="absolute right-2 top-1/2 -translate-y-1/2 z-[3] w-10 h-10 rounded-full flex items-center justify-center cursor-pointer border-none"
            style={{
              background: "rgba(255, 255, 255, 0.8)",
              backdropFilter: "blur(12px)",
              boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
              transition: "all 0.2s",
            }}
            aria-label="Scroll right"
          >
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M8 4L14 10L8 16" stroke="#0F1D35" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        </>
      )}
    </div>
  );
}
