import email
from flask import Flask, render_template, request, redirect, jsonify, url_for, session, flash
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
import PyPDF2 
from datetime import datetime
import docx2txt
from docx import Document  # For processing DOCX files
from flask_cors import CORS
import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin.exceptions import FirebaseError
from firebase_admin import credentials, auth, initialize_app
from firebase_admin import credentials, auth
from firebase_admin import firestore

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
ocr_history = []

# Initialize Firebase Admin
cred = credentials.Certificate('serviceAccountKey.json')
firebase_admin.initialize_app(cred)
db = firestore.client()



load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY')  
CORS(app, origins="*")  
CORS(app, supports_credentials=True)

app.config.update(
    SESSION_COOKIE_SECURE=True,  # Only send cookie over HTTPS. Set to False if you are not using HTTPS
    SESSION_COOKIE_HTTPONLY=True,  # Prevents client-side JS from reading the cookie
    SESSION_COOKIE_SAMESITE='Lax',  # Or 'None' if you need to send cookies for cross-site requests
)

UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads')
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'docx', 'txt', 'tif', 'tiff'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_ocr(file_path):
    try:
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.tif', '.tiff')):
            ocr_result = pytesseract.image_to_string(Image.open(file_path))
        elif file_path.lower().endswith('.pdf'):
            # Extract text from PDF using PyPDF2
            with open(file_path, 'rb') as pdf_file:
                reader = PyPDF2.PdfReader(pdf_file)
                ocr_result = ''
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    ocr_result += page.extract_text()
        elif file_path.lower().endswith('.docx'):
            # Extract text from DOCX using python-docx
            doc = Document(file_path)
            ocr_result = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        elif file_path.lower().endswith('.txt'):
            
            # Read text from plain text file
            with open(file_path, 'r') as file:
                ocr_result = file.read()
        else:
            return 'Unsupported file format for OCR'
        
        return ocr_result.strip()  # Remove leading/trailing whitespaces
    except Exception as e:
        return f'Error processing OCR: {str(e)}'



app.config.update({
    'UPLOAD_FOLDER': UPLOAD_FOLDER,
    'MAX_CONTENT_LENGTH': MAX_CONTENT_LENGTH
})

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def home():
     return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html')

@app.route('/sessionLogin', methods=['POST'])
def session_login():
    # Get the ID token sent from the client
    id_token = request.json.get('idToken')
    try:
        # Verify the ID token and extract the user's Firebase UID
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        user = auth.get_user(uid)
        session['user_id'] = uid
        session['email'] = user.email
        return jsonify({"status": "success"}), 200
    except firebase_admin.auth.AuthError:
        return jsonify({"status": "failure", "message": "Authentication failed."}), 401


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            user_record = auth.create_user(email=email, password=password)  # Create user without username
            # Prepare user data to save
            user_data = {
                "email": email,
            }
            # Save user data to Firestore in the 'users' collection
            db.collection('users').document(user_record.uid).set(user_data)
            flash('Registration successful. Please log in.')
            return redirect(url_for('login'))
        except Exception as e:
            print(e)
            return render_template('register.html', message="Registration failed")
    return render_template('register.html')



  

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash("Please log in to access the dashboard.")
        return redirect(url_for('login'))
    # Move the email retrieval outside of the conditional check
    username = session.get('email')
    # Now, if logged in, render the dashboard template with the email variable
    return render_template('dashboard.html', email=email)



@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Make sure to remove 'user_id'
    session.pop('email', None)
    return redirect(url_for('home'))


@app.route('/uploads', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        ocr_result = process_ocr(file_path)
        # Save a summary of the OCR result with timestamp and date
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ocr_summary = f"{timestamp}: OCR performed on file: {filename}"
        response = {'ocr_result': ocr_result}
        ocr_history.append(ocr_result)
        return jsonify(response)
    else:
        flash('Invalid file format')
        return redirect(request.url)
    
@app.route('/history')
def get_history():
     return jsonify({'history': ocr_history})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
