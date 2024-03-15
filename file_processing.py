import os
import fitz  
from google.cloud import vision

def allowed_file(filename, allowed_extensions={'png', 'jpg', 'jpeg', 'pdf'}):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def detect_text(image_path):
    client = vision.ImageAnnotatorClient()
    with open(image_path, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    annotations = response.text_annotations
    if response.error.message:
        raise Exception(f'{response.error.message}')
    return annotations[0].description if annotations else ''

def extract_text_from_pdf(pdf_path, upload_folder):
    doc = fitz.open(pdf_path)
    text = ""
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap()
        output_image_path = os.path.join(upload_folder, f"output_page_{page_num}.png")
        pix.save(output_image_path)
        text += detect_text(output_image_path) + "\n"
    return text

def process_file(file_path, allowed_extensions):
    if not allowed_file(file_path, allowed_extensions):
        raise ValueError("Unsupported file type.")
    if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
        return detect_text(file_path)
    elif file_path.lower().endswith('.pdf'):
        upload_folder = os.path.dirname(file_path)
        return extract_text_from_pdf(file_path, upload_folder)
