import asyncio
import logging
from livekit import agents
from livekit.agents import AgentSession, Agent
from livekit.plugins import openai, hedra
from dotenv import load_dotenv
import os

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HedraVoiceAgent:
    def __init__(self):
        self.hedra_avatar = None
        self.session = None
        
    async def start_session(self, room):
        """Start Hedra avatar session"""
        try:
            # Get avatar ID from environment
            avatar_id = os.getenv("HEDRA_AVATAR_ID")
            
            if not avatar_id or avatar_id == "your-avatar-id-here":
                logger.warning("⚠️ HEDRA_AVATAR_ID not set!")
                logger.warning("📋 To get your avatar ID:")
                logger.warning("1. Go to https://www.hedra.com/studio")
                logger.warning("2. Create an avatar image using the image generator")
                logger.warning("3. Go to your Library and hover over the image")
                logger.warning("4. Click the three dots icon and select 'Copy Asset ID'")
                logger.warning("5. Add the asset ID to your .env file as HEDRA_AVATAR_ID")
                logger.warning("6. Or upload via API: curl -X POST https://api.hedra.com/v1/assets")
                return False
            
            # Create avatar session with your avatar ID
            self.hedra_avatar = hedra.AvatarSession(
                avatar_id=avatar_id
            )
            
            # Create agent session with OpenAI realtime model
            self.session = AgentSession(
                stt=openai.STT(),
                llm=openai.LLM(model="gpt-3.5-turbo"),
                tts=openai.TTS(voice="alloy"),
            )
            
            # Start avatar (this begins LiveKit room participation)
            await self.hedra_avatar.start(self.session, room=room)
            
            # Create agent
            agent = Agent(
                instructions="You are a helpful AI assistant with a friendly personality. Keep responses concise for voice interaction."
            )
            
            # Start the session
            await self.session.start(agent=agent, room=room)
            
            logger.info("🎬 Hedra Live Avatar session started successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error starting Hedra session: {e}")
            logger.error("💡 This might be due to:")
            logger.error("   - Incorrect avatar ID")
            logger.error("   - Missing Hedra API key")
            logger.error("   - Network connectivity issues")
            logger.error("   - LiveKit connection problems")
            return False
    
    async def send_text_response(self, text):
        """Send text for avatar to speak"""
        if self.session:
            try:
                await self.session.generate_reply(instructions=f"Respond to: {text}")
                return True
            except Exception as e:
                logger.error(f"❌ Error sending text to avatar: {e}")
                return False
        return False
    
    async def stop_session(self):
        """Stop avatar session to end charges"""
        if self.hedra_avatar:
            try:
                await self.hedra_avatar.stop()
                logger.info("🛑 Hedra avatar session stopped")
            except Exception as e:
                logger.error(f"❌ Error stopping avatar: {e}")

# LiveKit Agent entry point
async def entrypoint(ctx: agents.JobContext):
    """Main entry point for LiveKit Agent"""
    logger.info("🚀 Starting Hedra Voice Agent...")
    
    await ctx.connect()
    
    # Create avatar session
    avatar_agent = HedraVoiceAgent()
    success = await avatar_agent.start_session(ctx.room)
    
    if success:
        logger.info("✅ Agent connected to room with Hedra avatar")
        
        # Keep the session alive
        await asyncio.sleep(3600)  # 1 hour max session
    else:
        logger.error("❌ Failed to start avatar session")

if __name__ == "__main__":
    # Run the LiveKit agent
    from livekit.agents import cli, WorkerOptions
    
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint)) 