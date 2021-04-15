import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("shaala-loka-firebase-adminsdk-xsp4x-5eea3da522.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

status = False

data = {
    'approval_status': status,
    'department': 'CSE',
    'designation': 'Prof',
    'email_id': 'tom@jssateb.ac.in',
    'instructor_id': '1JS001',
    'instructor_name': 'Tom',
    'org_id': '1JS',
    'password': 'tom123'
}

docref = db. collection('Organization').document(data['org_id']).collection('Instructor').document(data['instructor_id'])

docref.set(data)