"use client";

import { useState } from "react";
import type { QuizQuestion } from "@/lib/types";

interface QuizProps {
  questions: QuizQuestion[];
  title: string;
  accentColor?: string;
  onComplete?: (score: number, total: number, answers: { questionId: string; selected: number; correct: boolean }[]) => void;
}

export function Quiz({ questions, title, accentColor = "#059669", onComplete }: QuizProps) {
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [revealed, setRevealed] = useState<Record<string, boolean>>({});
  const [completed, setCompleted] = useState(false);

  const answeredCount = Object.keys(answers).length;
  const allAnswered = answeredCount === questions.length;

  function handleSelect(questionId: string, optionIndex: number) {
    if (revealed[questionId]) return;
    setAnswers((prev) => ({ ...prev, [questionId]: optionIndex }));
    setRevealed((prev) => ({ ...prev, [questionId]: true }));
  }

  function handleFinish() {
    const results = questions.map((q) => ({
      questionId: q.id,
      selected: answers[q.id] ?? -1,
      correct: answers[q.id] === q.correct,
    }));
    const score = results.filter((r) => r.correct).length;
    setCompleted(true);
    console.log("Quiz complete:", { score, total: questions.length });
    onComplete?.(score, questions.length, results);
  }

  const score = questions.filter((q) => answers[q.id] === q.correct).length;

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <div
          className="font-extrabold"
          style={{ fontSize: "22px", color: "#0F1D35" }}
        >
          {title}
        </div>
        <div
          className="text-xs font-bold px-2.5 py-1 rounded-full"
          style={{
            background: `${accentColor}15`,
            color: accentColor,
            border: `1px solid ${accentColor}30`,
          }}
        >
          {questions.length} questions
        </div>
      </div>

      <div className="space-y-5">
        {questions.map((q, qIdx) => {
          const isRevealed = revealed[q.id];
          const selected = answers[q.id];

          return (
            <div
              key={q.id}
              className="rounded-xl"
              style={{
                padding: "20px 24px",
                background: "rgba(255, 255, 255, 0.5)",
                backdropFilter: "blur(16px) saturate(1.6)",
                border: "1px solid rgba(255, 255, 255, 0.55)",
                boxShadow:
                  "0 1px 2px rgba(0, 0, 0, 0.03), 0 4px 16px rgba(0, 0, 0, 0.04), inset 0 1px 0 rgba(255, 255, 255, 0.6)",
              }}
            >
              <div
                className="font-semibold mb-3"
                style={{ fontSize: "16px", color: "#0F1D35" }}
              >
                <span style={{ color: accentColor, marginRight: "8px" }}>
                  {qIdx + 1}.
                </span>
                {q.question}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {q.options.map((opt, oIdx) => {
                  let bg = "rgba(255, 255, 255, 0.6)";
                  let borderColor = "rgba(0, 0, 0, 0.08)";
                  let textColor = "#374151";

                  if (isRevealed) {
                    if (oIdx === q.correct) {
                      bg = "rgba(5, 150, 105, 0.12)";
                      borderColor = "rgba(5, 150, 105, 0.4)";
                      textColor = "#065f46";
                    } else if (oIdx === selected && oIdx !== q.correct) {
                      bg = "rgba(220, 38, 38, 0.1)";
                      borderColor = "rgba(220, 38, 38, 0.35)";
                      textColor = "#991b1b";
                    }
                  }

                  return (
                    <button
                      key={oIdx}
                      onClick={() => handleSelect(q.id, oIdx)}
                      disabled={isRevealed}
                      className="text-left rounded-lg transition-all duration-200"
                      style={{
                        padding: "10px 14px",
                        fontSize: "14px",
                        background: bg,
                        border: `1.5px solid ${borderColor}`,
                        color: textColor,
                        cursor: isRevealed ? "default" : "pointer",
                        fontWeight: isRevealed && oIdx === q.correct ? 600 : 400,
                      }}
                      onMouseEnter={(e) => {
                        if (!isRevealed) {
                          e.currentTarget.style.background = `${accentColor}10`;
                          e.currentTarget.style.borderColor = `${accentColor}40`;
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (!isRevealed) {
                          e.currentTarget.style.background = bg;
                          e.currentTarget.style.borderColor = borderColor;
                        }
                      }}
                    >
                      <span
                        className="inline-block font-semibold mr-2"
                        style={{ color: isRevealed && oIdx === q.correct ? "#059669" : "#94a3b8", minWidth: "18px" }}
                      >
                        {String.fromCharCode(65 + oIdx)}.
                      </span>
                      {opt}
                    </button>
                  );
                })}
              </div>

              {isRevealed && (
                <div
                  className="mt-3 rounded-lg"
                  style={{
                    padding: "12px 16px",
                    fontSize: "14px",
                    lineHeight: "1.5",
                    background: selected === q.correct ? "rgba(5, 150, 105, 0.06)" : "rgba(220, 38, 38, 0.05)",
                    border: `1px solid ${selected === q.correct ? "rgba(5, 150, 105, 0.15)" : "rgba(220, 38, 38, 0.12)"}`,
                    color: "#475569",
                  }}
                >
                  <span className="font-semibold" style={{ color: selected === q.correct ? "#059669" : "#dc2626" }}>
                    {selected === q.correct ? "Correct!" : "Not quite."}
                  </span>{" "}
                  {q.explanation}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Score / Finish */}
      {allAnswered && !completed && (
        <div className="mt-6 text-center">
          <button
            onClick={handleFinish}
            className="rounded-xl font-bold transition-all duration-200"
            style={{
              padding: "14px 32px",
              fontSize: "16px",
              background: accentColor,
              color: "#fff",
              border: "none",
              cursor: "pointer",
              boxShadow: `0 4px 14px ${accentColor}40`,
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = "translateY(-2px)";
              e.currentTarget.style.boxShadow = `0 6px 20px ${accentColor}50`;
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = "translateY(0)";
              e.currentTarget.style.boxShadow = `0 4px 14px ${accentColor}40`;
            }}
          >
            See Your Score
          </button>
        </div>
      )}

      {completed && (
        <div
          className="mt-6 rounded-2xl text-center"
          style={{
            padding: "28px 24px",
            background: "rgba(255, 255, 255, 0.55)",
            backdropFilter: "blur(16px) saturate(1.6)",
            border: "1px solid rgba(255, 255, 255, 0.55)",
            boxShadow:
              "0 1px 2px rgba(0, 0, 0, 0.03), 0 4px 16px rgba(0, 0, 0, 0.04), inset 0 1px 0 rgba(255, 255, 255, 0.6)",
          }}
        >
          <div
            className="font-extrabold mb-2"
            style={{ fontSize: "36px", color: accentColor }}
          >
            {score}/{questions.length}
          </div>
          <div style={{ fontSize: "16px", color: "#475569" }}>
            {score === questions.length
              ? "Perfect score! You clearly know your stuff."
              : score >= questions.length * 0.6
              ? "Solid performance. You have a strong grasp of the material."
              : "Good effort. Review the explanations above to strengthen your knowledge."}
          </div>
        </div>
      )}
    </div>
  );
}
