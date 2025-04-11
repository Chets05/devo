import time
import os
import tempfile
import zipfile
import platform
import subprocess
from moviepy.editor import (AudioFileClip, CompositeVideoClip, CompositeAudioClip, ImageClip,
                            TextClip, VideoFileClip)
from moviepy.audio.fx.audio_loop import audio_loop
from moviepy.audio.fx.audio_normalize import audio_normalize
import requests
import logging

# Configure logging
logging.basicConfig(filename="render_engine.log", level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

def download_file(url, filename):
    with open(filename, 'wb') as f:
        headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        f.write(response.content)

def search_program(program_name):
    try: 
        search_cmd = "where" if platform.system() == "Windows" else "which"
        return subprocess.check_output([search_cmd, program_name]).decode().strip()
    except subprocess.CalledProcessError:
        return None

def get_program_path(program_name):
    program_path = search_program(program_name)
    return program_path

def get_output_media(audio_file_path, timed_captions, background_video_data, video_server):
    OUTPUT_FILE_NAME = "rendered_video.mp4"
    magick_path = get_program_path("magick")
    logging.debug(f"ImageMagick path: {magick_path}")
    if magick_path:
        os.environ['IMAGEMAGICK_BINARY'] = magick_path
    else:
        os.environ['IMAGEMAGICK_BINARY'] = '/usr/bin/convert'
    
    visual_clips = []
    try:
        for (t1, t2), video_url in background_video_data:
            if not video_url:
                logging.warning(f"Missing video URL for interval {t1}-{t2}")
                continue

            # Download the video file
            video_filename = tempfile.NamedTemporaryFile(delete=False).name
            try:
                logging.debug(f"Downloading video from URL: {video_url}")
                download_file(video_url, video_filename)
            except Exception as e:
                logging.error(f"Failed to download video from {video_url}: {e}")
                continue
            
            # Create VideoFileClip from the downloaded file
            try:
                video_clip = VideoFileClip(video_filename)
                video_clip = video_clip.set_start(t1)
                video_clip = video_clip.set_end(t2)
                visual_clips.append(video_clip)
            except Exception as e:
                logging.error(f"Failed to process video file {video_filename}: {e}")
                continue

    except Exception as e:
        logging.error(f"Error while processing background videos: {e}")

    audio_clips = []
    try:
        audio_file_clip = AudioFileClip(audio_file_path)
        audio_clips.append(audio_file_clip)
    except Exception as e:
        logging.error(f"Failed to load audio file {audio_file_path}: {e}")
        return None

    try:
        for (t1, t2), text in timed_captions:
            text_clip = TextClip(txt=text, fontsize=100, color="white", stroke_width=3, stroke_color="black", method="label")
            text_clip = text_clip.set_start(t1)
            text_clip = text_clip.set_end(t2)
            text_clip = text_clip.set_position(["center", 800])
            visual_clips.append(text_clip)
    except Exception as e:
        logging.error(f"Error while creating text clips: {e}")

    try:
        video = CompositeVideoClip(visual_clips)
        if audio_clips:
            audio = CompositeAudioClip(audio_clips)
            video.duration = audio.duration
            video.audio = audio

        logging.debug(f"Writing video to file: {OUTPUT_FILE_NAME}")
        video.write_videofile(OUTPUT_FILE_NAME, codec='libx264', audio_codec='aac', fps=25, preset='veryfast')
    except Exception as e:
        logging.error(f"Failed to render video: {e}")
        return None

    # Clean up downloaded files
    try:
        for (t1, t2), video_url in background_video_data:
            video_filename = tempfile.NamedTemporaryFile(delete=False).name
            os.remove(video_filename)
    except Exception as e:
        logging.error(f"Error during cleanup of temporary files: {e}")

    return OUTPUT_FILE_NAME