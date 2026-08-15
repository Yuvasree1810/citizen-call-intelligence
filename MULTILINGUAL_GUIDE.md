# Multilingual Support Implementation Guide

## Overview

Your complaint platform now has **production-grade multilingual support** using Groq's Whisper and Chat APIs. The system:

1. **Preserves Native Language** — Transcribes audio in its original language
2. **Auto-Detects Language** — Uses Whisper's detection or user selection
3. **Smart Translation** — Auto-translates non-English to English using Groq Chat
4. **Bidirectional** — Can translate between any supported languages

### Supported Languages
- **English (en)** — English
- **Tamil (ta)** — தமிழ்
- **Telugu (te)** — తెలుగు
- **Hindi (hi)** — हिन्दी
- **Malayalam (ml)** — മലയാളം

---

## Architecture

```
Audio Recording (Any Language)
    ↓
[Backend] Whisper Transcription (Preserves original language)
    ↓
[Backend] Language Detection + Auto-Translation to English
    ↓
Frontend receives:
  - text: Native transcription
  - translatedText: English version
  - detectedLanguage: Detected language code
  - confidence: Transcription confidence (0-1)
    ↓
Complaint Intelligence Service
    ↓
Classification, Priority, Sentiment, Department Routing
```

---

## API Endpoints

### POST /api/transcribe

**Request:**
```json
{
  "audio": Blob,           // Audio file
  "language": "ta"         // Optional: language hint (en, ta, te, hi, ml)
}
```

**Response:**
```json
{
  "success": true,
  "text": "குப்பை இன்று வசூல் செய்யவில்லை",  // Original language
  "translatedText": "Garbage was not collected today",  // English translation
  "detectedLanguage": "ta",                              // Detected: Tamil
  "confidence": 0.98                                     // Confidence score
}
```

### POST /api/translate

**Request:**
```json
{
  "text": "Garbage was not collected",
  "sourceLanguage": "en",
  "targetLanguage": "ta"
}
```

**Response:**
```json
{
  "success": true,
  "translatedText": "குப்பை வசூல் செய்யவில்லை",
  "sourceLanguage": "en",
  "targetLanguage": "ta"
}
```

---

## Frontend Usage

### Basic Speech-to-Text with Translation

```typescript
import { speechToTextService } from "./services/speechToTextService";
import { translationService } from "./services/translationService";

// Record audio and transcribe
async function recordComplaint(audioBlob: Blob, language: LanguageCode) {
  try {
    // Transcribe with automatic translation
    const result = await speechToTextService.transcribe(audioBlob, language);
    
    // result.text = Original language transcription
    // result.translatedText = English translation (auto-generated)
    // result.detectedLanguage = Detected language (en, ta, te, hi, ml)
    // result.confidence = Confidence score (0-1)
    
    console.log("Native:", result.text);
    console.log("English:", result.translatedText);
    console.log("Detected:", result.detectedLanguage);
    
    return result;
  } catch (error) {
    console.error("Transcription failed:", error.message);
  }
}
```

### Translate Complaint to Citizen's Preferred Language

```typescript
// Send confirmation/resolution in citizen's language
async function sendCitizenUpdate(
  complaintSummary: string,
  citizenLanguage: LanguageCode
) {
  try {
    const translation = await translationService.translate(
      complaintSummary,
      "en",  // System stores summaries in English
      citizenLanguage  // Translate to citizen's language
    );
    
    // Send notification in citizen's language
    console.log(translation.translatedText);
    
  } catch (error) {
    console.error("Translation failed:", error);
  }
}
```

### Complete Complaint Flow

