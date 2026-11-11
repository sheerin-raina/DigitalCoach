"""
Handles setting the connection to Firebase services either emulators or production.
"""

import json
import firebase_admin
from firebase_admin import firestore, firestore_async, credentials, auth
from google.cloud import firestore as google_firestore  # ADDED 10/20/26 - Marko
import os
from dotenv import load_dotenv
from utils.logger_config import get_logger

logger = get_logger(__name__)  # create logging instance to view outputs on Docker


def initialize_firebase():
    """
    Initializes Firebase Admin SDK.
    Supports:
    - Local Docker using GOOGLE_APPLICATION_CREDENTIALS file path
    - Render using FIREBASE_ADMIN_JSON environment variable
    """

    if firebase_admin._apps:
        return firebase_admin.get_app()

    load_dotenv()

    projectId = os.getenv("GCLOUD_PROJECT", "digitalcoach-31674")

    firebase_json = os.getenv("FIREBASE_ADMIN_JSON")

    if firebase_json:
        # Production (Render)
        logger.info("Using Firebase credentials from FIREBASE_ADMIN_JSON")

        cred = credentials.Certificate(json.loads(firebase_json))

        return firebase_admin.initialize_app(cred, options={"projectId": projectId})

    # Local Docker
    service_account_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    logger.info(f"Checking {service_account_path} for service account credentials.")

    if service_account_path and os.path.exists(service_account_path):
        logger.info("Found service account file!")

        cred = credentials.Certificate(service_account_path)

        return firebase_admin.initialize_app(cred, options={"projectId": projectId})

    # Last resort (Google default credentials)
    logger.warning("No Firebase credentials found. Attempting default credentials.")

    return firebase_admin.initialize_app()


def get_firestore_client():
    """Return an async Firestore client for local or production use."""
    load_dotenv()

    if os.getenv("FIRESTORE_EMULATOR_HOST"):
        project_id = os.getenv("GCLOUD_PROJECT", "digitalcoach-31674")

        return google_firestore.AsyncClient(project=project_id)

    initialize_firebase()
    return firestore_async.client()

# def get_firestore_client():
#     """
#     Initializes Firebase Admin SDK and then returns Firestore asynchronous client, i.e. connection to firestore database.
#     """
#     initialize_firebase()
#     return firestore_async.client()


def get_auth_client():
    """
    Initializes Firebase Admin SDK and returns authentication instance (handles Authentication operations)
    """
    initialize_firebase()
    return auth
