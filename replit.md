# AI Mock Interview Application

## Overview
An AI-powered web application that conducts realistic mock interviews for various job roles. Built with Flask and OpenAI GPT-5, this application provides:
- Role-specific interview questions (Software Engineer, Data Analyst, Sales, Product Manager, Marketing)
- Intelligent conversational AI that adapts to candidate responses
- Comprehensive feedback on communication, technical depth, clarity, and confidence
- Voice input support using Web Speech API

## Recent Changes
- November 22, 2025: Initial project setup
  - Configured Flask backend with session management
  - Integrated OpenAI GPT-5 for intelligent interview generation
  - Created responsive chat-based UI with ChatGPT-inspired design
  - Implemented voice recognition support
  - Added comprehensive feedback system

## Project Architecture

### Backend (Flask)
- **app.py**: Main Flask application with API endpoints
  - `/start_interview`: Initializes interview session for selected role
  - `/send_response`: Handles user responses and generates follow-up questions
  - `/get_feedback`: Analyzes interview and provides detailed feedback
  - `/reset_interview`: Clears session data
- **Session Management**: Server-side session storage for conversation history
- **OpenAI Integration**: Using GPT-5 model with role-specific prompts

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
- OpenAI 1.54.0 (using GPT-5 model)
- Gunicorn 21.2.0

## Environment Variables
- `OPENAI_API_KEY`: OpenAI API key for GPT-5 access (stored as secret) - **Required for AI features to work**
- `SESSION_SECRET`: Flask session encryption key (auto-generated if not provided)

## Setup Instructions
1. Get your OpenAI API key from https://platform.openai.com/account/api-keys
2. Add it to Replit Secrets as `OPENAI_API_KEY`
3. The Flask server will automatically restart and be ready to conduct AI-powered interviews

## Design Specifications
- Primary Color: #2563EB (Professional Blue)
- Font: Inter (Google Fonts)
- Layout: ChatGPT-inspired chat bubbles with clean spacing
- Mobile-responsive with floating input field
