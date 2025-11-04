#!/usr/bin/env python3
"""
Fix Incomplete Downloads Script
Finds and removes incomplete downloads from progress tracker,
allowing them to be re-downloaded.
"""

import os
import json
import shutil

def find_incomplete_downloads():
    """Find folders with .part files or missing video/audio files"""
    incomplete = []

    # Search in english and chinese folders
    search_dirs = ['english', 'chinese', 'indo']

    for search_dir in search_dirs:
        if not os.path.exists(search_dir):
            continue

        for root, dirs, files in os.walk(search_dir):
            # Check if this is a video_N folder
            if os.path.basename(root).startswith('video_'):
                # Check for .part files (incomplete downloads)
                part_files = [f for f in files if f.endswith('.part')]

                # Check for completed video/audio files
                video_files = [f for f in files
                              if (f.startswith('video_') or f == 'video.mp4')
                              and f.endswith('.mp4')
                              and not f.endswith('.part')]

                audio_files = [f for f in files
                              if (f.startswith('audio_') or f == 'audio.mp3')
                              and f.endswith('.mp3')
                              and not f.endswith('.part')]

                # If has .part files OR no completed media files
                if part_files or (not video_files and not audio_files):
                    # Try to find URL from video_details.txt
                    details_file = os.path.join(root, 'video_details.txt')
                    url = None
                    if os.path.exists(details_file):
                        with open(details_file, 'r') as f:
                            for line in f:
                                if line.startswith('URL:'):
                                    url = line.split('URL:')[1].strip()
                                    break

                    incomplete.append({
                        'folder': root,
                        'url': url,
                        'part_files': part_files,
                        'has_video': bool(video_files),
                        'has_audio': bool(audio_files)
                    })

    return incomplete

def fix_progress_file(urls_to_remove):
    """Remove URLs from progress tracker"""
    progress_file = 'download_progress.json'

    if not os.path.exists(progress_file):
        print("❌ No download_progress.json found")
        return False

    # Load current progress
    with open(progress_file, 'r') as f:
        completed = json.load(f)

    # Backup original
    backup_file = 'download_progress_backup.json'
    with open(backup_file, 'w') as f:
        json.dump(completed, f, indent=2)
    print(f"✅ Backed up progress to: {backup_file}")

    # Remove incomplete URLs
    original_count = len(completed)
    completed = [url for url in completed if url not in urls_to_remove]
    removed_count = original_count - len(completed)

    # Save updated progress
    with open(progress_file, 'w') as f:
        json.dump(completed, f, indent=2)

    print(f"✅ Removed {removed_count} URLs from progress tracker")
    return True

def main():
    print("=" * 80)
    print("🔍 Scanning for Incomplete Downloads")
    print("=" * 80)

    # Find incomplete downloads
    incomplete = find_incomplete_downloads()

    if not incomplete:
        print("\n✅ No incomplete downloads found! All videos are complete.")
        return

    print(f"\n⚠️  Found {len(incomplete)} incomplete download(s):\n")

    for item in incomplete:
        print(f"📁 Folder: {item['folder']}")
        if item['url']:
            print(f"   URL: {item['url']}")
        if item['part_files']:
            print(f"   ⚠️  Partial files: {', '.join(item['part_files'])}")
        print(f"   Has video: {item['has_video']}")
        print(f"   Has audio: {item['has_audio']}")
        print()

    # Ask for confirmation
    response = input("Do you want to clean up these incomplete downloads? (yes/no): ").strip().lower()

    if response not in ['yes', 'y']:
        print("\n❌ Cleanup cancelled")
        return

    print("\n🧹 Starting cleanup...")

    # Collect URLs to remove from progress
    urls_to_remove = [item['url'] for item in incomplete if item['url']]

    # Remove folders
    for item in incomplete:
        try:
            shutil.rmtree(item['folder'])
            print(f"✅ Removed: {item['folder']}")
        except Exception as e:
            print(f"❌ Error removing {item['folder']}: {e}")

    # Fix progress file
    if urls_to_remove:
        fix_progress_file(urls_to_remove)

    print("\n" + "=" * 80)
    print("✅ CLEANUP COMPLETE")
    print("=" * 80)
    print("\nYou can now re-run the batch download:")
    print("  python3 batch_download.py --input list.csv --media-type video --workers 3")
    print("\nThe incomplete videos will be downloaded again.")

if __name__ == "__main__":
    main()