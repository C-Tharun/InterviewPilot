import os
import json
import re
from flask import Flask, render_template, request, jsonify, session
import secrets
from groq import Groq
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# 🔥 FIX FOR WINDOWS PROXY ERROR 🔥
# Prevent Groq SDK from crashing due to system proxy settings
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", secrets.token_hex(32))

# Groq API key (FREE)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY environment variable is required. Add it in your .env file")

# Initialize Groq client (NOW WORKS ON WINDOWS)
groq_client = Groq(api_key=GROQ_API_KEY)

# FREE Model
MODEL_NAME = "llama-3.3-70b-versatile"

# -------------------------------------
# JOB ROLES DEFINITION
# -------------------------------------

JOB_ROLES = {
    "software_engineer": {
        "name": "Software Engineer",
        "description": "Technical interview focused on algorithms, system design, and coding",
        "areas": ["algorithms", "data structures", "system design", "coding practices"]
    },
    "data_analyst": {
        "name": "Data Analyst",
        "description": "Interview covering SQL, statistics, analysis, visualization",
        "areas": ["SQL", "data analysis", "statistics", "data visualization", "business insights"]
    },
    "sales": {
        "name": "Sales Representative",
        "description": "Sales interview focusing on communication, persuasion, negotiation",
        "areas": ["sales techniques", "customer relationship", "negotiation", "product knowledge"]
    },
    "product_manager": {
        "name": "Product Manager",
        "description": "Product interview focusing on strategy, users, features, execution",
        "areas": ["product strategy", "user research", "prioritization", "stakeholder management"]
    },
    "marketing": {
        "name": "Marketing Specialist",
        "description": "Marketing interview focused on campaigns, analytics, branding",
        "areas": ["marketing strategy", "campaign management", "analytics", "brand positioning"]
    }
}

# -------------------------------------
# ROUTES
# -------------------------------------

@app.route("/")
def index():
    return render_template("index.html", job_roles=JOB_ROLES)


@app.route("/start_interview", methods=["POST"])
def start_interview():
    data = request.json
    role = data.get("role")

    if role not in JOB_ROLES:
        return jsonify({"error": "Invalid role"}), 400

    session["role"] = role
    session["conversation_history"] = []
    session["question_count"] = 0
    session["interview_started"] = True

    role_info = JOB_ROLES[role]

    system_prompt = f"""
You are an expert interviewer for a {role_info['name']} role.

Your goals:
1. Ask ONE relevant question at a time
2. Adapt to confused / chatty / efficient candidates
3. Stay professional and role-specific
4. Ask 5–7 questions total
5. Start with an opening question now.
"""

    try:
        response = groq_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Start the interview now."}
            ]
        )

        question = response.choices[0].message.content

        session["conversation_history"].append({"role": "assistant", "content": question})
        session["question_count"] = 1
        session.modified = True

        return jsonify({
            "question": question,
            "question_count": 1,
            "role_name": role_info["name"]
        })

    except Exception as e:
        return jsonify({"error": f"Error starting interview: {e}"}), 500


@app.route("/send_response", methods=["POST"])
def send_response():
    if not session.get("interview_started"):
        return jsonify({"error": "No active interview"}), 400

    data = request.json
    user_response = data.get("response", "").strip()

    if not user_response:
        return jsonify({"error": "Empty response"}), 400

    role = session["role"]
    role_info = JOB_ROLES[role]
    history = session.get("conversation_history", [])
    question_count = session.get("question_count", 0)

    history.append({"role": "user", "content": user_response})

    system_prompt = f"""
You are an expert interviewer for a {role_info['name']} role.
Key areas: {', '.join(role_info['areas'])}
Current question number: {question_count}

Rules:
- Clarify if user seems confused
- Go deeper if user is efficient
- Redirect if off-topic
- End after 6–7 questions with: "That concludes our interview. Thank you!"
"""

    try:
        messages = [{"role": "system", "content": system_prompt}] + history

        response = groq_client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages
        )

        next_question = response.choices[0].message.content

        history.append({"role": "assistant", "content": next_question})

        is_completed = (
            "concludes our interview" in next_question.lower()
            or (question_count >= 5 and "thank you" in next_question.lower())
        )

        session["conversation_history"] = history
        session["question_count"] = question_count + 1
        session.modified = True

        return jsonify({
            "question": next_question,
            "question_count": question_count + 1,
            "is_completed": is_completed
        })

    except Exception as e:
        return jsonify({"error": f"Error generating response: {e}"}), 500


@app.route("/get_feedback", methods=["POST"])
def get_feedback():
    if not session.get("interview_started"):
        return jsonify({"error": "No active interview"}), 400

    role = session["role"]
    role_info = JOB_ROLES[role]
    history = session.get("conversation_history", [])

    feedback_prompt = f"""
Analyze the following interview for a {role_info['name']} role.

Transcript:
{json.dumps(history, indent=2)}

Provide your feedback as a valid JSON object with the following structure:
{{
    "overall_score": <number 0-100>,
    "communication": {{"score": <number 0-10>, "feedback": "<text>"}},
    "technical_depth": {{"score": <number 0-10>, "feedback": "<text>"}},
    "clarity": {{"score": <number 0-10>, "feedback": "<text>"}},
    "confidence": {{"score": <number 0-10>, "feedback": "<text>"}},
    "strengths": ["<strength1>", "<strength2>", ...],
    "areas_for_improvement": ["<area1>", "<area2>", ...],
    "recommendations": ["<rec1>", "<rec2>", ...]
}}

CRITICAL REQUIREMENTS:
1. ALWAYS provide at least 2-3 strengths, even if the performance was poor. Find positive aspects like effort, willingness to learn, honesty, etc.
2. The strengths array must NEVER be empty.
3. Return ONLY valid JSON, no markdown formatting, no code blocks, no explanations.
"""

    try:
        response = groq_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are an interview evaluator. Always respond with valid JSON only, no markdown, no code blocks, no explanations."},
                {"role": "user", "content": feedback_prompt}
            ]
        )

        content = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present (```json ... ``` or ``` ... ```)
        if content.startswith("```"):
            # Extract JSON from markdown code blocks
            lines = content.split("\n")
            # Remove first line if it's ```json or ```
            if lines[0].strip().startswith("```"):
                lines = lines[1:]
            # Remove last line if it's ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines).strip()
        
        # Try to parse JSON
        try:
            feedback = json.loads(content)
        except json.JSONDecodeError as json_err:
            # If JSON parsing fails, try to extract JSON object from the text
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                feedback = json.loads(json_match.group())
            else:
                raise ValueError(f"Could not parse JSON from response: {json_err}. Content: {content[:200]}")

        # Validate required fields
        required_fields = ["overall_score", "communication", "technical_depth", "clarity", "confidence", "strengths", "areas_for_improvement", "recommendations"]
        for field in required_fields:
            if field not in feedback:
                feedback[field] = {} if field in ["communication", "technical_depth", "clarity", "confidence"] else []
        
        # Ensure strengths is never empty
        if not feedback.get("strengths") or len(feedback["strengths"]) == 0:
            feedback["strengths"] = [
                "Demonstrated effort and engagement during the interview",
                "Showed willingness to learn and improve",
                "Maintained a positive attitude throughout the process"
            ]

        session.clear()
        return jsonify(feedback)

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Feedback generation error: {error_details}")
        return jsonify({"error": f"Error generating feedback: {str(e)}"}), 500


@app.route("/reset_interview", methods=["POST"])
def reset_interview():
    session.clear()
    return jsonify({"success": True})


if __name__ == "__main__":
    app.run(port=5000, debug=True)
