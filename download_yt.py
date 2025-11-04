#!/usr/bin/env python3
"""
YouTube Media & Transcript Downloader
Downloads audio or video (highest quality) and transcripts from YouTube videos.
- Manual transcripts → saves to language/tr/video_{n}/
- Auto-generated/No manual transcripts → saves to language/no_tr/video_{n}/

Usage:
    python download_yt.py <youtube_url> <output_dir> <language_code> <media_type>

Examples:
    python download_yt.py "https://youtube.com/watch?v=..." ./english en audio
    python download_yt.py "https://youtube.com/watch?v=..." ./chinese zh-CN video
"""

import subprocess
import sys
import json
import re
import os
import html
import shutil
from pathlib import Path

def extract_video_id(url):
    """Extract video ID from YouTube URL"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)',
        r'youtube\.com\/embed\/([^&\n?#]+)',
        r'youtube\.com\/v\/([^&\n?#]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_next_video_number(parent_dir):
    """Get the next available video number in the directory"""
    os.makedirs(parent_dir, exist_ok=True)
    
    existing_folders = [d for d in os.listdir(parent_dir) if d.startswith('video_')]
    
    if not existing_folders:
        return 1
    
    # Extract numbers from folder names
    numbers = []
    for folder in existing_folders:
        try:
            num = int(folder.split('_')[1])
            numbers.append(num)
        except:
            continue
    
    return max(numbers) + 1 if numbers else 1

def get_video_metadata(url):
    """Fetch video metadata using yt-dlp"""
    try:
        cmd = [
            'yt-dlp',
            '--dump-json',
            '--skip-download',
            url
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            metadata = json.loads(result.stdout)
            return {
                'title': metadata.get('title', 'N/A'),
                'channel': metadata.get('uploader', 'N/A'),
                'channel_id': metadata.get('channel_id', 'N/A'),
                'upload_date': metadata.get('upload_date', 'N/A'),
                'duration': metadata.get('duration', 0),
                'view_count': metadata.get('view_count', 0),
                'like_count': metadata.get('like_count', 0),
                'description': metadata.get('description', 'N/A'),
                'video_id': metadata.get('id', 'N/A'),
                'url': url
            }
        return None
    except Exception as e:
        print(f"Error fetching metadata: {e}")
        return None

def save_video_details(metadata, output_dir):
    """Save video details to text file"""
    if not metadata:
        return False
    
    details_path = os.path.join(output_dir, 'video_details.txt')
    
    try:
        with open(details_path, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("VIDEO DETAILS\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"Title: {metadata['title']}\n")
            f.write(f"Channel: {metadata['channel']}\n")
            f.write(f"Channel ID: {metadata['channel_id']}\n")
            f.write(f"Video ID: {metadata['video_id']}\n")
            f.write(f"URL: {metadata['url']}\n")
            f.write(f"Upload Date: {metadata['upload_date']}\n")
            f.write(f"Duration: {metadata['duration']} seconds\n")
            f.write(f"View Count: {metadata['view_count']:,}\n")
            f.write(f"Like Count: {metadata['like_count']:,}\n")
            f.write(f"\n{'=' * 60}\n")
            f.write("DESCRIPTION\n")
            f.write("=" * 60 + "\n\n")
            f.write(metadata['description'])
        
        print(f"✓ Video details saved")
        return True
    except Exception as e:
        print(f"✗ Error saving video details: {e}")
        return False

def check_manual_transcript_exists(url):
    """Check if manual transcript exists (not auto-generated)"""
    try:
        cmd = ['yt-dlp', '--list-subs', '--skip-download', url]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        lines = result.stdout.split('\n')
        for line in lines:
            if 'Language' in line or 'Available' in line or '---' in line:
                continue
            if line.strip() and '[auto]' not in line.lower():
                return True
        
        return False
    except Exception as e:
        print(f"Error checking transcripts: {e}")
        return False

def download_audio(url, output_dir):
    """
    Download audio using yt-dlp.
    First, it tries to download the best audio-only stream ('ba') for speed.
    If that fails, it falls back to downloading the best available stream (video+audio)
    and extracting the audio from it.
    """
    print("\n📥 Downloading audio...")
    print("-" * 60)
    
    output_template = os.path.join(output_dir, "audio.%(ext)s")
    
    try:
        # --- First Attempt: Try the fast audio-only method ---
        print("🚀 Attempting fast download (audio-only stream)...")
        cmd_audio_only = [
            'yt-dlp',
            '-f', 'ba',  # 'ba' = best audio
            '-x',
            '--audio-format', 'mp3',
            '--audio-quality', '0',
            '--progress',
            '-o', output_template,
            url
        ]
        
        result = subprocess.run(cmd_audio_only)
        
        # --- Fallback: If the first attempt failed, try the robust method ---
        if result.returncode != 0:
            print("\n⚠️ Audio-only stream failed. Falling back to robust method (will download video and extract audio)...")
            cmd_fallback = [
                'yt-dlp',
                # The '-f' flag is removed to let yt-dlp pick the best stream
                '-x',
                '--audio-format', 'mp3',
                '--audio-quality', '0',
                '--progress',
                '-o', output_template,
                url
            ]
            result = subprocess.run(cmd_fallback)

        # --- Final Result ---
        print("-" * 60)
        if result.returncode == 0:
            print("✓ Audio downloaded successfully: audio.mp3")
            return True
        else:
            print("✗ Audio download failed after all attempts.")
            return False
            
    except FileNotFoundError:
        print("✗ yt-dlp not found. Please install it first:")
        print("  brew install yt-dlp")
        return False
    except Exception as e:
        print(f"✗ An unexpected error occurred during audio download: {e}")
        return False

def download_video(url, output_dir):
    """
    Download video in the highest quality using yt-dlp.
    Downloads the best video+audio combination available.
    """
    print("\n📥 Downloading video...")
    print("-" * 60)

    output_template = os.path.join(output_dir, "video.%(ext)s")

    try:
        print("🚀 Downloading highest quality video (best video+audio)...")
        cmd = [
            'yt-dlp',
            '-f', 'bestvideo+bestaudio/best',  # Best video+audio, fallback to best single file
            '--merge-output-format', 'mp4',    # Merge to mp4 format
            '--progress',
            '-o', output_template,
            url
        ]

        result = subprocess.run(cmd)

        print("-" * 60)
        if result.returncode == 0:
            print("✓ Video downloaded successfully: video.mp4")
            return True
        else:
            print("✗ Video download failed.")
            return False

    except FileNotFoundError:
        print("✗ yt-dlp not found. Please install it first:")
        print("  brew install yt-dlp")
        return False
    except Exception as e:
        print(f"✗ An unexpected error occurred during video download: {e}")
        return False

def download_transcript(url, output_dir, primary_lang_code, allow_auto=False):
    """
    Download transcript for a specific primary language code.
    If the primary code fails, it attempts to download using common fallback Chinese codes.
    """
    print("\n📝 Downloading transcripts...")
    print("-" * 60)
    
    temp_base = os.path.join(output_dir, "temp_sub")
    
    # Define a list of language codes to try, starting with the primary
    lang_codes_to_try = [primary_lang_code]

    # Add common Chinese fallbacks if the primary is a Chinese variant
    # We add general 'zh' and other common variants for robustness
    if primary_lang_code.lower().startswith('zh'):
        if 'zh' not in lang_codes_to_try:
            lang_codes_to_try.append('zh')
        if 'zh-Hans' not in lang_codes_to_try:
            lang_codes_to_try.append('zh-Hans')
        if 'zh-Hant' not in lang_codes_to_try: # Traditional Chinese
            lang_codes_to_try.append('zh-Hant')
        if 'zh-TW' not in lang_codes_to_try: # Traditional Chinese (Taiwan)
            lang_codes_to_try.append('zh-TW')
        if 'zh-HK' not in lang_codes_to_try: # Traditional Chinese (Hong Kong)
            lang_codes_to_try.append('zh-HK')
        if 'zh-CN' not in lang_codes_to_try: # Simplified Chinese (China)
            lang_codes_to_try.append('zh-CN')
    elif primary_lang_code.lower().startswith('en'):
        if 'en' not in lang_codes_to_try:
            lang_codes_to_try.append('en')
        if 'en-US' not in lang_codes_to_try:
            lang_codes_to_try.append('en-US')
        if 'en-GB' not in lang_codes_to_try:
            lang_codes_to_try.append('en-GB')

    
    # Remove duplicates and preserve order
    seen = set()
    lang_codes_to_try_unique = []
    for code in lang_codes_to_try:
        if code not in seen:
            lang_codes_to_try_unique.append(code)
            seen.add(code)
    
    for current_lang_code in lang_codes_to_try_unique:
        print(f"🔄 Attempting to download transcript for language: '{current_lang_code}'...")
        try:
            cmd = [
                'yt-dlp',
                '--write-subs',
                '--sub-langs', f'{current_lang_code},-live_chat', 
                '--sub-format', 'vtt',
                '--skip-download',
                '-o', temp_base,
                url
            ]
            
            if not allow_auto:
                cmd.insert(4, '--no-write-auto-subs')
            else:
                cmd.insert(4, '--write-auto-subs')
            
            subprocess.run(cmd, capture_output=True, text=True, check=False)
            
            output_path = Path(output_dir)
            vtt_files = list(output_path.glob("temp_sub*.vtt"))
            
            if vtt_files:
                vtt_file = vtt_files[0]
                transcript_data = parse_vtt_file(vtt_file)
                
                try:
                    os.remove(vtt_file)
                except OSError as e:
                    print(f"Warning: Could not remove temp file {vtt_file}: {e}")
                
                if transcript_data: # Ensure the parsed data is not empty
                    print(f"✓ Transcript successfully found and parsed for '{current_lang_code}'.")
                    return transcript_data
            
            print(f"✗ No transcript file found or parsed for '{current_lang_code}'.")
                
        except FileNotFoundError:
            print("✗ yt-dlp not found. Please install it first:")
            print("  brew install yt-dlp")
            return None
        except Exception as e:
            print(f"✗ An error occurred while attempting '{current_lang_code}': {e}")
            # Don't return None here, try the next language code
            
    print("-" * 60)
    print("✗ No transcripts available after trying all specified language codes.")
    return None

def clean_text(text):
    """Clean and preprocess transcript text"""
    if not text:
        return ""
    
    # Decode HTML entities (&nbsp; → space, &amp; → &, etc.)
    text = html.unescape(text)

    # Use regex to remove VTT tags like <c> and <00:00:00.000>
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove extra whitespace and newlines
    text = ' '.join(text.split())
    
    # Remove any remaining special characters that might cause issues
    text = text.strip()
    
    return text

def parse_vtt_file(vtt_path):
    """Parse VTT file and extract text with sentence and word-level timestamps"""
    transcript_data = []
    
    try:
        with open(vtt_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Find a timestamp line, which indicates the start of a new segment
            if '-->' in line:
                timestamp_parts = line.split('-->')
                if len(timestamp_parts) == 2:
                    start_time_str = timestamp_parts[0].strip()
                    # Handle extra VTT metadata that can appear after the end time
                    end_time_str = timestamp_parts[1].strip().split(' ')[0] 
                    
                    start_seconds = timestamp_to_seconds(start_time_str)
                    end_seconds = timestamp_to_seconds(end_time_str)
                    
                    i += 1
                    text_lines = []
                    # Collect all text lines for this segment
                    while i < len(lines) and lines[i].strip():
                        text_lines.append(lines[i].strip())
                        i += 1
                    
                    raw_text = ' '.join(text_lines)
                    
                    # Create a clean version for the main 'text' field
                    clean_segment_text = clean_text(raw_text)
                    
                    if not clean_segment_text: # Skip empty segments
                        continue

                    # --- Word-level timestamp extraction ---
                    words_data = []
                    # Regex to find timestamped words: e.g., <00:00:01.839><c>talk</c>
                    matches = re.findall(r'<(\d{2}:\d{2}:\d{2}[,.]\d{3})><c>(.*?)</c>', raw_text)
                    
                    for timestamp_str, word_text in matches:
                        word = clean_text(word_text)
                        if word:
                            words_data.append({
                                'text': word,
                                'start': timestamp_to_seconds(timestamp_str),
                                'end': 0 # We will calculate the 'end' time next
                            })

                    # Post-process to calculate 'end' time for each word
                    if words_data:
                        for j in range(len(words_data) - 1):
                            # The end of one word is the start of the next
                            words_data[j]['end'] = words_data[j+1]['start']
                        # The last word's end time is the segment's end time
                        words_data[-1]['end'] = end_seconds

                    transcript_data.append({
                        'text': clean_segment_text,
                        'start': start_seconds,
                        'end': end_seconds,
                        'words': words_data # This list will be empty if no word-level data exists
                    })
            
            i += 1
            
        return transcript_data
    
    except Exception as e:
        print(f"✗ Error parsing VTT file: {e}")
        return None

def timestamp_to_seconds(timestamp):
    """Convert VTT timestamp to seconds, handling various formats."""
    try:
        # VTT can use a comma for the decimal part
        timestamp = timestamp.replace(',', '.')
        
        # Split into main time and milliseconds
        if '.' in timestamp:
            main_part, ms_part = timestamp.split('.')
            ms = int(ms_part) / 1000.0
        else:
            main_part = timestamp
            ms = 0

        parts = main_part.split(':')
        
        # Process HH:MM:SS or MM:SS
        if len(parts) == 3:
            h, m, s = map(int, parts)
            total_seconds = h * 3600 + m * 60 + s
        elif len(parts) == 2:
            m, s = map(int, parts)
            total_seconds = m * 60 + s
        else:
            return 0 # Invalid format

        return total_seconds + ms
    except ValueError:
        return 0 # Return 0 if conversion fails

def save_transcript(transcript_data, output_dir):
    """Save transcript in multiple formats"""
    if not transcript_data:
        return False
    
    # Save as TXT with timestamps
    txt_path = os.path.join(output_dir, "transcript.txt")
    with open(txt_path, 'w', encoding='utf-8') as f:
        for entry in transcript_data:
            timestamp = seconds_to_timestamp(entry['start'])
            f.write(f"[{timestamp}] {entry['text']}\n")
    
    # Save as JSON (full data with timestamps)
    json_path = os.path.join(output_dir, "transcript.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(transcript_data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Transcript saved: transcript.txt, transcript.json")
    return True

def seconds_to_timestamp(seconds):
    """Convert seconds to HH:MM:SS format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def process_video(url, base_output_dir, lang_code, media_type='audio'):
    """Process video: download audio/video and transcript to appropriate folder"""
    video_id = extract_video_id(url)
    if not video_id:
        print("✗ Invalid YouTube URL")
        return False

    print(f"\n{'='*60}")
    print(f"Processing video: {video_id}")
    print(f"URL: {url}")
    print(f"Language: {lang_code}")
    print(f"Media Type: {media_type}")
    print(f"{'='*60}")
    
    # 1. Fetch metadata
    print("\n📊 Fetching video metadata...")
    metadata = get_video_metadata(url)
    if not metadata:
        print("✗ Could not fetch video metadata. Aborting.")
        return False
    print(f"✓ Title: {metadata['title']}")
    print(f"✓ Channel: {metadata['channel']}")

    # 2. Attempt to get transcript data
    transcript = None
    transcript_type = None

    print("\n📝 Attempting to download manual transcript...")
    temp_dir_for_check = os.path.join(base_output_dir, "temp_check")
    # Pass the lang_code to the download function
    transcript = download_transcript(url, temp_dir_for_check, lang_code, allow_auto=False)
    
    if transcript:
        transcript_type = "manual"
        parent_dir = os.path.join(base_output_dir, 'tr')
        print(f"✓ Manual transcript found for language '{lang_code}'.")
    else:
        print(f"✗ No manual transcript found. Attempting auto-generated transcript...")
        # Pass the lang_code to the download function again for the fallback
        transcript = download_transcript(url, temp_dir_for_check, lang_code, allow_auto=True)
        parent_dir = os.path.join(base_output_dir, 'no_tr')
        if transcript:
            transcript_type = "auto-generated"
            print(f"✓ Auto-generated transcript found for language '{lang_code}'.")
        else:
            transcript_type = "none"
            print("✗ No transcripts available at all.")

    if os.path.exists(temp_dir_for_check):
        shutil.rmtree(temp_dir_for_check)

    # 3. Create folder and save everything
    video_num = get_next_video_number(parent_dir)
    video_folder = f"video_{video_num}"
    output_dir = os.path.join(parent_dir, video_folder)
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n📁 Saving all files to: {output_dir}")

    save_video_details(metadata, output_dir)

    # Download media based on type
    if media_type == 'video':
        media_success = download_video(url, output_dir)
        media_label = "Video"
    else:
        media_success = download_audio(url, output_dir)
        media_label = "Audio"

    transcript_success = save_transcript(transcript, output_dir)

    # 4. Final Summary
    print(f"\n{'='*60}")
    print("Summary:")
    print(f"  Folder: {output_dir}")
    print(f"  Video Details: ✓ Saved")
    print(f"  {media_label}: {'✓ Downloaded' if media_success else '✗ Failed'}")
    if transcript_type != "none":
        print(f"  Transcript ({transcript_type}): {'✓ Saved' if transcript_success else '✗ Failed'}")
    else:
        print(f"  Transcript: ✗ Not available")
    print(f"{'='*60}\n")

    return media_success or transcript_success

