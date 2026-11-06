from fastapi import FastAPI, Depends
from services.auth_guard import require_user
from fastapi.middleware.cors import CORSMiddleware
from services.firebase_setup import (
    initialize_firebase,
)  # initialize Firebase connection when backend starts
from routes import (
    jobs,
    create_answer,
    star_feedback,
    audio_analysis,
    heygen,
    assemblyai,
    llm,
    interview,
)
import os

api_description = """
This API provides a simple interface to the various ML models used in Digital Coach. 
## Video Transcript 
AssemblyAI provides the simple transcription service. 
## Feedback
Provided feedback is Star Scores, competency scores, and statistical feedback.  
"""

app = FastAPI(
    title="MLAPI",
    description=api_description,
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://digital-coach-eta.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

@app.on_event("startup")
async def startup_event():
    """
    Handles any setup that needs to occur when the FastAPI server starts, e.g. setting up Firebase Admin SDK.
    """

    # Initializes Firebase Admin SDK
    print("Initializing Firebase Admin SDK...")
    initialize_firebase()
    print("Firebase Admin SDK initialized")


@app.get("/")
def root():
    return {
        "message": "Welcome to the Digital Coach API, please see `/docs` for more information. If you want to access the Redis Queue (RQ) Dashboard to monitor your jobs, please see /rq."
    }


# Redis Queue dashboard and test Firestore routes must not be public.
# Access Redis through private infrastructure instead of exposing /rq.

# Add routes here
app.include_router(jobs.router, dependencies=[Depends(require_user)])
app.include_router(create_answer.router, dependencies=[Depends(require_user)])
app.include_router(star_feedback.router, dependencies=[Depends(require_user)])
app.include_router(audio_analysis.router, dependencies=[Depends(require_user)])
app.include_router(heygen.router, dependencies=[Depends(require_user)])
app.include_router(assemblyai.router, dependencies=[Depends(require_user)])
app.include_router(llm.router, dependencies=[Depends(require_user)])
app.include_router(interview.router, dependencies=[Depends(require_user)])
