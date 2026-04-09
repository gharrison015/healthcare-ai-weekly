"use client";

import { Quiz } from "@/components/quiz";
import { submitQuizResult } from "@/lib/quiz-analytics";
import type { QuizQuestion } from "@/lib/types";

interface QuizWrapperProps {
  questions: QuizQuestion[];
  title: string;
  slug: string;
  accentColor?: string;
}

export function QuizWrapper({ questions, title, slug, accentColor }: QuizWrapperProps) {
  const handleComplete = (score: number, total: number, answers: { questionId: string; selected: number; correct: boolean }[]) => {
    submitQuizResult(slug, score, total, answers.map(a => ({
      question_id: a.questionId,
      selected: a.selected,
      correct: a.correct,
    })));
  };

  return (
    <Quiz
      questions={questions}
      title={title}
      accentColor={accentColor}
      onComplete={handleComplete}
    />
  );
}
