#!/usr/bin/env python3
import os
import sys
from groq import Groq

def main(audio_path):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("GROQ_API_KEY missing. Set environment variable and retry.")
        return

    client = Groq(api_key=api_key)

    if not os.path.exists(audio_path):
        print("Audio file not found:", audio_path)
        return

    with open(audio_path, "rb") as f:
        filename = os.path.basename(audio_path)
        try:
            transcription = client.audio.transcriptions.create(
                file=(filename, f.read()),
                model="whisper-large-v3",
                temperature=0,
                response_format="verbose_json",
                # language can be set as a hint, e.g. language="ta"
            )
        except Exception as e:
            print("Transcription request failed:", repr(e))
            return

    # Inspect full response if verbose_json
    print("Full transcription object:", transcription)
    # Print the most useful fields
    print("Text:", getattr(transcription, "text", None))
    print("Detected language:", getattr(transcription, "language", None))
    print("Confidence:", getattr(transcription, "confidence", None))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python transcribe_test.py /path/to/audio.m4a")
    else:
        main(sys.argv[1])