```typescript
export async function submitComplaint(
  audioBlob: Blob,
  userLanguage: LanguageCode,
  imageUrl?: string
) {
  try {
    // Step 1: Transcribe and translate
    const speechResult = await speechToTextService.transcribe(
      audioBlob,
      userLanguage
    );
    
    // Step 2: Analyze complaint using translated text
    const intelligenceResult = await complaintIntelligenceService.analyze({
      language: speechResult.detectedLanguage,
      transcription: speechResult.text,  // Native transcription
      complaintText: speechResult.translatedText,  // English for processing
      imageUrl,
      location: userLocation,
    });
    
    // Step 3: Store both versions in database
    const complaint: CitizenComplaint = {
      language: speechResult.detectedLanguage,
      transcription: speechResult.text,  // Preserve original
      translatedText: speechResult.translatedText,  // For processing
      complaintText: intelligenceResult.summary,
      category: intelligenceResult.category,
      priority: intelligenceResult.priority,
      sentiment: intelligenceResult.sentiment,
      recommendedDepartment: intelligenceResult.recommendedDepartment,
      // ... other fields
    };
    
    // Step 4: Save complaint
    await complaintRepository.create(complaint);
    
    // Step 5: Send acknowledgment in citizen's language
    if (complaint.language !== "en") {
      const ackMessage = "Your complaint has been received and registered";
      const localizedAck = await translationService.translate(
        ackMessage,
        "en",
        complaint.language
      );
      console.log("Sending to citizen:", localizedAck.translatedText);
    }
    
    return complaint;
    
  } catch (error) {
    console.error("Complaint submission failed:", error);
    throw error;
  }
}
```

---

## Real-World Use Cases

### Use Case 1: Tamil-Speaking Citizen Reports Pothole

```
1. Citizen records: "வியத்ததே, சாலையில் பெரிய குழி உள்ளது"
   (Translation: "That pothole on the street is very big")

2. Whisper detects language as Tamil (ta)

3. Transcription:
   - Native: "வியத்ததே, சாலையில் பெரிய குழி உள்ளது"
   - English: "That pothole on the street is very big"

4. Intelligence service classifies as:
   - Category: Roads
   - Priority: MEDIUM
   - Sentiment: NEGATIVE

5. System sends acknowledgment:
   - EN: "Your complaint has been received"
   - TA: "உங்கள் புகார் பதிவு செய்யப்பட்டுள்ளது"

6. Department receives complaint in English for processing
```

### Use Case 2: Hindi-Speaking Citizen Gets Resolution Update

```
1. Citizen's original complaint (stored in DB):
   - Language: hindi
   - Transcription: "हमारे गली में तीन दिन से बिजली नहीं आ रही है"
   - Translated: "Electricity has not been available in our street for 3 days"

2. Department resolves and writes (in English):
   "Power restoration completed. New transformer installed and tested."

3. System translates resolution to Hindi:
   "बिजली की बहाली पूरी हुई। नया ट्रांसफॉर्मर स्थापित और परीक्षित किया गया।"

4. System sends notification in Hindi to citizen
```

### Use Case 3: Cross-Language Communication

```
// Department in Bangalore (English) sends update
const resolutionEnglish = "Garbage collection scheduled for tomorrow morning";

// System translates to Tamil for TN citizen
const resolutionTamil = await translationService.translate(
  resolutionEnglish,
  "en",
  "ta"
);
// Output: "நாளை காலை குப்பை சேகரணை திட்டமிடப்பட்டுள்ளது"
```

---

## Backend Integration (Node.js/Express)

### Environment Setup

Ensure your `.env` has:
```
GROQ_API_KEY=gsk_xxxxxxxxxxxxx
```

### Server Configuration

The backend (`server.js`) now provides:

1. **Smart Transcription**
   - Uses `audio.transcriptions.create()` (preserves language)
   - Auto-detects language
   - Returns confidence score

2. **Auto-Translation**
   - Non-English transcriptions → English
   - Uses Groq's mixtral-8x7b model
   - Optimized for complaint documentation

3. **Translation API**
   - Translate between any supported languages
   - Bidirectional (any language ↔ any language)
   - Professional-grade accuracy

### Key Changes from Previous Version

| Feature | Before | After |
|---------|--------|-------|
| **Transcription** | `translations.create()` (always English) | `transcriptions.create()` (native language) |
| **Language Detection** | No detection | Auto-detects language |
| **Original Text** | Lost | Preserved |
| **Translation** | Only Whisper's fixed English | Real translation API |
| **Confidence** | Hardcoded 0.95 | From Whisper's verbose_json |

---

## Error Handling

### Transcription Errors

```typescript
try {
  const result = await speechToTextService.transcribe(audioBlob, "ta");
} catch (error) {
  if ((error as any).notConfigured) {
    console.error("GROQ_API_KEY not configured in server");
  } else {
    console.error("Transcription failed:", error.message);
  }
}
```

### Translation Errors

The system has graceful fallback:
```typescript
// If translation fails, returns original text
const translation = await translationService.translate(text, "en", "ta");
// translation.translatedText = original text if API fails
```

---

## Performance Tips

