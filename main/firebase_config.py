import os
import firebase_admin
from firebase_admin import credentials, auth, firestore
import pyrebase
from django.conf import settings
from dotenv import load_dotenv

load_dotenv()

# Firebase Admin SDK Configuration
def initialize_firebase_admin():
    """Initialize Firebase Admin SDK"""
    if not firebase_admin._apps:
        # Use service account key file or environment variables
        if os.path.exists('firebase-service-account.json'):
            cred = credentials.Certificate('firebase-service-account.json')
        else:
            # Use environment variables for production
            cred = credentials.Certificate({
                "type": "service_account",
                "project_id": os.getenv('FIREBASE_PROJECT_ID'),
                "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID'),
                "private_key": os.getenv('FIREBASE_PRIVATE_KEY').replace('\\n', '\n'),
                "client_email": os.getenv('FIREBASE_CLIENT_EMAIL'),
                "client_id": os.getenv('FIREBASE_CLIENT_ID'),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": os.getenv('FIREBASE_CLIENT_CERT_URL')
            })
        
        firebase_admin.initialize_app(cred)
    
    return firebase_admin.get_app()

# Firebase Client SDK Configuration (Pyrebase)
FIREBASE_CONFIG = {
    'apiKey': os.getenv('FIREBASE_API_KEY', 'your-api-key'),
    'authDomain': os.getenv('FIREBASE_AUTH_DOMAIN', 'your-project.firebaseapp.com'),
    'databaseURL': os.getenv('FIREBASE_DATABASE_URL', 'https://your-project-default-rtdb.firebaseio.com/'),
    'projectId': os.getenv('FIREBASE_PROJECT_ID', 'your-project-id'),
    'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET', 'your-project.appspot.com'),
    'messagingSenderId': os.getenv('FIREBASE_MESSAGING_SENDER_ID', 'your-sender-id'),
    'appId': os.getenv('FIREBASE_APP_ID', 'your-app-id')
}

def get_firebase_client():
    """Get Firebase client instance (Pyrebase)"""
    firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
    return firebase

def get_firestore_client():
    """Get Firestore client instance"""
    initialize_firebase_admin()
    return firestore.client()

def get_auth_client():
    """Get Firebase Auth client instance"""
    initialize_firebase_admin()
    return auth

# Initialize Firebase on module import
firebase_app = initialize_firebase_admin()
firebase_client = get_firebase_client()
firestore_db = get_firestore_client()
auth_client = get_auth_client()