from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import tempfile, os, json, asyncio
from typing import Optional

from resume_parser import parse_resume_with_groq
from skill_analyzer import analyze_skills_with_groq
from learning_path import (
    generate_assessment_questions,
    generate_learning_path,
)
from interview import (
    create_interview_state,
    generate_question,
    evaluate_answer,
    decide_next_step,
    update_state,
    generate_report,
)

app = FastAPI(title="CareerCopilot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── In-memory session store ──────────────────────────────────────────────────
sessions: dict = {}


# ─── Step 1: Upload resume + pick role ────────────────────────────────────────
@app.post("/api/start")
async def start_session(
    role: str = Form(...),
    resume: UploadFile = File(...),
):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await resume.read())
        tmp_path = tmp.name

    try:
        parsed = parse_resume_with_groq(tmp_path)
        analysis = analyze_skills_with_groq(role=role, data=parsed)
    finally:
        os.unlink(tmp_path)

    import uuid
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "role": role,
        "parsed_resume": parsed,
        "analysis": analysis,
    }

    return {
        "session_id": session_id,
        "analysis": analysis,
        "skills": parsed.get("skills", []),
        "projects": parsed.get("projects", []),
        "experience_years": parsed.get("experience_years", 0),
    }


# ─── Learning Path: get assessment questions ──────────────────────────────────
@app.post("/api/learning/questions")
async def get_questions(data: dict):
    sid = data.get("session_id")
    if sid not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    s = sessions[sid]
    questions = generate_assessment_questions(s["role"], s["analysis"])
    s["assessment_questions"] = questions
    return {"questions": questions}


# ─── Learning Path: submit answers + generate path ────────────────────────────
@app.post("/api/learning/generate")
async def generate_path(data: dict):
    sid = data.get("session_id")
    answers = data.get("answers", {})
    if sid not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    s = sessions[sid]
    path = generate_learning_path(
        role=s["role"],
        analysis=s["analysis"],
        assessment_answers=answers,
    )
    s["learning_path"] = path
    return path


# ─── Interview: start ─────────────────────────────────────────────────────────
@app.post("/api/interview/start")
async def start_interview(data: dict):
    sid = data.get("session_id")
    if sid not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    s = sessions[sid]
    interview_state = create_interview_state(s["role"], s["analysis"])
    s["interview_state"] = interview_state
    s["action"] = "new"

    question = generate_question(interview_state, "new")
    interview_state["current_question"] = question

    return {
        "question": question,
        "question_number": 1,
        "max_questions": interview_state["max_questions"],
        "current_skill": interview_state["current_skill"],
        "difficulty": interview_state["difficulty"],
    }


# ─── Interview: submit answer ─────────────────────────────────────────────────
@app.post("/api/interview/answer")
async def submit_answer(data: dict):
    sid = data.get("session_id")
    answer = data.get("answer", "")
    if sid not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    s = sessions[sid]
    ist = s["interview_state"]

    question = ist.get("current_question", "")
    evaluation = evaluate_answer(question, answer)
    action = decide_next_step(ist, evaluation)
    update_state(ist, question, answer, evaluation)
    s["action"] = action

    done = ist["question_count"] >= ist["max_questions"]

    if done:
        report = generate_report(ist)
        s["interview_report"] = report
        return {
            "evaluation": evaluation,
            "done": True,
            "report": report,
        }

    next_q = generate_question(ist, action)
    ist["current_question"] = next_q

    return {
        "evaluation": evaluation,
        "done": False,
        "question": next_q,
        "question_number": ist["question_count"] + 1,
        "max_questions": ist["max_questions"],
        "current_skill": ist["current_skill"],
        "difficulty": ist["difficulty"],
    }


# ─── Health ───────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok"}
