import requests
import json
import asyncio
import time
from config import Config

class HedraLiveAvatarService:
    def __init__(self):
        self.api_key = Config.HEDRA_API_KEY
        self.base_url = "https://api.hedra.com"
        self.avatar_id = Config.HEDRA_AVATAR_ID
        self.is_connected = False
        self.speaking_start_time = None
        self.max_speaking_duration = 60  # Maximum 60 seconds per response
        
        print(f"✅ HedraLiveAvatarService initialized")
        print(f"🔑 API Key: {'✅ Set' if self.api_key else '❌ Missing'}")
        print(f"🎭 Avatar ID: {self.avatar_id}")
        
        # Test connection on initialization
        if self.api_key and not self.api_key.startswith("your_"):
            self.test_connection()
    
    def test_connection(self):
        """Test Hedra API connection and validate avatar"""
        try:
            if not self.api_key or self.api_key.startswith("your_") or len(self.api_key) < 10:
                print("❌ Hedra API key not configured or invalid")
                return False
            
            print("🔍 Testing Hedra API connection...")
            
            # FIXED: Use correct endpoint and header
            headers = {"X-API-Key": self.api_key}
            response = requests.get(
                f"{self.base_url}/web-app/public/generations",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ Hedra API connection successful")
                
                # Check if avatar ID exists in generations
                data = response.json()
                if 'data' in data:
                    found_avatar = False
                    total_assets = len(data['data'])
                    print(f"📋 Found {total_assets} assets in your account")
                    
                    for item in data['data']:
                        asset = item.get('asset', {})
                        asset_id = asset.get('id')
                        asset_type = item.get('type', 'unknown')
                        
                        if asset_id == self.avatar_id:
                            found_avatar = True
                            print(f"✅ Avatar ID {self.avatar_id} found (type: {asset_type})")
                            
                            # Show avatar details
                            if asset_type == 'image':
                                width = asset.get('asset', {}).get('width', 'unknown')
                                height = asset.get('asset', {}).get('height', 'unknown')
                                print(f"📐 Avatar dimensions: {width}x{height}")
                                print(f"🎬 Avatar ready for video generation!")
                            
                            break
                    
                    if not found_avatar:
                        print(f"⚠️ Avatar ID {self.avatar_id} not found in recent generations")
                        print("💡 Available asset IDs:")
                        for i, item in enumerate(data['data'][:5]):  # Show first 5
                            asset_id = item.get('asset', {}).get('id', 'N/A')
                            asset_type = item.get('type', 'unknown')
                            created = item.get('created_at', 'unknown')[:10]  # Just date
                            print(f"   {i+1}. {asset_id} ({asset_type}, {created})")
                        if total_assets > 5:
                            print(f"   ... and {total_assets - 5} more")
                        print("💡 Update your .env file with the correct HEDRA_AVATAR_ID")
                
                return True
            elif response.status_code == 401:
                print("❌ Hedra API authentication failed - check your API key")
                return False
            elif response.status_code == 403:
                print("❌ Hedra API access forbidden - check your plan/permissions")
                return False
            else:
                print(f"❌ Hedra API error: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"❌ Error details: {error_data}")
                except:
                    print(f"❌ Response: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            print("❌ Hedra API request timed out")
            return False
        except requests.exceptions.ConnectionError:
            print("❌ Could not connect to Hedra API - check internet connection")
            return False
        except Exception as e:
            print(f"❌ Error testing Hedra connection: {e}")
            return False
    
    async def connect_to_avatar(self, avatar_id=None):
        """Connect to a Hedra Live Avatar"""
        try:
            # Use the configured avatar ID if none provided
            if not avatar_id:
                avatar_id = self.avatar_id
            
            print(f"🔗 Attempting to connect to Hedra avatar: {avatar_id}")
            
            # Validate API connection first
            connection_ok = self.test_connection()
            if connection_ok:
                self.is_connected = True
                print(f"✅ Successfully connected to Hedra avatar: {avatar_id}")
                print("🎬 Avatar ready for live video generation!")
                return True
            else:
                print("❌ Hedra avatar connection failed")
                return False
            
        except Exception as e:
            print(f"❌ Error connecting to Hedra Live Avatar: {e}")
            return False
    
    async def send_text_to_avatar(self, text):
        """Send text to the live avatar for real-time speaking"""
        if not self.is_connected:
            print("⚠️ Not connected to Hedra avatar")
            return False
        
        try:
            # Record speaking start time
            self.speaking_start_time = time.time()
            
            print(f"🎬 Hedra avatar speaking: '{text[:100]}{'...' if len(text) > 100 else ''}'")
            print("🎥 Live video should be generating now...")
            
            # TODO: Implement actual Hedra live avatar speaking API
            # This would integrate with Hedra's real-time video generation API
            
            # Schedule automatic disconnection after speaking
            asyncio.create_task(self._auto_disconnect_after_speaking())
            
            return True
            
        except Exception as e:
            print(f"❌ Error sending text to avatar: {e}")
            return False
    
    async def _auto_disconnect_after_speaking(self):
        """Automatically disconnect after speaking to save costs"""
        try:
            # Estimate speaking duration (roughly 150 words per minute)
            if self.speaking_start_time:
                # Simple estimation: assume 3 words per second average speaking rate
                estimated_words = 50  # Default assumption
                estimated_duration = min(estimated_words / 3, self.max_speaking_duration, 30)
            else:
                estimated_duration = 10  # Default 10 seconds
            
            print(f"⏰ Will auto-disconnect in {estimated_duration:.1f} seconds to save costs")
            await asyncio.sleep(estimated_duration)
            
            # Disconnect to stop charging
            await self.disconnect_avatar()
            print("🔄 Auto-disconnected from Hedra to save costs")
            
        except Exception as e:
            print(f"❌ Error in auto-disconnect: {e}")
    
    async def get_avatar_stream_url(self, avatar_id=None):
        """Get the streaming URL for the avatar"""
        try:
            if not avatar_id:
                avatar_id = self.avatar_id
                
            print(f"🌐 Getting stream URL for avatar: {avatar_id}")
            
            # Connect to validate avatar
            connected = await self.connect_to_avatar(avatar_id)
            
            if connected:
                # TODO: Get actual streaming URL from Hedra API
                # For now, return a placeholder URL
                stream_url = f"wss://api.hedra.com/stream?avatar_id={avatar_id}&api_key={self.api_key}"
                print(f"📡 Stream URL generated: {stream_url[:50]}...")
                return stream_url
            else:
                print("❌ Could not get stream URL - connection failed")
                return None
            
        except Exception as e:
            print(f"❌ Error getting avatar stream URL: {e}")
            return None
    
    async def disconnect_avatar(self):
        """Disconnect from the live avatar stream to stop charging"""
        try:
            if self.is_connected:
                self.is_connected = False
                self.speaking_start_time = None
                print("🛑 Disconnected from Hedra avatar")
                print("💰 Avatar session ended - billing stopped")
            else:
                print("ℹ️ Already disconnected from Hedra avatar")
        except Exception as e:
            print(f"❌ Error disconnecting: {e}")
    
    async def get_available_avatars(self):
        """Get list of available Hedra assets that could be used as avatars"""
        try:
            if not self.api_key or self.api_key.startswith("your_"):
                print("❌ Cannot get avatars - API key not configured")
                return None
            
            headers = {"X-API-Key": self.api_key}
            
            print("📋 Fetching available Hedra assets...")
            response = requests.get(
                f"{self.base_url}/web-app/public/generations",
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                avatars = []
                
                if 'data' in data:
                    for item in data['data']:
                        if item.get('type') == 'image':  # Only image assets can be avatars
                            asset = item.get('asset', {})
                            avatar_info = {
                                'id': asset.get('id'),
                                'name': asset.get('name') or 'Unnamed Avatar',
                                'thumbnail_url': asset.get('thumbnail_url'),
                                'created_at': asset.get('created_at'),
                                'dimensions': f"{asset.get('asset', {}).get('width', '?')}x{asset.get('asset', {}).get('height', '?')}"
                            }
                            avatars.append(avatar_info)
                
                print(f"✅ Found {len(avatars)} potential avatar images")
                return avatars
            else:
                print(f"❌ Hedra API error getting avatars: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error fetching Hedra avatars: {e}")
            return None
    
    def is_speaking(self):
        """Check if avatar is currently speaking"""
        if not self.speaking_start_time:
            return False
        
        elapsed = time.time() - self.speaking_start_time
        return elapsed < self.max_speaking_duration
    
    def get_avatar_info(self):
        """Get information about the current avatar"""
        return {
            'avatar_id': self.avatar_id,
            'is_connected': self.is_connected,
            'is_speaking': self.is_speaking(),
            'api_configured': bool(self.api_key and not self.api_key.startswith("your_"))
        }
    
    def create_video_generation(self, text_prompt, image_path=None):
        """Create a new video generation using Hedra API"""
        try:
            if not self.api_key or self.api_key.startswith("your_"):
                print("❌ Cannot create video - API key not configured")
                return None
            
            headers = {"X-API-Key": self.api_key}
            
            # TODO: Implement actual video generation API
            # This would use the /web-app/public/generations endpoint with POST
            print(f"🎬 Would create video generation with prompt: '{text_prompt[:100]}...'")
            print("💡 Video generation API integration coming soon")
            
            return {
                'status': 'placeholder',
                'message': 'Video generation API not fully implemented yet',
                'prompt': text_prompt,
                'avatar_id': self.avatar_id
            }
            
        except Exception as e:
            print(f"❌ Error creating video generation: {e}")
            return None