import os
import json
from flask import Flask, render_template, request, jsonify, session
import secrets
from groq import Groq  # ← FREE API client

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", secrets.token_hex(32))

# Groq API key (FREE)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY environment variable is required. Please add it in Replit Secrets."
    )

# Initialize Groq client
groq_client = Groq(api_key=GROQ_API_KEY)

# Use FREE Llama 3.3 70B model (fast + powerful)
MODEL_NAME = "llama-3.3-70b-versatile"

JOB_ROLES = {
    "software_engineer": {
        "name":
        "Software Engineer",
        "description":
        "Technical interview focused on algorithms, system design, and coding",
        "areas":
        ["algorithms", "data structures", "system design", "coding practices"]
    },
    "data_analyst": {
        "name":
        "Data Analyst",
        "description":
        "Interview covering data analysis, SQL, statistics, and visualization",
        "areas": [
            "SQL", "data analysis", "statistics", "data visualization",
            "business insights"
        ]
    },
    "sales": {
        "name":
        "Sales Representative",
        "description":
        "Sales interview focusing on communication, persuasion, and customer relations",
        "areas": [
            "sales techniques", "customer relationship", "negotiation",
            "product knowledge"
        ]
    },
    "product_manager": {
        "name":
        "Product Manager",
        "description":
        "Product management interview on strategy, prioritization, and user focus",
        "areas": [
            "product strategy", "user research", "prioritization",
            "stakeholder management"
        ]
    },
    "marketing": {
        "name":
        "Marketing Specialist",
        "description":
        "Marketing interview covering campaigns, analytics, and creative strategy",
        "areas": [
            "marketing strategy", "campaign management", "analytics",
            "brand positioning"
        ]
    }
}


@app.route('/')
def index():
    return render_template('index.html', job_roles=JOB_ROLES)


@app.route('/start_interview', methods=['POST'])
def start_interview():
    data = request.json
    role = data.get('role')

    if role not in JOB_ROLES:
        return jsonify({"error": "Invalid role"}), 400

    session['role'] = role
    session['conversation_history'] = []
    session['question_count'] = 0
    session['interview_started'] = True

    role_info = JOB_ROLES[role]

    system_prompt = f"""You are an expert interviewer conducting a mock interview for a {role_info['name']} position.
Your goal is to:
1. Ask ONE relevant question at a time based on the role's key areas: {', '.join(role_info['areas'])}
2. Adapt your follow-up questions based on the candidate's previous answers
3. Handle different candidate types appropriately:
   - Confused candidates: Provide clarification or rephrase
   - Efficient candidates: Ask deeper, more challenging questions
   - Chatty candidates: Gently redirect and keep focused
   - Off-topic candidates: Politely bring them back to the topic
4. Ask 5-7 questions total before concluding the interview
5. Keep questions professional, relevant, and progressively challenging

Start with an opening question appropriate for this role."""

    try:
        response = groq_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{
                "role": "system",
                "content": system_prompt
            }, {
                "role": "user",
                "content": "Please ask your first interview question."
            }])

        question = response.choices[0].message.content

        session['conversation_history'].append({
            "role": "assistant",
            "content": question
        })
        session['question_count'] = 1
        session.modified = True

        return jsonify({
            "question": question,
            "question_count": 1,
            "role_name": role_info['name']
        })

    except Exception as e:
        app.logger.error(f"Error starting interview: {str(e)}")
        return jsonify({"error": f"Failed to start interview: {str(e)}"}), 500


@app.route('/send_response', methods=['POST'])
def send_response():
    if not session.get('interview_started'):
        return jsonify({"error": "No active interview"}), 400

    data = request.json
    user_response = data.get('response', '').strip()

    if not user_response:
        return jsonify({"error": "Empty response"}), 400

    role = session.get('role')
    role_info = JOB_ROLES[role]
    conversation_history = session.get('conversation_history', [])
    question_count = session.get('question_count', 0)

    conversation_history.append({"role": "user", "content": user_response})

    system_prompt = f"""You are an expert interviewer conducting a mock interview for a {role_info['name']} position.
Key areas: {', '.join(role_info['areas'])}

Current question count: {question_count}/7

Based on the candidate's response:
1. If they seem confused or unclear, offer clarification
2. If they're very efficient and concise, ask deeper questions
3. If they're too chatty or off-topic, politely redirect
4. If you've asked 6-7 questions, wrap up the interview by saying "That concludes our interview. Thank you!"

Ask your next question or conclude the interview."""

    try:
        messages = [{
            "role": "system",
            "content": system_prompt
        }] + conversation_history + [{
            "role":
            "user",
            "content":
            "Based on my response, what's your next question or comment?"
        }]

        response = groq_client.chat.completions.create(model=MODEL_NAME,
                                                       messages=messages)

        next_question = response.choices[0].message.content

        conversation_history.append({
            "role": "assistant",
            "content": next_question
        })

        is_completed = "concludes our interview" in next_question.lower() or (
            "thank you" in next_question.lower() and question_count >= 5)

        session['conversation_history'] = conversation_history
        session['question_count'] = question_count + 1
        session.modified = True

        return jsonify({
            "question": next_question,
            "question_count": question_count + 1,
            "is_completed": is_completed
        })

    except Exception as e:
        app.logger.error(f"Error sending response: {str(e)}")
        return jsonify({"error": f"Failed to process response: {str(e)}"}), 500


@app.route('/get_feedback', methods=['POST'])
def get_feedback():
    if not session.get('interview_started'):
        return jsonify({"error": "No active interview"}), 400

    role = session.get('role')
    role_info = JOB_ROLES[role]
    conversation_history = session.get('conversation_history', [])

    feedback_prompt = f"""Analyze this mock interview for a {role_info['name']} position and provide comprehensive feedback.

Interview transcript:
{json.dumps(conversation_history, indent=2)}

Provide detailed feedback in JSON format with these categories:
{{
  "overall_score": (1-10),
  "communication": {{
    "score": (1-10),
    "feedback": "detailed feedback on communication skills"
  }},
  "technical_depth": {{
    "score": (1-10),
    "feedback": "feedback on technical knowledge and depth"
  }},
  "clarity": {{
    "score": (1-10),
    "feedback": "feedback on clarity and articulation"
  }},
  "confidence": {{
    "score": (1-10),
    "feedback": "feedback on confidence and professionalism"
  }},
  "strengths": ["strength 1", "strength 2", "strength 3"],
  "areas_for_improvement": ["area 1", "area 2", "area 3"],
  "recommendations": ["recommendation 1", "recommendation 2", "recommendation 3"]
}}"""

    try:
        response = groq_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{
                "role":
                "system",
                "content":
                "You are an expert interview coach providing detailed, constructive feedback."
            }, {
                "role": "user",
                "content": feedback_prompt
            }])

        feedback_raw = response.choices[0].message.content
        feedback = json.loads(feedback_raw)

        session.clear()
        return jsonify(feedback)

    except Exception as e:
        app.logger.error(f"Error generating feedback: {str(e)}")
        return jsonify({"error":
                        f"Failed to generate feedback: {str(e)}"}), 500


@app.route('/reset_interview', methods=['POST'])
def reset_interview():
    session.clear()
    return jsonify({"success": True})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
