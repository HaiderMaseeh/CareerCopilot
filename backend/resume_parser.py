import pdfplumber
from groq import Groq
import json
from dotenv import load_dotenv
import os
load_dotenv()


client = Groq(
    api_key=os.getenv("Resume_parser"),
)


def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def parse_resume_with_groq(pdf_path):
    text = extract_text_from_pdf(pdf_path)

    schema = {
    "type": "object",
    "properties": {

        "skills": {
            "type": "array",
            "items": {"type": "string"}
        },

        "experience_years": {
            "type": "number"
        },

        "projects": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "details": {"type": "string"},
                    "summary": {"type": "string"}
                },
                "required": [
                    "name",
                    "details",
                    "summary"
                ],
                "additionalProperties": False
            }
        }

    },

        "required": [
            "skills",
            "experience_years",
            "projects"
        ],

        "additionalProperties": False
    }

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",

        messages=[
            {
                "role": "system",
                "content": (
                    "Extract resume skills and projects only. "
                    "Return only valid JSON matching the schema. "
                    "If a value is missing, use an empty string or empty list. "
                    "Do not invent information."
                )
            },
            {
                "role": "user",
                "content": f"""
Extract:

- skills
- total years of experience
- projects

Rules:
- Calculate total professional experience in years.
- If no professional experience exists, return 0.
-For each project:

- summary: maximum 50 words
- details: maximum 100 words

Return concise output.
- Return only valid JSON.

Resume text:
{text}
"""
            }
        ],
        
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "resume_extraction",
                "strict": True,
                "schema": schema
            }
        }
    )

    return json.loads(response.choices[0].message.content)