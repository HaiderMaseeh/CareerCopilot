from langgraph.graph import (
    StateGraph,
    END
)

from state import CareerState

from resume_parser import (
    parse_resume_with_groq
)

from skill_analyzer import (
    analyze_skills_with_groq
)

from interview import *

from learning_path import *

def resume_node(state):

    parsed_resume = parse_resume_with_groq(
        state["resume_path"]
    )

    state["parsed_resume"] = parsed_resume

    return state

def analysis_node(state):

    analysis = analyze_skills_with_groq(
        role=state["role"],
        data=state["parsed_resume"]
    )

    state["analysis"] = analysis

    return state

def route_choice(state):

    return state["choice"]

builder = StateGraph(
    CareerState
)

builder.add_node(
    "resume",
    resume_node
)

builder.add_node(
    "skill_analysis",
    analysis_node
)
builder.add_node("generate_assessment_questions", assessment_questions_node)

builder.add_node("collect_assessment_answers", assessment_answers_node)


builder.add_node("generate_learning_path", learning_path_node)


builder.add_node(
    "display_learning_path",
    display_learning_path_node
)

builder.add_node(
    "create_interview",
    create_interview_node
)

builder.add_node(
    "generate_question",
    generate_question_node
)

builder.add_node(
    "answer",
    answer_node
)

builder.add_node("evaluate_answer", evaluate_node)

builder.add_node(
    "update_interview",
    update_interview_node
)

builder.add_node("generate_report", report_node)
builder.set_entry_point(
    "resume"
)

# ==========================
# Resume -> Analysis
# ==========================

builder.add_edge(
    "resume",
    "skill_analysis"
)

builder.add_conditional_edges(
    "skill_analysis",
    route_choice,
    {
        "learning": "generate_assessment_questions",
        "interview": "create_interview"
    }
)

# ==========================
# Learning Path Flow
# ==========================

builder.add_edge(
    "generate_assessment_questions",
    "collect_assessment_answers"
)

builder.add_edge(
    "collect_assessment_answers",
    "generate_learning_path"
)

builder.add_edge(
    "generate_learning_path",
    "display_learning_path"
)

builder.add_edge(
    "display_learning_path",
    END
)

# ==========================
# Interview Flow
# ==========================

builder.add_edge(
    "create_interview",
    "generate_question"
)

builder.add_edge(
    "generate_question",
    "answer"
)

builder.add_edge(
    "answer",
    "evaluate_answer"
)

builder.add_edge(
    "evaluate_answer",
    "update_interview"
)

builder.add_conditional_edges(
    "update_interview",
    interview_router,
    {
        "continue": "generate_question",
        "report": "generate_report"
    }
)

builder.add_edge(
    "generate_report",
    END
)

graph = builder.compile()