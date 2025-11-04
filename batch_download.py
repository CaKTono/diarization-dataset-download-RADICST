#!/usr/bin/env python3
"""
Batch YouTube Video/Audio Downloader
Downloads multiple videos from a list with parallel processing and progress tracking.

Usage:
    python batch_download.py --input list.csv --media-type video --workers 3
    python batch_download.py --input list.txt --media-type audio --workers 5

Features:
    - Auto-detects CSV or TXT format
    - Parallel downloads (configurable workers)
    - Progress tracking and resume capability
    - Automatic language detection
    - Error handling and logging
    - Dry-run mode for testing
"""

import subprocess
import sys
import re
import json
import os
import argparse
import csv
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import time

class BatchDownloader:
    def __init__(self, input_file, media_type='audio', workers=3, dry_run=False):
        self.input_file = input_file
        self.media_type = media_type
        self.workers = workers
        self.dry_run = dry_run
        self.progress_file = 'download_progress.json'
        self.log_file = f'download_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        self.completed = self.load_progress()

    def log(self, message, also_print=True):
        """Log message to file and optionally print to console"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {message}"

        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_msg + '\n')

        if also_print:
            print(message)

    def load_progress(self):
        """Load previously completed downloads"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r') as f:
                    return set(json.load(f))
            except:
                return set()
        return set()

    def save_progress(self, url):
        """Save completed download to progress file"""
        self.completed.add(url)
        with open(self.progress_file, 'w') as f:
            json.dump(list(self.completed), f, indent=2)

    def parse_csv_file(self):
        """Parse CSV file and extract video information"""
        videos = []

        with open(self.input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                url = row['url'].strip()
                language = row['language'].strip()
                lang_code = row['language_code'].strip()
                speakers = row['speakers'].strip()
                category = row['category'].strip()
                notes = row['notes'].strip()

                # Determine output directory
                if language == 'english':
                    output_dir = './english'
                elif language == 'chinese':
                    output_dir = './chinese'
                elif language == 'indonesian' or language == 'indo':
                    output_dir = './indo'
                else:
                    output_dir = f'./{language}'

                # Create metadata string
                metadata_parts = []
                if speakers:
                    metadata_parts.append(f"{speakers} speakers")
                if category:
                    metadata_parts.append(category)
                if notes:
                    metadata_parts.append(notes)

                metadata = ', '.join(metadata_parts) if metadata_parts else 'Unknown'

                videos.append({
                    'url': url,
                    'language': lang_code,
                    'output_dir': output_dir,
                    'metadata': metadata,
                    'category': category,
                    'speakers': speakers
                })

        return videos

    def parse_txt_file(self):
        """Parse TXT file and extract video information"""
        videos = []

        with open(self.input_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split by language sections
        english_match = re.search(r'Youtube link:(.*?)# chinese', content, re.DOTALL)
        chinese_match = re.search(r'# chinese \(zh\)(.*?)(?:python download_yt\.py|$)', content, re.DOTALL)

        # Parse English videos
        if english_match:
            english_section = english_match.group(1)
            for line in english_section.split('\n'):
                url_match = re.search(r'(https://[^\s]+)', line)
                if url_match:
                    url = url_match.group(1)
                    # Extract metadata from comment
                    metadata = line.split('->')[1].strip() if '->' in line else 'Unknown'
                    videos.append({
                        'url': url,
                        'language': 'en',
                        'output_dir': './english',
                        'metadata': metadata
                    })

        # Parse Chinese videos
        if chinese_match:
            chinese_section = chinese_match.group(1)
            for line in chinese_section.split('\n'):
                url_match = re.search(r'(https://[^\s]+)', line)
                if url_match:
                    url = url_match.group(1)
                    # Try to detect language code from comment
                    lang_code = 'zh'
                    if 'zh-Hans' in line:
                        lang_code = 'zh-Hans'
                    elif 'zh-TW' in line:
                        lang_code = 'zh-TW'

                    metadata = line.split('->')[1].strip() if '->' in line else 'Unknown'
                    videos.append({
                        'url': url,
                        'language': lang_code,
                        'output_dir': './chinese',
                        'metadata': metadata
                    })

        return videos

    def parse_input_file(self):
        """Parse input file (auto-detect CSV or TXT format)"""
        file_ext = os.path.splitext(self.input_file)[1].lower()

        if file_ext == '.csv':
            self.log(f"📄 Parsing CSV file: {self.input_file}")
            return self.parse_csv_file()
        else:
            self.log(f"📄 Parsing TXT file: {self.input_file}")
            return self.parse_txt_file()

    def download_video(self, video_info):
        """Download a single video using the main download script"""
        url = video_info['url']
        lang = video_info['language']
        output_dir = video_info['output_dir']
        metadata = video_info['metadata']

        # Skip if already completed
        if url in self.completed:
            self.log(f"⏭️  Skipping (already completed): {url}")
            return {'status': 'skipped', 'url': url, 'metadata': metadata}

        self.log(f"📥 Starting download: {url} ({metadata})")

        if self.dry_run:
            self.log(f"   [DRY RUN] Would download: {url} to {output_dir} as {self.media_type}")
            time.sleep(0.5)  # Simulate work
            return {'status': 'dry_run', 'url': url, 'metadata': metadata}

        try:
            # Call the main download script
            cmd = [
                'python3',
                'download_yt.py',
                url,
                output_dir,
                lang,
                self.media_type
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minute timeout per video
            )

            if result.returncode == 0:
                self.save_progress(url)
                self.log(f"✅ Success: {url} ({metadata})")
                return {'status': 'success', 'url': url, 'metadata': metadata}
            else:
                error_msg = result.stderr[-500:] if result.stderr else 'Unknown error'
                self.log(f"❌ Failed: {url} - {error_msg}")
                return {'status': 'failed', 'url': url, 'metadata': metadata, 'error': error_msg}

        except subprocess.TimeoutExpired:
            self.log(f"⏱️  Timeout: {url} (exceeded 30 minutes)")
            return {'status': 'timeout', 'url': url, 'metadata': metadata}
        except Exception as e:
            self.log(f"❌ Error: {url} - {str(e)}")
            return {'status': 'error', 'url': url, 'metadata': metadata, 'error': str(e)}

    def run(self):
        """Run batch download with parallel processing"""
        self.log("=" * 80)
        self.log("🚀 Starting Batch Download")
        self.log(f"   Input file: {self.input_file}")
        self.log(f"   Media type: {self.media_type}")
        self.log(f"   Workers: {self.workers}")
        self.log(f"   Dry run: {self.dry_run}")
        self.log("=" * 80)

        # Parse input file
        videos = self.parse_input_file()
        total = len(videos)
        already_completed = len([v for v in videos if v['url'] in self.completed])
        to_download = total - already_completed

        self.log(f"\n📊 Statistics:")
        self.log(f"   Total videos: {total}")
        self.log(f"   Already completed: {already_completed}")
        self.log(f"   To download: {to_download}")
        self.log("")

        if to_download == 0:
            self.log("✅ All videos already downloaded!")
            return

        # Download with parallel workers
        results = {
            'success': [],
            'failed': [],
            'skipped': [],
            'timeout': [],
            'error': [],
            'dry_run': []
        }

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            # Submit all jobs
            future_to_video = {
                executor.submit(self.download_video, video): video
                for video in videos
            }

            # Process completed downloads
            completed_count = 0
            for future in as_completed(future_to_video):
                result = future.result()
                status = result['status']
                results[status].append(result)

                completed_count += 1
                progress = (completed_count / total) * 100
                self.log(f"\n📈 Progress: {completed_count}/{total} ({progress:.1f}%)")

        # Final summary
        elapsed_time = time.time() - start_time
        self.log("\n" + "=" * 80)
        self.log("📋 FINAL SUMMARY")
        self.log("=" * 80)
        self.log(f"✅ Successful: {len(results['success'])}")
        self.log(f"❌ Failed: {len(results['failed'])}")
        self.log(f"⏭️  Skipped: {len(results['skipped'])}")
        self.log(f"⏱️  Timeout: {len(results['timeout'])}")
        self.log(f"❌ Error: {len(results['error'])}")
        if self.dry_run:
            self.log(f"🧪 Dry run: {len(results['dry_run'])}")
        self.log(f"\n⏱️  Total time: {elapsed_time:.1f} seconds ({elapsed_time/60:.1f} minutes)")
        self.log(f"📄 Log file: {self.log_file}")
        self.log("=" * 80)

        # Show failed videos for retry
        if results['failed'] or results['error'] or results['timeout']:
            self.log("\n⚠️  Failed/Error/Timeout videos:")
            for result in results['failed'] + results['error'] + results['timeout']:
                self.log(f"   - {result['url']} ({result['metadata']})")
                if 'error' in result:
                    self.log(f"     Error: {result['error'][:100]}")

def main():
    parser = argparse.ArgumentParser(
        description='Batch download YouTube videos/audio with parallel processing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use CSV file (recommended) - download all as video with 3 workers
  python batch_download.py --input list.csv --media-type video --workers 3

  # Use TXT file - download all as audio with 5 workers
  python batch_download.py --input list.txt --media-type audio --workers 5

  # Dry run to test without downloading (auto-detects format)
  python batch_download.py --input list.csv --dry-run

  # Resume interrupted downloads (just run the same command again)
  python batch_download.py --input list.csv --media-type video --workers 3
        """
    )

    parser.add_argument(
        '--input',
        default='list.csv',
        help='Input file with YouTube URLs - CSV or TXT format (default: list.csv)'
    )

    parser.add_argument(
        '--media-type',
        choices=['audio', 'video'],
        default='audio',
        help='Download as audio or video (default: audio)'
    )

    parser.add_argument(
        '--workers',
        type=int,
        default=3,
        help='Number of parallel downloads (default: 3, recommended: 2-5)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Test run without actually downloading'
    )

    args = parser.parse_args()

    # Validate input file exists
    if not os.path.exists(args.input):
        print(f"❌ Error: Input file '{args.input}' not found")
        sys.exit(1)

    # Validate download script exists
    if not os.path.exists('download_yt.py'):
        print("❌ Error: download_yt.py not found in current directory")
        sys.exit(1)

    # Create and run downloader
    downloader = BatchDownloader(
        input_file=args.input,
        media_type=args.media_type,
        workers=args.workers,
        dry_run=args.dry_run
    )

    try:
        downloader.run()
    except KeyboardInterrupt:
        print("\n\n⚠️  Download interrupted by user")
        print(f"Progress saved to {downloader.progress_file}")
        print("Run the same command again to resume")
        sys.exit(0)

if __name__ == "__main__":
    main()
