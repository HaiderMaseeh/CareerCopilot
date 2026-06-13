from groq import Groq
import json

from dotenv import load_dotenv
import os
load_dotenv()



client = Groq(
    api_key=os.getenv("learning_path"),
)


def generate_assessment_questions(
    role,
    analysis
):
    prompt = f"""
    You are an AI Career Coach.

    Role:
    {role}

    Resume Analysis:

    {json.dumps(analysis, indent=2)}

    Generate exactly 5 assessment questions.

    Purpose:
    Understand the candidate's actual skill level.

    Rules:

    1. Questions should be easy.
    2. Questions should NOT be interview questions.
    3. Questions should focus on:
    - experience
    - confidence
    - projects
    - tools
    - career goals
    4. Maximum one sentence each.
    5. Return JSON only.

    Schema:

    {{
        "questions": [
            "...",
            "...",
            "...",
            "...",
            "..."
        ]
    }}
    """

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

        temperature=0.6
    )

    result = json.loads(
        response.choices[0].message.content
    )

    return result["questions"]


def collect_assessment_answers(
    questions
):

    answers = {}

    for idx, question in enumerate(
        questions,
        start=1
    ):

        print(f"\nQuestion {idx}")

        print(question)

        answer = input("> ")

        answers[question] = answer

    return answers

def generate_learning_path(
    role,
    analysis,
    assessment_answers
):

    prompt = f"""
You are an expert AI Career Coach and  Mentor.

Target Role:
{role}

Resume Analysis:
{json.dumps(analysis, indent=2)}

Assessment Answers:
{json.dumps(assessment_answers, indent=2)}

Your task:

Create a highly detailed and personalized learning roadmap.

IMPORTANT RULES:

1. Break every skill into subtopics.
2. Break every subtopic into concepts.
3. Include estimated learning time.
4. Include learning resources.
5. Resources must be FREE whenever possible.
6. Include:
   - YouTube videos
   - Official documentation
   - Free courses
   - Practice platforms

7. Recommend projects that match the user's level.
8. Projects should help prepare for the target role.
9.Maximum 4 skills,Maximum 3 subtopics per skill,Maximum 3 concepts per subtopic,Maximum 2 projects
10. Return ONLY valid JSON.

JSON Schema:

{{
  "current_level": "",

  "job_readiness_score": 0,

  "priority_skills": [],

  "roadmap": [

    {{
      "skill": "",

      "estimated_weeks": 0,

      "subtopics": [

        {{
          "topic": "",

          "estimated_days": 0,

          "concepts": [],

         

          "resources": [

            {{
              "type": "youtube",
              "title": ""
            }},

            {{
              "type": "documentation",
              "title": ""
            }},

            {{
              "type": "course",
              "title": ""
            }},

            {{
              "type": "practice",
              "title": ""
            }}
          ]
        }}
      ]
    }}
  ],

  "projects": [

    {{
      "title": "",

      "difficulty": "",

      "estimated_weeks": 0,

      "description": "",

      "skills_used": [],

      "learning_outcomes": []
    }}
  ]
}}

Example Structure:

Machine Learning
  -> Supervised Learning
      -> Classification
          -> Logistic Regression
          -> Decision Trees
          -> Random Forest
      -> Regression
          -> Linear Regression
          -> Ridge Regression

Deep Learning
  -> Neural Networks
  -> CNN
  -> RNN
  -> Transformers

MLOps
  -> Docker
  -> MLflow
  -> CI/CD
  -> Deployment

Generate a complete roadmap.
"""

    try:

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",

            response_format={
                "type": "json_object"
            },

            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0.4
        )

        result = json.loads(
            response.choices[0].message.content
        )

        return result

    except Exception as e:

        print(
            "Learning Path Generation Error:",
            e
        )

        return {
            "error": str(e)
        }
    
def display_learning_path(data):

    print("\n")
    print("=" * 80)
    print("LEARNING PATH")
    print("=" * 80)

    print(
        f"\nCurrent Level: {data['current_level']}"
    )

    print(
        f"Job Readiness Score: "
        f"{data['job_readiness_score']}/100"
    )

    print("\n")

    print("=" * 80)
    print("PRIORITY SKILLS")
    print("=" * 80)

    for idx, skill in enumerate(
        data["priority_skills"],
        start=1
    ):

        print(
            f"{idx}. {skill}"
        )

    print("\n")

    print("=" * 80)
    print("ROADMAP")
    print("=" * 80)

    for skill in data.get("roadmap", []):

        print("\n")
        print(
            f"SKILL: {skill['skill']}"
        )

        print(
            f"Estimated Time: "
            f"{skill['estimated_weeks']} Weeks"
        )

        print("-" * 60)

        for topic in skill["subtopics"]:

            print(
                f"\nTopic: {topic['topic']}"
            )

            print(
                f"Duration: "
                f"{topic['estimated_days']} Days"
            )

            print("\nConcepts:")

            for concept in topic["concepts"]:

                print(
                    f"  • {concept}"
                )

            print("\nResources:")

            for resource in topic["resources"]:

                print(
                    f"  [{resource['type'].upper()}]"
                )

                print(
                    f"  {resource['title']}"
                )

        print("\n")

    print("=" * 80)
    print("PROJECT RECOMMENDATIONS")
    print("=" * 80)
    projects = data.get("projects", [])

    if not projects:
            print("\nNo project recommendations generated.")
            return
    for project in data.get("projects", []):
        
        print("\n")

        print(
            f"Project: "
            f"{project['title']}"
        )

        print(
            f"Difficulty: "
            f"{project['difficulty']}"
        )

        print(
            f"Estimated Time: "
            f"{project['estimated_weeks']} Weeks"
        )

        print(
            f"\nDescription:"
        )

        print(
            project["description"]
        )

        print(
            "\nSkills Covered:"
        )

        for skill in project["skills_used"]:

            print(
                f"  • {skill}"
            )

        print(
            "\nLearning Outcomes:"
        )

        for outcome in project[
            "learning_outcomes"
        ]:

            print(
                f"  • {outcome}"
            )

    print("\n")

def assessment_questions_node(state):

    questions = generate_assessment_questions(
        state["role"],
        state["analysis"]
    )

    state["assessment_questions"] = questions

    return state

def assessment_answers_node(state):

    answers = {}

    print("\n")
    print("=" * 80)
    print("SKILL ASSESSMENT")
    print("=" * 80)

    for idx, question in enumerate(
        state["assessment_questions"],
        start=1
    ):

        print("\n")
        print(f"Question {idx}")

        print(question)

        answer = input("> ")

        answers[question] = answer

    state["assessment_answers"] = answers

    return state

def learning_path_node(state):

    learning_path = generate_learning_path(
        role=state["role"],
        analysis=state["analysis"],
        assessment_answers=state["assessment_answers"]
    )

    state["learning_path"] = learning_path

    return state


def display_learning_path_node(state):

    data = state["learning_path"]

    if "error" in data:

        print("\n")
        print("=" * 80)
        print("LEARNING PATH GENERATION FAILED")
        print("=" * 80)

        print(data["error"])

        return state

    display_learning_path(data)

    return state