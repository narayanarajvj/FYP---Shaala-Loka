import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("shaala-loka-firebase-adminsdk-xsp4x-5eea3da522.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

# docref = db.collection_group(u'1JS').where(u'org_id', u'==', u'1JS').get()

data = {
    'email_id': 'jss@jssateb.ac.in',
    'org_id': '1JS',
    'org_name': 'JSS',
    'password': 'jss123',
    'type': 'C'
}

docref = db.collection('Organization').document(data['org_id'])

docref.set(data)

data1 = {
    'id': data['org_id'],
    'password': data['password'],
    'role': 'Organization'
}

docref1 = db.collection('Login').document(data1['id'])

docref1.set(data1)