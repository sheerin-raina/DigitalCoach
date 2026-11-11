from schemas.create_answer import (
    CreateAnswerEvaluation,
    CreateAnswerJobResponse,
)

from schemas.feedback import OverallCompetencyFeedback

# Redis
from redisStore.myconnection import get_redis_con
from redisStore.queue import add_task_to_queue

# Functions
from tasks.audio_analysis import detect_audio_sentiment
from tasks.helpers.create_answer_helpers import compute_overall_score
from tasks.helpers.av_processing import (
    calculate_overall_audio_sentiment,
    # grab_top_five_keywords,
)
from redisStore.myconnection import get_redis_con
from tasks.helpers.competency_feedback import generate_competency_feedback
from utils.logger_config import get_logger
from rq.job import Job

logger = get_logger(__name__)


def create_answer(
    video_url: str,
    audio_job_id: str,
) -> CreateAnswerEvaluation:
    """
    Compute metrics for feedback based on results of audio analysis (can be extended in the future for facial analysis).

    Args:
        video_url (str): URL or path to the video file
        audio_job_id (str): Job ID for audio analysis

    Returns:
        CreateAnswer (CreateAnswerEvaluation): Complete analysis result
    """

    # Get the analysis job results
    # We can assume the analysis jobs are finished since this job is dependent on them

    try:
        audio_job = Job.fetch(audio_job_id, connection=get_redis_con())
        audio_result = audio_job.result

        if not audio_result:
            raise ValueError(f"Audio job {audio_job_id} has no result.")

    except Exception as e:
        logger.error(f"Failed to fetch audio job results: {str(e)}")
        raise e
    
    logger.info(f"Starting performance report for video URL: {video_url}")

    ### Process analysis results ### 

    # Compute audio sentiment analysis scores

    # Compute the STAR score for the response
    
    # Compute filler words
    
    # Compute pacing (WPM)       

    # Compute top five keywords from audio (may be used in feedback)


    # Generate competency feedback
    competency_feedback: OverallCompetencyFeedback = generate_competency_feedback(
        audio_result,
        candidate_transcript=" ".join(segment.text for segment in audio_result.sentiment_analysis),
    )


    # Build evaluation result
    evaluation = CreateAnswerEvaluation(
        # isStructured=text_answer.binary_prediction,
        predictionScore=0, # placeholder 
        overallSentiment=calculate_overall_audio_sentiment(audio_result),
        # topFiveKeywords=grab_top_five_keywords(audio_result),
        transcript="",
        competencyFeedback=competency_feedback,
    )

    # Calculate aggregate score
    evaluation.aggregateScore = compute_overall_score(evaluation)

    # Return final result
    return CreateAnswerJobResponse(
    job_id="",
    status="completed",
    result=evaluation,
    error=None
)
