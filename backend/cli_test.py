#!/usr/bin/env python3
"""
CLI Testing Tool for Backend
Usage: python cli_test.py [command] [options]
"""

import sys
import requests
import json
from pathlib import Path

API_BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    response = requests.get(f"{API_BASE_URL}/health")
    print(f"Health: {response.status_code} - {response.json()}")

def list_files():
    """List all processed files"""
    response = requests.get(f"{API_BASE_URL}/api/audio-files")
    if response.status_code == 200:
        files = response.json()["files"]
        print(f"Found {len(files)} processed files:")
        for file in files:
            print(f"  ID {file['id']}: {file['filename']} ({file['duration']:.1f}s)")
    else:
        print(f"Error: {response.status_code}")

def get_file_details(file_id):
    """Get details for specific file"""
    response = requests.get(f"{API_BASE_URL}/api/audio-files/{file_id}")
    if response.status_code == 200:
        file_data = response.json()
        print(f"File: {file_data['filename']}")
        print(f"Duration: {file_data['duration']:.2f}s")
        print(f"WPM: {file_data['wpm']:.1f}")
        print(f"Filler Ratio: {file_data['filler_ratio']:.3f}")
        print(f"Sentiment: {file_data['sentiment_score']:.3f}")
        print(f"Transcript: {file_data['transcript'][:200]}...")
    else:
        print(f"Error: {response.status_code}")

def upload_file(file_path):
    """Upload and process a file"""
    if not Path(file_path).exists():
        print(f"File not found: {file_path}")
        return
    
    with open(file_path, 'rb') as f:
        files = {'file': (Path(file_path).name, f, 'audio/mpeg')}
        response = requests.post(f"{API_BASE_URL}/api/process-audio", files=files)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ File processed successfully!")
        data = result['data']
        print(f"ID: {data['id']}")
        print(f"Duration: {data['duration']:.2f}s")
        print(f"WPM: {data['wpm']:.1f}")
        print(f"Filler Ratio: {data['filler_ratio']:.3f}")
        print(f"Sentiment: {data['sentiment_score']:.3f}")
    else:
        print(f"❌ Error: {response.text}")

def show_help():
    """Show help information"""
    print("""
Backend CLI Testing Tool

Commands:
  health                    - Test health endpoint
  list                     - List all processed files
  details <id>             - Get details for file ID
  upload <file_path>       - Upload and process file
  help                     - Show this help

Examples:
  python cli_test.py health
  python cli_test.py list
  python cli_test.py details 1
  python cli_test.py upload ../audio_files/Script_1.mp3
""")

def main():
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1]
    
    if command == "health":
        test_health()
    elif command == "list":
        list_files()
    elif command == "details" and len(sys.argv) > 2:
        get_file_details(int(sys.argv[2]))
    elif command == "upload" and len(sys.argv) > 2:
        upload_file(sys.argv[2])
    elif command == "help":
        show_help()
    else:
        print("Invalid command. Use 'help' for usage.")
        show_help()

if __name__ == "__main__":
    main() 