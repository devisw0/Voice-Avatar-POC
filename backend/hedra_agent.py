import asyncio
import logging
from livekit import agents
from livekit.agents import JobContext, AgentSession, Agent, RoomOutputOptions, RoomInputOptions, stt
from livekit.plugins import openai, hedra, silero, elevenlabs
from dotenv import load_dotenv
import os

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def entrypoint(ctx: JobContext):
    """Main entry point for LiveKit Agent with Hedra - CORRECTED VERSION"""
    logger.info("🚀 Starting Hedra Voice Agent...")
    logger.info(f"🏠 Connecting to room: {ctx.room.name}")
    
    await ctx.connect()
    
    # Get avatar ID from environment
    avatar_id = os.getenv("HEDRA_AVATAR_ID")
    
    if not avatar_id or avatar_id.startswith("your-") or avatar_id == "default-avatar-id":
        logger.warning("⚠️ HEDRA_AVATAR_ID not properly set!")
        logger.warning("📋 Please set: HEDRA_AVATAR_ID=4157bd2c-1ccd-40fe-8944-01b7d049401f")
        # Continue with audio-only fallback
        await start_audio_only_agent(ctx)
        return
    
    logger.info(f"🎬 Using Hedra Avatar ID: {avatar_id}")
    
    try:
        # CORRECTED: Create AgentSession with StreamAdapter for real streaming
        vad = silero.VAD.load()
        
        # FIXED: Use StreamAdapter for proper streaming STT
        streaming_stt = stt.StreamAdapter(
            stt=openai.STT(),
            vad=vad
        )
        
        session = AgentSession(
            vad=vad,
            stt=streaming_stt,  # Use StreamAdapter for real streaming
            llm=openai.LLM(model="gpt-3.5-turbo"), 
            tts=elevenlabs.TTS()  # Better for lip-sync accuracy
        )
        
        # CORRECTED: Create avatar session separately
        avatar = hedra.AvatarSession(avatar_id=avatar_id)
        
        # CRITICAL: Start avatar first, passing session and room
        await avatar.start(session, room=ctx.room)
        logger.info("🎬 Hedra avatar started successfully!")
        
        # Create agent
        agent = Agent(
            instructions="""You are a helpful AI assistant with a friendly personality. 
            Keep responses concise but engaging, suitable for voice interaction.
            Respond naturally and conversationally. Keep responses under 100 words."""
        )
        
        # CORRECTED: Start session with audio_enabled=False for avatar mode
        await session.start(
            agent=agent,
            room=ctx.room,
            room_input_options=RoomInputOptions(
                # CRITICAL: Enable audio input from room participants
                audio_enabled=True
            ),
            room_output_options=RoomOutputOptions(
                # CRITICAL: Disable audio output to room - avatar handles this
                audio_enabled=False,
            )
        )
        
        logger.info("✅ Hedra avatar agent fully started!")
        logger.info(f"🎬 Avatar is now live in room: {ctx.room.name}")
        logger.info("🎥 Video avatar should now be visible to users")
        
        # Keep session alive for maximum 1 hour (cost control)
        await asyncio.sleep(3600)
        
    except Exception as e:
        logger.error(f"❌ Error starting Hedra session: {e}")
        logger.error("💡 This could be due to:")
        logger.error("   - Incorrect avatar ID")
        logger.error("   - Missing Hedra API key")
        logger.error("   - Hedra service unavailable")
        logger.error("   - Network connectivity issues")
        logger.error("💡 Falling back to audio-only mode")
        await start_audio_only_agent(ctx)

async def start_audio_only_agent(ctx: JobContext):
    """Fallback audio-only agent with proper VAD"""
    try:
        # CORRECTED: Use proper VAD and StreamAdapter for audio-only mode
        vad = silero.VAD.load()
        
        streaming_stt = stt.StreamAdapter(
            stt=openai.STT(),
            vad=vad
        )
        
        session = AgentSession(
            vad=vad,
            stt=streaming_stt,  # Use StreamAdapter for streaming
            llm=openai.LLM(model="gpt-3.5-turbo"),
            tts=elevenlabs.TTS()  # Consistent TTS choice
        )
        
        agent = Agent(
            instructions="You are a helpful AI assistant. Keep responses brief and friendly for voice interaction."
        )
        
        await session.start(
            agent=agent, 
            room=ctx.room,
            room_input_options=RoomInputOptions(audio_enabled=True)
        )
        logger.info("✅ Audio-only agent started as fallback")
        logger.info("🔊 Users will hear OpenAI TTS responses")
        
        # Keep session alive for maximum 1 hour
        await asyncio.sleep(3600)
        
    except Exception as e:
        logger.error(f"❌ Error starting audio-only agent: {e}")
        logger.error("💡 Check your OpenAI API key and LiveKit configuration")

def test_environment():
    """Test environment configuration"""
    logger.info("🔍 Testing environment configuration...")
    
    # Test basic environment variables
    env_vars = {
        'LIVEKIT_URL': os.getenv('LIVEKIT_URL'),
        'LIVEKIT_API_KEY': os.getenv('LIVEKIT_API_KEY'),
        'LIVEKIT_API_SECRET': os.getenv('LIVEKIT_API_SECRET'),
        'HEDRA_API_KEY': os.getenv('HEDRA_API_KEY'),
        'HEDRA_AVATAR_ID': os.getenv('HEDRA_AVATAR_ID'),
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY')
    }
    
    for var, value in env_vars.items():
        if value:
            logger.info(f"   ✅ {var}: Set ({len(value)} chars)")
        else:
            logger.warning(f"   ❌ {var}: Missing")
    
    # Test Hedra API if key is available
    hedra_key = os.getenv('HEDRA_API_KEY')
    if hedra_key and not hedra_key.startswith('your_'):
        import requests
        try:
            logger.info("🔍 Testing Hedra API connection...")
            response = requests.get(
                "https://api.hedra.com/web-app/public/generations",
                headers={"X-API-Key": hedra_key},
                timeout=10
            )
            if response.status_code == 200:
                logger.info("   ✅ Hedra API connection successful")
                
                # Check for avatar ID
                avatar_id = os.getenv('HEDRA_AVATAR_ID')
                if avatar_id:
                    data = response.json()
                    found_avatar = False
                    if 'data' in data:
                        for item in data['data']:
                            if (item.get('asset', {}).get('id') == avatar_id or 
                                item.get('id') == avatar_id):
                                found_avatar = True
                                break
                    
                    if found_avatar:
                        logger.info(f"   ✅ Avatar ID {avatar_id} found")
                    else:
                        logger.warning(f"   ⚠️ Avatar ID {avatar_id} not found in recent generations")
                        logger.warning("   💡 Avatar might be older or use different ID")
                
            else:
                logger.warning(f"   ⚠️ Hedra API returned: {response.status_code}")
        except Exception as e:
            logger.warning(f"   ⚠️ Could not test Hedra API: {e}")

if __name__ == "__main__":
    from livekit.agents import cli, WorkerOptions
    
    logger.info("🎯 Starting LiveKit Agent Worker...")
    
    # Test environment before starting
    test_environment()
    
    logger.info("🚀 Starting agent worker...")
    logger.info("💡 Agent will:")
    logger.info("   1. Try to connect with Hedra avatar for VIDEO")
    logger.info("   2. Fall back to audio-only if Hedra fails")
    logger.info("   3. Auto-disconnect after 1 hour (cost control)")
    
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint)) 