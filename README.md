# Diarization-aware Multi-Language Audio/Video Dataset

A curated multi-language dataset builder for speech recognition, speaker diarization, and audio processing research. Downloads YouTube videos with high-quality transcripts and automatic organization by language and transcript availability.

## 📊 Dataset Overview

- **Languages**: English, Chinese (Simplified & Traditional)
- **Total Videos**: 39+ Videos
- **Content Types**: Podcasts, interviews, meetings, documentaries, news
- **Speaker Range**: 2-20 speakers per video
- **Transcript Support**: Manual and auto-generated transcripts with word-level timestamps

## 🚀 Quick Start

### Prerequisites

```bash
# Install yt-dlp
brew install yt-dlp

# Or with pip
pip install yt-dlp

# Python 3.7+ required
python3 --version
```

### Download All Videos

```bash
# Download as VIDEO (highest quality) to current directory
python3 batch_download.py --input list.csv --media-type video --workers 3

# Download as AUDIO (MP3, smaller files)
python3 batch_download.py --input list.csv --media-type audio --workers 5

# Download to custom output folder
python3 batch_download.py --input list.csv --media-type video --workers 3 --output /path/to/dataset
```

### Download Single Video

```bash
# Syntax: python3 download_yt.py <url> <output_dir> <language_code> <media_type>

# English video
python3 download_yt.py "https://youtube.com/watch?v=..." ./english en video

# Chinese audio
python3 download_yt.py "https://youtube.com/watch?v=..." ./chinese zh audio
```

## 📁 Project Structure

```
10_Hours_Dataset/
├── README.md                    # This file
├── list.csv                     # Curated video list (CSV format, recommended)
├── list.txt                     # Original video list (TXT format, legacy)
├── download_yt.py              # Single video downloader
├── download_yt_sim.py          # Simplified downloader
├── batch_download.py           # Batch downloader with parallel processing
├── enhance.py                  # Audio enhancement tools
├── download_progress.json      # Auto-generated progress tracker
├── download_log_*.txt          # Auto-generated download logs
│
├── english/                    # English videos
│   ├── tr/                     # Videos WITH manual transcripts
│   │   ├── video_1/
│   │   │   ├── video.mp4 or audio.mp3
│   │   │   ├── transcript.json       # Full transcript with word timestamps
│   │   │   ├── transcript.txt        # Human-readable transcript
│   │   │   └── video_details.txt     # Video metadata
│   │   └── video_2/
│   └── no_tr/                  # Videos WITHOUT manual transcripts (auto-generated)
│       └── video_1/
│
├── chinese/                    # Chinese videos
│   ├── tr/                     # Manual transcripts
│   └── no_tr/                  # Auto-generated transcripts
│
└── indo/                       # Indonesian videos (optional)
```

## 🎯 Features

### Core Features

- ✅ **Parallel Downloads** - Download 2-5 videos simultaneously
- ✅ **Auto Language Detection** - Automatically categorizes by language
- ✅ **Transcript Management** - Separates manual vs auto-generated transcripts
- ✅ **Progress Tracking** - Resume interrupted downloads
- ✅ **Word-Level Timestamps** - Precise timing for each word
- ✅ **Multiple Formats** - JSON (structured) and TXT (readable)
- ✅ **Video Metadata** - Title, channel, views, description, duration
- ✅ **Error Handling** - Continues on failures, logs all errors
- ✅ **Dry Run Mode** - Test before downloading

### Transcript Features

Each video includes:
- **Sentence-level timestamps** - Start/end time for each segment
- **Word-level timestamps** - Individual word timing
- **Multiple formats**:
  - `transcript.json` - Structured data with full timing
  - `transcript.txt` - Human-readable with timestamps
- **Clean text** - HTML entities decoded, VTT tags removed
- **Language-specific** - Supports multiple Chinese variants (zh, zh-Hans, zh-TW)

## 📖 Usage Guide

### Batch Download Script

The main tool for downloading multiple videos:

```bash
# Basic usage (uses list.csv by default)
python3 batch_download.py --media-type video --workers 3

# Specify input file
python3 batch_download.py --input list.csv --media-type audio --workers 5

# Dry run (test without downloading)
python3 batch_download.py --input list.csv --dry-run

# Resume interrupted downloads (just run the same command again)
python3 batch_download.py --input list.csv --media-type video --workers 3
```

