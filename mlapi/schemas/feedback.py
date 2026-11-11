"""
User's Performance Feedback Schemas
"""

from pydantic import BaseModel, Field
from typing import List
from schemas.jobs import JobStatus

class CompetencyFeedback(BaseModel):
    """
    Feedback for a specific competency
    """

    score: float | None = Field(..., ge=0, le=10, allow_inf_nan=False) # unavailable without evidence
    evaluation: str # States whether or not the user was compotent in some field 

class OverallCompetencyFeedback(BaseModel):
    """
    Overall Competency Feedback
    """

    communication_clarity: CompetencyFeedback  # Evaluation on communication clarity
    confidence: CompetencyFeedback # Evaluation on confidence
    engagement: CompetencyFeedback # Evaluation on engagement
    overall_score: float | None = Field(..., ge=0, le=30, allow_inf_nan=False) # legacy sum, not normalized report score
    summary: str # Summary of overall performance including evaluations for individual competencies


class StarFeedbackRequest(BaseModel):
    """
    Request model for STAR feedback
    """
    
    text: str

class StarClassification(BaseModel):
    """
    Classification result for a single sentence
    """

    sentence: str
    category: str


class StarPercentages(BaseModel):
    """
    Percentage breakdown of STAR components
    """

    action: float
    result: float
    situation: float
    task: float


class StarFeedbackEvaluation(BaseModel):
    """
    Results after performing STAR feedback analysis
    """

    fulfilled_star: bool
    percentages: StarPercentages
    classifications: List[StarClassification]
    feedback: List[str]

class StarFeedbackResponse(BaseModel):
    """
    Response model for STAR feedback job
    """

    job_id: str
    status: JobStatus
    result: StarFeedbackEvaluation | None = None
    error: str | None = None