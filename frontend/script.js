class VoiceAvatarApp {
    constructor() {
        this.isRecording = false;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.sessionId = this.generateSessionId();
        this.liveKitRoom = null;
        this.avatarConnected = false;
        
        this.initializeElements();
        this.setupEventListeners();
        this.checkMicrophonePermission();
        this.setupLiveKitConnection();
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
        this.micButton.addEventListener('mousedown', () => this.startRecording());
        this.micButton.addEventListener('mouseup', () => this.stopRecording());
        this.micButton.addEventListener('mouseleave', () => this.stopRecording());
        
        this.micButton.addEventListener('touchstart', (e) => {
            e.preventDefault();
            this.startRecording();
        });
        this.micButton.addEventListener('touchend', (e) => {
            e.preventDefault();
            this.stopRecording();
        });
        
        this.micButton.addEventListener('contextmenu', (e) => e.preventDefault());
        this.stopButton.addEventListener('click', () => this.disconnectAvatar());
    }
    
    async setupLiveKitConnection() {
        try {
            this.updateStatus('🔄 Setting up Live Avatar...');
            
            // Create LiveKit room with Hedra avatar
            const response = await fetch('http://localhost:5001/create-hedra-room', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: this.sessionId })
            });
            
            if (!response.ok) {
                throw new Error('Failed to create room');
            }
            
            const roomData = await response.json();
            
            if (roomData.success) {
                // Connect to LiveKit room
                await this.connectToLiveKitRoom(roomData);
                this.updateStatus('✅ Live Avatar ready');
            } else {
                this.updateStatus('⚠️ Using audio fallback');
            }
            
        } catch (error) {
            console.error('❌ LiveKit setup failed:', error);
            this.updateStatus('⚠️ Using audio fallback mode');
        }
    }
    
    async connectToLiveKitRoom(roomData) {
        try {
            // Check if LiveKit is available
            if (typeof LiveKit === 'undefined') {
                console.warn('⚠️ LiveKit not available, using audio fallback');
                this.updateStatus('⚠️ Using audio fallback');
                return;
            }
            
            // Import LiveKit client
            const { Room, RoomEvent, VideoTrack } = LiveKit;
            
            this.liveKitRoom = new Room();
            
            // Handle avatar video track
            this.liveKitRoom.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {
                console.log('📹 Track subscribed:', participant.identity);
                
                // Check if this is the Hedra avatar participant
                if (participant.identity.includes('hedra-avatar') && track instanceof VideoTrack) {
                    console.log('🎬 Hedra avatar video track received');
                    
                    // Attach avatar video to the video element
                    track.attach(this.hedraVideo);
                    this.hedraVideo.style.display = 'block';
                    this.avatarImage.style.display = 'none';
                    this.avatarConnected = true;
                    
                    // Show stop button
                    this.stopButton.style.display = 'block';
                }
            });
            
            this.liveKitRoom.on(RoomEvent.TrackUnsubscribed, (track, publication, participant) => {
                if (participant.identity.includes('hedra-avatar')) {
                    console.log('🎬 Hedra avatar disconnected');
                    this.fallbackToImage();
                }
            });
            
            // Connect to the room
            await this.liveKitRoom.connect(roomData.livekit_url, roomData.user_token);
            
            console.log('✅ Connected to LiveKit room');
            
        } catch (error) {
            console.error('❌ Error connecting to LiveKit room:', error);
            this.updateStatus('⚠️ Using audio fallback');
        }
    }
    
    async checkMicrophonePermission() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            stream.getTracks().forEach(track => track.stop());
            this.updateStatus('Ready to listen');
        } catch (error) {
            this.updateStatus('❌ Microphone access required');
        }
    }
    
    async startRecording() {
        if (this.isRecording) return;
        
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    sampleRate: 44100,
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true
                }
            });
            
            let mimeType = 'audio/wav';
            if (MediaRecorder.isTypeSupported('audio/wav')) {
                mimeType = 'audio/wav';
            } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
                mimeType = 'audio/mp4';
            } else {
                mimeType = 'audio/webm';
            }
            
            this.mediaRecorder = new MediaRecorder(stream, { mimeType });
            this.audioChunks = [];
            this.isRecording = true;
            
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };
            
            this.mediaRecorder.onstop = () => {
                this.processRecording();
                stream.getTracks().forEach(track => track.stop());
            };
            
            this.mediaRecorder.start();
            this.updateUI(true);
            this.updateStatus('🎤 Listening... Release to send');
            
        } catch (error) {
            console.error('❌ Error starting recording:', error);
            this.updateStatus('❌ Cannot access microphone');
        }
    }
    
    stopRecording() {
        if (!this.isRecording || !this.mediaRecorder) return;
        
        this.isRecording = false;
        this.mediaRecorder.stop();
        this.updateUI(false);
        this.updateStatus('🔄 Processing...');
    }
    
    async processRecording() {
        try {
            if (this.audioChunks.length === 0) {
                this.updateStatus('❌ No audio recorded');
                return;
            }
            
            const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
            
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.wav');
            formData.append('session_id', this.sessionId);
            
            const response = await fetch('http://localhost:5001/process-voice', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }
            
            const data = await response.json();
            
            console.log('📥 Response received:', data);
            
            // Add messages to conversation
            this.addMessage(data.transcript, 'user');
            this.addMessage(data.response, 'bot');
            
            // If avatar is connected, it will automatically speak
            // Otherwise, use audio fallback
            if (!this.avatarConnected && data.audio) {
                await this.playAudioResponse(data.audio);
            } else if (this.avatarConnected) {
                this.updateStatus('🎬 Avatar speaking...');
                // Avatar will speak automatically via LiveKit
            }
            
            this.updateStatus('✅ Ready to listen');
            
        } catch (error) {
            console.error('❌ Error processing recording:', error);
            this.addMessage('Sorry, I had trouble processing that. Please try again.', 'bot');
            this.updateStatus('❌ Error - Try again');
        }
    }
    
    async playAudioResponse(audioBase64) {
        try {
            this.setSpeaking(true);
            
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
            
            await audio.play();
            
        } catch (error) {
            console.error('❌ Error playing audio:', error);
            this.setSpeaking(false);
        }
    }
    
    async disconnectAvatar() {
        try {
            if (this.liveKitRoom) {
                await this.liveKitRoom.disconnect();
            }
            
            this.fallbackToImage();
            this.updateStatus('🛑 Avatar disconnected');
            
        } catch (error) {
            console.error('❌ Error disconnecting avatar:', error);
        }
    }
    
    fallbackToImage() {
        this.hedraVideo.style.display = 'none';
        this.avatarImage.style.display = 'block';
        this.avatarImage.src = 'assets/avatar-base.jpg';
        this.stopButton.style.display = 'none';
        this.avatarConnected = false;
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
}

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    window.voiceApp = new VoiceAvatarApp();
});

// Cleanup on page close
window.addEventListener('beforeunload', async () => {
    if (window.voiceApp && window.voiceApp.liveKitRoom) {
        await window.voiceApp.liveKitRoom.disconnect();
    }
}); 