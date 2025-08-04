class VoiceAvatarApp {
    constructor() {
        this.isRecording = false;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.sessionId = this.generateSessionId();
        this.hedraWebSocket = null;
        this.isHedraConnected = false;
        
        this.initializeElements();
        this.setupEventListeners();
        this.checkMicrophonePermission();
        this.connectToHedraAvatar();
    }
    
    generateSessionId() {
        return 'session_' + Math.random().toString(36).substr(2, 9);
    }
    
    initializeElements() {
        this.micButton = document.getElementById('micButton');
        this.stopButton = document.getElementById('stopButton');
        this.status = document.getElementById('status');
        this.conversation = document.getElementById('conversation');
        this.avatar = document.getElementById('avatar');
        this.speakingIndicator = document.getElementById('speakingIndicator');
        this.hedraVideo = document.getElementById('hedra-video');
        this.avatarImage = document.getElementById('avatar-image');
    }
    
    setupEventListeners() {
        // Mouse events for desktop
        this.micButton.addEventListener('mousedown', () => this.startRecording());
        this.micButton.addEventListener('mouseup', () => this.stopRecording());
        this.micButton.addEventListener('mouseleave', () => this.stopRecording());
        
        // Touch events for mobile
        this.micButton.addEventListener('touchstart', (e) => {
            e.preventDefault();
            this.startRecording();
        });
        this.micButton.addEventListener('touchend', (e) => {
            e.preventDefault();
            this.stopRecording();
        });
        
        // Prevent context menu on long press
        this.micButton.addEventListener('contextmenu', (e) => e.preventDefault());
        
        // Stop button for Hedra stream
        this.stopButton.addEventListener('click', () => this.stopHedraStream());
    }
    
    async checkMicrophonePermission() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            stream.getTracks().forEach(track => track.stop());
            this.updateStatus('Ready to listen');
        } catch (error) {
            this.updateStatus('Microphone access denied');
            console.error('Microphone permission denied:', error);
        }
    }
    
    async startRecording() {
        if (this.isRecording) return;
        
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    sampleRate: 44100,      // Standard sample rate
                    channelCount: 1,        // Mono for smaller files
                    echoCancellation: true,
                    noiseSuppression: true
                }
            });
            
            // FIXED: Better MIME type selection
            let mimeType = 'audio/wav';
            if (MediaRecorder.isTypeSupported('audio/wav')) {
                mimeType = 'audio/wav';
            } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
                mimeType = 'audio/mp4';
            } else {
                mimeType = 'audio/webm';  // Last resort
            }
            
            console.log(`Using audio format: ${mimeType}`);
            
            this.mediaRecorder = new MediaRecorder(stream, { mimeType });
            this.audioChunks = [];
            this.isRecording = true;
            
            this.mediaRecorder.ondataavailable = (event) => {
                this.audioChunks.push(event.data);
            };
            
            this.mediaRecorder.onstop = () => {
                this.processRecording();
                stream.getTracks().forEach(track => track.stop());
            };
            
            this.mediaRecorder.start();
            this.updateUI(true);
            this.updateStatus('Listening... Release to send');
            
        } catch (error) {
            console.error('Error starting recording:', error);
            this.updateStatus('Error accessing microphone');
        }
    }
    
    stopRecording() {
        if (!this.isRecording || !this.mediaRecorder) return;
        
        this.isRecording = false;
        this.mediaRecorder.stop();
        this.updateUI(false);
        this.updateStatus('Processing...');
    }
    
    async processRecording() {
        try {
            const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
            
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.wav');
            formData.append('session_id', this.sessionId);
            
            const response = await fetch('http://localhost:5001/process-voice', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error('Server error');
            }
            
            const data = await response.json();
            
            // Add user message to conversation
            this.addMessage(data.transcript, 'user');
            
            // Add bot response to conversation
            this.addMessage(data.response, 'bot');
            
            // Try to use Hedra Live Avatar first, fallback to audio
            const hedraSuccess = await this.sendTextToHedraAvatar(data.response);
            
            if (!hedraSuccess && data.audio) {
                await this.playAudioResponse(data.audio);
            }
            
            this.updateStatus('Ready to listen');
            
        } catch (error) {
            console.error('Error processing recording:', error);
            this.addMessage('Sorry, I had trouble processing that. Please try again.', 'bot');
            this.updateStatus('Error - Ready to try again');
        }
    }
    
    async playAudioResponse(audioBase64) {
        try {
            // Show speaking indicator
            this.setSpeaking(true);
            
            // Convert base64 to audio
            const audioData = atob(audioBase64);
            const audioArray = new Uint8Array(audioData.length);
            for (let i = 0; i < audioData.length; i++) {
                audioArray[i] = audioData.charCodeAt(i);
            }
            
            const audioBlob = new Blob([audioArray], { type: 'audio/mpeg' });
            const audioUrl = URL.createObjectURL(audioBlob);
            
            const audio = new Audio(audioUrl);
            
            audio.onended = () => {
                this.setSpeaking(false);
                URL.revokeObjectURL(audioUrl);
            };
            
            audio.onerror = () => {
                this.setSpeaking(false);
                URL.revokeObjectURL(audioUrl);
            };
            
            await audio.play();
            
        } catch (error) {
            console.error('Error playing audio:', error);
            this.setSpeaking(false);
        }
    }
    
    addMessage(text, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        const label = type === 'user' ? 'You' : 'Avatar';
        messageDiv.innerHTML = `<strong>${label}:</strong> ${text}`;
        
        this.conversation.appendChild(messageDiv);
        this.conversation.scrollTop = this.conversation.scrollHeight;
    }
    
    updateUI(recording) {
        if (recording) {
            this.micButton.classList.add('recording');
        } else {
            this.micButton.classList.remove('recording');
        }
    }
    
    updateStatus(text) {
        this.status.textContent = text;
    }
    
    setSpeaking(speaking) {
        if (speaking) {
            this.speakingIndicator.classList.add('active');
        } else {
            this.speakingIndicator.classList.remove('active');
        }
    }
    
    async connectToHedraAvatar() {
        try {
            const response = await fetch('http://localhost:5001/hedra/connect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    avatar_id: 'default-avatar-id'
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.success && data.stream_url) {
                    this.setupHedraVideoStream(data.stream_url);
                    this.isHedraConnected = true;
                    this.updateStatus('Connected to live avatar');
                } else {
                    console.log('Hedra avatar not available, using fallback');
                    this.isHedraConnected = false;
                }
            } else {
                console.log('Hedra avatar not available, using fallback');
                this.isHedraConnected = false;
            }
        } catch (error) {
            console.log('Hedra service not available, using fallback');
            this.isHedraConnected = false;
        }
    }
    
    setupHedraVideoStream(streamUrl) {
        try {
            // Check if streamUrl is valid
            if (!streamUrl || streamUrl === 'undefined' || streamUrl === 'null') {
                console.log('Invalid stream URL, falling back to image');
                this.fallbackToImage();
                return;
            }
            
            // Set up video stream from Hedra
            this.hedraVideo.srcObject = new MediaStream();
            this.hedraVideo.style.display = 'block';
            this.avatarImage.style.display = 'none';
            
            // Connect to Hedra WebSocket for real-time avatar control
            this.hedraWebSocket = new WebSocket(streamUrl);
            
            this.hedraWebSocket.onopen = () => {
                console.log('Connected to Hedra Live Avatar');
            };
            
            this.hedraWebSocket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'avatar_ready') {
                    console.log('Avatar is ready for interaction');
                }
            };
            
            this.hedraWebSocket.onerror = (error) => {
                console.error('Hedra WebSocket error:', error);
                this.fallbackToImage();
            };
            
        } catch (error) {
            console.error('Error setting up Hedra video stream:', error);
            this.fallbackToImage();
        }
    }
    
    fallbackToImage() {
        this.hedraVideo.style.display = 'none';
        this.avatarImage.style.display = 'block';
        this.avatarImage.src = 'assets/avatar-base.jpg'; // Use your robot avatar
        this.isHedraConnected = false;
    }
    
    async sendTextToHedraAvatar(text) {
        if (!this.isHedraConnected) {
            return false;
        }
        
        try {
            // Show stop button when avatar starts speaking
            this.stopButton.style.display = 'flex';
            this.updateStatus('Avatar speaking... Click stop to end stream');
            
            const response = await fetch('http://localhost:5001/hedra/speak', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text: text })
            });
            
            if (response.ok) {
                // Auto-hide stop button after estimated speaking time
                setTimeout(() => {
                    this.stopButton.style.display = 'none';
                    this.updateStatus('Ready to listen');
                }, Math.min(text.split(' ').length * 500, 30000)); // Max 30 seconds
            }
            
            return response.ok;
        } catch (error) {
            console.error('Error sending text to Hedra avatar:', error);
            return false;
        }
    }
    
    async stopHedraStream() {
        try {
            const response = await fetch('http://localhost:5001/hedra/disconnect', {
                method: 'POST'
            });
            
            if (response.ok) {
                this.stopButton.style.display = 'none';
                this.updateStatus('Stream stopped. Ready to listen');
                this.fallbackToImage();
            }
        } catch (error) {
            console.error('Error stopping Hedra stream:', error);
        }
    }
}

// Initialize the app when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new VoiceAvatarApp();
}); 