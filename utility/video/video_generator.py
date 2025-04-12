import os
import requests
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip, CompositeVideoClip, VideoFileClip, ColorClip
import numpy as np
from PIL import Image
import io
import tempfile
import urllib.request
import time

def resize_frame(frame, size):
    """Resize a frame using PIL with the correct resampling filter."""
    if isinstance(frame, np.ndarray):
        # Convert numpy array to PIL Image
        img = Image.fromarray(frame)
        # Resize using Lanczos (replacement for ANTIALIAS)
        img = img.resize(size, Image.Resampling.LANCZOS)
        # Convert back to numpy array
        return np.array(img)
    return frame

def download_image(url):
    """Download an image from a URL and return it as a numpy array."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        image = Image.open(io.BytesIO(response.content))
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        return np.array(image)
    except Exception as e:
        print(f"Error downloading image from {url}: {str(e)}")
        # Return a black image as fallback
        return np.zeros((720, 1280, 3), dtype=np.uint8)

def download_video(url):
    """Download a video from a URL and return the local file path."""
    try:
        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        temp_path = temp_file.name
        temp_file.close()
        
        # Download with proper headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()
        
        # Write the video data to the temporary file
        with open(temp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        return temp_path
    except Exception as e:
        print(f"Error downloading video from {url}: {str(e)}")
        if 'temp_path' in locals() and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except:
                pass
        return None

def create_video_from_photos(segments, audio_path, output_path, width=1280, height=720):
    """Create a video from a list of photo URLs and timing information."""
    
    if not segments:
        print("No segments provided")
        return
    
    clips = []
    current_time = 0
    
    for segment in segments:
        timing, url = segment
        start_time, end_time = timing
        duration = end_time - start_time
        
        if url:
            # Download and process the image
            image = download_image(url)
            clip = ImageClip(image)
            
            # Calculate zoom parameters
            img_aspect = image.shape[1] / image.shape[0]
            target_aspect = width / height
            
            if img_aspect > target_aspect:
                # Image is wider than target
                zoom = height / image.shape[0]
            else:
                # Image is taller than target
                zoom = width / image.shape[1]
            
            # Apply zoom and set duration
            clip = clip.resize(zoom)
            clip = clip.set_duration(duration)
            clip = clip.set_start(start_time)
            
            # Center the clip
            clip = clip.set_position(('center', 'center'))
            
            clips.append(clip)
        else:
            # Create a black clip if no image is available
            black_clip = ImageClip(np.zeros((height, width, 3), dtype=np.uint8))
            black_clip = black_clip.set_duration(duration)
            black_clip = black_clip.set_start(start_time)
            clips.append(black_clip)
    
    # Load the audio file
    audio = AudioFileClip(audio_path)
    
    # Create the final video
    final_video = CompositeVideoClip(clips, size=(width, height))
    final_video = final_video.set_audio(audio)
    final_video = final_video.set_duration(audio.duration)
    
    # Write the output file
    final_video.write_videofile(output_path, fps=30, codec='libx264', audio_codec='aac')
    
    # Clean up
    final_video.close()
    audio.close()
    for clip in clips:
        clip.close()

def create_video_from_videos(segments, audio_path, output_path, width=1280, height=720):
    """Create a video from a list of video URLs and timing information."""
    
    if not segments:
        print("No segments provided")
        return
    
    clips = []
    temp_files = []  # To keep track of temporary files for cleanup
    
    try:
        for segment in segments:
            timing, url = segment
            start_time, end_time = timing
            duration = end_time - start_time
            
            if url:
                # Download and process the video
                video_path = download_video(url)
                if video_path:
                    temp_files.append(video_path)
                    try:
                        clip = VideoFileClip(video_path)
                        
                        # Trim the clip to the required duration
                        if clip.duration > duration:
                            clip = clip.subclip(0, duration)
                        
                        # Calculate resize dimensions while maintaining aspect ratio
                        clip_aspect = clip.size[0] / clip.size[1]
                        target_aspect = width / height
                        
                        if clip_aspect > target_aspect:
                            # Video is wider than target
                            new_width = width
                            new_height = int(width / clip_aspect)
                        else:
                            # Video is taller than target
                            new_height = height
                            new_width = int(height * clip_aspect)
                        
                        # Create a custom resize function using PIL's Lanczos filter
                        clip = clip.fl_image(lambda frame: resize_frame(frame, (new_width, new_height)))
                        
                        # Set the start time
                        clip = clip.set_start(start_time)
                        
                        # Center the clip
                        x_offset = (width - new_width) // 2
                        y_offset = (height - new_height) // 2
                        clip = clip.set_position((x_offset, y_offset))
                        
                        clips.append(clip)
                    except Exception as e:
                        print(f"Error processing video clip: {str(e)}")
                        # Create a black clip as fallback
                        black_clip = ColorClip(size=(width, height), color=(0, 0, 0))
                        black_clip = black_clip.set_duration(duration)
                        black_clip = black_clip.set_start(start_time)
                        clips.append(black_clip)
            else:
                # Create a black clip if no video is available
                black_clip = ColorClip(size=(width, height), color=(0, 0, 0))
                black_clip = black_clip.set_duration(duration)
                black_clip = black_clip.set_start(start_time)
                clips.append(black_clip)
        
        if not clips:
            print("No valid clips to create video")
            return
        
        # Create a black background clip
        background = ColorClip(size=(width, height), color=(0, 0, 0))
        background = background.set_duration(max(clip.end for clip in clips))
        clips.insert(0, background)
        
        # Load the audio file
        audio = AudioFileClip(audio_path)
        
        # Create the final video
        final_video = CompositeVideoClip(clips, size=(width, height))
        final_video = final_video.set_audio(audio)
        final_video = final_video.set_duration(audio.duration)
        
        # Write the output file
        final_video.write_videofile(output_path, fps=30, codec='libx264', audio_codec='aac')
        
    except Exception as e:
        print(f"Error creating video: {str(e)}")
    finally:
        # Clean up
        for clip in clips:
            try:
                clip.close()
            except:
                pass
        if 'audio' in locals():
            try:
                audio.close()
            except:
                pass
        # Remove temporary files
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass 