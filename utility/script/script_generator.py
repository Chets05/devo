import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

# Configure the API key
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

def get_fallback_script(topic):
    """Generate a fallback script based on the topic."""
    if "cloud" in topic.lower():
        return """Fascinating Cloud Facts That Will Blow Your Mind:
- Clouds can weigh over a million pounds while floating in the air.
- The average cumulus cloud contains about 200,000 gallons of water.
- The highest clouds, called noctilucent clouds, form at about 50 miles above Earth.
- Some clouds can travel at speeds of over 100 miles per hour in the jet stream.
- The most common type of cloud is the cumulus cloud, which looks like cotton balls.
- Storm clouds can grow taller than Mount Everest."""
    elif "space" in topic.lower():
        return """Fascinating Space Facts That Will Blow Your Mind:
- The Sun is so massive that it makes up 99.86% of our solar system's total mass.
- A day on Venus is longer than its year! It takes 243 Earth days to rotate once.
- There's a giant hexagon-shaped storm on Saturn's north pole.
- The footprints left by Apollo astronauts on the Moon will last for at least 100 million years.
- If you could put Saturn in a giant bathtub, it would float! Its density is less than water.
- Stars don't actually twinkle - it's just Earth's atmosphere distorting their light."""
    else:
        return f"""Interesting Facts About {topic}:
- Scientists are constantly making new discoveries about {topic}.
- There are many fascinating aspects of {topic} that people don't know about.
- Research continues to reveal new insights about {topic}.
- The history of {topic} goes back many years.
- Modern technology has helped us better understand {topic}.
- There's still much to learn about {topic}."""

def generate_script(topic):
    try:
        # Initialize the model with the correct name
        model = genai.GenerativeModel('gemini-1.0-pro')
        
        # Create the prompt
        prompt = f"""Create a short, engaging script about {topic}. The script should:
        1. Be 30-45 seconds long when spoken
        2. Include 4-6 interesting facts
        3. Be conversational and engaging
        4. Be suitable for a video with background visuals
        
        Format the script as a series of bullet points, each containing one fact."""
        
        # Generate content
        response = model.generate_content(prompt)
        
        if response and response.text:
            return response.text
        else:
            return get_fallback_script(topic)
            
    except Exception as e:
        print(f"Error generating script: {str(e)}")
        return get_fallback_script(topic)
