"""
Routes for HeyGen related services like starting a session with an avatar.
"""
from fastapi import APIRouter, HTTPException
from schemas import HeyGenSessionRequest, HeyGenSessionResponse
from utils.logger_config import get_logger
import requests
from dotenv import load_dotenv
import os

logger = get_logger(__name__) # create a logger instance to log messages

router = APIRouter(prefix="/api/heygen", tags=["interview"])

# POST /api/heygen/start
@router.post(
    "/start",
    response_model=HeyGenSessionResponse,
    summary="Start interview session by getting session token and joining session room.",
    description="Starts interview with AI avatar."
    )
async def start_interview(configs: HeyGenSessionRequest):
    """
    Creates session token for end user based on provided session configurations for how the avatar looks, how it sounds, and what's its knowledge base.

    Args:
        avatar_id (str): ID for one of HeyGen LiveAvatar's avatars to choose what it looks like.
        voice_id (str): ID for one of HeyGen LiveAvatar's voices to choose how it sounds like.
        context_id (str): ID for Context created in HeyGen LiveAvatar to choose how the avatar behaves and what it knows.
        is_sandbox (bool): HeyGen LiveAvatar has a sandbox mode so the developer can test without using credits under strict session configurations. 

    Returns:
        HeyGenSessionResponse: Response model that contains the URL to connect to the created HeyGen LiveAvatar session.

    Raises:
        KeyError: If the HeyGen LiveAvatar API key is missing.
        ValueError: If the session configuration settings are invalid.
    """
    # URL to send to request to get session token from HeyGen LiveAvatar
    url = "https://api.liveavatar.com/v1/sessions/token"

    # Session configuration
    payload = {
        "mode": "FULL", # LiveAvatar has two modes FULL or CUSTOM
        "avatar_id": configs.avatar_id, 
        "is_sandbox": configs.is_sandbox,
        "avatar_persona": {
            "voice_id": configs.voice_id,
            "context_id": configs.context_id,
            "language": "en" # LiveAvatar supports other language but we assume that the interaction will be in English 
        }
    }
    logger.info("Attempting to retrieve HeyGen session token.")

    # Attempt to get session token
    try:
        # load variables from .env
        load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "digital-coach-app", ".env"))
        # get LiveAvatar API key
        api_key = os.getenv("HEYGEN_LIVEAVATAR_API")
        if not api_key: 
            raise KeyError("HEYGEN_LIVEAVATAR_API key not found in .env file.")
        
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "X-API-KEY": api_key,
        }

        # Debug session configuration
        # print(f"Payload: {payload}")
        # print(f"Headers: {headers}")

        # Send request to HeyGen LiveAvatar
        print("Getting Session Token...")
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            raise ValueError(f"Failed to create session token: {response.json()['message']}")

        # print(response.text)
        session_token = response.json()["data"]["session_token"] 

    except KeyError as e:
        logger.error(f"Can't start HeyGen session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error starting HeyGen session: {str(e)}")
    except ValueError as e:
        logger.error(f"Failed to retrieve session token: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to retrieve session token: {str(e)}")
    
    url = "https://api.liveavatar.com/v1/sessions/start"
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {session_token}"
    }

    logger.info("Attempting to start HeyGen sessions.")
    # Attempt to start session
    try:
        response = requests.post(url, headers=headers)
        if response.status_code != 201:
            raise ValueError(f"Failed to start HeyGen session: {response.json()['message']}")
        
        # Construct url for client to join session with avatar
        livekit_url= response.json()["data"]["livekit_url"]
        livekit_client_token = response.json()["data"]["livekit_client_token"]
        
        session_url = f"https://meet.livekit.io/custom?liveKitUrl={livekit_url}&token={livekit_client_token}"
    except ValueError as e:
        logger.error(f"Failed to start HeyGen session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start HeyGen session: {str(e)}")
    
    logger.info(f"HeyGen session URL: {session_url}")
    
    return HeyGenSessionResponse(session_url=session_url)

@router.get(
    "/session_token",
    summary="Requests a session token from HeyGen's LiveAvatar API.",
    description="Gets a session token from HeyGen's LiveAvatar API."
) 
async def get_session_token():
    """
    Creates session token for end user based on predefined session configurations for how the avatar looks, how it sounds, and what's its knowledge base. You can create new context within HeyGen's LiveAvatar API website: https://app.liveavatar.com/home

    Returns:
        session_token (str): String containing the session token for a HeyGen LiveAvatar session.

    Raises:
        KeyError: If the HeyGen LiveAvatar API key is missing.
        ValueError: If the session configuration settings are invalid.
    """
    # URL to send to request to get session token from HeyGen LiveAvatar
    url = "https://api.liveavatar.com/v1/sessions/token"

    # default session configuration
    interviewConfig = {
    #   "avatar_id": "dd73ea75-1218-4ef3-92ce-606d5f7fbc0a", # ID for one of HeyGen LiveAvatar's avatars to choose what it looks like.
      "avatar_id": "65f9e3c9-d48b-4118-b73a-4ae2e3cbb8f0",
      "voice_id": "62bbb4b2-bb26-4727-bc87-cfb2bd4e0cc8", # ID for one of HeyGen LiveAvatar's voices to choose how it sounds like.
      #"context_id": "e6a7bbca-1ac1-4a2f-b0f0-f6cfce199b97", # ID for Context created in HeyGen LiveAvatar to choose how the avatar behaves and what it knows. # old context: "595268c3-a4cf-499d-bf85-efd006fe8a47" 
      "context_id": "609a5458-39e1-4f26-a283-f56fb75ed5d6",
      "is_sandbox": True # HeyGen LiveAvatar has a sandbox mode so the developer can test without using credits under strict session configurations. (Only a subset of avatars are available in sandbox mode)
    }

    # Session configuration
    payload = {
        "mode": "FULL", # LiveAvatar has two modes FULL or CUSTOM
        "avatar_id": interviewConfig["avatar_id"], 
        "is_sandbox": interviewConfig["is_sandbox"],
        "avatar_persona": {
            "voice_id": interviewConfig["voice_id"],
            "context_id": interviewConfig["context_id"],
            "language": "en" # LiveAvatar supports other language but we assume that the interaction will be in English 
        }
    }
    logger.info("Attempting to retrieve HeyGen session token.")

    # Attempt to get session token
    try:
        # load variables from .env
        load_dotenv()
        # get LiveAvatar API key
        api_key = os.getenv("HEYGEN_LIVEAVATAR_API")
        if not api_key: 
            raise KeyError("HEYGEN_LIVEAVATAR_API key not found in .env file.")
        
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "X-API-KEY": api_key,
        }

        # Debug session configuration
        # print(f"Payload: {payload}")
        # print(f"Headers: {headers}")

        # Send request to HeyGen LiveAvatar
        print("Getting Session Token...")
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            raise ValueError(f"Failed to create session token: {response.json()['message']}")

        # print(response.text)
        session_token = response.json()["data"]["session_token"] 

        return session_token
    except KeyError as e:
        logger.error(f"Can't start HeyGen session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error starting HeyGen session: {str(e)}")
    except ValueError as e:
        logger.error(f"Failed to retrieve session token: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to retrieve session token: {str(e)}")