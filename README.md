# [AI Mock Interview Platform](https://interview-pilot-1ivv.onrender.com/)

An intelligent, adaptive AI-powered web application that conducts realistic mock interviews for various job roles. Built with Flask and Groq's FREE Llama 3.3 70B model, featuring real-time performance adaptation, resume-based context awareness, and a modern, professional UI.

## 🏗️ Architecture Diagram
Below is the high-level architecture of the AI Mock Interview Platform:

![Architecture Diagram](static/images/architecture.png)



## 🌟 Key Features

### 🎯 Adaptive Interview System
- **Dynamic Question Count**: Automatically adjusts interview length (4-9 questions) based on candidate performance
  - **Strong candidates** (avg score ≥ 7.0): 4-5 questions (they've proven themselves quickly)
  - **Average candidates** (avg score 4.0-7.0): 6-7 questions with balanced difficulty
  - **Struggling candidates** (avg score < 4.0): 7-9 questions (more opportunities to demonstrate knowledge)
  - **Hard Limit**: Maximum 9 questions, never exceeds this limit
- **Real-time Performance Evaluation**: Each answer is scored on clarity, technical depth, and confidence
- **Adaptive Difficulty**: Questions automatically escalate or simplify based on candidate responses
- **Natural Interview Flow**: Interviewer adapts naturally without revealing adaptive mechanisms
- **Human-like Opening**: Starts with warm, conversational questions about background and experience before technical questions
- **Proper Conclusion**: Interviews always end with clear conclusion messages, never abruptly
- **Goal Locking**: Question count locks after first answer to prevent constant changes

### 📄 Resume Upload & Context Awareness
- **Resume Upload**: Upload your resume (PDF or TXT) to make interviews context-aware
- **Intelligent Parsing**: Automatically extracts and summarizes resume content using AI
- **Personalized Questions**: Interviewer references your specific projects, skills, and experiences
- **Structured Summary**: Extracts name, education, experience, skills, and projects
- **Context Integration**: Questions are tailored based on your background

### 🎭 Interviewer Personas
Choose from three different interviewer styles:
- **Strict & High Bar**: Challenging questions, high expectations, direct feedback
- **Friendly & Supportive**: Warm, encouraging, makes you feel comfortable
- **Neutral (Professional)**: Balanced, objective, standard interview approach

### 💼 Role-Specific Interviews
- **Software Engineer**: Algorithms, data structures, system design, coding practices
- **Data Analyst**: SQL, statistics, data analysis, visualization, business insights
- **Sales Representative**: Sales techniques, customer relationships, negotiation, product knowledge
- **Product Manager**: Product strategy, user research, prioritization, stakeholder management
- **Marketing Specialist**: Marketing strategy, campaign management, analytics, brand positioning

### 📊 Comprehensive Feedback System
- **Overall Score**: 0-100 rating
- **Category Scores**: Detailed scoring across 4 dimensions:
  - Communication (0-10)
  - Technical Depth (0-10)
  - Clarity (0-10)
  - Confidence (0-10)
- **Actionable Insights**:
  - ✅ Strengths (always provided, even for struggling candidates)
  - 📈 Areas for Improvement
  - 💡 Personalized Recommendations
- **Downloadable Reports**: Export feedback as text file for offline review
- **Interview Metadata**: Includes total questions, interview length, role, persona, and timestamp

### 🔄 Retry Question Feature
- **Poor Performance Tracking**: Questions with scores < 4.0 are marked for retry
- **Practice Again**: Retry questions you didn't perform well on
- **Updated Feedback**: Retry scores and feedback are tracked and displayed
- **Completion Status**: Questions marked as completed when retry score ≥ 5.0

### 🎨 UI/UX
- **Gradient Backgrounds**: Professional color schemes
- **Smooth Animations**: Slide-in effects, pulse animations, and smooth transitions
- **Interactive Elements**: Hover effects, animated progress bars, and visual feedback
- **Progress Tracking**: Visual progress bar showing interview completion with question counter
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices
- **Voice Input Support**: Browser-based speech recognition (Chrome, Edge, Safari)
  - **Live Transcription**: Real-time display of speech-to-text while speaking
  - Continuous recognition with interim results for instant feedback
  - Automatic restart on errors for seamless experience

## 🚀 Getting Started

### Prerequisites
- Python 3.11 or higher
- Groq API key (FREE - no credit card required)
- Modern web browser (Chrome, Edge, or Safari for voice input)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd InterviewPilot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   
   Create a `.env` file in the root directory:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   SESSION_SECRET=your_secret_key_here  # Optional, auto-generated if not provided
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the application**
   
   Open your browser and navigate to: `http://localhost:5000`

## 📁 Project Structure

```
InterviewPilot/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html         # Frontend HTML template
├── static/
│   ├── style.css          # Modern CSS styling
│   └── script.js          # Frontend JavaScript logic
├── uploads/               # Resume uploads directory (auto-created)
└── .env                   # Environment variables (create this)
```

## 🔧 Technical Details

### Backend Architecture

**Flask Routes:**
- `GET /`: Renders the main interview interface
- `POST /upload_resume`: Handles resume file upload and text extraction
- `POST /start_interview`: Initializes interview session for selected role and persona
- `POST /send_response`: Processes candidate answers and generates adaptive follow-up questions
- `POST /get_feedback`: Analyzes complete interview and provides detailed feedback
- `POST /retry_question`: Generates retry question for poor-performing questions
- `POST /submit_retry_answer`: Evaluates retry answer and provides feedback
- `POST /reset_interview`: Clears session data

**Adaptive Interview Logic:**
1. **Performance Evaluation**: Each answer is evaluated using LLM-based scoring on three dimensions
2. **Performance Tracking**: Rolling average of performance scores maintained in session
3. **Dynamic Goal Calculation**: Target question count recalculated after each answer (4-9 questions)
4. **Goal Locking**: Question count locks after first answer to prevent constant changes
5. **Adaptive Prompting**: System prompts adjust difficulty and focus based on performance
6. **Completion Logic**: Multiple triggers ensure interviews end properly at goal count

**Session Management:**
- `conversation_history`: Full interview transcript
- `performance_history`: Array of performance scores (1-10) for each answer
- `dynamic_goal_count`: Target number of questions (updated dynamically, max 9)
- `locked_goal_count`: Locked goal count after first answer
- `question_count`: Current question number
- `resume_text`: Extracted resume text
- `resume_summary`: Structured resume summary
- `question_details`: Questions eligible for retry

**Resume Processing:**
- PDF parsing using PyPDF2
- Text file support
- AI-powered summarization
- Structured data extraction (name, education, experience, skills, projects)

### Frontend Features

**Interactive Components:**
- Role selection cards with hover effects
- Persona selection interface
- Resume upload with drag-and-drop support
- Real-time chat interface with animated message bubbles
- Progress bar with smooth animations
- Score displays with pulse effects
- Retry question cards with improved UI
- Download button for feedback reports

**Voice Recognition:**
- Web Speech API integration
- Microphone permission handling
- Visual feedback during recording
- Automatic error recovery
- Continuous recognition mode

**Interview Completion:**
- Automatic feedback prompt after completion
- Input disabling when interview ends
- Clear visual indicators
- Smooth transitions to feedback view

## 🎯 How the Adaptive System Works

1. **Initial Assessment**: Interview starts with a moderate difficulty question
2. **Performance Scoring**: Each answer is evaluated on:
   - **Clarity**: How well-articulated the response is
   - **Technical Depth**: Level of technical accuracy and detail
   - **Confidence**: Certainty and self-assurance displayed
3. **Dynamic Adjustment**: 
   - Strong answers → Increase difficulty, ask deeper questions, reduce total questions (4-5)
   - Average answers → Maintain balanced difficulty, moderate total (6-7)
   - Weak answers → Simplify questions, provide encouragement, increase total (7-9)
4. **Goal Adaptation**: Target question count adjusts based on rolling average performance
5. **Goal Locking**: After first answer, goal count locks to prevent constant changes
6. **Natural Conclusion**: Interview ends when goal count is reached (max 9) or interviewer naturally concludes

## 📦 Dependencies

- **Flask 3.0.0**: Web framework
- **groq**: Groq API client for Llama 3.3 70B model
- **python-dotenv**: Environment variable management
- **PyPDF2 3.0.1**: PDF parsing for resume uploads
- **gunicorn 21.2.0**: Production WSGI server (optional)
- **werkzeug**: File upload handling

## 🔐 Environment Variables

- `GROQ_API_KEY`: Your Groq API key (required)
- `SESSION_SECRET`: Flask session encryption key (optional, auto-generated)

## 🎨 Design Specifications

- **Primary Colors**: Professional blue gradient (#2563EB to #764ba2)
- **Typography**: Inter font family (Google Fonts)
- **Layout**: Modern card-based design with smooth animations
- **Responsive**: Mobile-first approach with breakpoints at 768px
- **Accessibility**: Clear visual hierarchy and intuitive navigation

## 🚀 Deployment

### Local Development
```bash
python app.py
```

### Production (using Gunicorn)
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 📝 Recent Updates

### Latest Enhancements (v2.0)
- ✅ **Resume Upload Feature**: Upload PDF or TXT resumes for context-aware interviews
- ✅ **AI Resume Parsing**: Automatic extraction and summarization of resume content
- ✅ **Interviewer Personas**: Choose from Strict, Friendly, or Neutral interviewer styles
- ✅ **Retry Question Feature**: Practice questions you didn't perform well on
- ✅ **Improved Completion Logic**: Interviews end properly at goal count (max 9 questions)
- ✅ **Goal Locking**: Question count locks after first answer to prevent constant changes
- ✅ **Enhanced UI**: Improved retry question cards and better visual feedback
- ✅ **Better Error Handling**: Robust error handling for resume uploads and retry functionality
- ✅ **Session Management**: Improved session handling for retry questions after interview completion

### Adaptive Interview System
- ✅ Real-time performance evaluation for each answer
- ✅ Dynamic question count adjustment (4-9 questions, max 9)
- ✅ Adaptive difficulty based on candidate performance
- ✅ Natural interview flow without revealing adaptive mechanisms
- ✅ Performance history tracking and rolling averages
- ✅ Hard limit of 9 questions maximum

### UI/UX Enhancements
- ✅ Gradient backgrounds and modern color schemes
- ✅ Smooth animations and transitions
- ✅ Interactive hover effects
- ✅ Visual progress indicators with question counter
- ✅ Enhanced feedback displays with animations
- ✅ Professional polish throughout
- ✅ Improved retry question UI with better layout

### Core Features
- ✅ Multi-role interview support (5 job roles)
- ✅ Comprehensive feedback system
- ✅ Downloadable feedback reports
- ✅ Voice input support with live transcription
- ✅ Responsive design
- ✅ Resume-based context awareness
- ✅ Interviewer persona selection

## 🐛 Known Issues & Solutions

### Session Cookie Size Warning
If you see warnings about session cookie size being too large:
- This is normal when resumes are uploaded (session stores resume data)
- The application still functions correctly
- For production, consider using server-side session storage (Redis, database)

### Voice Input
- Works best in Chrome, Edge, or Safari
- Requires microphone permissions
- May need HTTPS in production for microphone access

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.


## 👨‍💻 Creator

**Crafted in code by Tharun Subramanian**

- 🔗 [LinkedIn](https://www.linkedin.com/in/tharun-c/)
- 💻 [GitHub](https://github.com/C-Tharun/)

## 🙏 Acknowledgments

- Built with [Groq](https://groq.com/) FREE API and Llama 3.3 70B model
- Fonts provided by [Google Fonts](https://fonts.google.com/)
- PDF parsing with PyPDF2

---

**Note**: This application uses Groq's FREE API with the Llama 3.3 70B model - no credit card required! The API key is needed for API access but the service itself is free to use.

**Features Summary:**
- 🎯 Adaptive interviews (4-9 questions based on performance)
- 📄 Resume upload for context-aware interviews
- 🎭 Multiple interviewer personas
- 🔄 Retry question functionality
- 📊 Comprehensive feedback system
- 🎤 Voice input support
- 📱 Fully responsive design
