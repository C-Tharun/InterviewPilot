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

let selectedRole = null;

function selectRole(role) {
    selectedRole = role;
    document.getElementById('roleSelection').style.display = 'none';
    document.getElementById('personaSelection').style.display = 'block';
}

function selectPersona(persona) {
    if (!selectedRole) return;
    startInterview(selectedRole, persona);
}

function goBackToRoles() {
    document.getElementById('personaSelection').style.display = 'none';
    document.getElementById('roleSelection').style.display = 'block';
    selectedRole = null;
}

async function startInterview(role, persona = 'neutral') {
    currentRole = role;
    interviewCompleted = false;
    
    // Re-enable input when starting new interview
    const userInput = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');
    const voiceBtn = document.getElementById('voiceBtn');
    
    if (userInput) {
        userInput.disabled = false;
        userInput.placeholder = 'Type your answer here...';
    }
    if (sendBtn) {
        sendBtn.disabled = false;
        sendBtn.textContent = 'Send';
    }
    if (voiceBtn) {
        voiceBtn.disabled = false;
    }
    
    document.getElementById('personaSelection').style.display = 'none';
    showLoading(true);
    
    try {
        const response = await fetch('/start_interview', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ role: role, persona: persona })
        });

        const data = await response.json();
        
        if (response.ok) {
            document.getElementById('interviewContainer').style.display = 'block';
            document.getElementById('roleTitle').textContent = data.role_name + ' Interview';
            updateQuestionCounter(data.question_count, data.total_questions || 6);
            
            addMessageToChat('assistant', data.question);
            
            // Show voice tooltip on interview start
            showVoiceTooltip();
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
        const viewFeedback = confirm('Interview is completed. Would you like to view your feedback?');
        if (viewFeedback) {
            getFeedback();
        }
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
            // Ensure question_count and total_questions are valid numbers
            const questionCount = data.question_count || 1;
            const totalQuestions = data.total_questions || 6;
            updateQuestionCounter(questionCount, totalQuestions);
            
            // Check if interview is completed (from backend or from AI's message)
            const isCompleted = data.is_completed || checkIfInterviewConcluded(data.question);
            
            if (isCompleted) {
                interviewCompleted = true;
                // Disable input immediately when interview is completed
                disableInterviewInput();
                // Show feedback prompt after a short delay
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
    // Automatically show feedback after interview completion
    // Small delay to let user see the final message
    const confirmed = confirm('Interview completed! Would you like to see your detailed feedback?');
    if (confirmed) {
        getFeedback();
    } else {
        // If user cancels, still disable input but allow them to view feedback later
        disableInterviewInput();
    }
}

function checkIfInterviewConcluded(message) {
    // Check if the AI's message contains conclusion phrases
    const conclusionPhrases = [
        'that concludes our interview',
        'concludes our interview',
        'thank you for your time',
        'thank you for taking the time',
        'this concludes the interview',
        "we'll wrap up here",
        "that's all the questions",
        "we're done here"
    ];
    
    const messageLower = message.toLowerCase();
    return conclusionPhrases.some(phrase => messageLower.includes(phrase));
}

function disableInterviewInput() {
    const userInput = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');
    const voiceBtn = document.getElementById('voiceBtn');
    
    if (userInput) {
        userInput.disabled = true;
        userInput.placeholder = 'Interview completed. Click "View Feedback" to see your results.';
    }
    if (sendBtn) {
        sendBtn.disabled = true;
        sendBtn.textContent = 'Interview Completed';
    }
    if (voiceBtn) {
        voiceBtn.disabled = true;
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
    
    // Display interview metadata
    if (feedback.interview_metadata) {
        const meta = feedback.interview_metadata;
        document.getElementById('metadataQuestions').textContent = meta.total_questions || '-';
        document.getElementById('metadataLength').textContent = meta.interview_length || '-';
        document.getElementById('metadataRole').textContent = meta.role || '-';
        document.getElementById('metadataPersona').textContent = meta.persona || '-';
        document.getElementById('metadataTimestamp').textContent = meta.timestamp || '-';
    }
    
    // Display retry questions section
    displayRetryQuestions(feedback);
    
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

function showVoiceTooltip() {
    const tooltip = document.getElementById('voiceTooltip');
    if (tooltip) {
        tooltip.style.display = 'block';
        // Auto-hide after 10 seconds
        setTimeout(() => {
            if (tooltip.style.display !== 'none') {
                dismissVoiceTooltip();
            }
        }, 10000);
    }
}

function dismissVoiceTooltip() {
    const tooltip = document.getElementById('voiceTooltip');
    if (tooltip) {
        tooltip.style.display = 'none';
    }
}

// Resume Upload Functions
async function handleResumeUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const fileName = document.getElementById('resumeFileName');
    const uploadStatus = document.getElementById('resumeUploadStatus');
    
    fileName.textContent = file.name;
    uploadStatus.innerHTML = '<span class="uploading">Uploading...</span>';
    
    const formData = new FormData();
    formData.append('resume', file);
    
    try {
        const response = await fetch('/upload_resume', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            uploadStatus.innerHTML = '<span class="upload-success">✓ Resume uploaded successfully!</span>';
            fileName.style.color = 'var(--success-green)';
        } else {
            uploadStatus.innerHTML = '<span class="upload-error">✗ ' + (data.error || 'Upload failed') + '</span>';
            fileName.textContent = '';
        }
    } catch (error) {
        console.error('Upload error:', error);
        uploadStatus.innerHTML = '<span class="upload-error">✗ Upload failed. Please try again.</span>';
        fileName.textContent = '';
    }
}

// Retry Question Functions
let currentRetryQuestionIndex = -1;
let currentRetryQuestion = '';

function displayRetryQuestions(feedback) {
    const retrySection = document.getElementById('retryQuestionsSection');
    const retryList = document.getElementById('retryQuestionsList');
    
    if (!feedback.question_details || feedback.question_details.length === 0) {
        retrySection.style.display = 'none';
        return;
    }
    
    const poorQuestions = feedback.question_details.filter(q => q.can_retry !== false && q.original_score < 4.0);
    
    if (poorQuestions.length === 0) {
        retrySection.style.display = 'none';
        return;
    }
    
    retrySection.style.display = 'block';
    retryList.innerHTML = '';
    
    poorQuestions.forEach((question, index) => {
        // Find original index in question_details array
        const originalIndex = feedback.question_details.findIndex(q => 
            q.question === question.question && q.question_number === question.question_number
        );
        
        const questionDiv = document.createElement('div');
        questionDiv.className = 'retry-question-item';
        
        // Store data in data attributes to avoid syntax errors
        questionDiv.setAttribute('data-question-index', originalIndex);
        questionDiv.setAttribute('data-question-text', question.question);
        
        questionDiv.innerHTML = `
            <div class="retry-question-content">
                <div class="retry-question-header">
                    <span class="retry-question-number">Question ${question.question_number}</span>
                    <span class="retry-question-score">Score: ${question.original_score.toFixed(1)}/10</span>
                </div>
                <p class="retry-question-text">${question.question}</p>
                ${question.retry_score ? `
                    <div class="retry-result">
                        <strong>Retry Score: ${question.retry_score.toFixed(1)}/10</strong>
                        <p>${question.retry_feedback || ''}</p>
                    </div>
                ` : ''}
            </div>
            ${question.can_retry !== false ? `
                <button class="btn-primary btn-retry" type="button">
                    🔄 Retry This Question
                </button>
            ` : '<span class="retry-complete">✓ Completed</span>'}
        `;
        
        // Add event listener to retry button
        const retryButton = questionDiv.querySelector('.btn-retry');
        if (retryButton) {
            retryButton.addEventListener('click', () => {
                openRetryOverlay(originalIndex, question.question);
            });
        }
        
        retryList.appendChild(questionDiv);
    });
}

async function openRetryOverlay(questionIndex, questionText) {
    currentRetryQuestionIndex = questionIndex;
    currentRetryQuestion = questionText;
    
    const overlay = document.getElementById('retryOverlay');
    const retryMessages = document.getElementById('retryMessages');
    
    overlay.style.display = 'flex';
    
    // Show loading
    retryMessages.innerHTML = `
        <div class="message assistant">
            <div class="message-avatar">🤖</div>
            <div class="message-bubble">Loading question...</div>
        </div>
    `;
    
    // Blur the feedback container
    document.getElementById('feedbackContainer').style.filter = 'blur(5px)';
    document.getElementById('feedbackContainer').style.pointerEvents = 'none';
    
    // Fetch the retry question from server
    try {
        const response = await fetch('/retry_question', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question_index: questionIndex,
                question_text: questionText
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            retryMessages.innerHTML = `
                <div class="message assistant">
                    <div class="message-avatar">🤖</div>
                    <div class="message-bubble">${data.question}</div>
                </div>
            `;
        } else {
            retryMessages.innerHTML = `
                <div class="message assistant">
                    <div class="message-avatar">🤖</div>
                    <div class="message-bubble">${questionText}</div>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error fetching retry question:', error);
        retryMessages.innerHTML = `
            <div class="message assistant">
                <div class="message-avatar">🤖</div>
                <div class="message-bubble">${questionText}</div>
            </div>
        `;
    }
}

function closeRetryOverlay() {
    const overlay = document.getElementById('retryOverlay');
    overlay.style.display = 'none';
    
    // Unblur the feedback container
    document.getElementById('feedbackContainer').style.filter = 'none';
    document.getElementById('feedbackContainer').style.pointerEvents = 'auto';
    
    // Clear retry input
    document.getElementById('retryInput').value = '';
    currentRetryQuestionIndex = -1;
    currentRetryQuestion = '';
}

async function submitRetryAnswer() {
    const answer = document.getElementById('retryInput').value.trim();
    if (!answer) {
        alert('Please enter an answer');
        return;
    }
    
    const retryMessages = document.getElementById('retryMessages');
    const retryInput = document.getElementById('retryInput');
    
    // Add user message
    const userMsg = document.createElement('div');
    userMsg.className = 'message user';
    userMsg.innerHTML = `
        <div class="message-avatar">👤</div>
        <div class="message-bubble">${answer}</div>
    `;
    retryMessages.appendChild(userMsg);
    retryInput.value = '';
    
    // Show loading
    const loadingMsg = document.createElement('div');
    loadingMsg.className = 'message assistant';
    loadingMsg.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-bubble">Evaluating your answer...</div>
    `;
    retryMessages.appendChild(loadingMsg);
    retryMessages.scrollTop = retryMessages.scrollHeight;
    
    try {
        const response = await fetch('/submit_retry_answer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                answer: answer,
                question_index: currentRetryQuestionIndex,
                original_question: currentRetryQuestion
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Remove loading message
            loadingMsg.remove();
            
            // Add feedback message
            const feedbackMsg = document.createElement('div');
            feedbackMsg.className = 'message assistant';
            feedbackMsg.innerHTML = `
                <div class="message-avatar">🤖</div>
                <div class="message-bubble">
                    <strong>Retry Score: ${data.retry_score.toFixed(1)}/10</strong><br>
                    ${data.retry_feedback}
                </div>
            `;
            retryMessages.appendChild(feedbackMsg);
            
            // Update currentFeedback with retry data
            if (currentFeedback && currentFeedback.question_details && currentFeedback.question_details[currentRetryQuestionIndex]) {
                currentFeedback.question_details[currentRetryQuestionIndex].retry_score = data.retry_score;
                currentFeedback.question_details[currentRetryQuestionIndex].retry_feedback = data.retry_feedback;
                if (data.is_satisfactory) {
                    currentFeedback.question_details[currentRetryQuestionIndex].can_retry = false;
                }
            }
            
            // Close overlay after 3 seconds and refresh feedback
            setTimeout(() => {
                closeRetryOverlay();
                // Refresh feedback display to update retry status
                displayFeedback(currentFeedback);
            }, 3000);
        } else {
            alert('Error: ' + (data.error || 'Failed to submit answer'));
            loadingMsg.remove();
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Network error. Please try again.');
        loadingMsg.remove();
    }
}

function updateQuestionCounter(current, total) {
    const counter = document.getElementById('questionCounter');
    const progressBar = document.getElementById('progressBar');
    
    // Ensure values are valid numbers
    current = Number(current) || 1;
    total = Number(total) || 6;
    
    // Ensure current doesn't exceed total (cap it)
    if (current > total) {
        current = total;
    }
    
    if (counter) {
        counter.textContent = `Question ${current} of ${total}`;
    }
    
    if (progressBar) {
        const percentage = Math.min((current / total) * 100, 100);
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

