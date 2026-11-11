"""Legacy competency formulas adapted to explicit candidate text and timing.

These are heuristic indicators, not measurements of personality or vocal tone.
The caller must exclude interviewer text and supply candidate speaking time,
not the duration of the entire interview.
"""
import math
import re

from schemas.audio import SentimentAnalysisResult
from schemas.feedback import CompetencyFeedback, OverallCompetencyFeedback
from .constants import (
    FILLER_WORDS, HEDGE_PHRASES, FILLER_WEIGHT, HEDGE_WEIGHT,
    FILLER_HEDGE_BUFF, FILLER_HEDGE_SENS, MAX_CONFIDENCE_SCORE,
    MAX_CLARITY_SCORE, MIN_OPTIMAL_WPM, MAX_OPTIMAL_WPM, WPM_PENALTY,
    MAX_ENGAGEMENT_SCORE, BASE_ENGAGEMENT_SCORE, MONOTONE_PENALTY,
    MIN_SENTIMENT_VARIETY_RATIO, SENTIMENT_BONUS_LIMIT,
    SENTIMENT_VARIETY_BONUS_RATIO,
)


def _count_confidence_markers(transcript: str) -> dict[str, int]:
    def count(phrases):
        pattern = r"\b(?:" + "|".join(re.escape(p) for p in sorted(phrases, key=len, reverse=True)) + r")\b"
        return len(re.findall(pattern, transcript, re.IGNORECASE))
    return {"filler_words": count(FILLER_WORDS), "hedge_phrases": count(HEDGE_PHRASES)}


def _minutes(candidate_speaking_seconds: float | None) -> float | None:
    if candidate_speaking_seconds is None:
        return None
    if not math.isfinite(candidate_speaking_seconds) or candidate_speaking_seconds <= 0:
        raise ValueError("Candidate speaking time must be finite and greater than zero.")
    return candidate_speaking_seconds / 60.0


def _analyze_confidence(transcript: str, candidate_speaking_seconds: float | None) -> CompetencyFeedback:
    counts = _count_confidence_markers(transcript)
    minutes = _minutes(candidate_speaking_seconds)
    description = f"Detected {counts['filler_words']} filler words/phrases and {counts['hedge_phrases']} hedge phrases."
    if minutes is None:
        return CompetencyFeedback(score=None, evaluation=description + " A rate-based score requires candidate speaking time.")
    weighted_rate = (counts["filler_words"] * FILLER_WEIGHT + counts["hedge_phrases"] * HEDGE_WEIGHT) / minutes
    deduction = max(0, weighted_rate - FILLER_HEDGE_BUFF) * FILLER_HEDGE_SENS
    return CompetencyFeedback(
        score=round(max(0, MAX_CONFIDENCE_SCORE - deduction), 2),
        evaluation=description + f" Weighted marker rate: {weighted_rate:.1f} per minute. This is a transcript-based indicator, not a direct measure of confidence.",
    )


def _analyze_communication_clarity(transcript: str, candidate_speaking_seconds: float | None) -> CompetencyFeedback:
    minutes = _minutes(candidate_speaking_seconds)
    if minutes is None:
        return CompetencyFeedback(score=None, evaluation="Speech-rate scoring requires candidate speaking time.")
    speech_rate = len(transcript.split()) / minutes
    if MIN_OPTIMAL_WPM <= speech_rate <= MAX_OPTIMAL_WPM:
        score = MAX_CLARITY_SCORE
        advice = "within the configured pacing range"
    elif speech_rate < MIN_OPTIMAL_WPM:
        score = max(0, MAX_CLARITY_SCORE - (MIN_OPTIMAL_WPM - speech_rate) * WPM_PENALTY)
        advice = "below the configured pacing range"
    else:
        score = max(0, MAX_CLARITY_SCORE - (speech_rate - MAX_OPTIMAL_WPM) * WPM_PENALTY)
        advice = "above the configured pacing range"
    return CompetencyFeedback(score=round(score, 2), evaluation=f"Speech rate: {speech_rate:.0f} WPM, {advice}. This measures pacing only.")


def _analyze_engagement(audio_analysis: SentimentAnalysisResult) -> CompetencyFeedback:
    segments = audio_analysis.sentiment_analysis
    if not segments:
        return CompetencyFeedback(score=None, evaluation="No candidate sentiment segments are available.")
    non_neutral_ratio = sum(segment.sentiment != "NEUTRAL" for segment in segments) / len(segments)
    score = BASE_ENGAGEMENT_SCORE
    if non_neutral_ratio < MIN_SENTIMENT_VARIETY_RATIO:
        score -= MONOTONE_PENALTY
    else:
        score += min(non_neutral_ratio / SENTIMENT_VARIETY_BONUS_RATIO, 1) * SENTIMENT_BONUS_LIMIT
    return CompetencyFeedback(
        score=round(min(max(score, 0), MAX_ENGAGEMENT_SCORE), 2),
        evaluation=f"{non_neutral_ratio:.0%} of candidate text segments were classified as non-neutral. This legacy sentiment-based indicator does not measure vocal tone or establish engagement. Keyword bonuses are unavailable.",
    )


def generate_competency_feedback(
    audio_analysis: SentimentAnalysisResult,
    *,
    candidate_transcript: str,
    candidate_speaking_seconds: float | None = None,
) -> OverallCompetencyFeedback:
    """Apply existing formulas without inventing missing timing or keyword data.

    overall_score retains the legacy sum out of 30, only when every component
    is available. Mapping this to the interview report belongs to integration.
    """
    if not candidate_transcript.strip():
        raise ValueError("Candidate transcript must not be empty.")
    clarity = _analyze_communication_clarity(candidate_transcript, candidate_speaking_seconds)
    confidence = _analyze_confidence(candidate_transcript, candidate_speaking_seconds)
    engagement = _analyze_engagement(audio_analysis)
    components = (clarity, confidence, engagement)
    overall = round(sum(item.score for item in components), 2) if all(item.score is not None for item in components) else None
    summary = "Legacy competency indicators (sum out of 30)." if overall is not None else "Overall scoring is unavailable because one or more inputs are missing."
    return OverallCompetencyFeedback(
        communication_clarity=clarity, confidence=confidence, engagement=engagement,
        overall_score=overall,
        summary=summary + "\n" + "\n".join(item.evaluation for item in components),
    )
