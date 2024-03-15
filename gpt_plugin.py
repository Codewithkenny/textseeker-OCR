import os
import openai
from google.cloud import vision
import fitz  

class GPTPlugin:
    def __init__(self, openai_api_key):
        self.openai_api_key = openai_api_key
        openai.api_key = self.openai_api_key

    def process_file(self, file_path):
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            extracted_text = self._detect_text(file_path)
        elif file_path.lower().endswith('.pdf'):
            extracted_text = self._extract_text_from_pdf(file_path)
        else:
            raise ValueError("Unsupported file type.")
        return self._get_gpt_response(extracted_text)

    def _detect_text(self, image_path):
        client = vision.ImageAnnotatorClient()
        with open(image_path, 'rb') as image_file:
            content = image_file.read()
        image = vision.Image(content=content)
        response = client.text_detection(image=image)
        if response.error.message:
            raise Exception(f'{response.error.message}')
        return response.text_annotations[0].description if response.text_annotations else ''

    def _extract_text_from_pdf(self, pdf_path):
        doc = fitz.open(pdf_path)
        text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap()
            output_image_path = f"temp_page_{page_num}.png"
            pix.save(output_image_path)
            text += self._detect_text(output_image_path) + "\n"
            # Here, implement file cleanup if necessary
        return text

    def _get_gpt_response(self, extracted_text):
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=extracted_text,
            temperature=0.7,
            max_tokens=150
        )
        return response.choices[0].text.strip()
