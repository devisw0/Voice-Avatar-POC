# Voice Avatar POC

A complete voice avatar proof-of-concept that integrates OpenAI, ElevenLabs, and LiveKit for real-time voice interaction with an AI assistant.

## Project Structure

```
voice-avatar-poc/
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   ├── config.py
│   └── services/
│       ├── __init__.py
│       ├── openai_service.py
│       ├── elevenlabs_service.py
│       └── livekit_service.py
├── frontend/
│   ├── index.html
│   ├── script.js
│   ├── style.css
│   └── assets/
│       └── avatar-placeholder.png
├── .env
└── README.md
```

## Features

- **Voice Input**: Hold-to-talk recording with Web Audio API
- **AI Processing**: Speech → Text → AI Response → Speech pipeline
- **Visual Feedback**: Avatar animations during speaking
- **Session Management**: Conversation history tracking
- **Error Handling**: Robust error handling throughout the pipeline

## Backend Components

### Flask API Server
- Handles HTTP requests and coordinates between services
- Manages conversation history
- Provides LiveKit room management

### OpenAI Service
- Audio transcription using Whisper
- Conversational AI responses using GPT-3.5-turbo
- Context-aware conversations

### ElevenLabs Service
- Text-to-speech conversion with natural voices
- Voice selection and configuration
- Audio format handling

### LiveKit Service
- Real-time room creation
- Access token generation
- Participant management (ready for future video features)

## Frontend Components

### Voice Interface
- Push-to-talk microphone button
- Real-time recording status
- Conversation history display
- Visual speaking indicators

### Avatar System
- Animated avatar placeholder
- Speaking state indicators
- Responsive design for mobile/desktop

## API Endpoints

- `POST /process-voice` - Main voice processing pipeline
- `POST /create-room` - LiveKit room creation
- `POST /text-to-speech` - Direct TTS conversion
- `GET /voices` - Available voice options
- `GET /health` - System health check

## Setup Instructions

### 1. Get API Keys

**OpenAI:**
- Go to [OpenAI Platform](https://platform.openai.com/)
- Navigate to API keys section
- Create a new API key

**ElevenLabs:**
- Go to [ElevenLabs](https://elevenlabs.io/)
- Sign up and go to Profile → API keys
- Copy your API key

**LiveKit (Optional for future features):**
- Go to [LiveKit Cloud](https://cloud.livekit.io/)
- Create an account and get your API keys

### 2. Configure Environment Variables

Create a `.env` file in the root directory:

```bash
# OpenAI API
OPENAI_API_KEY=your_openai_api_key_here

# ElevenLabs API
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
ELEVENLABS_VOICE_ID=your_preferred_voice_id_here

# LiveKit Configuration
LIVEKIT_API_KEY=your_livekit_api_key_here
LIVEKIT_API_SECRET=your_livekit_api_secret_here
LIVEKIT_URL=wss://your-livekit-server.com

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
```

### 3. Install Dependencies

```bash
# Backend setup
cd backend
pip install -r requirements.txt
```

### 4. Run the Application

**Start the Backend:**
```bash
cd backend
python app.py
```

**Start the Frontend (in a new terminal):**
```bash
cd frontend
python -m http.server 8000
```

### 5. Access the Application

Open [http://localhost:8000](http://localhost:8000) in your browser.

## How It Works

1. **User speaks** while holding the microphone button
2. **Frontend records** audio using Web Audio API
3. **Audio is sent** to backend via HTTP POST
4. **OpenAI Whisper** transcribes the audio to text
5. **GPT-3.5-turbo** generates an AI response
6. **ElevenLabs** converts the response to speech
7. **Audio is returned** to frontend and played
8. **Avatar shows** visual feedback during speaking

## Expansion Possibilities

- **Video Avatar**: Integrate with LiveKit for real-time video
- **Voice Cloning**: Use ElevenLabs voice cloning features
- **Multi-user**: Support multiple participants via LiveKit
- **Avatar Animation**: Add lip-sync and gesture animations
- **Mobile App**: Convert to React Native or Flutter

## Troubleshooting

### Common Issues

1. **Microphone Permission Denied**
   - Make sure to allow microphone access in your browser
   - Check browser settings for microphone permissions

2. **API Key Errors**
   - Verify all API keys are correctly set in `.env`
   - Check that API keys have sufficient credits/permissions

3. **CORS Errors**
   - Ensure the backend is running on the correct port
   - Check that CORS is properly configured

4. **Audio Playback Issues**
   - Check browser audio settings
   - Ensure audio is not muted

## Development

The system is modular and ready for production scaling. Each service can be independently improved or replaced as needed.

### Adding New Features

1. **New AI Models**: Modify `openai_service.py`
2. **Different TTS**: Update `elevenlabs_service.py`
3. **Video Features**: Extend `livekit_service.py`
4. **UI Changes**: Modify frontend files in `frontend/`

## License

This project is for educational and demonstration purposes. 