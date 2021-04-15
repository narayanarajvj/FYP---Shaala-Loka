import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("shaala-loka-firebase-adminsdk-xsp4x-5eea3da522.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

status = False

data = {
    'approval_status': status,
    'level': 4,
    'section': 'A',
    'email_id': 'jerry@jssateb.ac.in',
    'student_id': '1JS17CS420',
    'student_name': 'Jerry',
    'org_id': '1JS',
    'password': 'jerry123'
}

docref = db. collection('Organization').document(data['org_id']).collection('Student').document(data['student_id'])

docref.set(data)