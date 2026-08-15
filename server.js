// server.js — Express backend for Groq Whisper transcription
// Runs alongside Vite dev server. Vite proxies /api/* → http://localhost:3001
// The GROQ_API_KEY is only ever read here, never exposed to the browser.

import express from "express";
import multer from "multer";
import { Groq } from "groq-sdk";
import { createRequire } from "module";
import * as dotenv from "dotenv";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { Readable } from "stream";

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const app = express();
const PORT = 3001;

// Use memory storage so we can pipe the buffer directly to Groq
const upload = multer({ storage: multer.memoryStorage() });

// Health check
app.get("/api/health", (_req, res) => {
  res.json({ ok: true });
});

// POST /api/transcribe
// Expects multipart/form-data with:
//   audio     — the recorded audio blob
//   language  — optional preferred language hint (en, ta, ml, te, hi)
// Returns: { success, text, detectedLanguage, confidence, translatedText (if non-English) }
app.post("/api/transcribe", upload.single("audio"), async (req, res) => {
  try {
    const apiKey = process.env.GROQ_API_KEY;
    if (!apiKey) {
      return res.status(503).json({
        success: false,
        error: "Voice service is not configured. GROQ_API_KEY is missing.",
      });
    }

    if (!req.file) {
      return res.status(400).json({ success: false, error: "No audio file received." });
    }

    const languageHint = (req.body.language || "").trim();
    const client = new Groq({ apiKey });

    const audioBuffer = req.file.buffer;
    const mimeType = req.file.mimetype || "audio/webm";
    const ext = mimeType.includes("webm")
      ? "webm"
      : mimeType.includes("mp4")
      ? "mp4"
      : mimeType.includes("mpeg") || mimeType.includes("mp3")
      ? "mp3"
      : mimeType.includes("wav")
      ? "wav"
      : mimeType.includes("m4a")
      ? "m4a"
      : "webm";

    const filename = `recording.${ext}`;

    // Step 1: Transcribe audio in its ORIGINAL language
    // This preserves native language context and nuance
    const transcription = await client.audio.transcriptions.create({
      file: new File([audioBuffer], filename, { type: mimeType }),
      model: "whisper-large-v3",
      temperature: 0,
      response_format: "verbose_json",
      language: languageHint || undefined, // Let Whisper detect if no hint provided
    });

    const nativeText = transcription.text || "";
    const detectedLanguage = transcription.language || languageHint || "en";
    
    // Confidence from Whisper's verbose_json (0-1 scale)
    let confidence = 0.95;
    if (transcription.confidence !== undefined) {
      confidence = transcription.confidence;
    }

    let translatedText = nativeText;
    let languageCode = mapLanguageCode(detectedLanguage);

    // Step 2: If detected language is not English, translate to English
    // This enables processing in complaint intelligence system
    if (languageCode !== "en" && nativeText.trim()) {
      try {
        const translation = await translateWithGroq(
          client,
          nativeText,
          languageCode,
          "en"
        );
        translatedText = translation;
      } catch (translationErr) {
        console.warn("[Translation Warning]", translationErr.message);
        // Fall back to native text if translation fails
        translatedText = nativeText;
      }
    }

    return res.json({
      success: true,
      text: nativeText,
      translatedText,
      detectedLanguage: languageCode,
      confidence,
    });
  } catch (err) {
    console.error("[Groq Whisper Error]", err);
    const message =
      err?.error?.message ||
      err?.message ||
      "Voice conversion failed. Please try again.";
    return res.status(500).json({ success: false, error: message });
  }
});

app.listen(PORT, () => {
  console.log(`[Backend] Groq transcription server running on http://localhost:${PORT}`);
});

// ============================================================
// Helper: Map Whisper language codes to internal codes
// ============================================================
function mapLanguageCode(whisperLang) {
  const langMap = {
    en: "en",
    ta: "ta",
    te: "te",
    hi: "hi",
    ml: "ml",
    // Whisper returns 2-letter codes; map to our supported set
    "en-us": "en",
    "en-gb": "en",
  };
  return langMap[whisperLang.toLowerCase()] || "en";
}

// ============================================================
// Helper: Translate text using Groq Chat API
// ============================================================
async function translateWithGroq(client, text, sourceLanguage, targetLanguage) {
  // Map our language codes to full language names for clarity
  const languageNames = {
    en: "English",
    ta: "Tamil",
    te: "Telugu",
    hi: "Hindi",
    ml: "Malayalam",
  };

  const sourceLangName = languageNames[sourceLanguage] || sourceLanguage;
  const targetLangName = languageNames[targetLanguage] || targetLanguage;

  const prompt = `Translate the following ${sourceLangName} complaint text into ${targetLangName}. 
Preserve the meaning and tone. Return ONLY the translated text, no explanation.

Original text:
${text}`;

  const completion = await client.chat.completions.create({
    model: "mixtral-8x7b-32768",
    messages: [
      {
        role: "system",
        content: `You are a professional translator specializing in regional languages and complaint documentation. 
Translate accurately preserving technical terms and context.`,
      },
      {
        role: "user",
        content: prompt,
      },
    ],
    temperature: 0.3,
    max_tokens: 1024,
  });

  return completion.choices[0].message.content.trim();
}

// ============================================================
// POST /api/translate
// Translate text between supported languages
// ============================================================
app.post("/api/translate", express.json(), async (req, res) => {
  try {
    const apiKey = process.env.GROQ_API_KEY;
    if (!apiKey) {
      return res.status(503).json({
        success: false,
        error: "Translation service is not configured.",
      });
    }

    const { text, sourceLanguage, targetLanguage = "en" } = req.body;

    if (!text) {
      return res.status(400).json({ success: false, error: "Text is required." });
    }

    if (sourceLanguage === targetLanguage) {
      return res.json({
        success: true,
        translatedText: text,
        sourceLanguage,
        targetLanguage,
      });
    }

    const client = new Groq({ apiKey });

    const translatedText = await translateWithGroq(
      client,
      text,
      sourceLanguage,
      targetLanguage
    );

    return res.json({
      success: true,
      translatedText,
      sourceLanguage,
      targetLanguage,
    });
  } catch (err) {
    console.error("[Translation Error]", err);
    const message = err?.error?.message || err?.message || "Translation failed";
    return res.status(500).json({ success: false, error: message });
  }
});
