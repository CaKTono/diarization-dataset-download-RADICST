#!/usr/bin/env python3
import sys
import subprocess
import os

def download_audio(url, output_dir="./"):
    """
    Download audio only from YouTube using yt-dlp
    
    Args:
        url: YouTube video URL
        output_dir: Directory to save the audio file (default: current directory)
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # yt-dlp command for audio download only
    command = [
        "yt-dlp",
        "-f", "bestaudio/best",  # Download best audio only
        "--extract-audio",       # Extract audio from video
        "--audio-format", "mp3", # Convert to MP3 format
        "--audio-quality", "0",  # Best audio quality (0 is highest)
        "--extractor-args", "youtube:player_client=android", # Use Android client to avoid SABR issues
        "-o", f"{output_dir}/%(title)s.%(ext)s", # Output template
        url
    ]
    
    try:
        print(f"Downloading audio from: {url}")
        print(f"Saving to: {output_dir}")
        print("-" * 50)
        
        # Run yt-dlp command
        result = subprocess.run(command, check=True, text=True)
        
        print("-" * 50)
        print("✓ Audio download completed successfully!")
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Error downloading audio: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("✗ Error: yt-dlp is not installed or not in PATH")
        print("Install it with: pip install yt-dlp")
        sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print("Usage: python download_yt.py <YouTube_URL> [output_directory]")
        print("Example: python download_yt.py 'https://www.youtube.com/watch?v=VIDEO_ID' ./music")
        sys.exit(1)
    
    url = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./"
    
    download_audio(url, output_dir)

if __name__ == "__main__":
    main()