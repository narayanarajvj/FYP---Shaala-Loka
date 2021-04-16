import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("shaala-loka-firebase-adminsdk-xsp4x-5eea3da522.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

id = '1JS'
password = 'jss123'

docref = db.collection('Login').where('id', '==', id).where('password', '==', password).get()

for doc in docref:
    if doc.to_dict()['id'] and doc.to_dict()['password']:
        print('Login Successfully')
        role = doc.to_dict()['role']
        print(role)