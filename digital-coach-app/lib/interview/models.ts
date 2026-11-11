/** Matches mlapi/schemas/interview.py. Backend Pydantic models validate ranges;
 * TypeScript interfaces describe data but do not validate Firestore at runtime.
 */
export interface ICompetencyMetric {
  score: number | null; // 0–10; null means unavailable
  summary: string;
}

export interface IFeedback {
  ai_feedback: string;
  overall_competency: {
    clarity: ICompetencyMetric;
    confidence: ICompetencyMetric;
    engagement: ICompetencyMetric;
    star: ICompetencyMetric;
  };
  sentiment?: string | null; // optional legacy field
}

export interface IMetrics {
  filler_count: number | null; // nonnegative integer
  overall_score: number | null; // 0–100; null if not computable
  wpm: number | null; // nonnegative; requires candidate speaking time
}

export interface IInterviewReport {
  feedback: IFeedback;
  metrics: IMetrics;
}

export interface ISentiments {
  positive: number; // percentage, 0–100
  negative: number;
  neutral: number;
}

export interface IInterview {
  id: string;
  date: string; // MM/DD/YYYY
  timeStarted: string;
  duration: string; // e.g. 10m 43s; total interview time, not candidate speaking time
  feedback?: IFeedback | null;
  metrics?: IMetrics | null;
  transcript?: string[] | string | null;
  sentiment?: string | ISentiments | null;
  url?: string | null;
}