**Parameters:**
- `--input` - Input file (CSV or TXT format, default: list.csv)
- `--media-type` - Download as 'audio' or 'video' (default: audio)
- `--workers` - Number of parallel downloads (default: 3, recommended: 2-5)
- `--output` - Custom output folder (default: current directory)
- `--no-log` - Disable logging to file (console output only)
- `--dry-run` - Test mode without actual downloads

**Worker Recommendations:**
- **Audio downloads**: 5 workers (faster, less bandwidth)
- **Video downloads**: 3 workers (more stable, large files)
- **Slow connection**: 2 workers (safer)

### Single Video Downloader

For downloading individual videos:

```bash
# Syntax
python3 download_yt.py <url> <output_dir> <language_code> <media_type>

# Examples
python3 download_yt.py "https://youtube.com/watch?v=abc123" ./english en video
python3 download_yt.py "https://youtube.com/watch?v=xyz789" ./chinese zh-Hans audio
```

**Language Codes:**
- English: `en`, `en-US`, `en-GB`
- Chinese (Simplified): `zh`, `zh-Hans`, `zh-CN`
- Chinese (Traditional): `zh-Hant`, `zh-TW`, `zh-HK`
- Indonesian: `id`

### Managing Your Video List

#### Using CSV (Recommended)

Edit `list.csv` in Excel, Google Sheets, or any text editor:

```csv
url,language,language_code,speakers,category,notes
https://youtube.com/watch?v=...,english,en,2,podcast,Lex Fridman - Guest Name
https://youtube.com/watch?v=...,chinese,zh-Hans,3,interview,Topic description
```

**Columns:**
- `url` - Full YouTube URL
- `language` - english/chinese/indonesian
- `language_code` - en/zh/zh-Hans/zh-TW/id
- `speakers` - Number of speakers (2, 3, 5, 20, etc.)
- `category` - podcast/interview/meeting/documentary/news
- `notes` - Additional context or description

#### Using TXT (Legacy)

Edit `list.txt` with simple format:

```
# English videos
https://youtube.com/watch?v=... -> 2 people
https://youtube.com/watch?v=... -> 3 people (description)

# Chinese videos (zh)
https://youtube.com/watch?v=... -> podcast (2 people) zh-Hans
```

## 📋 Output Format

### Directory Structure

Videos are automatically organized:
- `language/tr/video_N/` - Has manual transcripts
- `language/no_tr/video_N/` - Auto-generated or no transcripts

### Files Per Video

Each video folder contains:

**1. Media File**
- `video.mp4` - Highest quality video (bestvideo+bestaudio)
- `audio.mp3` - Best quality audio (320kbps equivalent)

**2. Transcript Files**

`transcript.json` - Structured format:
```json
[
  {
    "text": "Hello world",
    "start": 5.123,
    "end": 6.456,
    "words": [
      {"text": "Hello", "start": 5.123, "end": 5.789},
      {"text": "world", "start": 5.8, "end": 6.456}
    ]
  }
]
```

`transcript.txt` - Human-readable:
```
[00:00:05] Hello world
[00:00:07] This is a transcript example
```

**3. Metadata File**

`video_details.txt`:
```
============================================================
VIDEO DETAILS
============================================================

Title: Video Title Here
Channel: Channel Name
Channel ID: UC...
Video ID: abc123
URL: https://youtube.com/watch?v=abc123
Upload Date: 20240101
Duration: 3600 seconds
View Count: 1,234,567
Like Count: 12,345

============================================================
DESCRIPTION
============================================================

Full video description here...
```

## 🛠️ Advanced Usage

### Resume Interrupted Downloads

Progress is automatically saved to `download_progress.json`. To resume:

```bash
# Just run the exact same command again
python3 batch_download.py --input list.csv --media-type video --workers 3
```

Already completed videos are automatically skipped.

### Filter by Category (Manual)

Using CSV format, you can manually filter:

```bash
# Create a filtered CSV
grep "podcast" list.csv > podcasts_only.csv

# Download only podcasts
python3 batch_download.py --input podcasts_only.csv --media-type audio --workers 5
```

### Custom Output Folder

Download datasets to specific locations:

```bash
# Download to external drive
python3 batch_download.py --input list.csv --media-type video --output /Volumes/ExternalDrive/datasets

# Organize by project
python3 batch_download.py --input list_projectA.csv --output ./datasets/projectA
python3 batch_download.py --input list_projectB.csv --output ./datasets/projectB

# Download to network storage
python3 batch_download.py --input list.csv --output /mnt/nas/datasets/diarization
```