1. **Language Hint** — If you know the language, pass it to reduce detection time
2. **Batch Translations** — Translate multiple complaints in parallel
3. **Caching** — Store previously translated summaries to reduce API calls
4. **Async Processing** — Translate to citizen's language asynchronously after initial filing

---

## Testing

### Test Different Languages

```typescript
// Tamil
await speechToTextService.transcribe(tamilAudio, "ta");

// Telugu
await speechToTextService.transcribe(teluguAudio, "te");

// Hindi
await speechToTextService.transcribe(hindiAudio, "hi");

// Malayalam
await speechToTextService.transcribe(malayalamAudio, "ml");

// English
await speechToTextService.transcribe(englishAudio, "en");
```

### Verify Translation Quality

```typescript
const testPhrases = {
  ta: "சாலையில் பெரிய குழி உள்ளது",
  te: "చెత్త సంগ్రహ కూడా చేయబడలేదు",
  hi: "बिजली तीन दिन से नहीं आ रही है",
  ml: "വെള്ളം വിതരണം ഭാരം കുറഞ്ഞിരിക്കുന്നു",
};

for (const [lang, phrase] of Object.entries(testPhrases)) {
  const result = await translationService.translate(phrase, lang as LanguageCode, "en");
  console.log(`${lang}: ${result.translatedText}`);
}
```

---

## Production Checklist

- [ ] GROQ_API_KEY configured in server environment
- [ ] Backend server running (`npm run dev:backend`)
- [ ] Frontend connects to `/api/transcribe` endpoint
- [ ] Test transcription in each language
- [ ] Test translation quality with sample complaints
- [ ] Verify confidence scores are returned
- [ ] Error handling displays user-friendly messages
- [ ] Database stores both native and translated text
- [ ] Acknowledgments sent in citizen's language
- [ ] Resolution updates translated for citizen

---

## Troubleshooting

### "Voice service not configured" error
→ Check `GROQ_API_KEY` is set in `.env` and server restarted

### Translation returns empty
→ Check text is not empty, language codes are valid

### Wrong language detected
→ Pass language hint when user selects language explicitly

### Confidence score is low
→ Audio quality issue; ask user to re-record with better audio

---

## Python Reference (External Integration)

If you're building external tools or bots:

```python
from groq import Groq
import os

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Transcribe preserving language
def transcribe_native(audio_path, language_hint=None):
    with open(audio_path, "rb") as file:
        transcription = client.audio.transcriptions.create(
            file=(os.path.basename(audio_path), file.read()),
            model="whisper-large-v3",
            temperature=0,
            response_format="verbose_json",
            language=language_hint,  # Optional hint
        )
        return {
            "text": transcription.text,
            "language": transcription.language,
            "confidence": getattr(transcription, "confidence", 0.95),
        }

# Translate using Chat API
def translate_text(text, source_lang, target_lang):
    completion = client.chat.completions.create(
        model="mixtral-8x7b-32768",
        messages=[
            {
                "role": "system",
                "content": "You are a professional translator. Translate accurately preserving meaning and tone.",
            },
            {
                "role": "user",
                "content": f"Translate from {source_lang} to {target_lang}:\n{text}",
            },
        ],
        temperature=0.3,
        max_tokens=1024,
    )
    return completion.choices[0].message.content.strip()

# Example usage
if __name__ == "__main__":
    # Transcribe Tamil complaint
    result = transcribe_native("complaint_tamil.m4a", language_hint="ta")
    print(f"Native: {result['text']}")
    
    # Translate to English
    english = translate_text(result['text'], "ta", "en")
    print(f"English: {english}")
```

---

## Advanced: Custom Language Support

To add more languages (e.g., Kannada, Marathi):

1. **Update `types/index.ts`:**
   ```typescript
   export type LanguageCode = "en" | "ta" | "te" | "hi" | "ml" | "kn" | "mr";
   ```

2. **Update `server.js` mapping:**
   ```javascript
   const langMap = {
     en: "en", ta: "ta", te: "te", hi: "hi", ml: "ml",
     kn: "kn",  // Kannada
     mr: "mr",  // Marathi
   };
   ```

3. **Update language selector UI** and test transcription

---

## Support & Debugging

Enable detailed logging:
```typescript
// In frontend
localStorage.setItem("debug:multilingual", "true");

// In server.js
if (process.env.DEBUG) {
  console.log("[Transcription]", { language, confidence, textLength });
}
```

Check backend logs: `npm run dev:backend`
