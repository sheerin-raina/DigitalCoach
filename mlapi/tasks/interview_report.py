"""Generate and persist a report after sentiment analysis succeeds."""
import os
import re

from openai import OpenAI
from schemas.interview import CompetencyMetric, InterviewReport
from services.firebase_setup import get_firestore_client
from tasks.audio_analysis import detect_audio_sentiment
from tasks.helpers.competency_feedback import generate_competency_feedback, _count_confidence_markers
from tasks.prompts import INTERVIEW_STAR_REPORT_PROMPT


def build_interview_report(sentiment, star: CompetencyMetric) -> InterviewReport:
    # Sentiment segments contain candidate statements selected by the sentiment
    # prompt. Do not count interviewer dialogue or speaker labels as candidate text.
    candidate_text = "\n".join(segment.text for segment in sentiment.sentiment_analysis if segment.text.strip())
    if not candidate_text.strip():
        raise ValueError("No candidate statements were available for the report.")
    competency = generate_competency_feedback(sentiment, candidate_transcript=candidate_text)
    markers = _count_confidence_markers(candidate_text)
    def metric(item):
        return {"score": item.score, "summary": item.evaluation}
    return InterviewReport.model_validate({
        "feedback": {
            "ai_feedback": star.summary + "\n" + competency.summary,
            "overall_competency": {
                "star": star.model_dump(),
                "clarity": metric(competency.communication_clarity),
                "confidence": metric(competency.confidence),
                "engagement": metric(competency.engagement),
            },
        },
        "metrics": {
            "filler_count": markers["filler_words"],
            # Total interview duration is not candidate speaking time. Do not
            # invent WPM, average only available competencies, or use sentiment
            # classification confidence as a performance score.
            "wpm": None,
            "overall_score": None,
        },
    })


async def analyze_interview_report(user_id: str, interview_id: str) -> dict:
    """RQ completes only after validation and Firestore report persistence.

    Sentiment is saved separately by its existing task; if STAR generation or
    report saving fails, the job fails while preserving the saved transcript
    and sentiment for inspection.
    """
    sentiment = await detect_audio_sentiment(user_id, interview_id)
    candidate_text = "\n".join(segment.text for segment in sentiment.sentiment_analysis if segment.text.strip())
    if not candidate_text.strip():
        raise ValueError("No candidate statements were available for STAR analysis.")
    client = OpenAI(base_url=os.getenv("LM_BASE_URL"), api_key=os.getenv("LM_API_KEY"))
    response = client.chat.completions.create(
        model=os.getenv("MODEL"),
        messages=[
            {"role": "system", "content": INTERVIEW_STAR_REPORT_PROMPT},
            {"role": "user", "content": candidate_text},
        ],
    )
    content = (response.choices[0].message.content or "").strip()
    fenced = re.fullmatch(r"```(?:json)?\s*\n?(.*?)\n?```", content, re.DOTALL | re.IGNORECASE)
    if fenced:
        content = fenced.group(1).strip()
    star = CompetencyMetric.model_validate_json(content)
    report = build_interview_report(sentiment, star)
    document = get_firestore_client().collection("users").document(user_id).collection("interviews").document(interview_id)
    payload = report.model_dump(mode="json")
    await document.update(payload)
    return payload
