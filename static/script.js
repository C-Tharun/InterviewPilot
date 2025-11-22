let isListening = false;
let recognition = null;
let currentRole = null;
let interviewCompleted = false;
let currentFeedback = null;

if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onresult = function(event) {
        const transcript = event.results[0][0].transcript;
        const userInput = document.getElementById('userInput');
        userInput.value = (userInput.value + ' ' + transcript).trim();
        updateCharCount();
    };

    recognition.onend = function() {
        isListening = false;
        const voiceBtn = document.getElementById('voiceBtn');
        voiceBtn.classList.remove('listening');
    };

    recognition.onerror = function(event) {
        console.error('Speech recognition error:', event.error);
        isListening = false;
        const voiceBtn = document.getElementById('voiceBtn');
        voiceBtn.classList.remove('listening');
        if (event.error === 'not-allowed') {
            alert('Microphone access denied. Please enable microphone permissions to use voice input.');
        }
    };
} else {
    document.addEventListener('DOMContentLoaded', function() {
        const voiceBtn = document.getElementById('voiceBtn');
        if (voiceBtn) {
            voiceBtn.style.display = 'none';
        }
    });
}

function toggleVoiceInput() {
    if (!recognition) {
        alert('Voice recognition is not supported in your browser. Please use Chrome, Edge, or Safari.');
        return;
    }

    const voiceBtn = document.getElementById('voiceBtn');
    
    if (isListening) {
        recognition.stop();
        isListening = false;
        voiceBtn.classList.remove('listening');
    } else {
        recognition.start();
        isListening = true;
        voiceBtn.classList.add('listening');
    }
}

function updateCharCount() {
    const userInput = document.getElementById('userInput');
    const charCount = document.getElementById('charCount');
    charCount.textContent = userInput.value.length;
}

document.addEventListener('DOMContentLoaded', function() {
    const userInput = document.getElementById('userInput');
    if (userInput) {
        userInput.addEventListener('input', updateCharCount);
        userInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendResponse();
            }
        });
    }
});

