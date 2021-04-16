import firebase_admin
from firebase_admin import credentials, firestore
import EmailAlert

cred = credentials.Certificate("shaala-loka-firebase-adminsdk-xsp4x-5eea3da522.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

id = '1JS17CS420'
org_id = '1JS'
role = ''
password = 'jerry123'
email_id = "anaghakswamy14@gmail.com"

docref_ins = db.collection('Organization').document(org_id).collection('Instructor').where('instructor_id', '==', id).get()

docref_stud = db.collection('Organization').document(org_id).collection('Student').where('student_id', '==', id).get()

if docref_ins:
    for doc in docref_ins:
        if not doc.to_dict()['approval_status']:
            doc_id = doc.id
            db.collection('Organization').document(org_id).collection('Instructor').document(doc_id).update(
                {'approval_status': True})
        role = "Instructor"
elif docref_stud:
    for doc in docref_stud:
        if not doc.to_dict()['approval_status']:
            doc_id = doc.id
            db.collection('Organization').document(org_id).collection('Student').document(doc_id).update(
                {'approval_status': True})
        role = "Student"

if role:
    data = {
        'id': id,
        'password': password,
        'role': role
    }

    docref = db.collection('Login').document(data['id'])

    docref.set(data)

    EmailAlert.email_alert("Profile Authentication", "Your Organization have successfully authenticated your account "
                                                     f"(id: {id}). You can Login from now onwards.", email_id)
