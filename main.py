from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from flask_cors import CORS
import os
import mimetypes
from file_processing import process_file, allowed_file  # Ensure allowed_file checks MIME types now
from gpt_service import get_gpt_response

app = Flask(__name__)
CORS(app)

app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB upload limit
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
ALLOWED_MIME_TYPES = {'image/png', 'image/jpeg', 'application/pdf'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def home():
    return 'Welcome to TextSeeker!'

@app.route('/uploads', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if not allowed_file(file.filename, ALLOWED_EXTENSIONS):
        return jsonify({"error": "Unsupported file extension"}), 400
    
    # Check MIME type for additional security
    mime_type, _ = mimetypes.guess_type(file.filename)
    if mime_type not in ALLOWED_MIME_TYPES:
        return jsonify({"error": "Unsupported MIME type"}), 400
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    try:
        extracted_text = process_file(filepath, ALLOWED_EXTENSIONS)
        insights = get_gpt_response(extracted_text)
        return jsonify({"insights": insights}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
