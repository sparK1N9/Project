# Currently this code assumes that the user will input correct information and does not check if the input is valid.
#pip install pymongo
import os
import gridfs
import ResumeParser
from flask import Flask, render_template, request, redirect, url_for, session, escape
from pymongo import MongoClient
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'C:\\Users\\sparK1N9\\Desktop\\CS4523\\Project' #where the user-uploaded files will be temporarily saved

app = Flask(__name__)
db = MongoClient('mongodb://imran:password12345@ds113626.mlab.com:13626/profile-pal').get_database()
users = db.users
feedback_resume = db.Feedback_Resume
feedback_picture = db.Feedback_Picture
fs=gridfs.GridFS(db)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    if 'email' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['post', 'get'])
def login():
    if request.method=='POST':
        email = request.form["inputEmail"]
        password = request.form["inputPassword"]
        credential = {'email':email,'password':password}
        if not users.find_one(credential):
            return 'Incorrect login credential. <a href="http://127.0.0.1:13000/">Go back.</a>'
        session['email'] = email
        return redirect(url_for('dashboard'))
    return render_template("login.html")

@app.route('/signup', methods=['post', 'get'])
def signup():
    if request.method=='POST':
        name = request.form["name"].split()
        fname = name[0]
        lname = name[len(name) - 1]
        email = request.form["email"]
        password = request.form["password"]
        credential = {'email':email}
        if not users.find_one(credential):  
            credential = {'email':email,'password':password,'first_name':fname,'last_name':lname}
            db.users.insert_one(credential)
        else: return 'You have already signed up. <a href="http://127.0.0.1:13000/">Go back.</a>'
        session['email'] = email
        return redirect(url_for('dashboard'))
    return render_template('signup.html')

@app.route('/editProfile', methods=['post', 'get'])
def editprofile():
    if 'email' not in session: return '<a href="http://127.0.0.1:13000/">log in</a> first!' #requires an account to access this page
    flag = 0 # 0: no error, 1: password and confirm password not the same, 2: the new email is already associated with an account
    imageFlag = 0 # 0: no uploaded photo, 1: user has previously uploaded a photo
    if request.method=='POST':
        if 'confirm' in request.form:
            fname = request.form["firstName"]
            lname = request.form["lastName"]
            email = request.form["email"]
            confirmPassword = request.form["confirmPassword"]
            password = request.form["password"]
            credential = {'email':email}
            if password == confirmPassword and (email == session['email'] or not users.find_one(credential)):
                credential = {'email':email,'password':password,
                              'first_name':fname,'last_name':lname}
                users.find_one_and_update({'email': session['email']}, {'$inc': {'count': 1}, '$set':credential})
                session['email'] = email
                return redirect(url_for('dashboard'))
            elif password != confirmPassword:
                flag = 1
            elif email != session['email'] and users.find_one(credential):
                flag = 2
        if 'file' in request.form:
            file = request.files['resume']
            photo = request.files['photo']
            if file:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                parsed = ResumeParser.parseResume(filename, UPLOAD_FOLDER+'\\'+filename)
                users.find_one_and_update({'email': session['email']}, {'$inc': {'count': 1}, '$set':{'resume':parsed}})
                os.remove(UPLOAD_FOLDER+'\\'+filename)
            if photo:
                filename = secure_filename(photo.filename)
                file_id = fs.put(photo,filename=filename)
                data={'image':file_id}
                users.find_one_and_update({'email': session['email']}, {'$inc': {'count': 1}, '$set':data})
    user_info = users.find_one({'email':session['email']})
    if fs.exists(user_info['image']):
        imageFlag = 1
        image_data = fs.get(user_info['image'])
        f = open(UPLOAD_FOLDER+'\\static\\photo.jpg', 'wb')
        f.write(image_data.read())
        f.close()
    elif os.path.isfile(UPLOAD_FOLDER+'\\static\\photo.jpg'):
        os.remove(UPLOAD_FOLDER+'\\static\\photo.jpg')
#example format for user_info:
#{'email': 'ia761@nyu.edu', 'resume': 'resume', 'last_name': 'Ahmed', 'image': ObjectId('5a19230f7c051e1a6c474c67'), 'first_name': 'Imran', 'password': 'pass'}
    return render_template("profile2.html", flag = flag, user_info = user_info, imgFlag = imageFlag)

@app.route('/dashboard')
def dashboard():
    return render_template("dashboard.html")

@app.route("/profile")
def profile():
    imageFlag = 0 # 0: no uploaded photo, 1: user has previously uploaded a photo
    if 'email' not in session: return '<a href="http://127.0.0.1:13000/">log in</a> first!' #requires an account to access this page
    user_info = users.find_one({'email':session['email']})
    if fs.exists(user_info['image']):
        imageFlag = 1
        image_data = fs.get(user_info['image'])
        f = open(UPLOAD_FOLDER+'\\static\\photo.jpg', 'wb')
        f.write(image_data.read())
        f.close()
    elif os.path.isfile(UPLOAD_FOLDER+'\\static\\photo.jpg'):
        os.remove(UPLOAD_FOLDER+'\\static\\photo.jpg')
    return render_template("profile.html", user_info = user_info, imgFlag = imageFlag)

@app.route('/logout')
def logOut():
    session.pop('email', None)
    return 'You have logged out. <a href="http://127.0.0.1:13000/">Go back.</a>'


app.secret_key = 'A0Zr98j/3yX R~XXH!jN]LWX/,?RT'
app.run("127.0.0.1", 13000, debug=True)