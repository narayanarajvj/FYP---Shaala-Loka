from logging import error
from re import sub
from flask import Flask, render_template, request, flash, redirect, url_for, session
# from flask_session import Session
import firebase_admin
from firebase_admin import credentials, firestore, storage
import base64
from flask_mail import Mail, Message
import os
from dotenv import load_dotenv
from pytz import timezone
from werkzeug.utils import secure_filename
import json

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
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
import pickle
import numpy as np

# import nltk
# from pprint import pprint
# from Question.OuterQuestgen.Questgen import quiz_main
from Question import question


app = Flask(__name__)
app.secret_key = 'vijay'
# app.config["SESSION_PERMANENT"] = False
# app.config["SESSION_TYPE"] = "filesystem"
# Session(app)

mail = Mail()

load_dotenv()
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail.init_app(app)

cred = credentials.Certificate("shaala-loka-firebase-adminsdk-xsp4x-5eea3da522.json")
firebase_admin.initialize_app(cred, {
'storageBucket': 'shaala-loka.appspot.com'
})

bucket = storage.bucket()

db = firestore.client()

ALLOWED_EXTENSIONS = {'pdf'}


# NLP CONTEXT ANALYSIS STARTS HERE

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


def predict(filepath, blobname, orgId, stuId, stuName):
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

    doc_arc  = db.collection('Archives').where('org_id', '==', orgId).where('student_id','==', stuId).get()

    if not doc_arc:
        doc_em = db.collection('Organization').document(orgId).collection('Student').document(stuId).get()
        emailId = doc_em.to_dict()['email_id']
        data = {
            'interests': {
                str(reference[domain]): 0
            },
            'interests_list': [],
            'org_id': orgId,
            'student_id': stuId,
            'student_name': stuName,
            'email_id': emailId 
        }
        doc = db. collection('Archives').document()
        doc.set(data)

    data1 = {
        'domain': str(reference[domain]),
        'name': filepath,
        'path': blobname
    }

    docs  = db.collection('Archives').where('org_id', '==', orgId).where('student_id','==', stuId).get()

    if docs:
        for doc in docs:
            doc_id = doc.id
            doc_doc = db.collection('Archives').document(doc_id).collection('Documents').document()
            doc_doc.set(data1)
            doc_int = db.collection('Archives').document(doc_id)
            doc_int.update({f"interests.{str(reference[domain])}": firestore.Increment(1)})
            doc_int.update({'interests_list': firestore.ArrayUnion([str(reference[domain])])})

    os.remove(os.path.join(filepath))
    return 

# NLP CONTEXT ANALYSIS ENDS

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# NLP QUIZ

def quiz(textarea, orgId, insId, subjectId):
    docs_sh = db.collection('StudyHall').where('org_id', '==', orgId).where('instructor_id', '==', insId).where('subject_id', '==', subjectId).get()
    payload = {
        "input_text": textarea
    }

    questions = question.find_questions(payload)

    data = {
        'questions': questions
    }

    for doc in docs_sh:
        doc_id = doc.id
        docref = db.collection('StudyHall').document(doc_id).collection('Quiz').document(subjectId)
        docref.set(data)

    return

# HOME PAGE

@app.route("/")
@app.route("/home")
def main():
    # session.clear()
    return render_template("index.html")

# LOGIN STARTS HERE

@app.route("/login", methods=['POST', 'GET'])
def login():
    error = None
    if request.method == 'POST':
        id = request.form['id']
        password = request.form['password']

        password = base64.b64encode(password.encode("utf-8"))
        role = None

        docref = db.collection('Login').where('id', '==', id).where('password', '==', password).get()
        if docref:
            for doc in docref:
                if doc.to_dict()['id'] and doc.to_dict()['password']:
                    role = doc.to_dict()['role']
        else:
            error = 'Invalid ID or Password. Please try again!'
        if role == 'Organization':
            return redirect(url_for('organizationHome', orgId=id))
        elif role == 'Instructor':
            return redirect(url_for('instructorHome', insId=id))
        elif role == 'Student':
            return redirect(url_for('studentHome', stuId=id))
    return render_template('login.html', error=error)

# REGISTRATION STARTS HERE

