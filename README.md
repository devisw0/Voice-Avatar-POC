# Voice Avatar POC

A complete voice avatar proof-of-concept that integrates OpenAI, ElevenLabs, and Hedra Live Avatars through LiveKit Agents for real-time voice interaction with an AI assistant.

## Project Structure

```
Voice-Avatar-POC/
├── backend/
│   ├── app.py                    # Main Flask application
│   ├── hedra_agent.py           # LiveKit Agent with Hedra avatar
│   ├── simple_hedra_agent.py    # Simplified Hedra agent
│   ├── requirements.txt          # Python dependencies
│   ├── config.py                # Configuration management
│   └── services/
│       ├── __init__.py
│       ├── openai_service.py    # OpenAI Whisper + GPT
│       └── elevenlabs_service.py # ElevenLabs TTS
├── frontend/
│   ├── index.html               # Main UI with LiveKit client
│   ├── script.js                # Frontend logic with LiveKit
│   ├── style.css                # Styling
│   └── assets/
│       └── avatar-base.jpg      # Robot avatar image
├── .env                         # Environment variables
└── README.md
```

## Features

- **Voice Input**: Hold-to-talk recording with Web Audio API
- **AI Processing**: Speech → Text → AI Response → Speech pipeline
- **Live Avatar**: Real-time video avatar using Hedra Live Avatars
- **LiveKit Integration**: Proper real-time communication framework
- **Visual Feedback**: Avatar animations during speaking
- **Session Management**: Conversation history tracking
- **Error Handling**: Robust error handling with audio fallback

## Architecture

### Correct Hedra Integration (LiveKit Agents)
```
User Voice → Flask Backend → LiveKit Agent → Hedra Avatar → LiveKit Room → Frontend
```

### Why This Works
- **Hedra Live Avatars** work through **LiveKit Agents**, not direct API calls
- **LiveKit** provides the real-time communication infrastructure
- **Hedra** is a plugin within the LiveKit ecosystem
- This ensures proper cost control and reliability

## Backend Components

### Flask API Server
- Handles HTTP requests and coordinates between services
- Manages conversation history
- Creates LiveKit rooms for avatar sessions
- Provides audio fallback when avatar unavailable

### OpenAI Service
- Audio transcription using Whisper
- Conversational AI responses using GPT-3.5-turbo
- Context-aware conversations

### ElevenLabs Service
- Text-to-speech conversion with natural voices
- Audio fallback when Hedra avatar unavailable
- Voice selection and configuration

### LiveKit Agent (Hedra Integration)
- **hedra_agent.py**: Full LiveKit Agent with Hedra avatar
- **simple_hedra_agent.py**: Simplified version for testing
- Handles real-time avatar video streaming
- Manages avatar speaking and lip sync

## Frontend Components

### Voice Interface
- Push-to-talk microphone button
- Real-time recording status
- Conversation history display
- Visual speaking indicators

### Live Avatar System
- **LiveKit Client**: Real-time video streaming
- **Hedra Avatar**: Live video avatar with lip sync
- **Fallback System**: Static image when avatar unavailable
- **Stop Button**: Manual avatar disconnection

## API Endpoints

- `POST /process-voice` - Main voice processing pipeline
- `POST /create-hedra-room` - Create LiveKit room with avatar
- `POST /send-to-avatar` - Send text to avatar
- `GET /test-elevenlabs` - Test ElevenLabs connection
- `GET /health` - System health check

## Setup Instructions

### 1. Get Required API Keys

