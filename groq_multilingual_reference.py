#!/usr/bin/env python3
"""
Groq Multilingual Transcription & Translation Reference

This script demonstrates the enhanced multilingual capabilities using Groq's
Whisper Large V3 and Chat API, with strong real-world use cases for 
complaint management systems supporting Indian regional languages.

Usage:
    python groq_multilingual_reference.py --audio audio.m4a --language ta

Supported Languages:
    - en: English
    - ta: Tamil (தமிழ்)
    - te: Telugu (తెలుగు)
    - hi: Hindi (हिन्दी)
    - ml: Malayalam (മലയാളം)
"""

import os
import sys
from groq import Groq
from typing import Optional, Dict, Any

# Initialize Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


# ============================================================
# 1. NATIVE LANGUAGE TRANSCRIPTION
# ============================================================
def transcribe_native(
    audio_path: str,
    language_hint: Optional[str] = None,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Transcribe audio preserving the NATIVE language.
    
    This differs from audio.translations which always returns English.
    We use audio.transcriptions to preserve the original language while
    capturing all nuance and context of the complaint.
    
    Args:
        audio_path: Path to audio file (mp4, m4a, wav, mp3, webm)
        language_hint: Optional language code (en, ta, te, hi, ml) for faster detection
        verbose: Print detailed output
    
    Returns:
        {
            "text": "Original language transcription",
            "language": "ta",
            "confidence": 0.97,
            "duration_ms": 8500
        }
    
    Real-world example:
        Tamil citizen reports pothole:
        Audio: "சாலையில் பெரிய குழி உள்ளது"
        Result: Preserves Tamil, detects as 'ta', high confidence
    """
    if verbose:
        print(f"📝 Transcribing {audio_path}...")
        if language_hint:
            print(f"   Language hint: {language_hint}")

    with open(audio_path, "rb") as file:
        # Use transcriptions (not translations) to preserve original language
        transcription = client.audio.transcriptions.create(
            file=(os.path.basename(audio_path), file.read()),
            model="whisper-large-v3",
            temperature=0,  # Deterministic
            response_format="verbose_json",
            language=language_hint,  # Optional: speeds up detection
        )

    result = {
        "text": transcription.text,
        "language": transcription.language or language_hint or "en",
        "confidence": getattr(transcription, "confidence", 0.95),
        "duration_ms": getattr(transcription, "duration", 0),
    }

    if verbose:
        print(f"\n   ✓ Native Language: {result['language']}")
        print(f"   ✓ Confidence: {result['confidence'] * 100:.1f}%")
        print(f"   ✓ Transcription: {result['text'][:100]}...")

    return result


# ============================================================
# 2. SMART TRANSLATION (Any Language → Any Language)
# ============================================================
def translate_text(
    text: str,
    source_language: str,
    target_language: str = "en",
    verbose: bool = True
) -> Dict[str, str]:
    """
    Translate text between supported languages using Groq Chat API.
    
    Optimized for complaint documentation:
    - Preserves technical terms
    - Maintains tone (urgent/critical)
    - Handles regional context
    
    Args:
        text: Text to translate
        source_language: Source language code (ta, te, hi, ml, en)
        target_language: Target language code (default: en)
        verbose: Print output
    
    Returns:
        {"translatedText": "...", "sourceLanguage": "ta", "targetLanguage": "en"}
    
    Real-world examples:
        1. Tamil → English (processing):
           "குப்பை வசூல் செய்யவில்லை" → "Garbage was not collected"
        
        2. English → Tamil (citizen notification):
           "Your complaint has been received" → "உங்கள் புகார் பதிவு செய்யப்பட்டுள்ளது"
        
        3. Hindi → Telugu (cross-region):
           "बिजली आ गई" → "విద్యుత్ వచ్చింది"
    """
    if verbose:
        print(f"🌐 Translating {source_language.upper()} → {target_language.upper()}")

    # If source and target are same, skip translation
    if source_language == target_language:
        return {
            "translatedText": text,
            "sourceLanguage": source_language,
            "targetLanguage": target_language,
        }

    # Map language codes to full names for clarity
    language_names = {
        "en": "English",
        "ta": "Tamil",
        "te": "Telugu",
        "hi": "Hindi",
        "ml": "Malayalam",
    }

    source_name = language_names.get(source_language, source_language)
    target_name = language_names.get(target_language, target_language)

    # Create specialized prompt for complaint translation
    prompt = f"""Translate the following {source_name} complaint text to {target_name}.

IMPORTANT:
- Preserve the meaning exactly
- Keep technical terms (e.g., pothole, transformer, water board)
- Maintain the tone (urgent complaints stay urgent)
- Keep location names unchanged
- Return ONLY the translated text, no explanations

{source_name} text:
{text}"""

    # Use mixtral for high-quality translation
    completion = client.chat.completions.create(
        model="mixtral-8x7b-32768",
        messages=[
            {
                "role": "system",
                "content": (
                    f"You are a professional translator specializing in regional "
                    f"languages and government complaint documentation. Translate "
                    f"accurately while preserving context and urgency."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,  # Low temperature for consistency
        max_tokens=1024,
    )

    translated = completion.choices[0].message.content.strip()

    if verbose:
        print(f"   ✓ Translated")
        print(f"\n   Original ({source_name}):\n   {text}")
        print(f"\n   Translated ({target_name}):\n   {translated}\n")

    return {
        "translatedText": translated,
        "sourceLanguage": source_language,
        "targetLanguage": target_language,
    }


# ============================================================
# 3. LANGUAGE DETECTION (What language is this audio?)
# ============================================================
def detect_language(audio_path: str) -> Dict[str, Any]:
    """
    Detect the language of audio without explicitly setting it.
    
    Whisper automatically detects from audio content.
    Useful when you don't know the language beforehand.
    
    Args:
        audio_path: Path to audio file
    
    Returns:
        {
            "language": "ta",
            "confidence": 0.98,
            "detected_language_name": "Tamil"
        }
    """
    print(f"🔍 Detecting language from {audio_path}...")

    with open(audio_path, "rb") as file:
        # No language hint = Whisper auto-detects
        transcription = client.audio.transcriptions.create(
            file=(os.path.basename(audio_path), file.read()),
            model="whisper-large-v3",
            response_format="verbose_json",
        )

    language_map = {
        "en": "English",
        "ta": "Tamil",
        "te": "Telugu",
        "hi": "Hindi",
        "ml": "Malayalam",
    }

    lang_code = transcription.language or "unknown"
    lang_name = language_map.get(lang_code, "Unknown")

    result = {
        "language": lang_code,
        "confidence": getattr(transcription, "confidence", 0.95),
        "detected_language_name": lang_name,
        "text_preview": transcription.text[:100],
    }

    print(f"✓ Detected: {lang_name} ({lang_code})")
    print(f"✓ Confidence: {result['confidence'] * 100:.1f}%")
    print(f"✓ Preview: {result['text_preview']}...\n")

    return result


# ============================================================
# 4. COMPLETE MULTILINGUAL WORKFLOW
# ============================================================
def process_complaint_multilingual(audio_path: str, language_hint: Optional[str] = None) -> Dict[str, Any]:
    """
    Complete real-world workflow: Record → Detect → Transcribe → Translate → Process
    
    This is the full pipeline for a multilingual complaint management system:
    
    1. Accept audio from citizen in ANY language
    2. Detect/confirm language
    3. Transcribe preserving native language
    4. Auto-translate to English for processing
    5. Store both versions for reference/acknowledgment
    
    Args:
        audio_path: Path to recorded complaint audio
        language_hint: Optional language hint (speeds up processing)
    
    Returns:
        Complete complaint data ready for processing
    
    Real-world scenario:
        
        STEP 1: Tamil-speaking citizen records complaint
        Audio: "வியத்ததே, சாலையில் பெரிய குழி உள்ளது"
        
        STEP 2: System processes
        → Transcribes in Tamil (preserves original)
        → Detects language as Tamil (ta)
        → Translates to English
        → Gets confidence: 0.98
        
        STEP 3: System stores
        {
            "citizen_language": "ta",
            "complaint_text_native": "வியத்ததே, சாலையில் பெரிய குழி உள்ளது",
            "complaint_text_english": "That pothole on the street is very big",
            "confidence": 0.98,
            "category": "Roads",
            "priority": "MEDIUM"
        }
        
        STEP 4: System communicates
        - Acknowledgment to citizen: In Tamil
        - Processing by admin: In English
        - Resolution notification: In Tamil
    """
    print("=" * 70)
    print("🌍 MULTILINGUAL COMPLAINT PROCESSING WORKFLOW")
    print("=" * 70 + "\n")

    # STEP 1: Transcribe in native language
    print("STEP 1️⃣: Transcribing in native language...")
    transcription_result = transcribe_native(audio_path, language_hint)
    native_language = transcription_result["language"]
    native_text = transcription_result["text"]
    confidence = transcription_result["confidence"]

    # STEP 2: If not English, translate to English for processing
    print("\nSTEP 2️⃣: Translating to English for processing...")
    if native_language != "en":
        translation_result = translate_text(native_text, native_language, "en")
        english_text = translation_result["translatedText"]
    else:
        english_text = native_text
        print("   (Already in English, no translation needed)")

    # STEP 3: Would classify here using English text
    print("\nSTEP 3️⃣: Classification (using English text)...")
    print(f"   Would classify as: Roads > Pothole")
    print(f"   Category: Roads")
    print(f"   Priority: MEDIUM")
    print(f"   Sentiment: NEGATIVE")

    # STEP 4: Prepare for citizen notification in their language
    print("\nSTEP 4️⃣: Prepare acknowledgment in citizen's language...")
    if native_language != "en":
        acknowledgment_en = "Your complaint has been received and registered. Your complaint ID is CMP-001."
        ack_translated = translate_text(
            acknowledgment_en,
            "en",
            native_language,
            verbose=False
        )
        print(f"   English: {acknowledgment_en}")
        print(f"   {native_language.upper()}: {ack_translated['translatedText']}")

    # RETURN: Complete complaint data
    result = {
        "citizen_language": native_language,
        "complaint_text_native": native_text,
        "complaint_text_english": english_text,
        "confidence_score": confidence,
        "language_name": {"ta": "Tamil", "te": "Telugu", "hi": "Hindi", "ml": "Malayalam", "en": "English"}.get(
            native_language, "Unknown"
        ),
    }

    print("\n" + "=" * 70)
    print("✅ COMPLAINT PROCESSING COMPLETE")
    print("=" * 70 + "\n")

    return result


# ============================================================
# 5. BATCH PROCESSING: Multiple Complaints
# ============================================================
def batch_process_complaints(audio_files: list) -> list:
    """
    Process multiple complaints efficiently.
    
    Use case: Process overnight complaints, batch translations, etc.
    """
    print(f"📦 Batch processing {len(audio_files)} complaints...\n")

    results = []
    for i, audio_file in enumerate(audio_files, 1):
        print(f"\n--- Complaint {i}/{len(audio_files)} ---")
        if os.path.exists(audio_file):
            result = process_complaint_multilingual(audio_file)
            results.append(result)
        else:
            print(f"⚠️  File not found: {audio_file}")

    return results


# ============================================================
# 6. TRANSCRIPTION + TRANSLATION IN ONE CALL
# ============================================================
def transcribe_and_translate(
    audio_path: str,
    source_language: Optional[str] = None,
    target_language: str = "en"
) -> Dict[str, Any]:
    """
    One-shot: Transcribe audio and immediately translate to target language.
    
    Useful for quick processing without intermediate steps.
    """
    print(f"⚡ Quick transcribe + translate: {audio_path}")

    # Transcribe
    transcript = transcribe_native(audio_path, source_language, verbose=False)
    native_lang = transcript["language"]
    native_text = transcript["text"]

    # Translate if needed
    if native_lang != target_language:
        translation = translate_text(native_text, native_lang, target_language, verbose=False)
        target_text = translation["translatedText"]
    else:
        target_text = native_text

    return {
        "original_language": native_lang,
        "original_text": native_text,
        "target_language": target_language,
        "translated_text": target_text,
        "confidence": transcript["confidence"],
    }


# ============================================================
# 7. TEST SUITE WITH SAMPLE COMPLAINTS
# ============================================================
def demonstrate_all_languages():
    """
    Demonstrate multilingual capabilities with sample text.
    
    This shows how the system handles all supported languages
    without requiring actual audio files.
    """
    sample_complaints = {
        "ta": {
            "text": "சாலையில் பெரிய குழி உள்ளது. வாகனம் சேதமாயிற்று.",
            "english": "There is a large pothole on the street. The vehicle was damaged.",
        },
        "te": {
            "text": "చెత్త సంగ్రహ కూడా చేయబడలేదు. ఒక వారం నుండి.",
            "english": "Garbage has not been collected. It's been a week.",
        },
        "hi": {
            "text": "बिजली तीन दिन से नहीं आ रही है। समस्या बहुत है।",
            "english": "Electricity has not been coming for 3 days. It's very problematic.",
        },
        "ml": {
            "text": "വെള്ളം വിതരണം മുടങ്ങിയിരിക്കുന്നു. രണ്ട് ദിവസം ആയി.",
            "english": "Water supply has stopped. It's been 2 days.",
        },
        "en": {
            "text": "Street light is not working for a week. It's dangerous at night.",
            "english": "Street light is not working for a week. It's dangerous at night.",
        },
    }

    print("\n" + "=" * 70)
    print("🌏 DEMONSTRATING ALL SUPPORTED LANGUAGES")
    print("=" * 70)

    for lang, data in sample_complaints.items():
        print(f"\n{'─' * 70}")
        print(f"Language: {lang.upper()}")
        print(f"{'─' * 70}")
        print(f"Original: {data['text']}")

        # Translate to other languages
        if lang != "en":
            print(f"\nTranslations:")
            print(f"  → English: {data['english']}")

            # Translate to another language for fun
            other_langs = {"ta": "te", "te": "hi", "hi": "ml", "ml": "ta", "en": "ta"}
            target = other_langs[lang]

            result = translate_text(
                data["text"], lang, target, verbose=False
            )
            print(f"  → {target.upper()}: {result['translatedText']}")


# ============================================================
# MAIN: Command-line interface
# ============================================================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Groq Multilingual Transcription & Translation for Complaints"
    )
    parser.add_argument("--audio", help="Path to audio file to transcribe")
    parser.add_argument(
        "--language",
        help="Language hint (en, ta, te, hi, ml)",
        choices=["en", "ta", "te", "hi", "ml"],
    )
    parser.add_argument(
        "--translate",
        help="Target language to translate to",
        default="en",
        choices=["en", "ta", "te", "hi", "ml"],
    )
    parser.add_argument(
        "--detect",
        help="Only detect language from audio",
        action="store_true",
    )
    parser.add_argument(
        "--demo",
        help="Demonstrate all languages",
        action="store_true",
    )

    args = parser.parse_args()

    # Demo mode
    if args.demo:
        demonstrate_all_languages()

    # Detect mode
    elif args.detect and args.audio:
        detect_language(args.audio)

    # Full transcribe + translate
    elif args.audio:
        result = transcribe_and_translate(args.audio, args.language, args.translate)
        print("\n" + "=" * 70)
        print("📋 RESULT")
        print("=" * 70)
        for key, value in result.items():
            print(f"{key}: {value}")

    # No arguments: show usage
    else:
        parser.print_help()
        print("\n" + "=" * 70)
        print("EXAMPLES:")
        print("=" * 70)
        print("\n1. Transcribe Tamil audio:")
        print("   python groq_multilingual_reference.py --audio complaint.m4a --language ta")

        print("\n2. Detect language automatically:")
        print("   python groq_multilingual_reference.py --audio complaint.m4a --detect")

        print("\n3. Transcribe and translate to Tamil:")
        print("   python groq_multilingual_reference.py --audio complaint.m4a --translate ta")

        print("\n4. Demo all languages:")
        print("   python groq_multilingual_reference.py --demo")

        print("\n" + "=" * 70)
