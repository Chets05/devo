from openai import OpenAI
import os
import json
import re
from datetime import datetime
from utility.utils import log_response,LOG_TYPE_GPT
import requests
from dotenv import load_dotenv
import time

load_dotenv()

if len(os.environ.get("GROQ_API_KEY")) > 30:
    from groq import Groq
    model = "llama3-70b-8192"
    client = Groq(
        api_key=os.environ.get("GROQ_API_KEY"),
        )
else:
    model = "gpt-4o"
    OPENAI_API_KEY = os.environ.get('OPENAI_KEY')
    client = OpenAI(api_key=OPENAI_API_KEY)

log_directory = ".logs/gpt_logs"

prompt = """# Instructions

Given the following video script and timed captions, extract three visually concrete and specific keywords for each time segment that can be used to search for background videos. The keywords should be short and capture the main essence of the sentence. They can be synonyms or related terms. If a caption is vague or general, consider the next timed caption for more context. If a keyword is a single word, try to return a two-word keyword that is visually concrete. If a time frame contains two or more important pieces of information, divide it into shorter time frames with one keyword each. Ensure that the time periods are strictly consecutive and cover the entire length of the video. Each keyword should cover between 2-4 seconds. The output should be in JSON format, like this: [[[t1, t2], ["keyword1", "keyword2", "keyword3"]], [[t2, t3], ["keyword4", "keyword5", "keyword6"]], ...]. Please handle all edge cases, such as overlapping time segments, vague or general captions, and single-word keywords.

For example, if the caption is 'The cheetah is the fastest land animal, capable of running at speeds up to 75 mph', the keywords should include 'cheetah running', 'fastest animal', and '75 mph'. Similarly, for 'The Great Wall of China is one of the most iconic landmarks in the world', the keywords should be 'Great Wall of China', 'iconic landmark', and 'China landmark'.

Important Guidelines:

Use only English in your text queries.
Each search string must depict something visual.
The depictions have to be extremely visually concrete, like rainy street, or cat sleeping.
'emotional moment' <= BAD, because it doesn't depict something visually.
'crying child' <= GOOD, because it depicts something visual.
The list must always contain the most relevant and appropriate query searches.
['Car', 'Car driving', 'Car racing', 'Car parked'] <= BAD, because it's 4 strings.
['Fast car'] <= GOOD, because it's 1 string.
['Un chien', 'une voiture rapide', 'une maison rouge'] <= BAD, because the text query is NOT in English.

Note: Your response should be the response only and no extra text or data.
  """

def fix_json(json_str):
    # Replace typographical apostrophes with straight quotes
    json_str = json_str.replace("'", "'")
    # Replace any incorrect quotes (e.g., mixed single and double quotes)
    json_str = json_str.replace(""", "\"").replace(""", "\"").replace("'", "\"").replace("'", "\"")
    # Add escaping for quotes within the strings
    json_str = json_str.replace('"you didn"t"', '"you didn\'t"')
    return json_str

PEXELS_API_KEY = os.getenv('PEXELS_KEY')
RATE_LIMIT_DELAY = 2  # Increased delay to 2 seconds between requests
MAX_RETRIES = 3  # Maximum number of retries for failed requests

def search_pexels_videos(query, per_page=1):
    """Search for videos on Pexels with rate limiting and retries."""
    headers = {
        'Authorization': PEXELS_API_KEY,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # Clean up the query
    query = ' '.join(word for word in query.split() if len(word) > 2)
    if not query:
        query = "nature"  # fallback query
    
    url = f'https://api.pexels.com/videos/search?query={query}&per_page={per_page}'
    
    for attempt in range(MAX_RETRIES):
        try:
            # Add delay for rate limiting
            time.sleep(RATE_LIMIT_DELAY)
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if data.get('videos'):
                # Get the video with the best quality
                video = data['videos'][0]
                video_files = sorted(
                    video['video_files'],
                    key=lambda x: (x.get('width', 0) * x.get('height', 0)),
                    reverse=True
                )
                
                # Try to find a suitable quality video (HD or lower)
                for video_file in video_files:
                    if video_file.get('width', 0) <= 1920:  # Max Full HD
                        return video_file['link']
                
                # If no suitable quality found, use the lowest quality
                return video_files[-1]['link']
                    
            return None
            
        except requests.exceptions.RequestException as e:
            if attempt < MAX_RETRIES - 1:
                print(f"Attempt {attempt + 1} failed: {str(e)}. Retrying...")
                time.sleep(RATE_LIMIT_DELAY * 2)  # Double the delay on retry
            else:
                print(f"All attempts failed: {str(e)}")
                return None
        except Exception as e:
            print(f"Error searching for videos: {str(e)}")
            return None

def getVideoSearchQueriesTimed(script, captions_timed):
    """Generate search queries for each caption segment."""
    search_queries = []
    
    # Default queries for different types of content
    cloud_queries = [
        "timelapse clouds",
        "storm clouds forming",
        "beautiful cloudscape",
        "clouds in sky",
        "weather clouds",
        "cumulus clouds"
    ]
    
    for (start_time, end_time), caption in captions_timed:
        # Create search queries based on the caption
        queries = []
        
        # Add specific queries based on the caption content
        if "cloud" in script.lower():
            queries.extend(cloud_queries[:2])  # Add some default cloud queries
            
        # Add the caption as a query
        clean_caption = ' '.join(word for word in caption.split() if len(word) > 2 and not word.lower() in ['the', 'and', 'but', 'for', 'with'])
        if clean_caption:
            queries.append(clean_caption)
            
        # If we don't have any valid queries, use defaults
        if not queries:
            queries = cloud_queries[:2]
            
        search_queries.append(((start_time, end_time), queries))
    
    return search_queries

def call_OpenAI(script,captions_timed):
    user_content = """Script: {}
Timed Captions:{}
""".format(script,"".join(map(str,captions_timed)))
    print("Content", user_content)
    
    response = client.chat.completions.create(
        model= model,
        temperature=1,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_content}
        ]
    )
    
    text = response.choices[0].message.content.strip()
    text = re.sub('\s+', ' ', text)
    print("Text", text)
    log_response(LOG_TYPE_GPT,script,text)
    return text

def merge_empty_intervals(segments):
    """Merge consecutive segments with no video URL."""
    if not segments:
        return [((0, 10), None)]  # Default segment if no segments provided
    
    merged = []
    current_segment = list(segments[0])  # Convert to list for mutability
    
    for segment in segments[1:]:
        if current_segment[1] is None and segment[1] is None:
            # Merge consecutive None segments
            current_segment[0] = (current_segment[0][0], segment[0][1])
        else:
            merged.append(tuple(current_segment))  # Convert back to tuple
            current_segment = list(segment)
    
    merged.append(tuple(current_segment))  # Add the last segment
    return merged
