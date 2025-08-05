from flask import Flask, request, jsonify
from flask_cors import CORS
import base64
import uuid
import traceback
import requests
import asyncio
from datetime import datetime

from config import Config
from services.openai_service import OpenAIService
from services.elevenlabs_service import ElevenLabsService

app = Flask(__name__)
CORS(app)
app.config.from_object(Config)

# Initialize services
print("🔧 Initializing services...")
openai_service = OpenAIService()
elevenlabs_service = ElevenLabsService()
print("✅ Services initialized")

# Store conversation history
conversations = {}
active_rooms = {}  # Track active LiveKit rooms

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "services": {
            "openai": bool(Config.OPENAI_API_KEY),
            "elevenlabs": bool(Config.ELEVENLABS_API_KEY),
            "hedra": bool(Config.HEDRA_API_KEY),
            "livekit": bool(Config.LIVEKIT_API_KEY)
        }
    })

@app.route('/process-voice', methods=['POST'])
def process_voice():
    """Process voice input and return AI response"""
    try:
        print("🎤 Starting voice processing...")
        
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file provided"}), 400
        
        audio_file = request.files['audio']
        session_id = request.form.get('session_id', 'default')
        
        # Check file size
        audio_file.seek(0, 2)
        file_size = audio_file.tell()
        audio_file.seek(0)
        
        if file_size == 0:
            return jsonify({"error": "Empty audio file"}), 400
        
        # Transcribe audio
        print("🔊 Starting transcription...")
        transcript = openai_service.transcribe_audio_sync(audio_file)
        
        if not transcript:
            return jsonify({"error": "Failed to transcribe audio"}), 500
        
        print(f"✅ Transcription: '{transcript}'")
        
        # Generate AI response
        print("🤖 Generating AI response...")
        history = conversations.get(session_id, [])
        ai_response = openai_service.generate_response_sync(transcript, history)
        print(f"✅ AI Response: '{ai_response}'")
        
        # Update conversation history
        history.append({"role": "user", "content": transcript})
        history.append({"role": "assistant", "content": ai_response})
        conversations[session_id] = history[-10:]
        
        # Generate audio fallback
        print("🔊 Generating audio fallback...")
        audio_stream = elevenlabs_service.text_to_speech_sync(ai_response)
        audio_base64 = None
        
        if audio_stream:
            audio_bytes = audio_stream.getvalue()
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        return jsonify({
            "transcript": transcript,
            "response": ai_response,
            "audio": audio_base64,
            "session_id": session_id
        })
        
    except Exception as e:
        print(f"❌ ERROR in process_voice: {e}")
        print(f"❌ TRACEBACK: {traceback.format_exc()}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/create-hedra-room', methods=['POST'])
def create_hedra_room():
    """Create LiveKit room that the Hedra agent can join"""
    try:
        data = request.get_json() or {}
        session_id = data.get('session_id', str(uuid.uuid4()))
        
        # Check if we have LiveKit credentials
        if not all([Config.LIVEKIT_API_KEY, Config.LIVEKIT_API_SECRET, Config.LIVEKIT_URL]):
            print("❌ Missing LiveKit credentials")
            return jsonify({
                "success": False,
                "error": "LiveKit credentials not configured"
            }), 400
        
        # Import LiveKit API
        try:
            from livekit.api import AccessToken, VideoGrants
        except ImportError as e:
            print(f"❌ LiveKit import error: {e}")
            return jsonify({
                "success": False,
                "error": f"LiveKit not properly installed: {str(e)}"
            }), 500
        
        # Create a room name - use consistent naming
        room_name = f"hedra-room-{session_id}"
        
        # Generate access token for the frontend user
        token = AccessToken(Config.LIVEKIT_API_KEY, Config.LIVEKIT_API_SECRET) \
            .with_identity(f"user-{session_id}") \
            .with_name("Frontend User") \
            .with_grants(VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True
            ))
        
        user_token = token.to_jwt()
        
        # Store room info
        active_rooms[session_id] = {
            "room_name": room_name,
            "user_token": user_token,
            "created_at": datetime.now().isoformat()
        }
        
        print(f"🎬 Created room credentials for: {room_name}")
        print(f"🔗 LiveKit URL: {Config.LIVEKIT_URL}")
        print(f"👤 User token generated for session: {session_id}")
        
        return jsonify({
            "success": True,
            "room_name": room_name,
            "user_token": user_token,
            "livekit_url": Config.LIVEKIT_URL,
            "session_id": session_id
        })
        
    except Exception as e:
        print(f"❌ Error creating Hedra room: {e}")
        print(f"❌ Traceback: {traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": f"Room creation failed: {str(e)}"
        }), 500

