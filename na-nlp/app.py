from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin import storage
import os
import multiprocessing
from gensim.summarization import keywords
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from io import StringIO
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import resolve1
import os
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
import pickle
import numpy as np


app = Flask(__name__)


cred = credentials.Certificate("shaala-loka-firebase-adminsdk-xsp4x-5eea3da522.json")
firebase_admin.initialize_app(cred, {
'storageBucket': 'shaala-loka.appspot.com'
})

bucket = storage.bucket()
db = firestore.client()
ALLOWED_EXTENSIONS = {'pdf'}


# NLP Starts

class PdfConverter:
    
    def __init__(self, file_path):
        self.file_path = file_path

    def convert_pdf_to_txt(self, pagenos):
        rsrcmgr = PDFResourceManager()
        retstr = StringIO()
        laparams = LAParams()
        device = TextConverter(rsrcmgr, retstr, laparams=laparams)
        fp = open(self.file_path, 'rb')
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        password = ""
        maxpages = 1
        pagenos = range(pagenos, pagenos + maxpages)
        pagenos = set(pagenos)
        caching = True
        for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password, caching=caching,
                                      check_extractable=True):
            interpreter.process_page(page)
        fp.close()
        device.close()
        str = retstr.getvalue()
        retstr.close()
        return str


def max_occurrences(nums):
    max_val = 0
    result = nums[0]
    for i in nums:
        occu = nums.count(i)
        if occu > max_val:
            max_val = occu
            result = i
    return result


def predict(filepath, blobname):
    reference = {0: 'Biology', 1: 'Chemistry', 2: 'Civics', 3: 'CloudComputing', 4: 'History', 5: 'MachineLearning',
                 6: 'Networks', 7: 'Physics'}
    pdfConverter = PdfConverter(file_path=filepath)
    file = open(filepath, 'rb')
    parser = PDFParser(file)
    document = PDFDocument(parser)
    pages = resolve1(document.catalog['Pages'])['Count']
    file.close()
    data = []
    for i in range(0, pages + 1):
        page = pdfConverter.convert_pdf_to_txt(pagenos=i)
        if len(page.split(' ')) > 50:
            data.append(keywords(page, words=10, lemmatize=True).replace('\n', ' '))
    data = list(set(data))
    corpus = []
    for i in range(0, len(data)):
        data[i] = data[i].lower()
        data[i] = data[i].split()
        ps = PorterStemmer()
        all_stopwords = stopwords.words('english')
        data[i] = [ps.stem(word) for word in data[i] if not word in set(all_stopwords)]
        data[i] = ' '.join(data[i])
        corpus.append(data[i])
    corpus = list(set(corpus))
    clf = pickle.load(open("content/model.pkl", "rb"))
    corpus = np.array(corpus)
    corpus.reshape(1, -1)
    cv = pickle.load(open("content/cvector.pkl", "rb"))
    test = cv.transform(corpus).toarray()
    pred = clf.predict(test)
    domain = max_occurrences(list(pred))

    org_id = '1JS'
    student_id = '1JS17CS004'
    data = {
        'interests': {
            str(reference[domain]): 0
        },
        'org_id': org_id,
        'student_id': student_id
    }
    doc_arc  = db.collection('Archives').where('org_id', '==', org_id).where('student_id','==', student_id).get()

    if not doc_arc:
        doc = db. collection('Archives').document()
        doc.set(data)

    data1 = {
        'domain': str(reference[domain]),
        'name': filepath,
        'path': blobname
    }

    docs  = db.collection('Archives').where('org_id', '==', org_id).where('student_id','==', student_id).get()

    if docs:
        for doc in docs:
            doc_id = doc.id
            doc_doc = db.collection('Archives').document(doc_id).collection('Documents').document()
            doc_doc.set(data1)
            doc_int = db.collection('Archives').document(doc_id)
            doc_int.update({f"interests.{str(reference[domain])}": firestore.Increment(1)})

    os.remove(os.path.join(filepath))
    return 

# Nlp Ends

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('index.html')
	
@app.route('/uploader', methods = ['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file_uploaded = request.files['file']
        if file_uploaded and allowed_file(file_uploaded.filename):
            filename = secure_filename(file_uploaded.filename)
            file_uploaded.save(filename)
            file_uploaded.seek(0)
            org_id = '1JS'
            stu_id = '1JS17CS004'
            source_blob_name = org_id + '/' + stu_id + '/' + filename
            blob = bucket.blob(source_blob_name)
            blob.upload_from_file(file_uploaded)
            p1 = multiprocessing.Process(target=predict, args=(filename, str(blob.name)))
            p1.start()
            # print(blob.name)
            # main.predict(filename)
            # time.sleep(5)
            # blob.make_public()
            # blob = bucket.blob(org_id + '/' + stu_id + '/' + filename)
            # blob.download_to_filename('abc')
            # blob.download_to_filename(source_blob_name)
            # with open('file_uploaded', "wb") as file_obj:
            #     blob.download_to_file(file_obj)
            # filelist = [ f for f in os.listdir(".") if f.endswith('us.pdf') ]
            # print(filelist)
            # for f in filelist:
            # file_uploaded.close()
                # blob.download_to_filename(filename)
            # main.predict('https://storage.googleapis.com/shaala-loka.appspot.com/1JS/1JS17CS004/8th_Sem_Syllabus.pdf')
            # for blob in bucket.list_blobs(prefix='1JS/1JS17CS004'):
            #     print(str(blob.name))
                # if blob.name:
                #     blob.download_to_filename(blob.name)
                # destination_uri = '{}'.format('/content') 
                # blob.download_to_filename(destination_uri)
                # blob.download_to_filename(filename)

            return 'file uploaded successfully'
        return 'ERROR in FILE'
		
if __name__ == '__main__':
   app.run(debug = True)