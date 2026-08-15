# Migration Guide: Updating UI Components for Multilingual Support

This guide shows how to update your existing React components to leverage the enhanced multilingual support.

## What Changed

### Before (Previous Implementation)
- Audio always translated to English by Whisper
- Original language lost
- No language detection
- Fixed 0.95 confidence

### After (New Implementation)
- Audio transcribed in **native language**
- Automatically translated to English for processing
- Language detection with confidence scores
- **Both versions stored** in database

---

## Minimal Update: SubmitComplaint Component

### Current Code (Before)
```typescript
async function retryTranscription() {
  if (!lastAudioBlobRef.current) {
    resetVoice();
    return;
  }
  setVoiceState("transcribing");
  setVoiceError("");
  try {
    const sttResult = await speechToTextService.transcribe(lastAudioBlobRef.current, language);
    setComplaintText(sttResult.text);  // ← Uses text directly
    setVoiceState("success");
    setVoiceSuccess(true);
  } catch (err) {
    // error handling
  }
}
```

### Updated Code (After)
```typescript
// Add state to track transcription details
const [transcriptionDetails, setTranscriptionDetails] = useState<{
  native: string;
  translated: string;
  language: LanguageCode;
  confidence: number;
} | null>(null);

async function retryTranscription() {
  if (!lastAudioBlobRef.current) {
    resetVoice();
    return;
  }
  setVoiceState("transcribing");
  setVoiceError("");
  try {
    const sttResult = await speechToTextService.transcribe(lastAudioBlobRef.current, language);
    
    // Store original language transcription details
    setTranscriptionDetails({
      native: sttResult.text,  // Original language
      translated: sttResult.translatedText || sttResult.text,  // English
      language: sttResult.detectedLanguage,
      confidence: sttResult.confidence,
    });
    
    // Use translated text for complaint processing
    setComplaintText(sttResult.translatedText || sttResult.text);
    setVoiceState("success");
    setVoiceSuccess(true);
  } catch (err) {
    // error handling
  }
}
```

### When Submitting Complaint
```typescript
// When you create the complaint, include both versions:
const complaint: CitizenComplaint = {
  // ... existing fields ...
  transcription: transcriptionDetails?.native || "",  // Native language
  translatedText: transcriptionDetails?.translated || complaintText,  // English
  language: transcriptionDetails?.language || language,
  // ... rest of fields ...
};
```

---

## Full Example: Enhanced SubmitComplaint

Here's a complete updated version of key parts:

