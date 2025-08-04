from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import base64
import io
import uuid
from datetime import datetime
import traceback

from config import Config
from services.openai_service import OpenAIService
from services.elevenlabs_service import ElevenLabsService
from services.livekit_service import LiveKitService
from services.hedra_service import HedraLiveAvatarService

app = Flask(__name__)
CORS(app)
app.config.from_object(Config)

# Initialize services
print("🔧 Initializing services...")
openai_service = OpenAIService()
elevenlabs_service = ElevenLabsService()
livekit_service = LiveKitService()
hedra_service = HedraLiveAvatarService()
print("✅ All services initialized")

# Store conversation history
conversations = {}

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "services": {
            "openai": bool(Config.OPENAI_API_KEY),
            "elevenlabs": bool(Config.ELEVENLABS_API_KEY),
            "hedra": bool(Config.HEDRA_API_KEY)
        }
    })

@app.route('/process-voice', methods=['POST'])
def process_voice():
    """FIXED: Removed async to fix Flask 500 error"""
    try:
        print("🎤 Starting voice processing...")
        
        # Get audio file from request
        if 'audio' not in request.files:
            print("❌ No audio file in request")
            return jsonify({"error": "No audio file provided"}), 400
        
        audio_file = request.files['audio']
        session_id = request.form.get('session_id', 'default')
        
        print(f"📁 Audio file: {audio_file.filename}")
        
        # Check file size
        audio_file.seek(0, 2)  # Seek to end
        file_size = audio_file.tell()
        audio_file.seek(0)  # Reset to beginning
        print(f"📏 File size: {file_size} bytes")
        
        if file_size == 0:
            print("❌ Empty audio file")
            return jsonify({"error": "Empty audio file"}), 400
        
        # CRITICAL FIX: Use synchronous calls instead of async
        print("🔊 Starting transcription...")
        transcript = openai_service.transcribe_audio_sync(audio_file)
        
        if not transcript:
            print("❌ Transcription failed")
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
        
        # Generate speech
        print("🔊 Generating speech...")
        audio_stream = elevenlabs_service.text_to_speech_sync(ai_response)
        
        if not audio_stream:
            print("❌ Speech generation failed")
            return jsonify({"error": "Failed to generate speech"}), 500
        
        # Convert to base64
        audio_bytes = audio_stream.getvalue()
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        print("✅ Voice processing complete")
        
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

@app.route('/test-elevenlabs', methods=['GET'])
def test_elevenlabs():
    """Test ElevenLabs connection"""
    try:
        # Test with simple text
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

@app.route('/hedra/connect', methods=['POST'])
def connect_hedra_avatar():
    """Connect to Hedra (with proper error handling)"""
    try:
        data = request.get_json() or {}
        avatar_id = data.get('avatar_id', Config.HEDRA_AVATAR_ID)
        
        print(f"🎬 Attempting Hedra connection for avatar: {avatar_id}")
        
        # For now, return success=False to use ElevenLabs fallback
        # Until we get correct Hedra endpoints
        print("⚠️ Hedra integration disabled - using ElevenLabs fallback")
        
        return jsonify({
            "success": False,
            "message": "Hedra temporarily disabled, using audio fallback",
            "avatar_id": avatar_id
        })
        
    except Exception as e:
        print(f"❌ Error in hedra connect: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/hedra/status', methods=['GET'])
def get_hedra_status():
    """Get Hedra status"""
    return jsonify({
        "connected": False,
        "speaking": False,
        "message": "Hedra temporarily disabled"
    })

if __name__ == '__main__':
    print("🚀 Starting Voice Avatar POC server...")
    print(f"🔑 OpenAI Key: {'✅ Set' if Config.OPENAI_API_KEY else '❌ Missing'}")
    print(f"🔑 ElevenLabs Key: {'✅ Set' if Config.ELEVENLABS_API_KEY else '❌ Missing'}")
    print(f"🔑 ElevenLabs Voice: {Config.ELEVENLABS_VOICE_ID}")
    
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5001) 