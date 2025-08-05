class VoiceAvatarApp {
    constructor() {
        this.isRecording = false;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.sessionId = this.generateSessionId();
        this.liveKitRoom = null;
        this.avatarConnected = false;
        this.liveKitReady = false;
        
        this.initializeElements();
        this.setupEventListeners();
        this.checkMicrophonePermission();
        
        // Check if LiveKit is already loaded
        if (window.LiveKitReady && typeof LiveKit !== 'undefined') {
            this.onLiveKitReady();
        } else {
            this.updateStatus('🔄 Loading LiveKit...');
        }
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
    
    onLiveKitReady() {
        console.log('🎬 LiveKit is ready, setting up connection...');
        this.liveKitReady = true;
        this.setupLiveKitConnection();
    }
    
    onLiveKitFailed() {
        console.log('❌ LiveKit failed to load, using audio fallback');
        this.updateStatus('⚠️ Using audio fallback mode');
    }
    
    async setupLiveKitConnection() {
        console.log('🔧 DEBUG: setupLiveKitConnection started');
        console.log('🔧 DEBUG: window.LiveKitReady:', window.LiveKitReady);
        console.log('🔧 DEBUG: typeof LiveKit:', typeof LiveKit);
        console.log('🔧 DEBUG: typeof window.LiveKit:', typeof window.LiveKit);
        console.log('🔧 DEBUG: LiveKit object:', window.LiveKit);
        
        // Check what LiveKit-related objects exist
        const liveKitProps = Object.keys(window).filter(key => key.toLowerCase().includes('livekit'));
        console.log('🔧 DEBUG: LiveKit-related window properties:', liveKitProps);
        
        // Check for specific LiveKit objects that might exist
        console.log('🔧 DEBUG: window.Room:', typeof window.Room);
        console.log('🔧 DEBUG: window.RoomEvent:', typeof window.RoomEvent);
        console.log('🔧 DEBUG: window.Track:', typeof window.Track);
        
        // Let's try a different approach - see if we can find the LiveKit objects
        let LiveKitLib = null;
        if (typeof LiveKit !== 'undefined') {
            LiveKitLib = LiveKit;
        } else if (typeof window.LiveKit !== 'undefined') {
            LiveKitLib = window.LiveKit;
        } else if (typeof window.LivekitClient !== 'undefined') {
            // Found it! It's LivekitClient with lowercase 'k'
            LiveKitLib = window.LivekitClient;
        } else if (typeof window.Room !== 'undefined') {
            // Maybe LiveKit exposes individual components directly
            LiveKitLib = {
                Room: window.Room,
                RoomEvent: window.RoomEvent,
                Track: window.Track
            };
        }
        
        console.log('🔧 DEBUG: LiveKitLib found:', !!LiveKitLib);
        console.log('🔧 DEBUG: LiveKitLib object:', LiveKitLib);
        
        if (!this.liveKitReady || !LiveKitLib) {
            console.log('❌ DEBUG: LiveKit not ready or undefined');
            this.updateStatus('⚠️ LiveKit not available');
            return;
        }
        
        try {
            this.updateStatus('🔄 Connecting to Live Avatar...');
            console.log('🔧 DEBUG: About to fetch room credentials');
            
            // Get room credentials from Flask backend
            const response = await fetch('http://localhost:5001/create-hedra-room', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: this.sessionId })
            });
            
            console.log('🔧 DEBUG: Fetch response status:', response.status);
            console.log('🔧 DEBUG: Fetch response ok:', response.ok);
            
            if (!response.ok) {
                const errorData = await response.json();
                console.log('❌ DEBUG: Response not ok, error data:', errorData);
                throw new Error(`Failed to create room: ${response.status} - ${errorData.error || 'Unknown error'}`);
            }
            
            const roomData = await response.json();
            console.log('🔧 DEBUG: Room data received:', roomData);
            
            if (roomData.success) {
                console.log('🎬 Room data received:', roomData);
                await this.connectToLiveKitRoom(roomData);
            } else {
                console.log('❌ DEBUG: Room data success=false:', roomData);
                throw new Error(`Room creation failed: ${roomData.error || 'Unknown error'}`);
            }
            
        } catch (error) {
            console.error('❌ DEBUG: LiveKit setup failed with error:', error);
            console.error('❌ DEBUG: Error stack:', error.stack);
            this.updateStatus('⚠️ Using audio fallback mode');
        }
    }
    
    async connectToLiveKitRoom(roomData) {
        console.log('🔧 DEBUG: connectToLiveKitRoom started with data:', roomData);
        
        try {
            // Try to access LiveKit from global scope or window
            let LiveKitLib = null;
            if (typeof LiveKit !== 'undefined') {
                LiveKitLib = LiveKit;
            } else if (typeof window.LiveKit !== 'undefined') {
                LiveKitLib = window.LiveKit;
            } else if (typeof window.LivekitClient !== 'undefined') {
                // Found it! It's LivekitClient with lowercase 'k'
                LiveKitLib = window.LivekitClient;
            } else if (typeof window.Room !== 'undefined') {
                // Maybe LiveKit exposes individual components directly
                LiveKitLib = {
                    Room: window.Room,
                    RoomEvent: window.RoomEvent,
                    Track: window.Track
                };
            }
            
            console.log('🔧 DEBUG: LiveKitLib found:', !!LiveKitLib);
            
            if (!LiveKitLib) {
                throw new Error('LiveKit library not found in global scope');
            }
            
            const { Room, RoomEvent, Track } = LiveKitLib;
            console.log('🔧 DEBUG: LiveKit destructured successfully');
            console.log('🔧 DEBUG: Room:', !!Room, 'RoomEvent:', !!RoomEvent, 'Track:', !!Track);
            
            this.liveKitRoom = new Room({
                adaptiveStream: true,
                dynacast: true,
            });
            console.log('🔧 DEBUG: LiveKit Room created');
            
            // Set up event listeners BEFORE connecting
            this.liveKitRoom.on(RoomEvent.Connected, () => {
                console.log('✅ Connected to LiveKit room:', roomData.room_name);
                this.updateStatus('🎬 Connected - waiting for avatar...');
            });
            
            this.liveKitRoom.on(RoomEvent.Disconnected, (reason) => {
                console.log('❌ Disconnected from room:', reason);
                this.fallbackToImage();
                this.updateStatus('🛑 Disconnected from avatar');
            });
            
            this.liveKitRoom.on(RoomEvent.ParticipantConnected, (participant) => {
                console.log('👤 Participant connected:', participant.identity);
                
                // Check if this is the agent
                if (participant.identity.includes('agent') || participant.identity.includes('hedra')) {
                    console.log('🎬 Hedra agent detected!');
                    this.updateStatus('🎬 Avatar agent connected!');
                }
            });
            
            this.liveKitRoom.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {
                console.log('📹 Track subscribed:', {
                    participant: participant.identity,
                    trackSid: track.sid,
                    kind: track.kind,
                    source: track.source,
                    enabled: track.enabled,
                    muted: track.muted
                });
                
                // Check if this is a video track from the agent
                if (track.kind === Track.Kind.Video && 
                    (participant.identity.includes('agent') || participant.identity.includes('hedra'))) {
                    
                    console.log('🎥 Avatar video track received!');
                    console.log('📋 Track details:', {
                        dimensions: track.dimensions,
                        source: track.source,
                        sid: track.sid
                    });
                    
                    try {
                        // Attach the track to a video element
                        const videoElement = track.attach();
                        
                        // Configure video element
                        videoElement.id = 'hedra-video-live';
                        videoElement.style.cssText = `
                            display: block !important;
                            width: 100%;
                            height: 100%;
                            object-fit: cover;
                            border-radius: 50%;
                            position: absolute;
                            top: 0;
                            left: 0;
                        `;
                        videoElement.autoplay = true;
                        videoElement.playsInline = true;
                        videoElement.muted = false;
                        
                        // Add event listeners for debugging
                        videoElement.onloadedmetadata = () => {
                            console.log('✅ Video metadata loaded');
                            console.log('📐 Video dimensions:', videoElement.videoWidth, 'x', videoElement.videoHeight);
                        };
                        
                        videoElement.onplay = () => {
                            console.log('▶️ Video started playing');
                        };
                        
                        videoElement.onerror = (e) => {
                            console.error('❌ Video error:', e);
                        };
                        
                        // Replace the static image
                        this.avatarImage.style.display = 'none';
                        
                        // Remove existing video if any
                        const existingVideo = this.avatar.querySelector('#hedra-video-live');
                        if (existingVideo) {
                            existingVideo.remove();
                        }
                        
                        // Add new video
                        this.avatar.appendChild(videoElement);
                        this.hedraVideo = videoElement;
                        
                        this.avatarConnected = true;
                        this.stopButton.style.display = 'block';
                        this.updateStatus('🎬 Live Avatar active!');
                        
                        console.log('✅ Avatar video connected successfully!');
                        
                    } catch (error) {
                        console.error('❌ Error attaching video track:', error);
                    }
                }
            });
            
            this.liveKitRoom.on(RoomEvent.TrackUnsubscribed, (track, publication, participant) => {
                if (participant.identity.includes('agent') || participant.identity.includes('hedra')) {
                    console.log('🎬 Hedra avatar track disconnected');
                    this.fallbackToImage();
                }
            });
            
            // Connect to the room
            console.log('🔗 DEBUG: About to connect to LiveKit room...', {
                url: roomData.livekit_url,
                room: roomData.room_name
            });
            
            await this.liveKitRoom.connect(roomData.livekit_url, roomData.user_token);
            
            console.log('✅ DEBUG: LiveKit room connection established');
            
        } catch (error) {
            console.error('❌ DEBUG: Error in connectToLiveKitRoom:', error);
            console.error('❌ DEBUG: Error stack:', error.stack);
            this.updateStatus('⚠️ Connection failed - using audio fallback');
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
            
            // If avatar is connected, the agent will automatically speak
            // Otherwise, use audio fallback
            if (this.avatarConnected) {
                this.updateStatus('🎬 Avatar speaking...');
                this.setSpeaking(true);
                
                // Estimate speaking duration and reset indicator
                const estimatedDuration = Math.max(data.response.split(' ').length * 0.6, 2); // minimum 2 seconds
                setTimeout(() => {
                    this.setSpeaking(false);
                    this.updateStatus('✅ Ready to listen');
                }, estimatedDuration * 1000);
            } else if (data.audio) {
                await this.playAudioResponse(data.audio);
            } else {
                this.updateStatus('✅ Ready to listen');
            }
            
        } catch (error) {
            console.error('❌ Error processing recording:', error);
            this.addMessage('Sorry, I had trouble processing that. Please try again.', 'bot');
            this.updateStatus('❌ Error - Try again');
        }
    }
    
    async playAudioResponse(audioBase64) {
        try {
            this.setSpeaking(true);
            this.updateStatus('🔊 Playing audio response...');
            
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
                this.updateStatus('✅ Ready to listen');
            };
            
            audio.onerror = () => {
                this.setSpeaking(false);
                URL.revokeObjectURL(audioUrl);
                this.updateStatus('❌ Audio playback failed');
            };
            
            await audio.play();
            
        } catch (error) {
            console.error('❌ Error playing audio:', error);
            this.setSpeaking(false);
            this.updateStatus('❌ Audio playback error');
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
        // Show static image
        this.avatarImage.style.display = 'block';
        
        // Hide video and stop button
        if (this.hedraVideo) {
            this.hedraVideo.style.display = 'none';
        }
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
        console.log('Status:', text);
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