```typescript
import { useState, useRef, useEffect } from "react";
import type { LanguageCode, IntelligenceResult, CitizenComplaint } from "../../types";

type VoiceState = "idle" | "recording" | "transcribing" | "success" | "error";

// New: Track multilingual transcription details
interface TranscriptionData {
  nativeText: string;        // Original language
  translatedText: string;    // English translation
  detectedLanguage: LanguageCode;
  confidence: number;
}

export function SubmitComplaint({ 
  language, 
  onLanguageChange 
}: { 
  language: LanguageCode;
  onLanguageChange: (c: LanguageCode) => void 
}) {
  // Existing state
  const [complaintText, setComplaintText] = useState("");
  const [voiceState, setVoiceState] = useState<VoiceState>("idle");
  
  // NEW: Multilingual transcription state
  const [transcriptionData, setTranscriptionData] = useState<TranscriptionData | null>(null);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const lastAudioBlobRef = useRef<Blob | null>(null);

  // ... existing code ...

  async function startRecording() {
    setVoiceError("");
    setVoiceSuccess(false);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;
      audioChunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      recorder.onstop = async () => {
        const blob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        lastAudioBlobRef.current = blob;
        stream.getTracks().forEach((t) => t.stop());

        setVoiceState("transcribing");
        try {
          const sttResult = await speechToTextService.transcribe(blob, language);
          
          // NEW: Store both native and translated versions
          setTranscriptionData({
            nativeText: sttResult.text,
            translatedText: sttResult.translatedText || sttResult.text,
            detectedLanguage: sttResult.detectedLanguage,
            confidence: sttResult.confidence,
          });
          
          // Use translated text for display/processing
          setComplaintText(sttResult.translatedText || sttResult.text);
          
          setVoiceState("success");
          setVoiceSuccess(true);
        } catch (err) {
          const msg = (err as Error).message;
          const notConfigured = msg.includes("not configured");
          setVoiceError(
            notConfigured
              ? "Voice transcription service is not configured."
              : "Voice could not be transcribed. Please retry or enter manually."
          );
          setVoiceState("error");
        }
      };

      recorder.start();
      setVoiceState("recording");
      startTimer();
    } catch (err) {
      console.error("Microphone access denied:", err);
      setVoiceError("Microphone access is required for voice complaints.");
      setVoiceState("error");
    }
  }

  async function retryTranscription() {
    if (!lastAudioBlobRef.current) {
      resetVoice();
      return;
    }
    setVoiceState("transcribing");
    setVoiceError("");
    try {
      const sttResult = await speechToTextService.transcribe(
        lastAudioBlobRef.current,
        language
      );
      
      // NEW: Store multilingual data
      setTranscriptionData({
        nativeText: sttResult.text,
        translatedText: sttResult.translatedText || sttResult.text,
        detectedLanguage: sttResult.detectedLanguage,
        confidence: sttResult.confidence,
      });
      
      setComplaintText(sttResult.translatedText || sttResult.text);
      setVoiceState("success");
      setVoiceSuccess(true);
    } catch (err) {
      const msg = (err as Error).message;
      const notConfigured = msg.includes("not configured");
      setVoiceError(
        notConfigured
          ? "Voice transcription service is not configured."
          : "Voice could not be transcribed. Please retry or enter manually."
      );
      setVoiceState("error");
    }
  }

  // ... existing code ...

  async function submitComplaint() {
    if (!complaintText.trim()) {
      alert("Please enter or record a complaint.");
      return;
    }

    setStage("processing");

    try {
      // NEW: Pass both native and translated text to intelligence service
      const intelligenceResult = await complaintIntelligenceService.analyze({
        language: transcriptionData?.detectedLanguage || language,
        transcription: transcriptionData?.nativeText,  // Native language
        complaintText: transcriptionData?.translatedText || complaintText,  // English
        imageUrl,
        location,
      });

      setResult(intelligenceResult);

      // NEW: Create complaint with multilingual data
      const complaint: CitizenComplaint = {
        complaintId: generateComplaintId(),
        citizenId,
        language: transcriptionData?.detectedLanguage || language,
        transcription: transcriptionData?.nativeText || complaintText,  // Original language
        translatedText: transcriptionData?.translatedText || complaintText,  // English
        complaintText: intelligenceResult.summary,
        // ... other intelligence result fields ...
        confidence: transcriptionData?.confidence || 0.95,
        // ... rest of fields ...
      };

      await complaintRepository.create(complaint);
      setCreatedComplaint(complaint);

      // NEW: Send acknowledgment in citizen's language (if not English)
      if (complaint.language !== "en") {
        try {
          const acknowledgment =
            "Your complaint has been successfully received and registered. " +
            `Your complaint ID is ${complaint.complaintId}. ` +
            "You will receive updates via SMS.";

          const { translationService } = await import(
            "../../services/translationService"
          );

          const localized = await translationService.translate(
            acknowledgment,
            "en",
            complaint.language
          );

          console.log("Acknowledgment:", localized.translatedText);
          // Show notification in citizen's language
        } catch (err) {
          console.warn("Could not translate acknowledgment:", err);
        }
      }

      setStage("result");
      await refreshComplaints();
    } catch (err) {
      alert(`Error: ${err instanceof Error ? err.message : "Unknown error"}`);
      setStage("input");
    }
  }

  // NEW: Display transcription details to user
  function renderTranscriptionDetails() {
    if (!transcriptionData) return null;

    return (
      <div className="mt-4 p-4 bg-blue-50 rounded border border-blue-200">
        <p className="text-sm text-gray-600 mb-3 font-semibold">
          📝 Transcription Details
        </p>

        {transcriptionData.detectedLanguage !== "en" && (
          <div className="mb-3 p-3 bg-white rounded">
            <p className="text-xs text-gray-500 mb-1">Native Language</p>
            <p className="text-sm text-gray-800 italic">
              {transcriptionData.nativeText}
            </p>
            <p className="text-xs text-gray-500 mt-2">
              ({transcriptionData.detectedLanguage.toUpperCase()})
            </p>
          </div>
        )}

        <div className="p-3 bg-white rounded">
          <p className="text-xs text-gray-500 mb-1">English Translation</p>
          <p className="text-sm text-gray-800">
            {transcriptionData.translatedText}
          </p>
          <p className="text-xs text-green-600 mt-2">
            ✓ Confidence: {(transcriptionData.confidence * 100).toFixed(1)}%
          </p>
        </div>
      </div>
    );
  }

  // ... existing render code ...

  return (
    <div>
      {/* ... existing JSX ... */}

      {/* Add this after voice recording section */}
      {transcriptionData && renderTranscriptionDetails()}

      {/* Submit button remains same but now uses multilingual data */}
      <button onClick={submitComplaint} className="w-full bg-green-600 text-white py-3">
        Submit Complaint
      </button>
    </div>
  );
}
```

---

## Database Schema Update

If your database schema was storing only one transcription field, update it:

### Before
```typescript
interface CitizenComplaint {
  complaintId: string;
  complaintText: string;  // Usually English
  // ...
}
```

### After
```typescript
interface CitizenComplaint {
  complaintId: string;
  language: LanguageCode;           // Detected language
  transcription: string;             // Original language
  translatedText: string;            // English translation
  complaintText: string;             // Processing/summary
  // ...
}
```

