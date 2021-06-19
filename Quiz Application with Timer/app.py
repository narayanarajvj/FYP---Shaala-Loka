import firebase_admin
from firebase_admin import credentials, firestore, storage
from flask import Flask, render_template, request, flash, redirect, url_for

app = Flask(__name__)
app.secret_key = 'vijay'

cred = credentials.Certificate("shaala-loka-firebase-adminsdk-xsp4x-5eea3da522.json")
firebase_admin.initialize_app(cred, {
'storageBucket': 'shaala-loka.appspot.com'
})

db = firestore.client()


@app.route("/")
def main():
    
    return render_template("inst_Quiz.html")

if __name__ == '__main__':
    app.run(debug=True)
