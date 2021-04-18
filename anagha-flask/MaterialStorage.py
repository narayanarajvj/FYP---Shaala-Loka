import firebase_admin
from firebase_admin import credentials
from firebase_admin import storage

cred = credentials.Certificate("shaala-loka-firebase-adminsdk-xsp4x-5eea3da522.json")
firebase_admin.initialize_app(cred, {
    'storageBucket': '<BUCKET-ID>.appspot.com'
})

bucket = storage.bucket()

classname = 'aca'
org_id = '1JS'
filename = 'vj4.jpg'

blob = bucket.blob(org_id + '/' + classname + '/' + filename)
# blob.download_to_filename(org_id + '/' + classname + '/' + filename)
# blob.upload_from_filename(filename)
blob.make_public()
print(blob.public_url)

file_url = blob.generate_signed_url(datetime.timedelta(days=1), method='GET') #this URL valid for 1 day
print(file_url)
