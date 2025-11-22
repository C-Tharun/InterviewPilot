# AI Mock Interview Application

## Overview
An AI-powered web application that conducts realistic mock interviews for various job roles. Built with Flask and Groq's FREE Llama 3.3 70B model, this application provides:
- Role-specific interview questions (Software Engineer, Data Analyst, Sales, Product Manager, Marketing)
- Intelligent conversational AI that adapts to candidate responses
- Comprehensive feedback on communication, technical depth, clarity, and confidence
- Voice input support using Web Speech API

## Recent Changes
- November 22, 2025: Initial project setup and deployment
  - Configured Flask backend with session management
  - Integrated Groq FREE API with Llama 3.3 70B for intelligent interview generation
  - Created responsive chat-based UI with ChatGPT-inspired design
  - Implemented voice recognition support
  - Added comprehensive feedback system
  - Fixed API response handling and model compatibility

## Project Architecture

### Backend (Flask)
- **app.py**: Main Flask application with API endpoints
  - `/start_interview`: Initializes interview session for selected role
  - `/send_response`: Handles user responses and generates follow-up questions
  - `/get_feedback`: Analyzes interview and provides detailed feedback
  - `/reset_interview`: Clears session data
- **Session Management**: Server-side session storage for conversation history
- **Groq Integration**: Using FREE Llama 3.3 70B model with role-specific prompts

### Frontend
- **templates/index.html**: Single-page application structure
  - Role selection interface
  - Chat-based interview interface
  - Detailed feedback display
- **static/style.css**: Professional blue theme (#2563EB) with responsive design
- **static/script.js**: Handles user interactions, API calls, and voice recognition

### Key Features
1. **Role Selection**: 5 job roles with tailored interview approaches
2. **Adaptive Questioning**: AI adjusts to confused, efficient, chatty, or off-topic responses
3. **Progress Tracking**: Question counter and interview flow management
4. **Voice Input**: Browser-based speech recognition (Chrome, Edge, Safari)
5. **Comprehensive Feedback**: Scored analysis across 4 dimensions plus actionable recommendations

## Dependencies
- Flask 3.0.0
- Groq 0.9.0 (FREE AI API)
- Gunicorn 21.2.0
- python-dotenv 1.0.1

## Environment Variables
- `GROQ_API_KEY`: Groq API key for FREE Llama 3.3 70B access (stored as secret) - **Already configured and working!**
- `SESSION_SECRET`: Flask session encryption key (auto-generated if not provided)

## How It Works
The app uses Groq's completely FREE API with the powerful Llama 3.3 70B model - no credit card required! The API key is already set up and the app is ready to use immediately.

## Design Specifications
- Primary Color: #2563EB (Professional Blue)
- Font: Inter (Google Fonts)
- Layout: ChatGPT-inspired chat bubbles with clean spacing
- Mobile-responsive with floating input field
