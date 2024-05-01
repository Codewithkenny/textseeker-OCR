import os
import tempfile
from google.cloud import vision
import fitz  # PyMuPDF

def is_allowed_file(filename, allowed_extensions={'png', 'jpg', 'jpeg', 'pdf'}):
    """Check if the file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def detect_text_from_image(image_path):
    """Detect and extract text from an image using Google Cloud Vision API."""
    client = vision.ImageAnnotatorClient()
    with open(image_path, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    if response.error.message:
        raise RuntimeError(f'Error detecting text: {response.error.message}')
    return response.text_annotations[0].description if response.text_annotations else ''

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF by converting each page to an image and extracting text."""
    text = []
    with tempfile.TemporaryDirectory() as tempdir:
        doc = fitz.open(pdf_path)
        for page in doc:
            pix = page.get_pixmap()
            output_image_path = os.path.join(tempdir, f"page_{page.number}.png")
            pix.save(output_image_path)
            text.append(detect_text_from_image(output_image_path))
    return "\n".join(text)

def process_file(filepath):
    """Process the file based on its type and extract text."""
    _, file_extension = os.path.splitext(filepath)
    if file_extension.lower() in ['.png', '.jpg', '.jpeg']:
        return detect_text_from_image(filepath)
    elif file_extension.lower() == '.pdf':
        return extract_text_from_pdf(filepath)
    else:
        raise ValueError("Unsupported file type.")
