import openai
import io
from config import Config

class OpenAIService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        print("✅ OpenAI service initialized")
    
    def transcribe_audio_sync(self, audio_file):
        """FIXED: Synchronous transcription to fix Flask 500 error"""
        try:
            print("🔊 Reading audio file...")
            audio_bytes = audio_file.read()
            audio_file.seek(0)
            
            print(f"📏 Audio size: {len(audio_bytes)} bytes")
            
            if len(audio_bytes) == 0:
                print("❌ Audio file is empty")
                return None
            
            # Create proper file object for OpenAI
            audio_io = io.BytesIO(audio_bytes)
            audio_io.name = 'audio.wav'  # Force WAV extension
            
            print("🤖 Sending to OpenAI Whisper...")
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_io,
                response_format="text"
            )
            
            print(f"✅ Transcription successful: {transcript}")
            return transcript
            
        except Exception as e:
            print(f"❌ Transcription error: {e}")
            
            # FALLBACK: Try with different extension
            try:
                print("🔄 Trying fallback transcription...")
                audio_io = io.BytesIO(audio_bytes)
                audio_io.name = 'audio.mp3'
                
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_io,
                    response_format="text"
                )
                
                return transcript
                
            except Exception as e2:
                print(f"❌ Fallback transcription failed: {e2}")
                return None
    
    def generate_response_sync(self, user_message, conversation_history=None):
        """FIXED: Synchronous response generation"""
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful AI assistant with a friendly personality. Keep responses concise but engaging, suitable for voice interaction."
                }
            ]
            
            if conversation_history:
                messages.extend(conversation_history)
            
            messages.append({
                "role": "user",
                "content": user_message
            })
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=150,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"❌ Error generating response: {e}")
            return "I'm sorry, I'm having trouble processing that right now." 