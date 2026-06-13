from typing import TypedDict


class CareerState(TypedDict):

    # inputs
    resume_path: str
    role: str
    choice: str

    # shared
    parsed_resume: dict
    analysis: dict

    # learning path
    assessment_questions: list
    assessment_answers: dict
    learning_path: dict

    # interview
    interview_state: dict
    current_question: str
    current_answer: str
    evaluation: dict
    action: str
    interview_report: dict