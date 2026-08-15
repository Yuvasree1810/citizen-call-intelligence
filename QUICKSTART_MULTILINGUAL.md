# Quick Start: Multilingual Speech-to-Text with Groq

Get your multilingual complaint platform running in 5 minutes.

## Prerequisites

✅ **Already Done:**
- Groq SDK installed (`groq-sdk` in package.json)
- GROQ_API_KEY in `.env` file
- Backend server configured (Express + Groq)

## 1. Start the Application

```bash
# Terminal 1: Backend + Frontend (concurrently)
npm run dev

# OR separately:
# Terminal 1: Backend
npm run dev:backend

# Terminal 2: Frontend
npm run dev:frontend
```

**Expected Output:**
```
[Backend] Groq transcription server running on http://localhost:3001
[Frontend] Vite running at http://localhost:5173
```

## 2. Test Multilingual Speech-to-Text

### In Browser Console (Developer Tools)

```javascript
// Test 1: Transcribe English
const englishAudio = await fetch('/audio/english-sample.wav').then(r => r.blob());
const result = await fetch('/api/transcribe', {
  method: 'POST',
  body: new FormData()
    .append('audio', englishAudio, 'test.wav')
    .append('language', 'en')
}).then(r => r.json());

console.log('Result:', result);
// Output:
// {
//   success: true,
//   text: "There is a pothole on the street",
//   translatedText: "There is a pothole on the street",
//   detectedLanguage: "en",
//   confidence: 0.97
// }
```

### Test All Supported Languages

```javascript
const languages = ['en', 'ta', 'te', 'hi', 'ml'];

async function testLanguage(lang) {
  console.log(`\n🌐 Testing ${lang}...`);
  // Record audio or provide audio blob
  // const audioBlob = ... your audio
  // const result = await speechToTextService.transcribe(audioBlob, lang);
  // console.log(result);
}
```

## 3. Navigate to Complaint Form

1. Open browser: http://localhost:5173
2. Select "Citizen" role
3. Click "File Complaint"
4. Choose language (Tamil, Telugu, Hindi, Malayalam, or English)
5. Click "🎤 Start Recording"
6. Speak in that language
7. Stop recording
8. See transcription in **both native language and English**

## 4. Key Features to Try

### Feature 1: Native Language Preservation
```
1. Select "தமிழ் (Tamil)"
2. Record: "சாலையில் பெரிய குழி உள்ளது"
3. See:
   - Native: "சாலையில் பெரிய குழி உள்ளது"
   - English: "There is a big pothole on the road"
```

### Feature 2: Language Detection
```
Whisper automatically detects if language hint is wrong:
1. Select "Malayalam"
2. Record in Tamil anyway
3. System detects: "ta" (not "ml")
4. Shows confidence: 0.98
```

### Feature 3: Automatic English Translation
```
1. Record complaint in any language
2. Backend auto-translates to English
3. Only English sent to classification/processing
4. Native text stored separately
```

### Feature 4: Real Translation API
```
Direct translation between languages:
POST /api/translate
{
  "text": "சாலையில் பெரிய குழி உள்ளது",
  "sourceLanguage": "ta",
  "targetLanguage": "en"
}
→ "There is a big pothole on the road"
```

## 5. Verify Implementation

### Check Backend API

```bash
# Test transcription endpoint
curl -X POST http://localhost:3001/api/transcribe \
  -F "audio=@audio.m4a" \
  -F "language=ta"

# Response:
# {
#   "success": true,
#   "text": "...",
#   "translatedText": "...",
#   "detectedLanguage": "ta",
#   "confidence": 0.97
# }
```

```bash
# Test translation endpoint
curl -X POST http://localhost:3001/api/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "சாலையில் பெரிய குழி உள்ளது",
    "sourceLanguage": "ta",
    "targetLanguage": "en"
  }'

# Response:
# {
#   "success": true,
#   "translatedText": "There is a big pothole on the road",
#   "sourceLanguage": "ta",
#   "targetLanguage": "en"
# }
```

## 6. Check Database Storage

After submitting a complaint, verify it's stored correctly:

```javascript
// In browser console or backend
const complaint = await complaintRepository.getById('CMP-...');

console.log({
  language: complaint.language,          // "ta"
  transcription: complaint.transcription, // Tamil text
  translatedText: complaint.translatedText, // English text
  confidence: complaint.confidence,      // 0.97
});
```

## 7. Common Issues & Fixes

### Issue: "Voice service not configured"
**Cause:** GROQ_API_KEY missing  
**Fix:**
```bash
# Check .env file
cat .env | grep GROQ_API_KEY

# Should show: GROQ_API_KEY=gsk_...
```

### Issue: Wrong language detected
**Cause:** Poor audio quality or Whisper confusion  
**Fix:** Pass explicit language hint
```javascript
const result = await speechToTextService.transcribe(audioBlob, "ta");
// "ta" hint helps Whisper
```

