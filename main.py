import pyrebase
from flask import Flask, flash, redirect, render_template, request, session, abort, url_for,Response
import cv2
import os
import face_recognition

app = Flask(__name__)       #Initialze flask constructor
video=cv2.VideoCapture(1)

#Add your own details
config = {

    "projectId": "chatapp-f550f",
    "storageBucket": "chatapp-f550f.appspot.com",
    "messagingSenderId": "709295344868",
    "appId": "1:709295344868:web:dda9f4ccfde3a24b0170f1",
    "measurementId": "G-HRJWDK5ZQ7",
  "apiKey": "AIzaSyDbSsqUM7ce2EcMdZRXOAjQZk0TL6NcF9o",
  "authDomain": "chatapp-f550f.firebaseapp.com",
  "databaseURL": "PASTE_HERE",
}

#initialize firebase
firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
db = firebase.database()

#Initialze person as dictionary
person = {"is_logged_in": False, "name": "", "email": "", "uid": ""}
KNOWN_FACES_DIR = 'known_faces'
TOLERANCE = 0.4

# Load known faces and labels from the 'known_faces' directory
known_faces_encodings = []
known_faces_labels = []

for person_name in os.listdir(KNOWN_FACES_DIR):
    person_dir = os.path.join(KNOWN_FACES_DIR, person_name)
    if not os.path.isdir(person_dir):
        continue  # Skip if not a directory
    for filename in os.listdir(person_dir):
        image_path = os.path.join(person_dir, filename)
        image = face_recognition.load_image_file(image_path)
        face_locations = face_recognition.face_locations(image)
        if len(face_locations) > 0:
            face_location = face_locations[0]  # Get the location of the top face
            face_encodings = face_recognition.face_encodings(image, [face_location])
            known_faces_encodings.extend(face_encodings)
            known_faces_labels.extend([person_name] * len(face_encodings))  # Repeat label for each encoding


def generate_frames():
    video_capture = cv2.VideoCapture(0)
    while True:
        ret, frame = video_capture.read()
        
        if not ret:
            break
        
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        
        for face_location in face_locations:
            face_encodings = face_recognition.face_encodings(rgb_frame, [face_location])
            for face_encoding in face_encodings:
                results = face_recognition.compare_faces(known_faces_encodings, face_encoding, TOLERANCE)
                match = "Unknown"
                if True in results:
                    match = known_faces_labels[results.index(True)]
                top_left = (face_location[3], face_location[0])
                bottom_right = (face_location[1], face_location[2])
                cv2.rectangle(frame, top_left, bottom_right, (0, 255, 0), 2)
                cv2.putText(frame, match, (face_location[3] + 6, face_location[2] - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')



@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

#Login
@app.route("/")
def login():
    return render_template("login.html")

#Sign up/ Register
@app.route("/signup")
def signup():
    return render_template("signup.html")

#Welcome page
@app.route("/welcome")
def welcome():
    if person["is_logged_in"] == True:
        return render_template("welcome.html", email = person["email"], name = person["name"])
    else:
        return redirect(url_for('login'))

#If someone clicks on login, they are redirected to /result
@app.route("/result", methods = ["POST", "GET"])
def result():
    if request.method == "POST":        #Only if data has been posted
        result = request.form           #Get the data
        email = result["email"]
        password = result["pass"]
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            global person
            person["is_logged_in"] = True
            person["email"] = user["email"]
            person["uid"] = user["localId"]
            #Get the name of the user
            data = db.child("users").get()
            person["name"] = data.val()[person["uid"]]["name"]
            #Redirect to welcome page
            return redirect(url_for('welcome'))
        except:
            #If there is any error, redirect back to login
            return redirect(url_for('login'))
    else:
        if person["is_logged_in"] == True:
            return redirect(url_for('welcome'))
        else:
            return redirect(url_for('login'))

#If someone clicks on register, they are redirected to /register
@app.route("/register", methods = ["POST", "GET"])
def register():
    if request.method == "POST":        #Only listen to POST
        result = request.form           #Get the data submitted
        email = result["email"]
        password = result["pass"]
        name = result["name"]
        try:
            auth.create_user_with_email_and_password(email, password)
            user = auth.sign_in_with_email_and_password(email, password)
            global person
            person["is_logged_in"] = True
            person["email"] = user["email"]
            person["uid"] = user["localId"]
            person["name"] = name
            data = {"name": name, "email": email}
            db.child("users").child(person["uid"]).set(data)
            return redirect(url_for('welcome'))
        except:
            return redirect(url_for('register'))

    else:
        if person["is_logged_in"] == True:
            return redirect(url_for('welcome'))
        else:
            return redirect(url_for('register'))

if __name__ == "__main__":
    app.run()
