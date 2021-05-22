from flask import Flask, render_template, request, flash, redirect, url_for
import firebase_admin
from firebase_admin import credentials, firestore
import base64
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = 'vijay'

mail = Mail()

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'shaalaloka@gmail.com'
app.config['MAIL_PASSWORD'] = 'tfgkdqhihsasqhyn'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail.init_app(app)

cred = credentials.Certificate("shaala-loka-firebase-adminsdk-xsp4x-5eea3da522.json")
firebase_admin.initialize_app(cred)

db = firestore.client()


@app.route("/")
@app.route("/home")
def main():
    return render_template("index.html")


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
            return render_template("inst_Landing.html")
        elif role == 'Student':
            return render_template("stu_Landing.html")
    return render_template('login.html', error=error)


@app.route("/organization-registration", methods=["POST", "GET"])
def organizationRegistration():
    if request.method == 'POST':
        orgId = request.form['org_id']
        orgName = request.form['org_name']
        emailId = request.form['email_id']
        password = request.form['password']

        enc_password = base64.b64encode(password.encode("utf-8"))

        data = {
            'email_id': emailId,
            'org_id': orgId,
            'org_name': orgName,
            'password': enc_password,
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

        flash('You are Successfully Registered! Please Login...')
        return redirect(url_for('login'))
    return render_template("orgRegistration.html")


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

    return render_template("instRegistration.html", error=error)


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

        names = request.json['data']
        for name in names:
            print(name)

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

    return render_template("stuRegistration.html", error=error)


@app.route("/<orgId>")
def organizationHome(orgId):
    return render_template("org_Landing.html", orgId=orgId)


@app.route("/<orgId>/instructor")
def organizationInstructor(orgId):
    docs = db.collection(u'Organization').document(orgId).collection('Instructor').order_by(u'id').limit(
        10).stream()
    return render_template("org_Instructor.html", orgId=orgId, docs=docs)


@app.route("/<orgId>/student")
def organizationStudent(orgId):
    docs = db.collection(u'Organization').document(orgId).collection('Student').order_by(u'id').limit(
        10).stream()
    return render_template("org_Student.html", orgId=orgId, docs=docs)


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

    if role:
        data = {
            'id': id,
            'password': password,
            'role': role
        }
        docref = db.collection('Login').document(data['id'])
        docref.set(data)

    flash(id+" Approved Successfully")

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

    msg = Message('Shaala Loka - Profile Disabled - '+orgId, sender='shaalaloka@gmail.com', recipients=[email])
    msg.body = f"Your Organization has disabled your account (ID: {id}). You will be unable to Login henceforth."
    mail.send(msg)

    docs2 = db.collection('Login').where('id', '==', id).get()
    for doc in docs2:
        key2 = doc.id
        db.collection('Login').document(key2).delete()

    flash(id+" Removed Successfully")
    if collectionName == "Instructor":
        return redirect(url_for('organizationInstructor', orgId=orgId))
    if collectionName == "Student":
        return redirect(url_for('organizationStudent', orgId=orgId))
    return redirect(url_for('organizationHome', orgId=orgId))


if __name__ == '__main__':
    app.run(debug=True)
