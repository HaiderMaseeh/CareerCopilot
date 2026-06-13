from groq import Groq
import json

import os
from dotenv import load_dotenv
load_dotenv()

client = Groq(
    api_key=os.getenv("Skill_Analyzer"),
)


def analyze_skills_with_groq(role, data):
    skills = data.get("skills", [])

    schema = {
    "type": "object",
    "properties": {

        "resume_score": {
            "type": "integer"
        },

        "strong_skills": {
            "type": "array",
            "items": {"type": "string"}
        },

        "weak_skills": {
            "type": "array",
            "items": {"type": "string"}
        },

        "recommended_skills": {
            "type": "array",
            "items": {"type": "string"}
        },

        "improvement_priority": {
            "type": "array",
            "items": {"type": "string"}
        },

        "summary": {
            "type": "string"
        }

        },

            "required": [
                "resume_score",
                "strong_skills",
                "weak_skills",
                "recommended_skills",
                "improvement_priority",
                "summary"
            ],

            "additionalProperties": False
       }
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a career skills evaluator. "
                    "Given a target role and a list of skills extracted "
                    "from a resume, identify strong skills, weak skills, "
                    "and missing skills that should be learned."
                )
            },
            {
                "role": "user",
                "content": f"""
Role:
{role}

Resume Skills:
{skills}

Instructions:

1. strong_skills:
   - Select only from the provided skills.
   - Skills that are highly relevant to the role.

2. weak_skills:
   - Select only from the provided skills.
   - Skills that contribute less to the role.

3. recommended_skills:
   - Suggest important skills for the role.
   - Do NOT include skills already present.

4. summary:
   - Brief evaluation in 2-3 sentences.

5. resume_score:
   - Score from 0-100
   - Based on suitability for the target role.
   - Consider:
       • relevant skills
       • missing skills
       • project relevance

6. improvement_priority:
   - Top 5 skills/topics to learn next.
   - Ordered from highest impact to lowest.

Return ONLY valid JSON.
"""
            }
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "skill_analysis",
                "strict": True,
                "schema": schema
            }
        }
    )

    return json.loads(response.choices[0].message.content)