async function startInterview(role) {
    currentRole = role;
    interviewCompleted = false;
    
    showLoading(true);
    
    try {
        const response = await fetch('/start_interview', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ role: role })
        });

        const data = await response.json();
        
        if (response.ok) {
            document.getElementById('roleSelection').style.display = 'none';
            document.getElementById('interviewContainer').style.display = 'block';
            document.getElementById('roleTitle').textContent = data.role_name + ' Interview';
            document.getElementById('questionCounter').textContent = 'Question ' + data.question_count;
            
            addMessageToChat('assistant', data.question);
        } else {
            alert('Error: ' + (data.error || 'Failed to start interview'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Network error. Please try again.');
    } finally {
        showLoading(false);
    }
}

async function sendResponse() {
    const userInput = document.getElementById('userInput');
    const response = userInput.value.trim();
    
    if (!response) {
        alert('Please enter a response before sending.');
        return;
    }
    
    if (interviewCompleted) {
        alert('Interview is completed. Please view feedback.');
        return;
    }
    
    addMessageToChat('user', response);
    userInput.value = '';
    updateCharCount();
    
    const sendBtn = document.getElementById('sendBtn');
    sendBtn.disabled = true;
    showLoading(true);
    
    try {
        const apiResponse = await fetch('/send_response', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ response: response })
        });

        const data = await apiResponse.json();
        
        if (apiResponse.ok) {
            addMessageToChat('assistant', data.question);
            document.getElementById('questionCounter').textContent = 'Question ' + data.question_count;
            
            if (data.is_completed) {
                interviewCompleted = true;
                setTimeout(() => {
                    showFeedbackPrompt();
                }, 2000);
            }
        } else {
            alert('Error: ' + (data.error || 'Failed to send response'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Network error. Please try again.');
    } finally {
        showLoading(false);
        sendBtn.disabled = false;
    }
}

function addMessageToChat(role, content) {
    const messagesContainer = document.getElementById('messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message ' + role;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = role === 'assistant' ? '🤖' : '👤';
    
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.textContent = content;
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(bubble);
    
    messagesContainer.appendChild(messageDiv);
    
    const chatContainer = document.getElementById('chatContainer');
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function showFeedbackPrompt() {
    const confirmed = confirm('Interview completed! Would you like to see your detailed feedback?');
    if (confirmed) {
        getFeedback();
    }
}

async function getFeedback() {
    showLoading(true);
    
    try {
        const response = await fetch('/get_feedback', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();
        
        if (response.ok) {
            currentFeedback = data; // Store feedback for download
            displayFeedback(data);
            document.getElementById('interviewContainer').style.display = 'none';
            document.getElementById('feedbackContainer').style.display = 'block';
        } else {
            alert('Error: ' + (data.error || 'Failed to get feedback'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Network error. Please try again.');
    } finally {
        showLoading(false);
    }
}

function displayFeedback(feedback) {
    document.getElementById('overallScore').textContent = feedback.overall_score;
    
    const categories = ['communication', 'technical_depth', 'clarity', 'confidence'];
    const categoryIds = {
        'communication': 'comm',
        'technical_depth': 'tech',
        'clarity': 'clarity',
        'confidence': 'conf'
    };
    
    categories.forEach(category => {
        const catData = feedback[category];
        if (catData) {
            const id = categoryIds[category];
            const scorePercent = (catData.score / 10) * 100;
            
            setTimeout(() => {
                document.getElementById(id + 'Score').style.width = scorePercent + '%';
            }, 100);
            
            document.getElementById(id + 'Value').textContent = catData.score + '/10';
            document.getElementById(id + 'Feedback').textContent = catData.feedback;
        }
    });
    
    const strengthsList = document.getElementById('strengthsList');
    strengthsList.innerHTML = '';
    if (feedback.strengths) {
        feedback.strengths.forEach(strength => {
            const li = document.createElement('li');
            li.textContent = strength;
            strengthsList.appendChild(li);
        });
    }
    
    const improvementsList = document.getElementById('improvementsList');
    improvementsList.innerHTML = '';
    if (feedback.areas_for_improvement) {
        feedback.areas_for_improvement.forEach(area => {
            const li = document.createElement('li');
            li.textContent = area;
            improvementsList.appendChild(li);
        });
    }
    
    const recommendationsList = document.getElementById('recommendationsList');
    recommendationsList.innerHTML = '';
    if (feedback.recommendations) {
        feedback.recommendations.forEach(rec => {
            const li = document.createElement('li');
            li.textContent = rec;
            recommendationsList.appendChild(li);
        });
    }
}

async function exitInterview() {
    const confirmed = confirm('Are you sure you want to exit the interview? Your progress will be lost.');
    if (confirmed) {
        await fetch('/reset_interview', {
            method: 'POST'
        });
        location.reload();
    }
}

async function startNewInterview() {
    await fetch('/reset_interview', {
        method: 'POST'
    });
    location.reload();
}

function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    overlay.style.display = show ? 'flex' : 'none';
}

function downloadFeedback() {
    if (!currentFeedback) {
        alert('No feedback available to download.');
        return;
    }

    const feedback = currentFeedback;
    const roleTitle = document.getElementById('roleTitle') ? document.getElementById('roleTitle').textContent.replace(' Interview', '') : 'Interview';
    
    // Generate report content
    let report = `INTERVIEW FEEDBACK REPORT\n`;
    report += `========================\n\n`;
    report += `Role: ${roleTitle}\n`;
    report += `Date: ${new Date().toLocaleDateString()}\n\n`;
    
    report += `OVERALL SCORE: ${feedback.overall_score}/100\n\n`;
    
    report += `CATEGORY SCORES:\n`;
    report += `----------------\n`;
    
    const categories = ['communication', 'technical_depth', 'clarity', 'confidence'];
    const categoryNames = {
        'communication': 'Communication',
        'technical_depth': 'Technical Depth',
        'clarity': 'Clarity',
        'confidence': 'Confidence'
    };
    
    categories.forEach(category => {
        const catData = feedback[category];
        if (catData) {
            report += `${categoryNames[category]}: ${catData.score}/10\n`;
            report += `  ${catData.feedback}\n\n`;
        }
    });
    
    report += `STRENGTHS:\n`;
    report += `----------\n`;
    if (feedback.strengths && feedback.strengths.length > 0) {
        feedback.strengths.forEach((strength, index) => {
            report += `${index + 1}. ${strength}\n`;
        });
    } else {
        report += `No specific strengths identified.\n`;
    }
    
    report += `\nAREAS FOR IMPROVEMENT:\n`;
    report += `----------------------\n`;
    if (feedback.areas_for_improvement && feedback.areas_for_improvement.length > 0) {
        feedback.areas_for_improvement.forEach((area, index) => {
            report += `${index + 1}. ${area}\n`;
        });
    } else {
        report += `No specific areas identified.\n`;
    }
    
    report += `\nRECOMMENDATIONS:\n`;
    report += `----------------\n`;
    if (feedback.recommendations && feedback.recommendations.length > 0) {
        feedback.recommendations.forEach((rec, index) => {
            report += `${index + 1}. ${rec}\n`;
        });
    } else {
        report += `No specific recommendations.\n`;
    }
    
    report += `\n\n--- End of Report ---\n`;
    report += `Generated by AI Mock Interview Platform\n`;
    
    // Create and download file
    const blob = new Blob([report], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `interview_feedback_${roleTitle.replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}
