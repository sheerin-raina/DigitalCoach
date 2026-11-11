from schemas import (
    SentimentAnalysisResult,
)
from utils.logger_config import get_logger
import os
from openai import OpenAI
from pydantic import ValidationError
from dotenv import load_dotenv
from data.interviews import getTranscriptById
from services.firebase_setup import get_firestore_client
from tasks.prompts import SENTIMENT_ANALYSIS_PROMPT
import json
import re
logger = get_logger(__name__)

def parse_sentiment_response(content: str) -> SentimentAnalysisResult:
    """Accept raw JSON or a single Markdown-fenced JSON response."""
    content = content.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*\n?(.*?)\n?```", content, re.DOTALL | re.IGNORECASE)
    if fenced:
        content = fenced.group(1).strip()
    return SentimentAnalysisResult.model_validate_json(content)

load_dotenv() # load environment variables
async def detect_audio_sentiment(user_id: str, interview_id: str) -> SentimentAnalysisResult:
    """
    Generate audio sentiment analysis using local LLM. This should be a job performed by a Redis RQ Worker.

    Args:
        user_id (str): User id that owns the interview to be analyzed.
        interview_id (str): Id of the interview undergoing sentiment analysis
    Returns:
        result (SentimentAnalysisResult): Sentiment analysis results according to SentimentAnalysisResult schema
    """

    logger.info(f"Starting sentiment analysis on interview={interview_id}...")

    # extract relevant environment variables
    base_url = os.getenv("LM_BASE_URL")
    api_key = os.getenv("LM_API_KEY")
    model_name = os.getenv("MODEL")
    # initialize OpenAI-compliant LLM client
    client = OpenAI(base_url=base_url, api_key=api_key)

    # get interview's transcript
    transcript = await getTranscriptById(user_id, interview_id)
    if isinstance(transcript, list):
        transcript = "\n".join(transcript)
    transcript = (transcript or "").replace("\\n", "\n").strip()
    if not transcript:
        raise ValueError("The interview was saved without a transcript to analyze.")

    # initialize messages for LLM 
    # system messages provide additional context to the LLM
    # user messages are the messages the LLM actually responds to
    model_messages = [
                {
                    "role": "system",
                    "content": SENTIMENT_ANALYSIS_PROMPT
                },
                {
                    "role": "user",
                    "content": transcript # pass the transcript to the LLM for sentiment analysis
                }
            ]
    try:
        response = client.chat.completions.create(
            model=model_name, # llm model name from docker model runner (you can find this by running `docker model list` in your CMD)
            messages = model_messages,
        )

    except Exception as e:
        logger.error(f"Error communicating with LLM: {e}")
        logger.error(f"Sentiment analysis for interview={interview_id} failed.")
        # return SentimentAnalysisResult(error=f"Error communicating with LLM: {e}")
        raise
    
    db = get_firestore_client()
    # parse and return LLM response
    try:
        logger.info(f"Verifying LLM sentiment analysis on interview={interview_id}...")

        llm_response = response.choices[0].message.content # extract LLM's JSON response string
        
        # verify LLM JSON response is the correct shape 
        if not llm_response:
            raise ValueError("The model returned an empty analysis response.")
        validated_data = parse_sentiment_response(llm_response)
        logger.info(f"Sentiment Analysis on interview={interview_id} successful!")

        # add sentiment analysis to user's interview as a JSON string to be parsed later and converted into an overall sentiment
        # get reference to interview
        interviewRef = db.collection("users").document(user_id).collection("interviews").document(interview_id)
        await interviewRef.update({"sentiment": validated_data.model_dump_json()})

        return validated_data
    except ValidationError as e:
        logger.error(f"LLM sentiment analysis on interview={interview_id} is in invalid shape. Reason: {e}")
        # return SentimentAnalysisResult(error=f"LLM sentiment analysis on interview={interview_id} is in invalid shape. Reason: {e}")
        raise