**OpenAI:**
- Go to [OpenAI Platform](https://platform.openai.com/)
- Navigate to API keys section
- Create a new API key

**ElevenLabs:**
- Go to [ElevenLabs](https://elevenlabs.io/)
- Sign up and go to Profile → API keys
- Copy your API key

**Hedra:**
- Go to [Hedra](https://hedra.com/)
- Sign up and get your API key
- **📋 To get your avatar ID:**
  1. Go to https://www.hedra.com/studio
  2. Create an avatar image using the image generator
  3. Go to your Library and hover over the image
  4. Click the three dots icon and select "Copy Asset ID"
  5. Add the asset ID to your `.env` file as `HEDRA_AVATAR_ID`
  6. **Alternative:** Upload via API: `curl -X POST https://api.hedra.com/v1/assets`

**LiveKit (REQUIRED for Hedra):**
- Go to [LiveKit Cloud](https://cloud.livekit.io/)
- Create account and project
- Get API keys from Settings → API Keys

### 2. Configure Environment Variables

Create a `.env` file in the root directory:

```bash
# OpenAI API
OPENAI_API_KEY=sk-your-actual-openai-api-key-here

# ElevenLabs API
ELEVENLABS_API_KEY=your-actual-elevenlabs-api-key-here
ELEVENLABS_VOICE_ID=EXAVITQu4vr4xnSDxMaL

# Hedra Live Avatar API
HEDRA_API_KEY=your-actual-hedra-api-key-here
HEDRA_AVATAR_ID=your-preferred-avatar-id-here

# LiveKit Configuration (REQUIRED for Hedra)
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your-livekit-api-key
LIVEKIT_API_SECRET=your-livekit-api-secret

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
```

### 3. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
cd backend
pip install -r requirements.txt
```

### 4. Run the Application

**Option A: Full Implementation (Recommended)**
```bash
# Terminal 1: Start LiveKit Agent with Hedra
cd backend
python hedra_agent.py

# Terminal 2: Start Flask Backend
cd backend
python app.py

# Terminal 3: Start Frontend
cd frontend
python -m http.server 8000
```

**Option B: Quick Test (Audio Only)**
```bash
# Terminal 1: Start Flask Backend
cd backend
python app.py

# Terminal 2: Start Frontend
cd frontend
python -m http.server 8000
```

### 5. Access the Application

Open your browser and go to: `http://localhost:8000`

## Expected Flow

1. **Page Load**: LiveKit room creation and avatar connection
2. **Voice Input**: Hold microphone button and speak
3. **Processing**: Voice → OpenAI → AI Response
4. **Avatar Response**: 
   - **With Hedra**: Live video avatar speaks with lip sync
   - **Without Hedra**: Audio playback with static image
5. **Conversation**: Full conversation history maintained

## Troubleshooting

### Common Issues

**"LiveKit setup failed"**
- Check LiveKit credentials in `.env`
- Ensure LiveKit project is active
- Verify network connectivity

**"Hedra avatar not available"**
- Check Hedra API key in `.env`
- Verify avatar ID is correct
- Upload robot image to Hedra Studio first

**"Audio fallback mode"**
- This is normal when Hedra is not configured
- Audio will still work perfectly
- Check console for specific error messages

### Debug Steps

1. **Test Basic Audio Flow**:
   ```bash
   curl http://localhost:5001/test-elevenlabs
   ```

2. **Check Health Status**:
   ```bash
   curl http://localhost:5001/health
   ```

3. **Verify Environment**:
   - All API keys are set in `.env`
   - No spaces around `=` in `.env`
   - Virtual environment is activated

## Cost Control

The system includes built-in cost controls:
- **Automatic Disconnection**: Sessions auto-end after 1 hour
- **Manual Stop**: Stop button to disconnect avatar
- **Audio Fallback**: Uses ElevenLabs when Hedra unavailable
- **Session Limits**: Maximum session duration enforced

## Next Steps

1. **Test Basic Audio**: Ensure voice → AI → audio works
2. **Setup LiveKit**: Create account and get credentials
3. **Upload Avatar**: Upload robot image to Hedra Studio
4. **Enable Live Avatar**: Run with LiveKit Agent
5. **Customize**: Modify avatar appearance and behavior

## Architecture Benefits

- **Proper Integration**: Uses Hedra's intended LiveKit framework
- **Cost Control**: Built-in session management and limits
- **Reliability**: Fallback systems for all components
- **Scalability**: LiveKit handles real-time communication
- **Future-Proof**: Built on industry-standard frameworks 