# backend/simple_hedra_agent.py
import asyncio
import os
from livekit import agents
from livekit.agents import AgentSession, Agent
from livekit.plugins import openai, hedra
from dotenv import load_dotenv

load_dotenv()

async def entrypoint(ctx: agents.JobContext):
    """Simple Hedra avatar agent"""
    await ctx.connect()
    
    # Get avatar ID from environment
    avatar_id = os.getenv("HEDRA_AVATAR_ID")
    
    if not avatar_id or avatar_id == "your-avatar-id-here":
        print("❌ HEDRA_AVATAR_ID not set!")
        print("📋 To get your avatar ID:")
        print("1. Go to https://www.hedra.com/studio")
        print("2. Create an avatar image using the image generator")
        print("3. Go to your Library and hover over the image")
        print("4. Click the three dots icon and select 'Copy Asset ID'")
        print("5. Add the asset ID to your .env file as HEDRA_AVATAR_ID")
        print("6. Or upload via API: curl -X POST https://api.hedra.com/v1/assets")
        return
    
    # Create avatar with your avatar ID
    hedra_avatar = hedra.AvatarSession(
        avatar_id=avatar_id
    )
    
    # Create session with OpenAI realtime model
    session = AgentSession(
        stt=openai.STT(),
        llm=openai.LLM(model="gpt-3.5-turbo"),
        tts=openai.TTS(voice="alloy")
    )
    
    # Start avatar
    await hedra_avatar.start(session, room=ctx.room)
    
    # Create agent
    agent = Agent(
        instructions="You are a helpful AI assistant. Keep responses brief for voice interaction."
    )
    
    # Start session
    await session.start(agent=agent, room=ctx.room)
    
    print("🎬 Hedra avatar agent started and ready!")

if __name__ == "__main__":
    from livekit.agents import cli, WorkerOptions
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint)) 