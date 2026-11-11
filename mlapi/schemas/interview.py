"""
Interview-related schemas
"""

from pydantic import BaseModel, Field


class CompetencyMetric(BaseModel):
    """
    Model that represents a competency metric such as clarity, engagement, or confidence
    """
    score: float | None = Field(..., ge=0, le=10, allow_inf_nan=False) # 0–10; null when unavailable
    summary: str # ai-generated feedback about the user's competency in regards to this metric 
    

class OverallCompetency(BaseModel):
    """
    Model representing the overall competencies that the user will be given feedback on.
    """
    clarity: CompetencyMetric
    confidence: CompetencyMetric
    engagement: CompetencyMetric
    star: CompetencyMetric


class Feedback(BaseModel):
    """
    Model representing the AI-generated feedback which provides overall feedback, clarity of responses, confidence in the responses, how engaging the responses were, and how well they follow the STAR response structure.
    
    (Note: This should match the IFeedback interface in /digital-coach-app/lib/interview/models.ts)
    """
    ai_feedback: str
    overall_competency: OverallCompetency 
    sentiment: str | None = None # optional legacy field; analysis is stored on Interview

class Metrics(BaseModel):
    """
    Metrics based on user's performance during the interview, e.g. how many filler words were detected
    """
    filler_count: int | None = Field(..., ge=0) # null when unavailable
    overall_score: float | None = Field(..., ge=0, le=100, allow_inf_nan=False) # 0–100; no weighting implied
    wpm: float | None = Field(..., ge=0, allow_inf_nan=False) # requires candidate speaking time

class SentimentPercents(BaseModel):
    """
    Model representing the shape of the overall sentiment analysis percentages.
    """
    positive: float = Field(ge=0, le=100, allow_inf_nan=False) # percentage of the responses that were positive sentiment
    negative: float = Field(ge=0, le=100, allow_inf_nan=False) # percentage of the responses that were negative sentiment
    neutral: float = Field(ge=0, le=100, allow_inf_nan=False) # percentage of the responses that were neutral sentiment

class InterviewReport(BaseModel):
    """Validated analysis update; all report fields must be supplied.

    Null scores represent missing evidence, never zero performance. Overall
    score normalization and weighting are the report generator's responsibility.
    """
    feedback: Feedback
    metrics: Metrics


class Interview(BaseModel): 
    """
    Model representing an interview 
    
    (Note: This should match the IInterview interface in /digital-coach-app/lib/interview/models.ts)
    """
    id: str # id for the interview
    date: str # MM/DD/YYYY
    timeStarted: str # HH:MM 12-hour
    duration: str # MMm SSs, e.g. 10m 43s not 0-padded
    feedback: Feedback | None = None
    metrics: Metrics | None = None
    transcript: list[str] | str | None = None # transcript may either be an array of dialogues from avatar and user or a single long string
    sentiment: str | SentimentPercents | None = None
    url: str | None = None # download for user's side of the interview


class CreateInterviewRequest(BaseModel):
    """
    Model representing the shape of the request made from the client to create a new interview document. 
    """
    userId: str # user's id from Firebase Authentication
    interview: Interview # partially filled interview to insert

class CreateInterviewResponse(BaseModel): 
    """
    Model representing the response made after creating a new interview.
    """
    job_id: str = "" # id of the analysis job started on the interview
    success: bool

class AnalyzeInterviewRequest(BaseModel):
    """
    Model representing the shape for requesting an analysis of an interview which includes tasks like sentiment analysis and feedback generation.
    """
    user_id: str
    interview_id: str

class GetInterviewRequest(BaseModel):
    """
    Model representing the shape of the request made from the client to retrieve an interview document.
    """
    userId: str # user's id from Firebase Authentication
    interviewId: str # interview id

class GetInterviewResponse(BaseModel):
    """
    Model representing the response made from retrieving an interview.
    """
    interview: Interview | None
