# Whisper Transcription Lab – Brief Report

## 1. Prompted vs Unprompted Transcriptions
The results are mostly similar. Adding a prompt helped a bit with some specific words (like “hukilau” or “akule”), but overall the transcription did not change much.  
Most of the main errors (like “lead” vs “lid” or “shore” vs “show”) were still there. So the prompt gives small improvements, but it’s not a big difference.

---

## 2. Benefits of Chunking for Long Audio
Chunking helps to:
- Avoid very long requests that may fail or be slow
- Reduce weird repetitions or hallucinations
- Make processing more stable

It also allows adding timestamps more easily and tracking progress chunk by chunk.
One disadvantage was, if not indicating the language, the chunks are lacking context of the whole audio and language is missidentified.
---

## 3. Challenges Faced
- Some words are still misheard even with prompts
- Audio quality affects results a lot
- Splitting into chunks requires handling offsets correctly for timestamps
- Slight inconsistencies between chunks (tone, wording)

---

## 4. Recommendations to Improve Accuracy
- Improve audio quality (clean, normalize, less noise)
- Use smaller chunks (5–10 seconds works well)
- Add prompts only for important vocabulary

---