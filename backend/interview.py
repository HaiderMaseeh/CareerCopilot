from groq import Groq
import json
import os
from dotenv import load_dotenv

load_dotenv()
client = Groq(
    api_key=os.getenv("Interview_agent"),
)


def create_interview_state(role, analysis):

    strong_skills = analysis.get("strong_skills", [])

    return {
        "role": role,
        "resume_score": analysis["resume_score"],
        "strong_skills": strong_skills,
        "weak_skills": analysis.get("weak_skills", []),
        "recommended_skills": analysis.get(
            "recommended_skills",
            []
        ),

        "question_count": 0,
        "max_questions": 10,

        "current_skill":
            strong_skills[0]
            if strong_skills
            else role,

        "difficulty": "easy",

        "last_score": None,

        "history": []
    }


def evaluate_answer(question, answer):

    prompt = f"""
You are a senior technical interviewer.

Question:
{question}

Candidate Answer:
{answer}

Evaluate the answer.

Scoring:

0-2 = nonsense or empty
3-4 = poor
5-6 = average
7-8 = good
9-10 = excellent

Return ONLY valid JSON.

{{
    "score": 0,
    "follow_up_needed": false,
    "strengths": [],
    "weaknesses": []
}}
"""

    try:

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            response_format={
                "type": "json_object"
            },
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0
        )

        content = response.choices[0].message.content

        return json.loads(content)

    except Exception as e:

        print("Evaluation Error:", e)

        return {
            "score": 0,
            "follow_up_needed": False,
            "strengths": [],
            "weaknesses": []
        }


def decide_next_step(state, evaluation):

    score = evaluation["score"]

    if score <= 3:

        state["difficulty"] = "easy"

        return "follow_up"

    elif score <= 6:

        state["difficulty"] = "medium"

        return "same_topic"

    else:

        state["difficulty"] = "hard"

        skills = state["strong_skills"]

        if skills:

            current = state["current_skill"]

            if current in skills:

                idx = skills.index(current)

                if idx + 1 < len(skills):

                    state["current_skill"] = skills[idx + 1]

        return "next_topic"


def generate_question(state, action="new"):

    history = state["history"][-3:]

    prompt = f"""
You are a senior interviewer.

Candidate Role:
{state["role"]}

Current Skill:
{state["current_skill"]}

Difficulty:
{state["difficulty"]}

Question Number:
{state["question_count"] + 1}

Recent History:
{history}

Action:
{action}

Rules:

1. Ask only ONE question.
2. Maximum 2 sentences.
3. Interview style.
4. No long scenarios.
5. No huge paragraphs.
6. Focus on current skill.
7. If action is follow_up ask deeper.
8. If action is next_topic move to new skill.
9. Return question only.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.7
    )

    return response.choices[0].message.content.strip()


def update_state(
    state,
    question,
    answer,
    evaluation
):

    state["history"].append(
        {
            "question": question,
            "answer": answer,
            "score": evaluation["score"]
        }
    )

    state["last_score"] = evaluation["score"]

    state["question_count"] += 1

    return state


def generate_report(state):

    prompt = f"""
You are a hiring manager.

Interview History:

{json.dumps(state["history"], indent=2)}

Generate JSON:

{{
    "technical_score": 0,
    "communication_score": 0,
    "strengths": [],
    "weaknesses": [],
    "hiring_recommendation": "",
    "overall_feedback": ""
}}
"""

    try:

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            response_format={
                "type": "json_object"
            },
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return json.loads(
            response.choices[0].message.content
        )

    except Exception as e:

        return {
            "error": str(e)
        }


def multiline_input():

    print("\nEnter answer.")
    print("Type END on a new line when finished.\n")

    lines = []

    while True:

        line = input()

        if line.strip().upper() == "END":
            break

        lines.append(line)

    return "\n".join(lines)


# =========================
# LANGGRAPH INTERVIEW NODES
# =========================

def create_interview_node(state):

    state["interview_state"] = create_interview_state(
        state["role"],
        state["analysis"]
    )

    state["action"] = "new"

    return state

def generate_question_node(state):

    question = generate_question(
        state["interview_state"],
        state["action"]
    )

    state["current_question"] = question

    print("\n")
    print("=" * 80)

    q_no = (
        state["interview_state"]["question_count"]
        + 1
    )

    print(f"Question {q_no}")

    print(question)

    return state

def answer_node(state):

    answer = multiline_input()

    state["current_answer"] = answer

    return state

def evaluate_node(state):

    evaluation = evaluate_answer(
        state["current_question"],
        state["current_answer"]
    )

    state["evaluation"] = evaluation

    print(
        "\nScore:",
        evaluation["score"]
    )

    return state
def update_interview_node(state):

    update_state(
        state["interview_state"],
        state["current_question"],
        state["current_answer"],
        state["evaluation"]
    )

    state["action"] = decide_next_step(
        state["interview_state"],
        state["evaluation"]
    )

    return state

def interview_router(state):

    interview_state = state["interview_state"]

    if (
        interview_state["question_count"]
        >= interview_state["max_questions"]
    ):

        return "report"

    return "continue"


def report_node(state):

    report = generate_report(
        state["interview_state"]
    )

    state["interview_report"] = report

    return state