---

## Other Components to Update

### 1. CitizenComplaints.tsx (Display Complaints)
Show original language option:

```typescript
// Display both versions
<div>
  <p className="text-gray-700">{complaint.complaintText}</p>
  
  {complaint.language !== "en" && (
    <details className="mt-2 text-sm">
      <summary className="cursor-pointer text-blue-600">
        View in {complaint.language.toUpperCase()}
      </summary>
      <p className="mt-2 text-gray-600 italic">{complaint.transcription}</p>
    </details>
  )}
</div>
```

### 2. AdminComplaintDetail.tsx
Show all language versions:

```typescript
<div className="bg-gray-50 p-4 rounded">
  <h3 className="font-semibold mb-3">Complaint Details</h3>
  
  {complaint.language !== "en" && (
    <div className="mb-4 p-3 bg-white rounded border">
      <p className="text-xs text-gray-500 mb-1">
        Original ({complaint.language.toUpperCase()})
      </p>
      <p className="text-gray-800">{complaint.transcription}</p>
    </div>
  )}
  
  <div className="p-3 bg-white rounded border">
    <p className="text-xs text-gray-500 mb-1">Translated (English)</p>
    <p className="text-gray-800">{complaint.translatedText}</p>
  </div>
</div>
```

### 3. ComplaintResult.tsx
Show transcription with native language:

```typescript
{complaint.language !== "en" && (
  <div className="mt-4 p-4 bg-blue-50 rounded">
    <p className="text-sm text-gray-600 mb-2">Recorded in {complaint.language}</p>
    <p className="text-gray-800 italic">{complaint.transcription}</p>
  </div>
)}
```

---

## Testing the Migration

### Test Checklist

- [ ] Record complaint in Tamil — verify both native and English stored
- [ ] Record complaint in Telugu — check language detection
- [ ] Verify confidence scores are realistic (>0.9)
- [ ] Check translations are accurate
- [ ] Confirm database stores multilingual data
- [ ] Test complaint processing uses English translation
- [ ] Verify admin/department sees English version
- [ ] Check citizen sees their native language options

### Test Scenario

```typescript
// 1. Record Tamil complaint
// Audio: "சாலையில் பெரிய குழி உள்ளது"
// ↓ Whisper detects Tamil, transcribes natively
// Native: "சாலையில் பெரிய குழி உள்ளது"
// Translation: "There is a large pothole on the street"
// Confidence: 0.97

// 2. Intelligence service uses English for processing
// ✓ Category: Roads
// ✓ Priority: MEDIUM

// 3. Database stores:
// - language: "ta"
// - transcription: "சாலையில் பெரிய குழி உள்ளது"
// - translatedText: "There is a large pothole on the street"

// 4. UI shows to citizen: Native Tamil with details
// 5. UI shows to admin: English for processing
```

---

## Backward Compatibility

If you have old complaints without multilingual data:

```typescript
// Safe fallback in display components
const displayText = complaint.translatedText || complaint.complaintText || "";
const nativeText = complaint.transcription || complaint.complaintText || "";
const lang = complaint.language || "en";
```

---

## Performance Considerations

### Caching Translations
If displaying same complaint multiple times:

```typescript
const translationCache = new Map<string, string>();

async function getCachedTranslation(
  text: string,
  targetLanguage: LanguageCode
): Promise<string> {
  const key = `${text.substring(0, 50)}-${targetLanguage}`;
  
  if (translationCache.has(key)) {
    return translationCache.get(key)!;
  }
  
  const result = await translationService.translate(text, "en", targetLanguage);
  translationCache.set(key, result.translatedText);
  return result.translatedText;
}
```

### Lazy Translation
Translate to citizen's language only when needed:

```typescript
// Don't translate immediately — wait until citizen views update
const handleViewStatus = async () => {
  const statusMessage = "Your complaint is being reviewed";
  
  if (complaint.language !== "en") {
    const translated = await translationService.translate(
      statusMessage,
      "en",
      complaint.language
    );
    showNotification(translated.translatedText);
  } else {
    showNotification(statusMessage);
  }
};
```

---

## Rollback Plan

If you need to revert:

1. Keep previous `speechToTextService` endpoints working
2. Existing data with only `complaintText` still works
3. New fields are optional with fallbacks
4. UI gracefully handles missing `transcription`/`translatedText`

---

## Summary of Changes

| Component | Change | Impact |
|-----------|--------|--------|
| **Backend** | Preserve original language + auto-translate | Multilingual data stored |
| **Frontend** | Capture & store native + translated text | Better user experience |
| **Database** | Add `transcription`, `translatedText`, `language` | Full language history |
| **UI** | Show original language options | Citizens see their language |
| **Admin** | See English for processing | Unified processing workflow |

All changes are **backward compatible** — existing code continues to work.
