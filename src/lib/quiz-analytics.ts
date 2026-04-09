import { supabase } from './supabase';

interface QuizAnswer {
  question_id: string;
  selected: number;
  correct: boolean;
}

export async function submitQuizResult(
  quizSlug: string,
  score: number,
  totalQuestions: number,
  answers: QuizAnswer[]
) {
  // Generate or retrieve anonymous session ID (no PII)
  let sessionId = typeof window !== 'undefined'
    ? sessionStorage.getItem('quiz_session_id')
    : null;

  if (!sessionId) {
    sessionId = crypto.randomUUID();
    if (typeof window !== 'undefined') {
      sessionStorage.setItem('quiz_session_id', sessionId);
    }
  }

  const { error } = await supabase.from('quiz_attempts').insert({
    quiz_slug: quizSlug,
    score,
    total_questions: totalQuestions,
    answers,
    session_id: sessionId,
  });

  if (error) {
    console.error('Failed to submit quiz result:', error.message);
    // Don't throw — quiz UX should not break if analytics fail
  }
}
