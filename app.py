import os
import json
import re
import random
from flask import Flask, render_template, request, jsonify, session
import secrets
from groq import Groq
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import PyPDF2
from io import BytesIO

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
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

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


@app.route("/upload_resume", methods=["POST"])
def upload_resume():
    """Handle resume file upload and extract text"""
    if 'resume' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['resume']
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    # Validate file extension
    allowed_extensions = {'.pdf', '.txt'}
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        return jsonify({"error": "Invalid file type. Please upload a PDF or TXT file."}), 400
    
    try:
        resume_text = ""
        
        if file_ext == '.pdf':
            # Extract text from PDF
            file_content = file.read()
            pdf_reader = PyPDF2.PdfReader(BytesIO(file_content))
            resume_text = ""
            for page in pdf_reader.pages:
                resume_text += page.extract_text() + "\n"
        else:  # .txt
            # Read text file
            resume_text = file.read().decode('utf-8', errors='ignore')
        
        if not resume_text.strip():
            return jsonify({"error": "Could not extract text from file. Please ensure the file contains readable text."}), 400
        
        # Store resume text in session
        session["resume_text"] = resume_text
        session["resume_uploaded"] = True
        
        # Generate a summary of the resume using LLM
        try:
            summary_prompt = f"""
Extract and summarize the following resume in a structured JSON format:

Resume Text:
{resume_text[:3000]}  # Limit to first 3000 chars for context

Return a JSON object with the following structure:
{{
    "name": "<candidate name if available>",
    "email": "<email if available>",
    "phone": "<phone if available>",
    "education": ["<degree1>", "<degree2>", ...],
    "experience": ["<job1>", "<job2>", ...],
    "skills": ["<skill1>", "<skill2>", ...],
    "projects": ["<project1>", "<project2>", ...],
    "summary": "<brief professional summary>"
}}

Return ONLY valid JSON, no markdown, no code blocks.
"""
            
            summary_response = groq_client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "You are a resume parser. Return only valid JSON, no markdown, no code blocks."},
                    {"role": "user", "content": summary_prompt}
                ]
            )
            
            summary_content = summary_response.choices[0].message.content.strip()
            
            # Remove markdown if present
            if summary_content.startswith("```"):
                lines = summary_content.split("\n")
                if lines[0].strip().startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                summary_content = "\n".join(lines).strip()
            
            # Parse JSON summary
            try:
                resume_summary = json.loads(summary_content)
            except json.JSONDecodeError:
                # Try to extract JSON from text
                json_match = re.search(r'\{.*\}', summary_content, re.DOTALL)
                if json_match:
                    resume_summary = json.loads(json_match.group())
                else:
                    resume_summary = {"summary": "Resume uploaded successfully"}
            
            session["resume_summary"] = resume_summary
        except Exception as e:
            print(f"Error generating resume summary: {e}")
            # Continue without summary if LLM fails
            session["resume_summary"] = {}
        
        session.modified = True
        
        return jsonify({
            "success": True,
            "message": "Resume uploaded successfully",
            "filename": file.filename
        })
    
    except Exception as e:
        print(f"Error processing resume: {e}")
        return jsonify({"error": f"Error processing file: {str(e)}"}), 500


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
    
    Dynamic Question Count: Automatically adjusts interview length (4-9 questions) based on candidate performance
    - Strong candidates (avg score ≥ 7.0): 4-5 questions (they've proven themselves quickly)
    - Average candidates (avg score 4.0-7.0): 6-7 questions with balanced difficulty
    - Struggling candidates (avg score < 4.0): 7-9 questions (more opportunities to demonstrate knowledge)
    
    MAXIMUM: 9 questions (hard limit, never exceeds this)
    """
    if not performance_history or len(performance_history) == 0:
        return 6  # Default
    
    avg_performance = sum(performance_history) / len(performance_history)
    
    if avg_performance >= 7.0:
        # Strong candidate: 4-5 questions (they've proven themselves quickly)
        # Use 4 for very strong (>=8.0), 5 for strong (7.0-7.9)
        goal = 4 if avg_performance >= 8.0 else 5
    elif avg_performance >= 4.0:
        # Average candidate: 6-7 questions with balanced difficulty
        # Use 6 for lower average (4.0-5.4), 7 for higher average (5.5-6.9)
        goal = 6 if avg_performance < 5.5 else 7
    else:
        # Struggling candidate: 7-9 questions (more opportunities to demonstrate knowledge)
        # Use 7 for moderate struggle (3.0-3.9), 8-9 for significant struggle (<3.0)
        if avg_performance >= 3.0:
            goal = 7
        else:
            goal = random.choice([8, 9])  # 8 or 9 for very struggling candidates
    
    # HARD CAP: Never exceed 9 questions
    return min(goal, 9)


@app.route("/start_interview", methods=["POST"])
def start_interview():
    data = request.json
    role = data.get("role")

    if role not in JOB_ROLES:
        return jsonify({"error": "Invalid role"}), 400

    role_info = JOB_ROLES[role]

    # Get persona from request
    persona = data.get("persona", "neutral")  # Default to neutral
    
    # Get resume context if available
    resume_text = session.get("resume_text", "")
    resume_summary = session.get("resume_summary", {})
    has_resume = session.get("resume_uploaded", False)
    
    # Initialize session with adaptive tracking
    session["role"] = role
    session["persona"] = persona
    session["conversation_history"] = []
    session["question_count"] = 0
    session["interview_started"] = True
    session["interview_start_time"] = None  # Will be set when first question is asked
    session["performance_history"] = []
    session["dynamic_goal_count"] = 6  # Will be adjusted after first answer
    session["locked_goal_count"] = None  # Lock goal count once we're close to completion
    session["poor_questions"] = []  # Track questions with poor performance for retry
    session["question_details"] = []  # Store question text and performance for retry

    # Persona-based interview styles
    persona_styles = {
        "strict": {
            "tone": "You are a strict, high-bar interviewer. Set high expectations, ask challenging questions, and be direct. Push candidates to demonstrate excellence. Be professional but firm.",
            "opening": "Start with a direct, professional question about their background. Be concise and expect detailed, technical answers."
        },
        "friendly": {
            "tone": "You are a friendly, supportive interviewer. Be warm, encouraging, and make the candidate feel comfortable. Help them showcase their best work. Be conversational and positive.",
            "opening": "Start with a warm, welcoming question about their background. Be encouraging and make them feel at ease."
        },
        "neutral": {
            "tone": "You are a professional, neutral interviewer. Maintain a balanced, objective approach. Be professional and fair. Focus on assessing skills without being overly strict or overly friendly.",
            "opening": "Start with a professional, neutral question about their background. Be balanced and objective."
        }
    }
    
    persona_info = persona_styles.get(persona, persona_styles["neutral"])
    
    # Role-specific opening question templates
    opening_questions = {
        "software_engineer": f"Start the interview by asking the candidate to tell you about their background, experience, and any interesting projects they've worked on. {persona_info['opening']}",
        "data_analyst": f"Start the interview by asking the candidate to share their background in data analysis, any relevant projects they've worked on, and what interests them about working with data. {persona_info['opening']}",
        "sales": f"Start the interview by asking the candidate to tell you about their sales experience, any notable achievements or deals they've closed, and what draws them to sales. {persona_info['opening']}",
        "product_manager": f"Start the interview by asking the candidate to share their background in product management, any products they've worked on, and what excites them about building products. {persona_info['opening']}",
        "marketing": f"Start the interview by asking the candidate to tell you about their marketing experience, any campaigns they've worked on, and what aspects of marketing they're most passionate about. {persona_info['opening']}"
    }
    
    opening_instruction = opening_questions.get(role, f"Start the interview by asking the candidate to tell you about their background and experience. {persona_info['opening']}")
    
    # Get resume context if available
    resume_text = session.get("resume_text", "")
    resume_summary = session.get("resume_summary", {})
    has_resume = session.get("resume_uploaded", False)
    
    # Build resume context if available
    resume_context = ""
    if has_resume and resume_text:
        resume_preview = resume_text[:1000]  # First 1000 chars for context
        if resume_summary:
            resume_context = f"""
IMPORTANT - Resume Context Available:
The candidate has uploaded their resume. Use this information to make the interview context-aware and personalized.

Resume Summary: {json.dumps(resume_summary, indent=2)}
Resume Preview: {resume_preview}

When asking questions:
- Reference specific projects, skills, or experiences from their resume
- Ask follow-up questions about things mentioned in their resume
- Make connections like "You mentioned working on [X] in your resume... tell me more about that"
"""
        else:
            resume_context = f"""
IMPORTANT - Resume Context Available:
The candidate has uploaded their resume. Use this information to make the interview context-aware.

Resume Content: {resume_preview}

Reference specific details from their resume when asking questions.
"""

    system_prompt = f"""
You are an expert interviewer for a {role_info['name']} role.

{persona_info['tone']}

{resume_context}

Your approach:
1. Start with an opening question about the candidate's background, experience, or projects
2. Make it feel like a natural human conversation
3. After learning about their background, gradually transition to more technical/role-specific questions
4. Ask ONE relevant question at a time
5. Adapt naturally to the candidate's responses
6. If they answer well, gradually increase difficulty
7. If they struggle, simplify and be supportive (but maintain your persona style)
8. Behave like a human interviewer - adjust difficulty naturally
9. Never mention question counts or adaptive rules
10. Stay consistent with your interview persona

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

        # Set interview start time on first question
        from datetime import datetime
        if not session.get("interview_start_time"):
            session["interview_start_time"] = datetime.now().isoformat()

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
    
    # Ensure question_count is valid (defensive check - count from history if needed)
    # Count actual questions from history to verify
    actual_question_count = sum(1 for msg in history if msg.get("role") == "assistant")
    
    # Use the higher of session count or actual count (defensive)
    if question_count < actual_question_count:
        question_count = actual_question_count
    
    # Ensure at least 1 question has been asked (shouldn't happen, but safety check)
    if question_count == 0 and len(history) > 0:
        question_count = 1

    # Evaluate the candidate's answer
    performance_data = evaluate_answer_performance(user_response, role_info)
    performance_score = performance_data["performance_score"]
    performance_history.append(performance_score)
    
    # Track poor questions for retry (score < 4.0)
    if performance_score < 4.0 and len(history) > 0:
        # Get the last question asked
        last_question = None
        for msg in reversed(history):
            if msg.get("role") == "assistant":
                last_question = msg.get("content")
                break
        
        if last_question:
            question_details = session.get("question_details", [])
            question_details.append({
                "question": last_question,
                "question_number": question_count,
                "original_score": performance_score,
                "can_retry": True
            })
            session["question_details"] = question_details
    
    # Calculate average performance for context
    avg_performance = sum(performance_history) / len(performance_history) if performance_history else 5.0
    
    # Recalculate dynamic goal count based on updated performance
    # BUT: Lock the goal count after the FIRST answer to prevent constant changes
    locked_goal = session.get("locked_goal_count")
    
    if locked_goal is not None:
        # Goal is already locked, use it - DO NOT CHANGE
        # Ensure locked goal doesn't exceed 9 (hard limit)
        dynamic_goal_count = min(locked_goal, 9)
    else:
        # Calculate new goal count
        new_goal = calculate_dynamic_goal_count(performance_history)
        # Ensure new goal doesn't exceed 9 (shouldn't happen, but safety check)
        new_goal = min(new_goal, 9)
        # Lock it after we've answered at least 1 question (prevents goal from changing mid-interview)
        # This allows the goal to adjust based on first answer, then stays fixed
        if question_count >= 1:
            session["locked_goal_count"] = new_goal
            dynamic_goal_count = new_goal
        else:
            dynamic_goal_count = new_goal
    
    history.append({"role": "user", "content": user_response})

    # Get persona for consistent interview style
    persona = session.get("persona", "neutral")
    persona_styles = {
        "strict": "Maintain your strict, high-bar approach. Push for excellence and detailed answers.",
        "friendly": "Maintain your friendly, supportive approach. Be encouraging and help them succeed.",
        "neutral": "Maintain your professional, neutral approach. Be balanced and objective."
    }
    persona_context = persona_styles.get(persona, persona_styles["neutral"])
    
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
    # We should conclude if:
    # 1. The next question (question_count + 1) will reach or exceed the goal count
    # 2. We've asked at least 4 questions (minimum)
    next_question_number = question_count + 1
    # Use locked goal if available, otherwise use current dynamic goal
    target_goal = session.get("locked_goal_count") or dynamic_goal_count
    # Ensure target_goal never exceeds 9 (hard limit)
    target_goal = min(target_goal, 9)
    should_conclude = ((next_question_number >= target_goal) and (question_count >= 3)) or (next_question_number >= 9)
    
    # Get resume context if available
    resume_text = session.get("resume_text", "")
    resume_summary = session.get("resume_summary", {})
    has_resume = session.get("resume_uploaded", False)
    
    resume_context = ""
    if has_resume and resume_text:
        resume_preview = resume_text[:800]
        if resume_summary:
            resume_context = f"\nResume Context Available: {json.dumps(resume_summary, indent=2)}\nReference their resume when relevant.\n"
        else:
            resume_context = f"\nResume Context: {resume_preview}\nReference their resume when relevant.\n"
    
    system_prompt = f"""
You are an expert interviewer for a {role_info['name']} role.
Key areas: {', '.join(role_info['areas'])}

{persona_context}

{resume_context}

Current context:
- This is question #{question_count + 1}
- {difficulty_context}
- {question_style}

Your behavior:
- Adapt naturally to the candidate's performance level while maintaining your interview persona
- Never mention question counts, difficulty levels, or adaptive rules to the candidate
- Behave like a human interviewer adjusting naturally
- If they answer well, ask follow-up questions that go deeper
- If they struggle, simplify and provide encouragement (but maintain your persona style)
- Stay professional and role-specific
- ALWAYS ask a question - never end abruptly without asking something
- {"CRITICAL: This is the FINAL question. After the candidate responds to this question, you MUST conclude the interview. End with a clear closing statement like: 'That concludes our interview. Thank you for your time and for sharing your insights with me today!' or 'Thank you for your time today. We'll be in touch soon.' Make sure your conclusion is clear and definitive." if should_conclude else "Continue with another question after they respond."}
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

        # Update question count BEFORE checking completion to ensure consistency
        new_question_count = question_count + 1

        # Check if interview should end
        # Check for clear conclusion phrases that indicate the interview is ending
        explicit_conclusion_phrases = [
            "that concludes our interview",
            "concludes our interview", 
            "thank you for your time",
            "thank you for taking the time",
            "this concludes the interview",
            "we'll wrap up here",
            "that's all the questions",
            "we're done here"
        ]
        
        explicit_conclusion = any(phrase in next_question.lower() for phrase in explicit_conclusion_phrases)
        
        # Mark as completed if:
        # 1. We intended to conclude (should_conclude was True), OR
        # 2. Interviewer explicitly concluded, OR
        # 3. We've reached or exceeded the goal count (and asked at least 4 questions)
        min_questions = 4
        # Use locked goal if available, otherwise use current dynamic goal
        target_goal = session.get("locked_goal_count") or dynamic_goal_count
        # Ensure target_goal never exceeds 9 (hard limit)
        target_goal = min(target_goal, 9)
        has_reached_goal = new_question_count >= target_goal
        has_min_questions = new_question_count >= min_questions
        
        # Force completion if we've exceeded the goal (safety check)
        # This prevents interviews from continuing indefinitely
        force_complete = new_question_count > target_goal
        
        # If we intended to conclude, force completion regardless
        # This ensures interviews end when they should
        is_completed = (
            should_conclude or  # We told the AI to conclude, so mark it complete
            explicit_conclusion or 
            (has_reached_goal and has_min_questions) or
            force_complete  # Safety: if we've exceeded goal, force completion
        )
        
        # HARD LIMIT: Never exceed 9 questions - force completion at 9
        if new_question_count >= 9:
            is_completed = True
        
        # Update session
        session["conversation_history"] = history
        session["question_count"] = new_question_count
        session["performance_history"] = performance_history
        session["dynamic_goal_count"] = dynamic_goal_count
        session.modified = True

        # Use locked goal for total_questions display, otherwise use current dynamic goal
        # Ensure display_total never exceeds 9 (hard limit)
        display_total = session.get("locked_goal_count") or dynamic_goal_count
        display_total = min(display_total, 9)
        
        return jsonify({
            "question": next_question,
            "question_count": new_question_count,
            "total_questions": display_total,
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
    interview_start_time = session.get("interview_start_time")
    persona = session.get("persona", "neutral")
    
    # Calculate interview length
    interview_length = "N/A"
    if interview_start_time:
        from datetime import datetime
        try:
            start_time = datetime.fromisoformat(interview_start_time)
            end_time = datetime.now()
            duration = end_time - start_time
            minutes = int(duration.total_seconds() // 60)
            seconds = int(duration.total_seconds() % 60)
            interview_length = f"{minutes}m {seconds}s"
        except:
            pass
    
    # Get persona display name
    persona_names = {
        "strict": "Strict & High Bar",
        "friendly": "Friendly & Supportive",
        "neutral": "Neutral (Professional)"
    }
    persona_display = persona_names.get(persona, "Neutral (Professional)")
    
    feedback_prompt = f"""
Analyze the following interview for a {role_info['name']} role.

Interview Details:
- Total Questions Asked: {question_count}
- Interview Length: {interview_length}
- Role: {role_info['name']}
- Interviewer Persona: {persona_display}
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

        # Add interview metadata to feedback
        from datetime import datetime
        feedback["interview_metadata"] = {
            "total_questions": question_count,
            "interview_length": interview_length,
            "role": role_info["name"],
            "persona": persona_display,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Add question details for retry functionality
        question_details = session.get("question_details", [])
        feedback["question_details"] = question_details
        
        # Store necessary data for retry functionality before clearing session
        retry_data = {
            "role": role,
            "persona": persona,
            "resume_text": session.get("resume_text", ""),
            "resume_summary": session.get("resume_summary", {}),
            "resume_uploaded": session.get("resume_uploaded", False),
            "question_details": question_details
        }
        # Store in session with a different key so it persists after clear
        session["retry_data"] = retry_data

        session.clear()
        # Restore retry data after clear
        session["retry_data"] = retry_data
        return jsonify(feedback)

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Feedback generation error: {error_details}")
        return jsonify({"error": f"Error generating feedback: {str(e)}"}), 500


@app.route("/retry_question", methods=["POST"])
def retry_question():
    """Handle retry of a specific question"""
    data = request.json
    question_index = data.get("question_index")
    question_text = data.get("question_text")
    
    if not question_text:
        return jsonify({"error": "Question text required"}), 400
    
    # Get data from session or request
    retry_data = session.get("retry_data")
    if retry_data:
        role = retry_data.get("role")
        persona = retry_data.get("persona", "neutral")
        resume_text = retry_data.get("resume_text", "")
        resume_summary = retry_data.get("resume_summary", {})
        has_resume = retry_data.get("resume_uploaded", False)
    else:
        # Fallback: try to get from request or use defaults
        role = data.get("role") or session.get("role")
        persona = data.get("persona") or session.get("persona", "neutral")
        resume_text = session.get("resume_text", "")
        resume_summary = session.get("resume_summary", {})
        has_resume = session.get("resume_uploaded", False)
    
    if not role or role not in JOB_ROLES:
        return jsonify({"error": "Invalid role"}), 400
    
    role_info = JOB_ROLES[role]
    
    resume_context = ""
    if has_resume and resume_text:
        resume_preview = resume_text[:1000]
        if resume_summary:
            resume_context = f"Resume Context: {json.dumps(resume_summary, indent=2)}"
        else:
            resume_context = f"Resume Content: {resume_preview}"
    
    persona_styles = {
        "strict": "Maintain your strict, high-bar approach.",
        "friendly": "Maintain your friendly, supportive approach.",
        "neutral": "Maintain your professional, neutral approach."
    }
    persona_context = persona_styles.get(persona, persona_styles["neutral"])
    
    system_prompt = f"""
You are an expert interviewer for a {role_info['name']} role.

{persona_context}

{resume_context}

The candidate wants to retry answering this question: "{question_text}"

Ask this question again in a clear, supportive way. After they answer, provide brief feedback on their response.
"""
    
    try:
        response = groq_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Ask this question again: {question_text}"}
            ]
        )
        
        retry_question = response.choices[0].message.content
        
        return jsonify({
            "question": retry_question,
            "original_question": question_text
        })
    
    except Exception as e:
        return jsonify({"error": f"Error generating retry question: {e}"}), 500