@app.route("/organization-registration", methods=["POST", "GET"])
def organizationRegistration():
    if request.method == 'POST':
        orgId = request.form['org_id']
        orgName = request.form['org_name']
        emailId = request.form['email_id']
        password = request.form['password']
        type = request.form['type']

        enc_password = base64.b64encode(password.encode("utf-8"))

        data = {
            'email_id': emailId,
            'org_id': orgId,
            'org_name': orgName,
            'password': enc_password,
            'type': type,
            'instructors': [],
            'students': []
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

        flash('You are Successfully Registered! Please Login...')
        return redirect(url_for('login'))
    return render_template("registration/orgRegistration.html")


@app.route("/instructor-registration", methods=["POST", "GET"])
def instructorRegistration():
    error = None
    if request.method == 'POST':
        instId = request.form['instructor_id']
        instName = request.form['instructor_name']
        orgId = request.form['org_id']
        emailId = request.form['email_id']
        designation = request.form['designation']
        dept = request.form['department']
        password = request.form['password']
        enc_password = base64.b64encode(password.encode("utf-8"))

        org_ref = db.collection('Organization').where('org_id', '==', orgId).get()
        if org_ref:
            for doc in org_ref:
                if doc.to_dict()['org_id']:
                    status = False
                    data = {
                        'approval_status': status,
                        'department': dept,
                        'designation': designation,
                        'email_id': emailId,
                        'id': instId,
                        'instructor_name': instName,
                        'org_id': orgId,
                        'password': enc_password
                    }

                    docref = db.collection('Organization').document(data['org_id']).collection('Instructor').document(
                        data['id'])
                    docref.set(data)

                    flash(
                        'You are Successfully Registered! Please wait till Organization Approve and you will be soon notified...')
                    return redirect(url_for('login'))
        else:
            error = 'Organization ID does not exist. Please enter the valid ID...'

    return render_template("registration/instRegistration.html", error=error)


@app.route("/student-registration", methods=["POST", "GET"])
def studentRegistration():
    error = None
    if request.method == 'POST':
        stuId = request.form['student_id']
        stuName = request.form['student_name']
        orgId = request.form['org_id']
        emailId = request.form['email_id']
        password = request.form['password']
        level = request.form['level']
        sec = request.form['section']
        stuDept = request.form['department']
        enc_password = base64.b64encode(password.encode("utf-8"))

        org_ref = db.collection('Organization').where('org_id', '==', orgId).get()
        if org_ref:
            for doc in org_ref:
                if doc.to_dict()['org_id']:
                    status = False

                    data = {
                        'approval_status': status,
                        'department': stuDept,
                        'level': level,
                        'section': sec,
                        'email_id': emailId,
                        'id': stuId,
                        'student_name': stuName,
                        'org_id': orgId,
                        'password': enc_password
                    }

                    docref = db.collection('Organization').document(data['org_id']).collection('Student').document(
                        data['id'])

                    docref.set(data)
                    flash(
                        'You are Successfully Registered! Please wait till Organization Approve and you will be soon notified...')
                    return redirect(url_for('login'))
        else:
            error = 'Organization ID does not exist. Please enter the valid ID...'

    return render_template("registration/stuRegistration.html", error=error)

# ORGANIZATION STARTS HERE

@app.route("/<orgId>")
def organizationHome(orgId):
    docs = db.collection('Organization').where('org_id', '==', orgId).get()
    for doc in docs:
        if doc.to_dict()['org_id'] == orgId:
            orgName = doc.to_dict()['org_name']
    return render_template("organization/org_Landing.html", orgId=orgId, orgName=orgName)


@app.route("/<orgId>/instructor")
def organizationInstructor(orgId):
    docs = db.collection(u'Organization').document(orgId).collection('Instructor').order_by(u'id').limit(
        10).get()
    return render_template("organization/org_Instructor.html", orgId=orgId, docs=docs)


@app.route("/<orgId>/student")
def organizationStudent(orgId):
    docs = db.collection(u'Organization').document(orgId).collection('Student').order_by(u'id').limit(
        10).get()
    return render_template("organization/org_Student.html", orgId=orgId, docs=docs)


@app.route("/<orgId>/approve/<collectionName>/<id>")
def approval(orgId, collectionName, id):
    role = None
    password = None
    email = None
    docref = db.collection('Organization').document(orgId).collection(collectionName).where('id', '==', id).get()
    for doc in docref:
        if not doc.to_dict()['approval_status']:
            doc_id = doc.id
            db.collection('Organization').document(orgId).collection(collectionName).document(doc_id).update(
                {'approval_status': True})
            password = doc.to_dict()['password']
            email = doc.to_dict()['email_id']
        role = collectionName

    arr_upd = db.collection('Organization').document(orgId)
    if collectionName == "Instructor":
        arr_upd.update({u'instructors': firestore.ArrayUnion([id])})
    elif collectionName == "Student":
        arr_upd.update({u'students': firestore.ArrayUnion([id])})

    if role and password:
        data = {
            'id': id,
            'password': password,
            'role': role
        }
        docref = db.collection('Login').document(data['id'])
        docref.set(data)

    flash("ID: "+id+" Approved Successfully")

    msg = Message('Shaala Loka - Profile Approved - '+orgId, sender='shaalaloka@gmail.com', recipients=[email])
    msg.body = f"Your Organization has successfully authenticated your account (ID: {id}). You can Login from now " \
               "onwards."
    mail.send(msg)
    if collectionName == "Instructor":
        return redirect(url_for('organizationInstructor', orgId=orgId))
    if collectionName == "Student":
        return redirect(url_for('organizationStudent', orgId=orgId))
    return redirect(url_for('organizationHome', orgId=orgId))

@app.route("/<orgId>/remove/<collectionName>/<id>")
def removal(orgId, collectionName, id):
    email = None
    docs = db.collection('Organization').document(orgId).collection(collectionName).where('id', '==', id).get()
    for doc in docs:
        key1 = doc.id
        email = doc.to_dict()['email_id']
        db.collection('Organization').document(orgId).collection(collectionName).document(key1).delete()

    arr_upd = db.collection('Organization').document(orgId)
    if collectionName == "Instructor":
        arr_upd.update({u'instructors': firestore.ArrayRemove([id])})
    elif collectionName == "Student":
        arr_upd.update({u'students': firestore.ArrayRemove([id])})

    msg = Message('Shaala Loka - Profile Disabled - '+orgId, sender='shaalaloka@gmail.com', recipients=[email])
    msg.body = f"Your Organization has disabled your account (ID: {id}). You will be unable to Login henceforth."
    mail.send(msg)

    docs2 = db.collection('Login').where('id', '==', id).get()
    for doc in docs2:
        key2 = doc.id
        db.collection('Login').document(key2).delete()

    flash("ID: "+id+" Removed Successfully")
    if collectionName == "Instructor":
        return redirect(url_for('organizationInstructor', orgId=orgId))
    if collectionName == "Student":
        return redirect(url_for('organizationStudent', orgId=orgId))
    return redirect(url_for('organizationHome', orgId=orgId))

# INSTRUCTOR STARTS HERE

@app.route("/instructor/<insId>")
def instructorHome(insId):
    insName = None
    orgId = None
    docs_org = db.collection('Organization').where('instructors', 'array_contains', insId).get()
    for doc in docs_org:
        orgName = doc.to_dict()['org_name']
        orgId = doc.to_dict()['org_id']

    docs_ins = db.collection('Organization').document(orgId).collection('Instructor').where('id', '==', insId).get()
    for doc in docs_ins:
        insName = doc.to_dict()['instructor_name']

    return render_template("instructor/inst_Landing.html", orgId=orgId, insId=insId, insName=insName)

@app.route("/<orgId>/<insId>/<insName>/schedule")
def instructorSchedule(orgId, insId, insName):
    docs_list = []
    docs_sh = db.collection('StudyHall').where('org_id', '==', orgId).where('instructor_id', '==', insId).get()
    for doc in docs_sh:
        doc_id = doc.id
        docs = db.collection('StudyHall').document(doc_id).collection('Schedule').limit(10).get()
        for d in docs:
            dict = d.to_dict()
            dict['sh_name'] = doc.to_dict()['sh_name']
            dict['level'] = doc.to_dict()['level']
            dict['section'] = doc.to_dict()['section']
            docs_list.append(dict)
    docs_list = sorted(docs_list, key = lambda i: (i['date'], i['time']))
    return render_template("instructor/inst_Schedule.html", orgId=orgId, insId=insId, insName=insName, docs_list=docs_list)

@app.route("/<orgId>/<insId>/<insName>/study-hall")
def instructorStudyHall(orgId, insId, insName):
    docs = db.collection('StudyHall').where('org_id', '==', orgId).where('instructor_id', '==', insId).order_by('subject_id').limit(10).get()
    return render_template("instructor/inst_StudyRoom.html", orgId=orgId, insId=insId, insName=insName, docs=docs)

@app.route("/<orgId>/<insId>/<insName>/new-study-hall", methods=["POST", "GET"])
def instructorNewClassroom(orgId, insId, insName):
    if request.method == 'POST':
        subjectId = request.form['subject_id']
        sh_name = request.form['subject_name']
        description = request.form['description']
        department = request.form['department']
        level = request.form['level']
        section = request.form['section']

        docs = db.collection('StudyHall').where('org_id', '==', orgId).where('instructor_id', '==', insId).where('subject_id', '==', subjectId).get()
        if docs:
            docs = db.collection('StudyHall').where('org_id', '==', orgId).where('instructor_id', '==', insId).order_by('subject_id').limit(10).get()
            error = f"Subject Code - {subjectId} is already used. Use a different Subject Code."
            return render_template("instructor/inst_StudyRoom.html", orgId=orgId, insId=insId, insName=insName, error=error, docs=docs)

        docref = db.collection('StudyHall').document()
        data = {
            'sh_id': docref.id,
            'subject_id': subjectId,
            'sh_name': sh_name,
            'description': description,
            'department': department,
            'level': level,
            'section': section,
            'instructor_id': insId,
            'instructor_name': insName,
            'org_id': orgId,
            'students': [],
            'session_link': None
        }
        docref.set(data)
    return redirect(url_for('instructorStudyHall', orgId=orgId, insId=insId, insName=insName))

@app.route("/<orgId>/<insId>/<insName>/study-hall/<subjectId>/<sh_name>")
def instructorSpecificStudyHall(orgId, insId, insName, subjectId, sh_name):
    docs = None
    docs_sh = db.collection('StudyHall').where('org_id', '==', orgId).where('instructor_id', '==', insId).where('subject_id', '==', subjectId).get()
    for doc in docs_sh:
        doc_id = doc.id
        docs = db.collection('StudyHall').document(doc_id).collection('Scores').order_by('student_id').limit(30).get()
    return render_template("instructor/inst_SpecificStudyRoom.html", orgId=orgId, insId=insId, insName=insName, subjectId=subjectId, sh_name=sh_name, docs=docs)

@app.route("/<orgId>/<insId>/<insName>/<subjectId>/<sh_name>/new-schedule", methods=["POST", "GET"])
def studyHallNewSchedule(orgId, insId, insName, subjectId, sh_name):
    if request.method == 'POST':
        topic_name = request.form['topic_name']
        date = request.form['date']
        time = request.form['time']

        data = {
            'topic_name': topic_name,
            'date': date,
            'time': time
        }

        docs = db.collection('StudyHall').where('org_id', '==', orgId).where('instructor_id', '==', insId).where('subject_id', '==', subjectId).get()
        for doc in docs:
            doc_id = doc.id
            docref = db.collection('StudyHall').document(doc_id).collection('Schedule').document()
            docref.set(data)
            docs = db.collection('StudyHall').document(doc_id).collection('Scores').order_by('student_id').limit(30).get()
    return redirect(url_for('instructorSpecificStudyHall', orgId=orgId, insId=insId, insName=insName, subjectId=subjectId, sh_name=sh_name, docs=docs))

@app.route("/<orgId>/<insId>/<insName>/<subjectId>/<sh_name>/discussion", methods=["POST", "GET"])
def instructorDiscussionRoom(orgId, insId, insName, subjectId, sh_name):
    docs = None
    docs_sh = db.collection('StudyHall').where('org_id', '==', orgId).where('instructor_id', '==', insId).where('subject_id', '==', subjectId).get()
    if request.method == 'POST':
        message = request.form['message']
        timestamp = firestore.SERVER_TIMESTAMP
        data = {
            'id': insId,
            'name': insName,
            'message': message,
            'timestamp': timestamp
        }
        for doc in docs_sh:
            doc_id = doc.id
            docref = db.collection('StudyHall').document(doc_id).collection('ChatRoom').document()
            docref.set(data)

    for doc in docs_sh:
        doc_id = doc.id
        docs = db.collection('StudyHall').document(doc_id).collection('ChatRoom').order_by('timestamp').limit(30).get()

    def convert_timestamp(timestamp):
        timestamp = timestamp.astimezone(timezone('Asia/Kolkata'))
        hr,mi = timestamp.hour, timestamp.minute
        return str(hr)+":"+str(mi)

    return render_template("instructor/inst_Discussions.html", orgId=orgId, insId=insId, insName=insName, subjectId=subjectId, sh_name=sh_name, docs=docs, convert_timestamp=convert_timestamp)

@app.route("/<orgId>/<insId>/<insName>/<subjectId>/<sh_name>/resources", methods=["POST", "GET"])
def instructorResources(orgId, insId, insName, subjectId, sh_name):
    docs = None
    docs_sh = db.collection('StudyHall').where('org_id', '==', orgId).where('instructor_id', '==', insId).where('subject_id', '==', subjectId).get()
    if request.method == 'POST':
        file_uploaded = request.files['inst_resources']
        filename = secure_filename(file_uploaded.filename)
        blob = bucket.blob(orgId + '/' + insId + '/' + subjectId +'/'+ filename)
        blob.upload_from_file(file_uploaded)
        blob.make_public()
        url = blob.public_url
        timestamp = firestore.SERVER_TIMESTAMP
        data = {
            'filename': filename,
            'instructor_id': insId,
            'name': insName,
            'timestamp': timestamp,
            'url': url
        }
        for doc in docs_sh:
            doc_id = doc.id
            doc_res = db.collection('StudyHall').document(doc_id).collection('Resources').where('filename', '==', filename).get()
            if not doc_res:
                docref = db.collection('StudyHall').document(doc_id).collection('Resources').document()
                docref.set(data)
        
    for doc in docs_sh:
        doc_id = doc.id
        docs = db.collection('StudyHall').document(doc_id).collection('Resources').order_by('timestamp').limit(20).get()

    return render_template("instructor/inst_StudyRoom_Resources.html", orgId=orgId, insId=insId, insName=insName, subjectId=subjectId, sh_name=sh_name, docs=docs)

@app.route("/<orgId>/<insId>/<insName>/<subjectId>/<sh_name>/session-link", methods=["POST", "GET"])
def instructorSessionLink(orgId, insId, insName, subjectId, sh_name):
    if request.method == 'POST':
        link = request.form['meetLink']
        docs_sh = db.collection('StudyHall').where('org_id', '==', orgId).where('instructor_id', '==', insId).where('subject_id', '==', subjectId).get()
        for doc in docs_sh:
            doc_id = doc.id
            db.collection('StudyHall').document(doc_id).update({'session_link': link})
            docs = db.collection('StudyHall').document(doc_id).collection('Scores').order_by('student_id').limit(30).get()
    return redirect(url_for('instructorSpecificStudyHall', orgId=orgId, insId=insId, insName=insName, subjectId=subjectId, sh_name=sh_name, docs=docs))

@app.route("/<orgId>/<insId>/<insName>/<subjectId>/<sh_name>/clear-session-link")
def instructorClearSessionLink(orgId, insId, insName, subjectId, sh_name):
    docs = None
    docs_sh = db.collection('StudyHall').where('org_id', '==', orgId).where('instructor_id', '==', insId).where('subject_id', '==', subjectId).get()
    for doc in docs_sh:
        doc_id = doc.id
        db.collection('StudyHall').document(doc_id).update('session_link', firestore.DELETE_FIELD)
        docs = db.collection('StudyHall').document(doc_id).collection('Scores').order_by('student_id').limit(30).get()
    return redirect(url_for('instructorSpecificStudyHall', orgId=orgId, insId=insId, insName=insName, subjectId=subjectId, sh_name=sh_name, docs=docs))  

@app.route("/<orgId>/<insId>/<insName>/<subjectId>/<sh_name>/quiz", methods=["POST", "GET"])
def instructorQuiz(orgId, insId, insName, subjectId, sh_name):
    error = None
    if request.method == 'POST':
        textarea = request.form['textarea']
        if len(textarea.split()) > 50:
            p2 = multiprocessing.Process(target=quiz, args=(textarea, orgId, insId, subjectId))
            p2.start()
            flash("Quiz has successfully generated for students")
        else:
            error = "Please give sufficient content with a minimum of 50 words without any symbols"
    return render_template("instructor/inst_Quiz.html", orgId=orgId, insId=insId, insName=insName, subjectId=subjectId, sh_name=sh_name, error=error)

@app.route("/<orgId>/<insId>/<insName>/<subjectId>/<sh_name>/clear-quiz")
def instructorClearQuiz(orgId, insId, insName, subjectId, sh_name):
    docs_sh = db.collection('StudyHall').where('org_id', '==', orgId).where('instructor_id', '==', insId).where('subject_id', '==', subjectId).get()
    for doc in docs_sh:
        doc_id = doc.id
        docref = db.collection('StudyHall').document(doc_id).collection('Quiz').document(subjectId)
        docref.update("questions", firestore.DELETE_FIELD)
        flash("Previous Quiz has successfully ended")
        docs = db.collection('StudyHall').document(doc_id).collection('Scores').where('flag', '==', True).get()
        for d in docs:
            d_id = d.id
            docre = db.collection('StudyHall').document(doc_id).collection('Scores').document(d_id)
            docre.update({"flag": False})
    return redirect(url_for('instructorQuiz', orgId=orgId, insId=insId, insName=insName, subjectId=subjectId, sh_name=sh_name))

@app.route("/<orgId>/<insId>/<insName>/archives")
def instructorArchives(orgId, insId, insName):
    docs = db.collection('Archives').where('org_id', '==', orgId).limit(15).get()
    return render_template("instructor/inst_Archives.html", orgId=orgId, insId=insId, insName=insName, docs=docs)

@app.route("/<orgId>/<insId>/<insName>/filter", methods=["POST", "GET"])
def instructorArchivesFilter(orgId, insId, insName):
    if request.method == 'POST':
        domains = request.form.getlist('domain')
        docs = db.collection('Archives').where('org_id', '==', orgId).where('interests_list', 'array_contains_any', domains).get()
    if domains:
        return render_template("instructor/inst_Archives.html", orgId=orgId, insId=insId, insName=insName, docs=docs, domains=domains)
    else:
        return redirect(url_for('instructorArchives', orgId=orgId, insId=insId, insName=insName))

# STUDENT STARTS HERE

@app.route("/student/<stuId>")
def studentHome(stuId):
    stuName = None
    orgId = None
    docs_org = db.collection('Organization').where('students', 'array_contains', stuId).get()
    for doc in docs_org:
        orgName = doc.to_dict()['org_name']
        orgId = doc.to_dict()['org_id']

    docs_ins = db.collection('Organization').document(orgId).collection('Student').where('id', '==', stuId).get()
    for doc in docs_ins:
        stuName = doc.to_dict()['student_name']

    return render_template("student/stu_Landing.html", orgId=orgId, stuId=stuId, stuName=stuName)

@app.route("/student/<orgId>/<stuId>/<stuName>/schedule")
def studentSchedule(orgId, stuId, stuName):
    docs_list = []
    docs_sh = db.collection('StudyHall').where('org_id', '==', orgId).where('students', 'array_contains', stuId).get()
    for doc in docs_sh:
        doc_id = doc.id
        docs = db.collection('StudyHall').document(doc_id).collection('Schedule').limit(10).get()
        for d in docs:
            dict = d.to_dict()
            dict['sh_name'] = doc.to_dict()['sh_name']
            dict['level'] = doc.to_dict()['level']
            dict['section'] = doc.to_dict()['section']
            dict['instructor_name'] = doc.to_dict()['instructor_name']
            docs_list.append(dict)
    docs_list = sorted(docs_list, key = lambda i: (i['date'], i['time']))
    return render_template("student/stu_Schedule.html", orgId=orgId, stuId=stuId, stuName=stuName, docs_list=docs_list)

@app.route("/student/<orgId>/<stuId>/<stuName>/study-hall")
def studentStudyHall(orgId, stuId, stuName):
    doc_type = db.collection('Organization').document(orgId).get()
    if doc_type.to_dict()['type'] == 'S':
        doc_info = db.collection('Organization').document(orgId).collection('Student').document(stuId).get()
        level = doc_info.to_dict()['level']
        section = doc_info.to_dict()['section']
        docs_join = db.collection('StudyHall').where('org_id', '==', orgId).where('level', '==', level).where('section', '==', section).get()
    elif doc_type.to_dict()['type'] == 'C':
        doc_info = db.collection('Organization').document(orgId).collection('Student').document(stuId).get()
        level = doc_info.to_dict()['level']
        department = doc_info.to_dict()['department']
        section = doc_info.to_dict()['section']
        docs_join = db.collection('StudyHall').where('org_id', '==', orgId).where('department', '==', department).where('level', '==', level).where('section', '==', section).get()
    
    docs = db.collection('StudyHall').where('org_id', '==', orgId).where('students', 'array_contains', stuId).order_by('subject_id').limit(10).get()
    return render_template("student/stu_StudyRoom.html", orgId=orgId, stuId=stuId, stuName=stuName, docs=docs, docs_join=docs_join)

@app.route("/student/<orgId>/<stuId>/<stuName>/<insId>/<subjectId>/join-new")
def studentJoin(orgId, stuId, stuName, insId,subjectId):
    docs = db.collection('StudyHall').where('org_id', '==', orgId).where('instructor_id', '==', insId).where('subject_id', '==', subjectId).get()
    for doc in docs:
        doc_id = doc.id
        student_list = db.collection('StudyHall').document(doc_id)
        student_list.update({'students': firestore.ArrayUnion([stuId])})
    return redirect(url_for("studentStudyHall", orgId=orgId, stuId=stuId, stuName=stuName))

@app.route("/student/<orgId>/<stuId>/<stuName>/study-hall/<subjectId>/<sh_name>")
def studentSpecificStudyHall(orgId, stuId, stuName, subjectId, sh_name):
    docs_sh = db.collection('StudyHall').where('org_id', '==', orgId).where('students', 'array_contains', stuId).where('subject_id', '==', subjectId).get()
    for doc in docs_sh:
        insName = doc.to_dict()['instructor_name']
        session_link = doc.to_dict()['session_link']
        doc_id = doc.id
        docs = db.collection('StudyHall').document(doc_id).collection('Scores').where('student_id', '==', stuId).where('student_name', '==', stuName).get()
        if docs:
            for d in docs:
                score = d.to_dict()['score']
        else:
            score = 0
    return render_template("student/stu_SpecificStudyRoom.html", orgId=orgId, insName=insName, stuId=stuId, stuName=stuName, subjectId=subjectId, sh_name=sh_name, session_link=session_link, score=score)

@app.route("/student/<orgId>/<stuId>/<stuName>/<subjectId>/<sh_name>/resources", methods=["POST", "GET"])
def studentResources(orgId, stuId, stuName, subjectId, sh_name):
    docs = None
    insName = None
    docs_sh = db.collection('StudyHall').where('org_id', '==', orgId).where('students', 'array_contains', stuId).where('subject_id', '==', subjectId).get()
    if request.method == 'POST':
        file_uploaded = request.files['stu_resources']
        filename = secure_filename(file_uploaded.filename)
        for doc in docs_sh:
            insId = doc.to_dict()['instructor_id']
        blob = bucket.blob(orgId + '/' + insId + '/' + subjectId +'/'+ filename)
        blob.upload_from_file(file_uploaded)
        blob.make_public()
        url = blob.public_url
        timestamp = firestore.SERVER_TIMESTAMP
        data = {
            'filename': filename,
            'student_id': stuId,
            'name': stuName,
            'timestamp': timestamp,
            'url': url
        }
        for doc in docs_sh:
            doc_id = doc.id
            doc_res = db.collection('StudyHall').document(doc_id).collection('Resources').where('filename', '==', filename).get()
            if not doc_res:
                docref = db.collection('StudyHall').document(doc_id).collection('Resources').document()
                docref.set(data)
        
    for doc in docs_sh:
        doc_id = doc.id
        insName = doc.to_dict()['instructor_name']
        docs = db.collection('StudyHall').document(doc_id).collection('Resources').order_by('timestamp').limit(20).get()

    return render_template("student/stu_StudyRoom_Resources.html", orgId=orgId, insName=insName, stuId=stuId, stuName=stuName, subjectId=subjectId, sh_name=sh_name, docs=docs)

@app.route("/student/<orgId>/<stuId>/<stuName>/<subjectId>/<sh_name>/discussion", methods=["POST", "GET"])
def studentDiscussionRoom(orgId, stuId, stuName, subjectId, sh_name):
    docs = None
    docs_sh = db.collection('StudyHall').where('org_id', '==', orgId).where('students', 'array_contains', stuId).where('subject_id', '==', subjectId).get()
    if request.method == 'POST':
        message = request.form['message']
        timestamp = firestore.SERVER_TIMESTAMP
        data = {
            'id': stuId,
            'name': stuName,
            'message': message,
            'timestamp': timestamp
        }
        for doc in docs_sh:
            doc_id = doc.id
            docref = db.collection('StudyHall').document(doc_id).collection('ChatRoom').document()
            docref.set(data)

    for doc in docs_sh:
        doc_id = doc.id
        docs = db.collection('StudyHall').document(doc_id).collection('ChatRoom').order_by('timestamp').limit(30).get()

    def convert_timestamp(timestamp):
        timestamp = timestamp.astimezone(timezone('Asia/Kolkata'))
        hr,mi = timestamp.hour, timestamp.minute
        return str(hr)+":"+str(mi)

    return render_template("student/stu_Discussions.html", orgId=orgId, stuId=stuId, stuName=stuName, subjectId=subjectId, sh_name=sh_name, docs=docs, convert_timestamp=convert_timestamp)

@app.route("/student/<orgId>/<stuId>/<stuName>/<subjectId>/<sh_name>/quiz")
def studentQuiz(orgId, stuId, stuName, subjectId, sh_name):
    docs = None
    questions = None
    insName = None
    docs_sh = db.collection('StudyHall').where('org_id', '==', orgId).where('students', 'array_contains', stuId).where('subject_id', '==', subjectId).get()
    for doc in docs_sh:
        doc_id = doc.id
        insName = doc.to_dict()['instructor_name']
        docs = db.collection('StudyHall').document(doc_id).collection('Quiz').document(subjectId).get()
        questions = docs.to_dict()['questions']
    return render_template("student/stu_Quiz.html", orgId=orgId, insName=insName, stuId=stuId, stuName=stuName, subjectId=subjectId, sh_name=sh_name, questions=questions)

@app.route("/student/<orgId>/<stuId>/<stuName>/<subjectId>/<sh_name>/get-score", methods=['GET', 'POST'])
def studentScore(orgId, stuId, stuName, subjectId, sh_name):
    if request.method == "POST":
        score = request.data
        docs_sh = db.collection('StudyHall').where('org_id', '==', orgId).where('students', 'array_contains', stuId).where('subject_id', '==', subjectId).get()
        for doc in docs_sh:
            doc_id = doc.id
            docs = db.collection('StudyHall').document(doc_id).collection('Scores').where('student_id', '==', stuId).where('student_name', '==', stuName).get()
            if not docs:
                data = {
                    'student_id': stuId,
                    'student_name': stuName,
                    'score': int(score),
                    'flag': True
                }
                docref = db.collection('StudyHall').document(doc_id).collection('Scores').document()
                docref.set(data)
            else:
                for d in docs:
                    d_id = d.id
                    flag_doc = db.collection('StudyHall').document(doc_id).collection('Scores').document(d_id).get()
                    flag = flag_doc.to_dict()['flag']
                    if not flag:
                        score_doc = db.collection('StudyHall').document(doc_id).collection('Scores').document(d_id)
                        score_doc.update({"score": firestore.Increment(int(score))})
                        score_doc.update({"flag": True})

    return redirect(url_for("studentQuiz", orgId=orgId, stuId=stuId, stuName=stuName, subjectId=subjectId, sh_name=sh_name))

@app.route("/student/<orgId>/<stuId>/<stuName>/archives")
def studentArchives(orgId, stuId, stuName):
    files_count = 0
    interests = None
    docs = None
    docs_int = db.collection('Archives').where('org_id', '==', orgId).where('student_id', '==', stuId).get()
    for doc in docs_int:
        doc_id = doc.id
        interests = doc.to_dict()['interests']

        for item in interests.values():
            files_count += int(item)
        docs = db.collection('Archives').document(doc_id).collection('Documents').limit(10).get()
    return render_template("student/stu_Archives.html", orgId=orgId, stuId=stuId, stuName=stuName, docs=docs, interests=interests, files_count=files_count)

@app.route("/student/<orgId>/<stuId>/<stuName>/archives-predict", methods = ['GET', 'POST'])
def studentArchivesPredict(orgId, stuId, stuName):
    if request.method == 'POST':
        file_uploaded = request.files['stu_resources']
        if file_uploaded and allowed_file(file_uploaded.filename):
            filename = secure_filename(file_uploaded.filename)
            docs  = db.collection('Archives').where('org_id', '==', orgId).where('student_id','==', stuId).get()
            if docs:
                for doc in docs:
                    doc_id = doc.id
                    doc_doc = db.collection('Archives').document(doc_id).collection('Documents').where('name', '==', filename).get()
                    if not doc_doc:
                        file_uploaded.save(filename)
                        file_uploaded.seek(0)
                        source_blob_name = orgId + '/' + stuId + '/' + filename
                        blob = bucket.blob(source_blob_name)
                        blob.upload_from_file(file_uploaded)
                        p1 = multiprocessing.Process(target=predict, args=(filename, str(blob.name), orgId, stuId, stuName))
                        p1.start()
                    else:
                        return redirect(url_for("studentArchives", orgId=orgId, stuId=stuId, stuName=stuName))
            else:
                file_uploaded.save(filename)
                file_uploaded.seek(0)
                source_blob_name = orgId + '/' + stuId + '/' + filename
                blob = bucket.blob(source_blob_name)
                blob.upload_from_file(file_uploaded)
                p1 = multiprocessing.Process(target=predict, args=(filename, str(blob.name), orgId, stuId, stuName))
                p1.start()
    return redirect(url_for("studentArchives", orgId=orgId, stuId=stuId, stuName=stuName))


if __name__ == '__main__':
    app.run(debug=True)

