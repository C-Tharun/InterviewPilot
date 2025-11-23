# AI Mock Interview Platform

An intelligent, adaptive AI-powered web application that conducts realistic mock interviews for various job roles. Built with Flask and Groq's FREE Llama 3.3 70B model, featuring real-time performance adaptation and a modern, professional UI.

## 🌟 Key Features

### 🎯 Adaptive Interview System
- **Dynamic Question Count**: Automatically adjusts interview length (4-9 questions) based on candidate performance
  - **Strong candidates** (avg score ≥ 7.0): 4-5 questions (they've proven themselves quickly)
  - **Average candidates** (avg score 4.0-7.0): 6-7 questions with balanced difficulty
  - **Struggling candidates** (avg score < 4.0): 7-9 questions (more opportunities to demonstrate knowledge)
- **Real-time Performance Evaluation**: Each answer is scored on clarity, technical depth, and confidence
- **Adaptive Difficulty**: Questions automatically escalate or simplify based on candidate responses
- **Natural Interview Flow**: Interviewer adapts naturally without revealing adaptive mechanisms
- **Human-like Opening**: Starts with warm, conversational questions about background and experience before technical questions
- **Proper Conclusion**: Interviews always end with clear conclusion messages, never abruptly

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

### 🎨 Modern UI/UX
- **Gradient Backgrounds**: Beautiful, professional color schemes
- **Smooth Animations**: Slide-in effects, pulse animations, and smooth transitions
- **Interactive Elements**: Hover effects, animated progress bars, and visual feedback
- **Progress Tracking**: Visual progress bar showing interview completion
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices
- **Voice Input Support**: Browser-based speech recognition (Chrome, Edge, Safari)
  - **Live Transcription**: Real-time display of speech-to-text while speaking
  - Continuous recognition with interim results for instant feedback

## 🚀 Getting Started

### Prerequisites
- Python 3.11 or higher
- Groq API key (FREE - no credit card required)

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
└── .env                   # Environment variables (create this)
```

## 🔧 Technical Details

### Backend Architecture

**Flask Routes:**
- `GET /`: Renders the main interview interface
- `POST /start_interview`: Initializes interview session for selected role
- `POST /send_response`: Processes candidate answers and generates adaptive follow-up questions
- `POST /get_feedback`: Analyzes complete interview and provides detailed feedback
- `POST /reset_interview`: Clears session data

**Adaptive Interview Logic:**
1. **Performance Evaluation**: Each answer is evaluated using LLM-based scoring on three dimensions
2. **Performance Tracking**: Rolling average of performance scores maintained in session
3. **Dynamic Goal Calculation**: Target question count recalculated after each answer
4. **Adaptive Prompting**: System prompts adjust difficulty and focus based on performance

**Session Management:**
- `conversation_history`: Full interview transcript
- `performance_history`: Array of performance scores (1-10) for each answer
- `dynamic_goal_count`: Target number of questions (updated dynamically)
- `question_count`: Current question number

### Frontend Features

**Interactive Components:**
- Role selection cards with hover effects
- Real-time chat interface with animated message bubbles
- Progress bar with smooth animations
- Score displays with pulse effects
- Download button for feedback reports

**Voice Recognition:**
- Web Speech API integration
- Microphone permission handling
- Visual feedback during recording

## 🎯 How the Adaptive System Works

1. **Initial Assessment**: Interview starts with a moderate difficulty question
2. **Performance Scoring**: Each answer is evaluated on:
   - **Clarity**: How well-articulated the response is
   - **Technical Depth**: Level of technical accuracy and detail
   - **Confidence**: Certainty and self-assurance displayed
3. **Dynamic Adjustment**: 
   - Strong answers → Increase difficulty, ask deeper questions
   - Average answers → Maintain balanced difficulty
   - Weak answers → Simplify questions, provide encouragement
4. **Goal Adaptation**: Target question count adjusts based on rolling average performance
5. **Natural Conclusion**: Interview ends when goal count is reached or interviewer naturally concludes

## 📦 Dependencies

- **Flask 3.0.0**: Web framework
- **groq**: Groq API client for Llama 3.3 70B model
- **python-dotenv**: Environment variable management
- **gunicorn**: Production WSGI server (optional)

## 🔐 Environment Variables

- `GROQ_API_KEY`: Your Groq API key (required)
- `SESSION_SECRET`: Flask session encryption key (optional, auto-generated)

## 🎨 Design Specifications

- **Primary Colors**: Professional blue gradient (#2563EB to #764ba2)
- **Typography**: Inter font family (Google Fonts)
- **Layout**: Modern card-based design with smooth animations
- **Responsive**: Mobile-first approach with breakpoints at 768px

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

### Latest Enhancements
- ✅ **Live Voice Transcription**: Real-time display of speech-to-text while speaking
- ✅ **Reversed Adaptive Logic**: Strong candidates get fewer questions (4-5), struggling candidates get more (7-9)
- ✅ **Human-like Opening**: Interviews start with warm questions about background and experience
- ✅ **Proper Interview Conclusion**: Interviews always end with clear messages, never abruptly
- ✅ **Professional Footer**: Added footer with creator credit and social media links

### Adaptive Interview System
- ✅ Real-time performance evaluation for each answer
- ✅ Dynamic question count adjustment (4-9 questions)
- ✅ Adaptive difficulty based on candidate performance
- ✅ Natural interview flow without revealing adaptive mechanisms
- ✅ Performance history tracking and rolling averages

### Modern UI/UX Enhancements
- ✅ Gradient backgrounds and modern color schemes
- ✅ Smooth animations and transitions
- ✅ Interactive hover effects
- ✅ Visual progress indicators
- ✅ Enhanced feedback displays with animations
- ✅ Professional polish throughout

### Core Features
- ✅ Multi-role interview support (5 job roles)
- ✅ Comprehensive feedback system
- ✅ Downloadable feedback reports
- ✅ Voice input support
- ✅ Responsive design

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is open source and available under the MIT License.

## 👨‍💻 Creator

**Crafted in code by Tharun Subramanian**

- 🔗 [LinkedIn](https://www.linkedin.com/in/tharun-subramanian)
- 💻 [GitHub](https://github.com/tharun-subramanian)

## 🙏 Acknowledgments

- Built with [Groq](https://groq.com/) FREE API and Llama 3.3 70B model
- UI inspired by modern design systems
- Fonts provided by [Google Fonts](https://fonts.google.com/)

---

**Note**: This application uses Groq's FREE API with the Llama 3.3 70B model - no credit card required! The API key is needed for API access but the service itself is free to use.