@app.route('/send-to-avatar', methods=['POST'])
def send_to_avatar():
    """Send text to avatar via LiveKit room"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        text = data.get('text', '')
        
        if not session_id or session_id not in active_rooms:
            return jsonify({"error": "No active room for session"}), 400
        
        # The agent automatically responds to voice input through LiveKit
        print(f"💬 Text for avatar: {text}")
        
        return jsonify({
            "success": True,
            "message": "Agent will respond automatically to voice input"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/test-elevenlabs', methods=['GET'])
def test_elevenlabs():
    """Test ElevenLabs connection"""
    try:
        audio_stream = elevenlabs_service.text_to_speech_sync("Hello, this is a test.")
        
        if audio_stream:
            return jsonify({
                "status": "success",
                "message": "ElevenLabs working correctly",
                "voice_id": Config.ELEVENLABS_VOICE_ID
            })
        else:
            return jsonify({
                "status": "error", 
                "message": "ElevenLabs connection failed"
            }), 500
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"ElevenLabs test failed: {str(e)}"
        }), 500

@app.route('/test-livekit', methods=['GET'])
def test_livekit():
    """Test LiveKit connection and configuration"""
    try:
        # Test LiveKit imports
        from livekit.api import AccessToken, VideoGrants
        
        # Test token generation
        test_token = AccessToken(Config.LIVEKIT_API_KEY, Config.LIVEKIT_API_SECRET) \
            .with_identity("test-user") \
            .with_name("Test User") \
            .with_grants(VideoGrants(
                room_join=True,
                room="test-room",
                can_publish=True,
                can_subscribe=True
            ))
        
        jwt_token = test_token.to_jwt()
        
        return jsonify({
            "status": "success",
            "message": "LiveKit working correctly",
            "livekit_url": Config.LIVEKIT_URL,
            "token_generated": bool(jwt_token)
        })
        
    except ImportError as e:
        return jsonify({
            "status": "error",
            "message": f"LiveKit import failed: {str(e)}"
        }), 500
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"LiveKit test failed: {str(e)}"
        }), 500

if __name__ == '__main__':
    print("🚀 Starting Voice Avatar POC server...")
    print(f"🔑 OpenAI Key: {'✅ Set' if Config.OPENAI_API_KEY else '❌ Missing'}")
    print(f"🔑 ElevenLabs Key: {'✅ Set' if Config.ELEVENLABS_API_KEY else '❌ Missing'}")
    print(f"🔑 Hedra Key: {'✅ Set' if Config.HEDRA_API_KEY else '❌ Missing'}")
    print(f"🔑 LiveKit URL: {'✅ Set' if Config.LIVEKIT_URL else '❌ Missing'}")
    print(f"🔑 LiveKit API Key: {'✅ Set' if Config.LIVEKIT_API_KEY else '❌ Missing'}")
    
    # Test LiveKit configuration on startup
    try:
        from livekit.api import AccessToken, VideoGrants
        print("✅ LiveKit API imports successful")
    except ImportError as e:
        print(f"❌ LiveKit API import failed: {e}")
        print("💡 Try: pip install livekit-api")
    
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5001) 