@app.route("/submit_retry_answer", methods=["POST"])
def submit_retry_answer():
    """Evaluate retry answer and update feedback"""
    data = request.json
    answer = data.get("answer", "").strip()
    question_index = data.get("question_index")
    original_question = data.get("original_question", "")
    
    if not answer:
        return jsonify({"error": "Answer required"}), 400
    
    # Get data from session or request
    retry_data = session.get("retry_data")
    if retry_data:
        role = retry_data.get("role")
        question_details = retry_data.get("question_details", [])
    else:
        # Fallback: try to get from session
        role = session.get("role")
        question_details = session.get("question_details", [])
    
    if not role or role not in JOB_ROLES:
        return jsonify({"error": "Invalid role"}), 400
    
    role_info = JOB_ROLES[role]
    
    # Evaluate the retry answer
    performance_data = evaluate_answer_performance(answer, role_info)
    retry_score = performance_data["performance_score"]
    
    # Update question details
    if question_index is not None and question_index < len(question_details):
        question_details[question_index]["retry_score"] = retry_score
        question_details[question_index]["retry_answer"] = answer
        # Mark as satisfactory if retry score is >= 5.0
        if retry_score >= 5.0:
            question_details[question_index]["can_retry"] = False
        
        # Update retry_data in session
        if retry_data:
            retry_data["question_details"] = question_details
            session["retry_data"] = retry_data
        else:
            session["question_details"] = question_details
    
    # Generate feedback for the retry
    retry_feedback_prompt = f"""
The candidate retried answering this question: "{original_question}"

Their retry answer: "{answer}"

Provide brief feedback (2-3 sentences) on their retry answer. Be constructive and specific.
"""
    
    try:
        response = groq_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are an interview evaluator providing constructive feedback."},
                {"role": "user", "content": retry_feedback_prompt}
            ]
        )
        
        retry_feedback = response.choices[0].message.content
        
        return jsonify({
            "retry_score": retry_score,
            "retry_feedback": retry_feedback,
            "is_satisfactory": retry_score >= 5.0
        })
    
    except Exception as e:
        return jsonify({"error": f"Error generating retry feedback: {e}"}), 500


@app.route("/reset_interview", methods=["POST"])
def reset_interview():
    session.clear()
    return jsonify({"success": True})


if __name__ == "__main__":
    app.run(port=5000, debug=True)
