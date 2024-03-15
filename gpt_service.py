import os
import openai

openai.api_key = os.getenv('OPENAI_API_KEY')

def get_gpt_response(extracted_text):
    response = openai.Completion.create(
        model="text-davinci-002",  # Adjust model as necessary
        prompt=extracted_text,
        temperature=0.7,
        max_tokens=150
    )
    return response.choices[0].text.strip()
