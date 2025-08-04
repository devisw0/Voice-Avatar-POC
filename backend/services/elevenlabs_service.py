import requests
import io
from config import Config

class ElevenLabsService:
    def __init__(self):
        self.api_key = Config.ELEVENLABS_API_KEY
        self.voice_id = Config.ELEVENLABS_VOICE_ID
        self.base_url = "https://api.elevenlabs.io/v1"
        
        print(f"✅ ElevenLabs service initialized")
        print(f"🔑 API Key: {'✅ Set' if self.api_key else '❌ Missing'}")
        print(f"🎵 Voice ID: {self.voice_id}")
    
    def text_to_speech_sync(self, text):
        """FIXED: Synchronous text-to-speech"""
        try:
            if not self.api_key:
                print("❌ ElevenLabs API key missing")
                return None
            
            url = f"{self.base_url}/text-to-speech/{self.voice_id}"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5
                }
            }
            
            print(f"🔊 Generating speech for: '{text[:50]}...'")
            
            response = requests.post(url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                print("✅ ElevenLabs speech generated successfully")
                return io.BytesIO(response.content)
            else:
                print(f"❌ ElevenLabs API error: {response.status_code}")
                print(f"❌ Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error with text-to-speech: {e}")
            return None
    
    def get_available_voices_sync(self):
        """Get available voices (synchronous)"""
        try:
            url = f"{self.base_url}/voices"
            headers = {"xi-api-key": self.api_key}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ ElevenLabs voices error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error fetching voices: {e}")
            return None 