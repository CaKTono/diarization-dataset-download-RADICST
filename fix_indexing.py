#!/usr/bin/env python3
"""
Script to fix indexing in the english/tr directory by renaming folders to have sequential numbering.
Starting from video_1 to video_n with no gaps in the sequence.
"""

import os
import re
from pathlib import Path


def fix_indexing(directory_path, dry_run=True):
    """
    Renames subdirectories in the given directory to have sequential numbering.
    
    Args:
        directory_path (str): Path to the directory containing video folders
        dry_run (bool): If True, only show what would be renamed without making changes
    """
    dir_path = Path(directory_path)
    
    if not dir_path.exists():
        print(f"Directory does not exist: {directory_path}")
        return
    
    # Find all directories that match the pattern "video_XX"
    video_dirs = [d for d in dir_path.iterdir() if d.is_dir() and d.name.startswith("video_")]
    
    # Sort directories by their numeric value (extracted from the name)
    def extract_number(dir_name):
        match = re.search(r'video_(\d+)', dir_name.name)
        return int(match.group(1)) if match else 0
    
    video_dirs.sort(key=extract_number)
    
    print(f"Found {len(video_dirs)} video directories:")
    for i, video_dir in enumerate(video_dirs):
        print(f"  {i+1}. {video_dir.name}")
    
    # Create a mapping of old names to new names
    rename_map = {}
    for idx, video_dir in enumerate(video_dirs, start=1):
        new_name = f"video_{idx}"
        if video_dir.name != new_name:
            rename_map[video_dir] = dir_path / new_name
            print(f"Will rename: {video_dir.name} -> {new_name}")
    
    if not rename_map:
        print("No renaming needed - directories are already sequentially numbered.")
        return
    
    if dry_run:
        print(f"\n(Dry run) Would rename {len(rename_map)} directories.")
        print("To perform the actual renaming, run with dry_run=False")
        return
    
    # For automated execution, skip confirmation
    print(f"Renaming {len(rename_map)} directories...")
    
    # Perform the renaming
    for old_path, new_path in rename_map.items():
        print(f"Renaming {old_path.name} -> {new_path.name}")
        old_path.rename(new_path)
    
    print(f"\nSuccessfully renamed {len(rename_map)} directories.")


if __name__ == "__main__":
    # Default path - you can change this if needed
    target_directory = "/Users/calvin_kristianto/Music/10_Hours_Dataset/english/tr"
    
    print(f"Fixing indexing in: {target_directory}")
    fix_indexing(target_directory, dry_run=False)