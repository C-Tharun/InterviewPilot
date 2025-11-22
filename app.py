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


def evaluate_answer_performance(user_response, role_info):
    """Evaluate candidate's answer performance using LLM"""
    evaluation_prompt = f"""
Evaluate the candidate's answer for a {role_info['name']} role interview.

Answer: "{user_response}"

Rate the answer on three dimensions (1-10 scale):
- clarity: How clear and well-articulated is the answer?
- technical_depth: How technically deep and accurate is the answer?
- confidence: How confident and certain does the candidate sound?

Return ONLY a valid JSON object:
{{
    "clarity": <number 1-10>,
    "technical_depth": <number 1-10>,
    "confidence": <number 1-10>
}}

No explanations, no markdown, just JSON.
"""

    try:
        response = groq_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are an answer evaluator. Return only valid JSON."},
                {"role": "user", "content": evaluation_prompt}
            ]
        )
        
        content = response.choices[0].message.content.strip()
        
        # Remove markdown if present
        if content.startswith("```"):
            lines = content.split("\n")
            if lines[0].strip().startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines).strip()
        
        # Parse JSON
        try:
            scores = json.loads(content)
        except json.JSONDecodeError:
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                scores = json.loads(json_match.group())
            else:
                # Fallback: use heuristics
                return calculate_heuristic_score(user_response)
        
        # Calculate overall performance score (1-10)
        performance_score = (scores.get("clarity", 5) + scores.get("technical_depth", 5) + scores.get("confidence", 5)) / 3
        return {
            "clarity": scores.get("clarity", 5),
            "technical_depth": scores.get("technical_depth", 5),
            "confidence": scores.get("confidence", 5),
            "performance_score": round(performance_score, 2)
        }
    except Exception as e:
        print(f"Evaluation error: {e}")
        return calculate_heuristic_score(user_response)


def calculate_heuristic_score(user_response):
    """Fallback heuristic scoring if LLM evaluation fails"""
    response_lower = user_response.lower()
    score = 5.0  # Base score
    
    # Positive indicators
    if len(user_response) > 100:
        score += 1.0
    if any(word in response_lower for word in ["because", "example", "specifically", "detail"]):
        score += 0.5
    if any(word in response_lower for word in ["algorithm", "design", "system", "architecture"]):
        score += 0.5
    
    # Negative indicators
    if any(phrase in response_lower for phrase in ["not sure", "i think", "maybe", "i don't know", "unsure"]):
        score -= 1.5
    if len(user_response) < 30:
        score -= 1.0
    
    score = max(1.0, min(10.0, score))
    
    return {
        "clarity": max(1, min(10, round(score + 0.5))),
        "technical_depth": max(1, min(10, round(score))),
        "confidence": max(1, min(10, round(score - 0.5))),
        "performance_score": round(score, 2)
    }


def calculate_dynamic_goal_count(performance_history):
    """Calculate target question count based on performance history
    
    Logic: Strong candidates (high scores) get fewer questions (they've proven themselves)
           Struggling candidates (low scores) get more questions (more opportunity to show knowledge)
    """
    if not performance_history or len(performance_history) == 0:
        return 6  # Default
    
    avg_performance = sum(performance_history) / len(performance_history)
    
    if avg_performance >= 7.0:
        return 5  # Strong candidate: 4-5 questions (they've proven themselves quickly)
    elif avg_performance >= 4.0:
        return 6  # Average candidate: 6-7 questions
    else:
        return 8  # Struggling candidate: 7-9 questions (give them more chances)