### Issue: Translation not working
**Cause:** API timeout or network issue  
**Fix:** Check backend logs
```bash
npm run dev:backend
# Look for error messages
```

### Issue: Confidence score seems wrong
**Cause:** Whisper may not return confidence in all cases  
**Fix:** Fallback to 0.95
```typescript
const confidence = result.confidence || 0.95;
```

## 8. Architecture Diagram

```
┌─ Frontend ──────────────────────────────────────┐
│                                                   │
│  1. User records in Tamil                        │
│  2. Sends audio to /api/transcribe              │
│     └─ Body: { audio: Blob, language: "ta" }   │
│                                                   │
└─────────────────────┬───────────────────────────┘
                      │
                      ↓
┌─ Backend (server.js) ─────────────────────────┐
│                                                  │
│  3. Receives audio                             │
│  4. Calls Groq Whisper:                        │
│     audio.transcriptions.create()              │
│     └─ Returns: Native Tamil text              │
│  5. Detects language: "ta"                     │
│  6. Calls Groq Chat API:                       │
│     Translates Tamil → English                 │
│  7. Returns both versions                      │
│                                                  │
└─────────────────────┬──────────────────────────┘
                      │
                      ↓
┌─ Response ──────────────────────────────────────┐
│                                                  │
│  {                                              │
│    text: "சாலையில் பெரிய குழி உள்ளது",       │
│    translatedText: "Big pothole on road",      │
│    detectedLanguage: "ta",                     │
│    confidence: 0.97                            │
│  }                                              │
│                                                  │
└─────────────────────┬──────────────────────────┘
                      │
                      ↓
┌─ Frontend Processing ──────────────────────────┐
│                                                  │
│  8. Store in state:                            │
│     - nativeText: Tamil                        │
│     - translatedText: English                  │
│  9. Intelligence Service:                      │
│     - Uses translatedText for classification   │
│  10. Database:                                  │
│      - Store both versions + detected language │
│                                                  │
└──────────────────────────────────────────────┘
```

## 9. Next Steps

### Immediate
- [ ] Test speech-to-text in all 5 languages
- [ ] Verify translations are accurate
- [ ] Check database stores multilingual data
- [ ] Test classification with translated text

### Short Term
- [ ] Update UI components (see MIGRATION_GUIDE.md)
- [ ] Add language display to complaint details
- [ ] Test with real citizen complaints
- [ ] Monitor Groq API usage

### Production
- [ ] Set up error logging/monitoring
- [ ] Configure rate limiting for API
- [ ] Performance test under load
- [ ] Set up backup for translation failures
- [ ] Document for support team

## 10. Code Examples

### Use Speech-to-Text in Your Component

```typescript
import { speechToTextService } from "./services/speechToTextService";

async function handleRecord(audioBlob: Blob, language: LanguageCode) {
  try {
    const result = await speechToTextService.transcribe(audioBlob, language);
    
    // result.text = Native language
    // result.translatedText = English
    // result.detectedLanguage = Detected language
    // result.confidence = Confidence score
    
    console.log("Recorded:", result.text);
    console.log("Translated:", result.translatedText);
  } catch (error) {
    console.error("Failed:", error.message);
  }
}
```

### Translate Text Manually

```typescript
import { translationService } from "./services/translationService";

async function translateText(text: string) {
  const result = await translationService.translate(
    text,
    "ta",  // From Tamil
    "en"   // To English
  );
  console.log(result.translatedText);
}
```

### Complete Complaint Flow

See `src/services/multilingualComplaintExample.tsx` for a full working example.

## 11. Performance & Cost

### Groq API Usage

Each complaint uses 2 Groq API calls:
1. **Transcription** — Whisper Large V3 ($0.50/hour audio)
2. **Translation** — Mixtral 8x7B chat ($0.27/1M tokens)

For 100 complaints/day:
- Avg 1 min audio per complaint
- Avg 200 words translated
- **Estimated cost: ~$1.50-2/day**

### Optimization Tips

1. **Caching** — Cache translations of common phrases
2. **Batch** — Translate multiple complaints together
3. **Async** — Translate in background after submission
4. **Selective** — Only translate non-English complaints

## 12. Troubleshooting Commands

```bash
# Check if backend is running
curl http://localhost:3001/api/health

# Check GROQ_API_KEY is set
node -e "console.log(process.env.GROQ_API_KEY ? '✓ Set' : '✗ Not set')"

# Test endpoint directly
curl -X POST http://localhost:3001/api/transcribe \
  -F "audio=@sample.wav" \
  -F "language=ta" \
  -H "Content-Type: multipart/form-data"

# View backend logs
npm run dev:backend | grep -i "error\|warning"
```

## 13. Support Resources

- **API Docs:** See `MULTILINGUAL_GUIDE.md`
- **Migration:** See `MIGRATION_GUIDE.md`
- **Examples:** See `src/services/multilingualComplaintExample.tsx`
- **Groq Docs:** https://console.groq.com/docs

---

**Ready?** Start with Step 1 and follow through! 🚀
