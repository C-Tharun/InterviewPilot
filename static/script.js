let isListening = false;
let recognition = null;
let currentRole = null;
let interviewCompleted = false;
let currentFeedback = null;
let voiceBaseText = '';  // Store the text that was in the textarea when voice started

// Initialize speech recognition
function initializeSpeechRecognition() {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.continuous = true;  // Keep listening continuously
        recognition.interimResults = true;  // Enable interim results for real-time display
        recognition.lang = 'en-US';

        recognition.onstart = function() {
            console.log('Speech recognition started');
            const userInput = document.getElementById('userInput');
            if (userInput) {
                userInput.placeholder = 'Listening... Speak now!';
            }
        };

        recognition.onaudiostart = function() {
            console.log('Audio capture started');
        };

        recognition.onaudioend = function() {
            console.log('Audio capture ended');
        };

        recognition.onsoundstart = function() {
            console.log('Sound detected');
        };

        recognition.onsoundend = function() {
            console.log('Sound ended');
        };

        recognition.onspeechstart = function() {
            console.log('Speech detected');
        };

        recognition.onspeechend = function() {
            console.log('Speech ended');
        };

        recognition.onresult = function(event) {
            console.log('Speech recognition result received, resultIndex:', event.resultIndex, 'results.length:', event.results.length);
            
            if (!event.results || event.results.length === 0) {
                console.log('No results in event');
                return;
            }

            let interimTranscript = '';
            let finalTranscript = '';
            const userInput = document.getElementById('userInput');

            if (!userInput) {
                console.error('userInput element not found');
                return;
            }

            // Process all results from the last processed index
            for (let i = event.resultIndex; i < event.results.length; i++) {
                if (!event.results[i] || !event.results[i][0]) {
                    continue;
                }
                const transcript = event.results[i][0].transcript;
                const confidence = event.results[i][0].confidence;
                console.log(`Result ${i}: transcript="${transcript}", isFinal=${event.results[i].isFinal}, confidence=${confidence}`);
                
                if (event.results[i].isFinal) {
                    finalTranscript += transcript + ' ';
                } else {
                    interimTranscript += transcript;
                }
            }

            console.log('Final transcript:', finalTranscript, 'Interim transcript:', interimTranscript);

            // Update the base text with final transcripts (these are confirmed)
            if (finalTranscript.trim()) {
                voiceBaseText += finalTranscript;
            }

            // Update textarea with base text + interim transcript (for real-time display)
            const displayText = (voiceBaseText + interimTranscript).trim();
            userInput.value = displayText;
            updateCharCount();
            
            // Reset placeholder if we have text
            if (displayText) {
                userInput.placeholder = 'Type your answer here...';
            }
            
            // Scroll to bottom of textarea to see the latest text
            setTimeout(() => {
                userInput.scrollTop = userInput.scrollHeight;
            }, 0);
        };

        recognition.onend = function() {
            console.log('Speech recognition ended, isListening:', isListening);
            // If user is still listening (button still active), restart recognition
            if (isListening) {
                setTimeout(() => {
                    if (isListening) {
                        try {
                            console.log('Restarting speech recognition');
                            recognition.start();
                        } catch (e) {
                            if (e.name !== 'InvalidStateError') {
                                console.error('Recognition restart error:', e);
                            }
                        }
                    }
                }, 100);
            } else {
                // User manually stopped, finalize the text
                const userInput = document.getElementById('userInput');
                if (userInput) {
                    userInput.value = voiceBaseText.trim();
                    updateCharCount();
                }
            }
        };

        recognition.onerror = function(event) {
            console.error('Speech recognition error:', event.error, 'Error details:', event);
            const userInput = document.getElementById('userInput');
            
            // Don't stop on 'no-speech' error, just restart (this is normal when user pauses)
            if (event.error === 'no-speech') {
                console.log('No speech detected, will restart if still listening');
                if (isListening) {
                    setTimeout(() => {
                        if (isListening) {
                            try {
                                console.log('Restarting after no-speech');
                                recognition.start();
                            } catch (e) {
                                console.log('Recognition restart after no-speech failed:', e);
                            }
                        }
                    }, 1000);
                }
                if (userInput) {
                    userInput.placeholder = 'No speech detected. Please speak...';
                }
                return;
            }
            
            // For other errors, stop listening
            if (event.error !== 'aborted' && event.error !== 'no-speech') {
                isListening = false;
                const voiceBtn = document.getElementById('voiceBtn');
                if (voiceBtn) {
                    voiceBtn.classList.remove('listening');
                }
                
                if (userInput) {
                    userInput.placeholder = 'Type your answer here...';
                }
                
                if (event.error === 'not-allowed') {
                    alert('Microphone access denied. Please enable microphone permissions to use voice input.');
                } else if (event.error === 'network') {
                    alert('Network error. Please check your internet connection.');
                } else if (event.error === 'audio-capture') {
                    alert('No microphone found. Please connect a microphone and try again.');
                } else {
                    console.error('Speech recognition error:', event.error);
                    alert('Voice recognition error: ' + event.error + '. Please try again.');
                }
            }
        };
    } else {
        console.log('Speech recognition not supported');
        document.addEventListener('DOMContentLoaded', function() {
            const voiceBtn = document.getElementById('voiceBtn');
            if (voiceBtn) {
                voiceBtn.style.display = 'none';
            }
        });
    }
}

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeSpeechRecognition);
} else {
    initializeSpeechRecognition();
}

