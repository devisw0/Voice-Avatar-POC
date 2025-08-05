import asyncio
import logging
from livekit import agents
from livekit.agents import JobContext, JobProcess
from livekit.plugins import openai, hedra
from dotenv import load_dotenv
import os

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def entrypoint(ctx: JobContext):
    """Main entry point for LiveKit Agent with Hedra"""
    logger.info("🚀 Starting Hedra Voice Agent...")
    logger.info(f"🏠 Connecting to room: {ctx.room.name}")
    
    await ctx.connect()
    
    # Get avatar ID from environment
    avatar_id = os.getenv("HEDRA_AVATAR_ID")
    
    if not avatar_id or avatar_id.startswith("your-") or avatar_id == "default-avatar-id":
        logger.warning("⚠️ HEDRA_AVATAR_ID not properly set!")
        logger.warning("📋 Please set a valid Hedra avatar ID in your .env file")
        return
    
    logger.info(f"🎬 Using Hedra Avatar ID: {avatar_id}")
    
    try:
        # Create Hedra avatar session
        avatar_session = hedra.AvatarSession(
            avatar_id=avatar_id,
            quality="medium",  # Cost optimization
            fps=24
        )
        
        # Start the avatar session
        await avatar_session.connect()
        
        # Create agent session with proper components
        agent_session = agents.AgentSession(
            stt=openai.STT(),
            llm=openai.LLM(model="gpt-3.5-turbo"),
            tts=hedra.TTS(avatar_session=avatar_session)  # Use Hedra TTS
        )
        
        # Create and start agent
        agent = agents.Agent(
            instructions="""You are a helpful AI assistant with a friendly personality. 
            Keep responses concise but engaging, suitable for voice interaction.
            Respond naturally and conversationally. Keep responses under 100 words."""
        )
        
        # Start the session
        await agent_session.start(agent=agent, room=ctx.room)
        
        logger.info("✅ Hedra avatar agent started successfully!")
        logger.info(f"🎬 Avatar is now live in room: {ctx.room.name}")
        
        # Keep session alive for maximum 1 hour
        await asyncio.sleep(3600)
        
    except Exception as e:
        logger.error(f"❌ Error starting Hedra session: {e}")
        logger.error("💡 Falling back to audio-only mode")
        
        # Fallback to audio-only agent
        agent_session = agents.AgentSession(
            stt=openai.STT(),
            llm=openai.LLM(model="gpt-3.5-turbo"),
            tts=openai.TTS(voice="alloy")
        )
        
        agent = agents.Agent(
            instructions="You are a helpful AI assistant. Keep responses brief for voice interaction."
        )
        
        await agent_session.start(agent=agent, room=ctx.room)
        logger.info("✅ Audio-only agent started as fallback")
        
        # Keep session alive
        await asyncio.sleep(3600)

if __name__ == "__main__":
    from livekit.agents import cli, WorkerOptions
    
    logger.info("🎯 Starting LiveKit Agent Worker...")
    logger.info("📋 Environment check:")
    logger.info(f"   - LIVEKIT_URL: {'✅' if os.getenv('LIVEKIT_URL') else '❌'}")
    logger.info(f"   - LIVEKIT_API_KEY: {'✅' if os.getenv('LIVEKIT_API_KEY') else '❌'}")
    logger.info(f"   - HEDRA_API_KEY: {'✅' if os.getenv('HEDRA_API_KEY') else '❌'}")
    logger.info(f"   - HEDRA_AVATAR_ID: {'✅' if os.getenv('HEDRA_AVATAR_ID') else '❌'}")
    
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint)) 