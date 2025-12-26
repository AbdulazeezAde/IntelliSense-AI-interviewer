#!/usr/bin/env python3
"""CLI helper to download a small VOSK model into ./models by default."""
import argparse
from app.stt.vosk_helper import download_and_extract_model

parser = argparse.ArgumentParser(description="Download a VOSK model for local STT usage")
parser.add_argument("--url", help="Model zip URL", default=None)
parser.add_argument("--dest", help="Destination directory", default=None)

if __name__ == '__main__':
    args = parser.parse_args()
    url = args.url or None
    dest = args.dest or None
    path = download_and_extract_model(url, dest)
    print("Model extracted to:", path)