def main():
    if len(sys.argv) < 5:
        print("Usage: python download_yt.py <youtube_url> <output_dir> <language_code> <media_type>")
        print("\nLanguage Codes: en (English), zh-CN (Chinese, Simplified), es (Spanish), etc.")
        print("Media Types: audio, video")
        print("\nExamples:")
        print("  python download_yt.py 'https://...' ./english en audio")
        print("  python download_yt.py 'https://...' ./chinese zh-CN video")
        sys.exit(1)

    url = sys.argv[1]
    base_output_dir = sys.argv[2]
    lang_code = sys.argv[3]
    media_type = sys.argv[4].lower()

    if media_type not in ['audio', 'video']:
        print("✗ Invalid media type. Must be 'audio' or 'video'")
        sys.exit(1)

    process_video(url, base_output_dir, lang_code, media_type)

if __name__ == "__main__":
    main()

'''
# First video
python download_yt.py "https://www.youtube.com/watch?v=oX7OduG1YmI&t=39s" ./english
# → saves to ./english/tr/video_1/ or ./english/no_tr/video_1/

# Second video
python download_yt.py "https://www.youtube.com/watch?v=ANOTHER_ID" ./english
# → saves to ./english/tr/video_2/ or ./english/no_tr/video_2/

# Chinese videos
python download_yt.py "https://www.youtube.com/watch?v=VIDEO_ID" ./chinese
# → saves to ./chinese/tr/video_1/ or ./chinese/no_tr/video_1/
'''