The output folder will be created automatically if it doesn't exist. Language subfolders (`english/`, `chinese/`) are created inside.

### Disable Logging

For cleaner console output without log files:

```bash
# No log file created (console output only)
python3 batch_download.py --input list.csv --media-type video --workers 3 --no-log

# Useful for testing or monitoring in real-time
python3 batch_download.py --input list.csv --dry-run --no-log
```

Note: Progress tracking (`download_progress.json`) still works even with `--no-log`.

### Check Download Logs

All activity is logged with timestamps (when logging is enabled):

```bash
# View latest log
ls -lt download_log_*.txt | head -1 | xargs cat

# Monitor ongoing download
tail -f download_log_*.txt
```

## 🔧 Troubleshooting

### yt-dlp Not Found

```bash
# macOS
brew install yt-dlp

# Linux
pip install yt-dlp

# Update to latest
brew upgrade yt-dlp
# or
pip install -U yt-dlp
```

### HTTP 403 Forbidden Errors

YouTube occasionally blocks downloads. Solutions:

1. **Update yt-dlp** (most common fix):
```bash
brew upgrade yt-dlp
# or
pip install -U yt-dlp
```

2. **Use video mode** instead of audio (often more stable)

3. **Reduce workers** to avoid rate limiting:
```bash
python3 batch_download.py --workers 2
```

### Download Fails with Timeout

Increase timeout in `batch_download.py` line 153:
```python
timeout=1800  # Change to 3600 for 1 hour
```

### No Transcripts Available

Some videos don't have transcripts. The script:
- ✅ Tries manual transcripts first
- ✅ Falls back to auto-generated
- ✅ Still downloads video/audio if no transcripts exist
- ✅ Organizes into `no_tr/` folder

### Resume Not Working

If `download_progress.json` is corrupted:

```bash
# Remove progress file to start fresh
rm download_progress.json

# Or manually edit the JSON to remove problematic URLs
nano download_progress.json
```

## 📊 Dataset Statistics

After downloading, check your dataset:

```bash
# Count videos by type
find english/tr -name "*.mp4" | wc -l     # English with manual transcripts
find english/no_tr -name "*.mp4" | wc -l  # English with auto transcripts
find chinese/tr -name "*.mp4" | wc -l     # Chinese with manual transcripts

# Calculate total size
du -sh english/ chinese/

# Count total transcripts
find . -name "transcript.json" | wc -l
```

## 🤝 Contributing

### Adding New Videos

1. **Edit list.csv**:
```csv
https://youtube.com/watch?v=NEW_ID,english,en,2,podcast,Description
```

2. **Test with dry run**:
```bash
python3 batch_download.py --dry-run
```

3. **Download**:
```bash
python3 batch_download.py --media-type video --workers 3
```

### Suggesting Improvements

Feel free to enhance:
- Add more language support
- Improve transcript parsing
- Add filtering options
- Create dataset analysis tools

## 📝 Notes

### Language Support

Currently optimized for:
- ✅ English (en, en-US, en-GB)
- ✅ Chinese Simplified (zh, zh-Hans, zh-CN)
- ✅ Chinese Traditional (zh-Hant, zh-TW, zh-HK)

Easy to add more languages by modifying `download_yt.py` line 260.

### Transcript Quality

- **Manual transcripts** (`tr/` folder): High accuracy, professionally created
- **Auto-generated** (`no_tr/` folder): Good accuracy, may have errors
- **Word-level timestamps**: Available for most auto-generated transcripts

## 📄 License

This is a data collection tool. Respect YouTube's Terms of Service and copyright laws:
- Only download content you have rights to use
- Respect creators' copyright
- Use for research/educational purposes
- Don't redistribute downloaded content without permission

## 🔗 Related Tools

- **yt-dlp**: https://github.com/yt-dlp/yt-dlp
- **YouTube Data API**: For metadata and search
- **Whisper**: For improved transcription (OpenAI)
- **PyAnnote**: For speaker diarization

## 📧 Support

For issues or questions:
1. Check the Troubleshooting section
2. Review download logs in `download_log_*.txt`
3. Ensure yt-dlp is up to date
4. Test with `--dry-run` first

---

Last Updated: November 2025