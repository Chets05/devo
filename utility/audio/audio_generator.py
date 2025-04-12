import edge_tts
import asyncio

def generate_audio(text):
    output_filename = "audio_tts.wav"
    
    async def _generate():
        communicate = edge_tts.Communicate(text, "en-AU-WilliamNeural")
        await communicate.save(output_filename)
    
    # Run the async function in a new event loop
    asyncio.run(_generate())
    
    return output_filename