@app.route("/start_interview", methods=["POST"])
def start_interview():
    data = request.json
    role = data.get("role")

    if role not in JOB_ROLES:
        return jsonify({"error": "Invalid role"}), 400

    role_info = JOB_ROLES[role]

    # Initialize session with adaptive tracking
    session["role"] = role
    session["conversation_history"] = []
    session["question_count"] = 0
    session["interview_started"] = True
    session["performance_history"] = []
    session["dynamic_goal_count"] = 6  # Will be adjusted after first answer

    # Role-specific opening question templates for a human-like start
    opening_questions = {
        "software_engineer": "Start the interview by asking the candidate to tell you about their background, experience, and any interesting projects they've worked on. Be warm and conversational, like a real human interviewer would.",
        "data_analyst": "Start the interview by asking the candidate to share their background in data analysis, any relevant projects they've worked on, and what interests them about working with data. Be warm and conversational.",
        "sales": "Start the interview by asking the candidate to tell you about their sales experience, any notable achievements or deals they've closed, and what draws them to sales. Be warm and conversational.",
        "product_manager": "Start the interview by asking the candidate to share their background in product management, any products they've worked on, and what excites them about building products. Be warm and conversational.",
        "marketing": "Start the interview by asking the candidate to tell you about their marketing experience, any campaigns they've worked on, and what aspects of marketing they're most passionate about. Be warm and conversational."
    }
    
    opening_instruction = opening_questions.get(role, "Start the interview by asking the candidate to tell you about their background and experience. Be warm and conversational.")

    system_prompt = f"""
You are an expert, friendly interviewer for a {role_info['name']} role.

Your approach:
1. Start with a warm, conversational opening question about the candidate's background, experience, or projects
2. Make it feel like a natural human conversation - not robotic or overly formal
3. After learning about their background, gradually transition to more technical/role-specific questions
4. Ask ONE relevant question at a time
5. Adapt naturally to the candidate's responses
6. If they answer well, gradually increase difficulty
7. If they struggle, simplify and be supportive
8. Behave like a human interviewer - adjust difficulty naturally
9. Never mention question counts or adaptive rules
10. Stay professional but personable

Key areas to cover later in the interview: {', '.join(role_info['areas'])}

{opening_instruction}
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
            "role_name": role_info["name"],
            "total_questions": session["dynamic_goal_count"]
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
    performance_history = session.get("performance_history", [])
    dynamic_goal_count = session.get("dynamic_goal_count", 6)

    # Evaluate the candidate's answer
    performance_data = evaluate_answer_performance(user_response, role_info)
    performance_score = performance_data["performance_score"]
    performance_history.append(performance_score)
    
    # Recalculate dynamic goal count based on updated performance
    dynamic_goal_count = calculate_dynamic_goal_count(performance_history)
    
    # Calculate average performance for context
    avg_performance = sum(performance_history) / len(performance_history) if performance_history else 5.0
    
    history.append({"role": "user", "content": user_response})

    # Build adaptive system prompt
    # Note: Strong candidates get fewer questions (they've proven themselves), 
    # struggling candidates get more questions (more opportunity to show knowledge)
    if avg_performance >= 7.0:
        difficulty_context = "The candidate is performing very well and has demonstrated strong knowledge. Ask a few deeper, challenging questions to confirm their expertise, then conclude efficiently."
        question_style = "Ask deeper, more challenging questions. Since they're doing well, you can wrap up sooner after confirming their strong performance."
    elif avg_performance >= 4.0:
        difficulty_context = "The candidate is performing at an average level. Maintain moderate difficulty. Balance fundamentals with some depth."
        question_style = "Ask balanced questions covering core concepts."
    else:
        difficulty_context = "The candidate is struggling. Simplify questions and be supportive. Give them more opportunities to demonstrate their knowledge. Focus on fundamentals and basic concepts."
        question_style = "Ask simpler, more encouraging questions. Provide more questions to give them chances to show what they know."

    # Determine if we should start wrapping up
    questions_remaining = dynamic_goal_count - (question_count + 1)  # +1 because we're about to ask the next question
    should_conclude = questions_remaining <= 0 and question_count >= 3  # At least 3 questions asked
    
    system_prompt = f"""
You are an expert interviewer for a {role_info['name']} role.
Key areas: {', '.join(role_info['areas'])}

Current context:
- This is question #{question_count + 1}
- {difficulty_context}
- {question_style}

Your behavior:
- Adapt naturally to the candidate's performance level
- Never mention question counts, difficulty levels, or adaptive rules to the candidate
- Behave like a human interviewer adjusting naturally
- If they answer well, ask follow-up questions that go deeper
- If they struggle, simplify and provide encouragement
- Stay professional and role-specific
- ALWAYS ask a question - never end abruptly without asking something
- {"IMPORTANT: After the candidate responds to THIS question, you should conclude the interview naturally. Say something like: 'That concludes our interview. Thank you for your time!' But FIRST, ask this question and wait for their response." if should_conclude else "Continue with another question after they respond."}
- NEVER end the interview in the middle of asking a question
- Always give the candidate a chance to respond before concluding
"""

    try:
        messages = [{"role": "system", "content": system_prompt}] + history

        response = groq_client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages
        )

        next_question = response.choices[0].message.content

        history.append({"role": "assistant", "content": next_question})

        # Check if interview should end
        # IMPORTANT: Only mark as completed if the interviewer EXPLICITLY concludes
        # We check for clear conclusion phrases that indicate the interview is ending
        explicit_conclusion_phrases = [
            "that concludes our interview",
            "concludes our interview", 
            "thank you for your time",
            "thank you for taking the time",
            "this concludes the interview",
            "we'll wrap up here"
        ]
        
        explicit_conclusion = any(phrase in next_question.lower() for phrase in explicit_conclusion_phrases)
        
        # Only mark as completed if:
        # 1. Interviewer explicitly concluded with a clear ending statement, OR
        # 2. We've significantly exceeded the goal count (safety check)
        # But NEVER end if we haven't reached at least the minimum question count
        min_questions = 4  # Always ask at least 4 questions
        is_completed = (
            explicit_conclusion or 
            (question_count + 1 >= max(dynamic_goal_count + 1, min_questions) and explicit_conclusion)
        )
        
        # If we're at goal but no explicit conclusion, the next prompt will guide conclusion
        # This ensures the user always gets to respond to the current question

        # Update session
        session["conversation_history"] = history
        session["question_count"] = question_count + 1
        session["performance_history"] = performance_history
        session["dynamic_goal_count"] = dynamic_goal_count
        session.modified = True

        return jsonify({
            "question": next_question,
            "question_count": question_count + 1,
            "total_questions": dynamic_goal_count,
            "is_completed": is_completed,
            "performance_score": round(avg_performance, 1)
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

    question_count = session.get("question_count", 0)
    performance_history = session.get("performance_history", [])
    
    feedback_prompt = f"""
Analyze the following interview for a {role_info['name']} role.

Interview Details:
- Total Questions Asked: {question_count}
- Performance Trend: {'Strong' if performance_history and sum(performance_history)/len(performance_history) >= 7 else 'Average' if performance_history and sum(performance_history)/len(performance_history) >= 4 else 'Needs Improvement'}

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
