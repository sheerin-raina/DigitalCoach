from fastapi import APIRouter
from utils.logger_config import get_logger
from schemas import (
    CreateInterviewResponse,
    CreateInterviewRequest,
    AnalyzeInterviewRequest,
    GetInterviewRequest,
    GetInterviewResponse,
)
from services.firebase_setup import get_firestore_client
from fastapi import HTTPException
from fastapi.responses import FileResponse
import os

logger = get_logger(__name__)  # create a logger instance to log messages

router = APIRouter(prefix="/api/interview", tags=["interview"])
from services.orchestrator import start_interview_analysis


# POST /api/interview
@router.post(
    "/",
    response_model=CreateInterviewResponse,
    summary="Create partially populated interview given after user finishes their interview.",
    description="Creates interview document populated with initial data from user's interview before it gets analyzed.",
)
async def create_interview(request: CreateInterviewRequest):
    logger.info(
        f"Attempting to create new interview document for user={request.userId}..."
    )
    try:
        db = get_firestore_client()
        # convert interview pydantic object into a dictionary
        interview = request.interview.model_dump()

        BASE_URL = os.getenv("BACKEND_URL")

        video_download_url = f"{BASE_URL}/api/interview/download/{interview['id']}"
        interview["url"] = video_download_url

        # get reference to user's interview collection
        interviewRef = (
            db.collection("users").document(request.userId).collection("interviews")
        )

        # add interview document to user's interview using the given interview id
        await interviewRef.document(interview["id"]).set(interview)

        logger.info("Inserted new interview!")

        logger.info(f"Starting analysis on interview={interview['id']}")
        # Start analysis jobs on interview
        analysisRequest = AnalyzeInterviewRequest(
            user_id=request.userId, interview_id=interview["id"]
        )
        try:
            job_id = start_interview_analysis(analysisRequest)
        except Exception:
            logger.exception("Interview saved, but analysis could not be queued")
            return CreateInterviewResponse(success=True)

        return CreateInterviewResponse(job_id=job_id, success=True)
    except Exception as e:
        logger.exception("Failed to create interview")
        raise HTTPException(status_code=500, detail="Unable to save interview.") from e


# GET /api/interview
@router.get(
    "/",
    response_model=GetInterviewResponse,
    summary="Get interview document given user and interview id.",
    description="Retrieves an interview document with a given id from a user with a given id.",
)
async def get_interview(userId: str, interviewId: str):
    db = get_firestore_client()
    logger.info(
        f"Attempting to retrieve interview document with id {interviewId} from user={userId}..."
    )
    try:
        interview = await (
            db.collection("users")
            .document(userId)
            .collection("interviews")
            .document(interviewId)
            .get()
        )
        logger.info("Retrieved interview!")
        return GetInterviewResponse(interview=interview.to_dict() if interview.exists else None)
    except Exception as e:
        logger.info(f"Failed to retrieve interview: {e}")
        return GetInterviewResponse(interview=None)


@router.get(
    "/download/{interview_id}",
    summary="Download user's interview file",
    description="Returns the audio/video file for a given interview id so the user can download it.",
)
async def download_interview(interview_id: str):
    """
    Args:
        user_id: ID of the user
        interview_id: ID of the interview

    Returns:
        FileResponse: Downloadable interview file
    """
    # Path where interviews are stored
    file_path = os.path.join("mlapi/data/interviews", f"{interview_id}.mp4")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Interview file not found")

    return FileResponse(
        path=file_path, filename=f"{interview_id}.mp4", media_type="video/mp4"
    )
