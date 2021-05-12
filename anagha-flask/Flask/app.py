import app as app
from flask import Flask, render_template, request
import firebase_admin
from firebase_admin import credentials, firestore
import EmailAlert
import base64

app = Flask(__name__)

if not firebase_admin._apps:
    cred = credentials.Certificate("shaala-loka-firebase-adminsdk-xsp4x-fabfa6fc72.json")
    firebase_admin.initialize_app(cred)

@app.route("/")
def main():
    return render_template("index.html")


@app.route("/Login")  # index
def login():
    return render_template("login.html")

@app.route("/onSubmitLogin", methods=["POST"])  #login #for different logins based on role
def onSubmitlogin():
    if request.method == 'POST':
        try:
            id= request.form['id']
            password= request.form['password']
            print("hellohii")
            db = firestore.client()
            print("database")
            id = id
            # password = base64.b64encode(password.encode("utf-8"))
            password=password
            print("details entered")
            print(password)
            docref = db.collection('Login').where('id', '==', id).where('password', '==', password).get()
            print("docref initialised")
            for doc in docref:
                if doc.to_dict()['id'] and doc.to_dict()['password']:
                    print('Login Successfully')
                    role = doc.to_dict()['role']
                    print(role)
            if role == 'Organization':
                return render_template("org_Landing.html")
            elif role == 'Instructor':
                return render_template("inst_Landing.html")
            elif role == 'Student':
                return render_template("stu_Landing.html")
            else:
                return render_template("stu_Landing.html")
        except:
            #to put alert message if not a organisation, instructor, student
            print("hello")
            return render_template("stu_Landing.html")


@app.route("/OrgRegistration")  # login
def org_registration():
    return render_template("orgRegistration.html")

@app.route("/org_registration", methods=["POST"]) #for org registration on submit in orgRgistration page
def org_reg():
    if request.method == 'POST':
        try:
            orgId = request.form['org_id']
            orgName = request.form['org_name']
            emailId=request.form['email_id']
            password=request.form['password']
            conf_password=request.form['password_two']
            # if password == conf_password:
            db = firestore.client()

            enc_password = base64.b64encode(password.encode("utf-8"))
            print(str(enc_password))
    # docref = db.collection_group(u'1JS').where(u'org_id', u'==', u'1JS').get()

            data = {
                'email_id':emailId,
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
            return render_template("orgRegistration.html")
        except:
            #to put a alert msg if dteails not entered properly
            return render_template("orgRegistration.html")


@app.route("/InstructorRegistration")  # login
def ins_registration():
    return render_template("instRegistration.html")

@app.route("/inst_registration", methods=["POST"]) #for instructor registration on submit in instRegistartion
def inst_reg():
    if request.method == 'POST':
        try:
            instId=request.form['instructor_id']
            instName=request.form['instructor_name']
            orgId = request.form['org_id']
            emailId = request.form['email_id']
            designation=request.form['designation']
            dept=request.form['department']
            password = request.form['password']
            password2 = request.form['password_two']
            # if password==password2: #some more conditions to be written
            db = firestore.client()

            docref = db.collection('Organization').where('org_id', '==', orgId).get()
            for doc in docref:
                if doc.to_dict()['org_id']:
                #encrypting password
                    enc_password = base64.b64encode(password.encode("utf-8"))
                    print(str(enc_password))

                    status = False

                    data = {
                        'approval_status': status,
                        'department': dept,
                        'designation': designation,
                        'email_id': emailId,
                        'instructor_id': instId,
                        'instructor_name': instName,
                        'org_id': orgId,
                        'password': enc_password
                    }

                    docref = db.collection('Organization').document(data['org_id']).collection('Instructor').document(
                        data['instructor_id'])

                    docref.set(data)
                    return render_template("instRegistration.html")

            # else:
            #     # write a alert page for entering password correctly
        except:
            msg="Please verify the Organization ID"
            return render_template("instRegistration.html", msg=msg)


@app.route("/StudentRegistration")  # login
def stud_registration():
    return render_template("stuRegistration.html")


@app.route("/stu_registration", methods=["POST"]) #for student registration on submit in stuRegistration
def stu_reg():
    if request.method == 'POST':
        try:
            stuId = request.form['student_id']
            stuName = request.form['student_name']
            orgId = request.form['org_id']
            emailId = request.form['email_id']
            password = request.form['password']
            password2 = request.form['password_two']
            level=request.form['level']
            sec=request.form['section']
            stuDept=request.form['department'] #to add the field in database
            # if password == password2:  # some more conditions to be written
            db = firestore.client()
            docref = db.collection('Organization').where('org_id', '==', orgId).get()
            for doc in docref:
                if doc.to_dict()['org_id']:
                    # encrypting password
                    enc_password = base64.b64encode(password.encode("utf-8"))
                    print(str(enc_password))

                    status = False

                    data = {
                        'approval_status': status,
                        'department' : stuDept,
                        'level': level,
                        'section': sec,
                        'email_id': emailId,
                        'student_id': stuId,
                        'student_name': stuName,
                        'org_id': orgId,
                        'password': enc_password
                    }

                    docref = db.collection('Organization').document(data['org_id']).collection('Student').document(
                        data['student_id'])

                    docref.set(data)
                    return render_template("stuRegistration.html")

        except:
            msg="Please verify the Organization ID"
            return render_template("stuRegistration.html", msg=msg)



@app.route("/OrgLanding")  # OrgLanding  #org_Instructor #org_Student
def org_landing():
    return render_template("org_Landing.html")

# @app.route("/OrgLanding")  # OrgLanding  #org_Instructor #org_Student
# def org_landing():
#     return render_template("org_Landing.html")



@app.route("/InstructorLanding")   #instructorLanding
def inst_landing():
    return render_template("inst_Landing.html")


@app.route("/StudentLanding")  #studentLanding
def stud_landing():
    return render_template("stu_Landing.html")


@app.route("/OrgInstructor")  # organisationlanding
def org_Instructor():
    return render_template("org_Instructor.html")


@app.route("/OrgStudent")  # organisationlanding
def org_Student():
    return render_template("org_Student.html")


if __name__ == "__main__":
    app.run()
