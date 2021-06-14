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
                    # print('Login Successfully')
                    role = doc.to_dict()['role']
                    # print(role)
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
        arr_upd.update({u'students': firestore.ArrayRemovew([id])})

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
            error = f"Subject ID - {subjectId} is already used. Use a different Subject ID"
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
    docs = db.collection('StudyHall').where('org_id', '==', orgId).where('students', 'array_contains', stuId).order_by('subject_id').limit(10).get()
    return render_template("student/stu_StudyRoom.html", orgId=orgId, stuId=stuId, stuName=stuName, docs=docs)

@app.route("/student/<orgId>/<stuId>/<stuName>/study-hall/<subjectId>/<sh_name>")
def studentSpecificStudyHall(orgId, stuId, stuName, subjectId, sh_name):
    docs_sh = db.collection('StudyHall').where('org_id', '==', orgId).where('students', 'array_contains', stuId).where('subject_id', '==', subjectId).get()
    for doc in docs_sh:
        insName = doc.to_dict()['instructor_name']
        session_link = doc.to_dict()['session_link']
    return render_template("student/stu_SpecificStudyRoom.html", orgId=orgId, insName=insName, stuId=stuId, stuName=stuName, subjectId=subjectId, sh_name=sh_name, session_link=session_link)

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


if __name__ == '__main__':
    app.run(debug=True)

