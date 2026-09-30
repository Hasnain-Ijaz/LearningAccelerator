import pyrebase
import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st

# Your exact Firebase Web Configuration
firebase_config = {
    "apiKey": "AIzaSyDquk8cNPkQ2onzVlgzhriwm_LS8jHMdhY",
    "authDomain": "learningaccelerator-61452.firebaseapp.com",
    "projectId": "learningaccelerator-61452",
    "storageBucket": "learningaccelerator-61452.firebasestorage.app",
    "messagingSenderId": "700119982345",
    "appId": "1:700119982345:web:b170ac89d94a29924cb3d8",
    "databaseURL": ""
}

# Initialize Pyrebase for User Authentication (Signup / Login)
try:
    firebase = pyrebase.initialize_app(firebase_config)
    auth = firebase.auth()
except Exception as e:
    auth = None

# Initialize Firebase Admin for Firestore Database operations
if not firebase_admin._apps:
    try:
        if "firebase" in st.secrets:
            cred_dict = dict(st.secrets["firebase"])
            cred = credentials.Certificate(cred_dict)
        else:
            cred = credentials.Certificate("firebase_credentials.json")
        firebase_admin.initialize_app(cred)
    except Exception as e:
        print(f"Firebase Admin Error: {e}")

db = firestore.client() if firebase_admin._apps else None

# --- Core Database & Auth Functions ---

def sign_up(email, password, name, student_id, department):
    """Register a new student account using Firebase Auth and store profile in Firestore."""
    if not auth:
        return False, "Pyrebase auth not initialized."
    try:
        user = auth.create_user_with_email_and_password(email, password)
        user_id = user['localId']
        if db:
            db.collection("users").document(user_id).set({
                "uid": user_id,
                "name": name,
                "email": email,
                "student_id": student_id,
                "department": department
            })
        return True, user
    except Exception as e:
        return False, str(e)

def sign_in(email, password):
    """Authenticate existing student and fetch profile details from Firestore."""
    if not auth:
        return False, "Pyrebase auth not initialized."
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        user_id = user['localId']
        
        name, student_id, department = "Student", "STU-2024-042", "Computer Science"
        if db:
            user_info = db.collection("users").document(user_id).get().to_dict()
            if user_info:
                name = user_info.get('name', 'Student')
                student_id = user_info.get('student_id', 'STU-2024-042')
                department = user_info.get('department', 'Computer Science')
                
        return True, {
            "localId": user_id,
            "email": email,
            "name": name,
            "student_id": student_id,
            "department": department
        }
    except Exception as e:
        return False, "Invalid email or password"

def save_document_record(uid, filename, file_size):
    """Save uploaded document metadata to user's Firestore subcollection."""
    if db:
        try:
            doc_ref = db.collection("users").document(uid).collection("documents").document()
            doc_ref.set({
                "id": doc_ref.id,
                "filename": filename,
                "size": file_size,
                "upload_date": firestore.SERVER_TIMESTAMP
            })
        except Exception:
            pass

def delete_document_record(uid, doc_id):
    """Delete a document record from Firestore."""
    if db:
        try:
            db.collection("users").document(uid).collection("documents").document(doc_id).delete()
        except Exception:
            pass

def get_user_documents(uid):
    """Retrieve all uploaded document records for the specific user from Firestore."""
    if db:
        try:
            docs_ref = db.collection("users").document(uid).collection("documents").order_by("upload_date", direction=firestore.Query.DESCENDING).stream()
            return [{"id": d.id, **d.to_dict()} for d in docs_ref]
        except Exception:
            return []
    return []