function toggleVoiceInput() {
    console.log('toggleVoiceInput called, isListening:', isListening);
    
    if (!recognition) {
        alert('Voice recognition is not supported in your browser. Please use Chrome, Edge, or Safari.');
        return;
    }

    const voiceBtn = document.getElementById('voiceBtn');
    const userInput = document.getElementById('userInput');
    
    if (!voiceBtn || !userInput) {
        console.error('Voice button or user input not found');
        return;
    }
    
    if (isListening) {
        // Stop listening
        console.log('Stopping voice recognition');
        isListening = false;
        recognition.stop();
        voiceBtn.classList.remove('listening');
        
        // Finalize the text
        userInput.value = voiceBaseText.trim();
        updateCharCount();
    } else {
        // Start listening
        console.log('Starting voice recognition');
        // Store the current text as base text
        voiceBaseText = userInput.value.trim();
        if (voiceBaseText && !voiceBaseText.endsWith(' ')) {
            voiceBaseText += ' ';
        }
        
        // Request microphone permission first
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(function(stream) {
                console.log('Microphone access granted');
                // Stop the stream as we just needed permission
                stream.getTracks().forEach(track => track.stop());
                
                // Now start recognition
                try {
                    recognition.start();
                    isListening = true;
                    voiceBtn.classList.add('listening');
                    userInput.placeholder = 'Listening... Speak now!';
                    console.log('Voice recognition started successfully');
                } catch (e) {
                    console.error('Error starting recognition:', e);
                    // If already running, stop first then restart
                    if (e.name === 'InvalidStateError') {
                        recognition.stop();
                        setTimeout(() => {
                            try {
                                recognition.start();
                                isListening = true;
                                voiceBtn.classList.add('listening');
                                userInput.placeholder = 'Listening... Speak now!';
                                console.log('Voice recognition restarted successfully');
                            } catch (e2) {
                                console.error('Failed to restart recognition:', e2);
                                alert('Could not start voice recognition. Please try again.');
                                userInput.placeholder = 'Type your answer here...';
                            }
                        }, 300);
                    } else {
                        alert('Could not start voice recognition: ' + e.message);
                        userInput.placeholder = 'Type your answer here...';
                    }
                }
            })
            .catch(function(err) {
                console.error('Microphone access denied:', err);
                alert('Microphone access is required for voice input. Please allow microphone access and try again.');
                userInput.placeholder = 'Type your answer here...';
            });
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
            updateQuestionCounter(data.question_count, data.total_questions || 6);
            
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
            updateQuestionCounter(data.question_count, data.total_questions || 6);
            
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

function updateQuestionCounter(current, total) {
    const counter = document.getElementById('questionCounter');
    const progressBar = document.getElementById('progressBar');
    
    if (counter) {
        counter.textContent = `Question ${current} of ${total}`;
    }
    
    if (progressBar) {
        const percentage = (current / total) * 100;
        progressBar.style.width = percentage + '%';
    }
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

