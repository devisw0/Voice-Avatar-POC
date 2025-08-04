import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # ElevenLabs Configuration
    ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
    ELEVENLABS_VOICE_ID = os.getenv('ELEVENLABS_VOICE_ID', 'EXAVITQu4vr4xnSDxMaL')  # Default voice
    
    # Hedra Live Avatar Configuration
    HEDRA_API_KEY = os.getenv('HEDRA_API_KEY')
    HEDRA_AVATAR_ID = os.getenv('HEDRA_AVATAR_ID', 'default-avatar-id')
    
    # LiveKit Configuration
    LIVEKIT_API_KEY = os.getenv('LIVEKIT_API_KEY')
    LIVEKIT_API_SECRET = os.getenv('LIVEKIT_API_SECRET')
    LIVEKIT_URL = os.getenv('LIVEKIT_URL')
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true' 