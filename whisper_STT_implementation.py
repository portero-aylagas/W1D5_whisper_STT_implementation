# %% [markdown]
# ## Step 1: Setting Up the Environment

# %%
from openai import OpenAI
import io
import os
from dotenv import load_dotenv
from pydub import AudioSegment
import io
from pathlib import Path
import json

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# %% [markdown]
# ## Step 2: Downloading Sample Meeting Audio

# %%


audio_file = "audio/HI009clip.mp3"  

audio_path = Path(audio_file)
audio_name = audio_path.stem

# Read file as bytes and wrap in BytesIO
with open(audio_file, "rb") as f:
    buffer = io.BytesIO(f.read())

# Load mp3
audio = AudioSegment.from_mp3("audio/HI009clip.mp3")

# Export to in-memory buffer
def export_to_buffer(audio_segment, format="mp3"):
    buffer = io.BytesIO()
    audio_segment.export(buffer, format=format)
    buffer.name = f"clip_10s.{format}"
    buffer.seek(0)
    return buffer   


# %% [markdown]
# ## Step 3: Basic Transcription (Without Chunking)

# %%
# Cut first 10 seconds (milliseconds)
audio_10s = audio[:10_000]

buffer_10s = export_to_buffer(audio_10s)

# Send to Whisper
print("🤖 Transcribing 10s audio without context...")
transcript = client.audio.transcriptions.create(
    model="whisper-1",
    file=   buffer_10s
)

print(transcript.text)

# %% [markdown]
# ## Step 4: Transcription with Prompts (Guided Approach)

# %%
buffer = export_to_buffer(audio)

# %%
# Transcribe with context prompt
print("🤖 Transcribing full audio with context...")

prompt = """
This is an interview transcript about a Hawaiian fishing custom called hukilau.
Important vocabulary and spellings:
Cassidy, informant, hukilau, lau, leaf, rope, net, floaters, floats, dried coconut,
top of the net, bottom of the net, pocket on the net, lead weights, sinkers,
shore, two boats, school of fish, haul, akule, Polynesian, Japanese, aji.
The word lead means the metal used as a weight, not lid.
The word shore means beach/coast, not show.
The word lau means leaf.
"""

transcript = client.audio.transcriptions.create(
    model="whisper-1",
    file=buffer,
    prompt=prompt,
    language="en"
)

print(transcript.text)

# %% [markdown]
# ## Step 5: Transcription Without Prompts (Unguided Approach)

# %%
# Transcribe
print("🤖 Transcribing full audio without context...")
transcript = client.audio.transcriptions.create(
    model="whisper-1",
    file=buffer
)

print(transcript.text)

# %% [markdown]
# **Comparison:** The unguided audio has a sligthly worse performance, but they are actually very similar.

# %% [markdown]
# ## Step 6: Implementing Audio Chunking

# %%

chunk_duration = 5  # seconds
chunk_duration_ms = chunk_duration * 1000

# Split into chunks
chunks = [
    audio[i:i + chunk_duration_ms]
    for i in range(0, len(audio), chunk_duration_ms)
]

print(f"\n🔪 Split into {len(chunks)} chunks")

# Transcribe each chunk (no prompt)
all_transcripts = []

for i, chunk in enumerate(chunks):
    print(f"\n🤖 Transcribing chunk {i + 1}/{len(chunks)}...")

    # Prepare buffer
    buffer = io.BytesIO()
    chunk.export(buffer, format="mp3")
    buffer.seek(0)
    buffer.name = f"chunk_{i + 1}.mp3"

    # Transcribe
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=buffer,
        language="en",
    )

    all_transcripts.append(transcript.text)
    print(f"Chunk {i + 1}: {transcript.text}")

# Combine
print("\n📝 Complete Transcription:")
print("-" * 40)

full_text = " ".join(all_transcripts)
print(full_text)

# %% [markdown]
# ## Step 7: Transcribing Chunks with Timestamps

# %%
all_segments = []

for i, chunk in enumerate(chunks):
    chunk_offset_seconds = i * chunk_duration  # must match chunk size (seconds)

    print(f"\n🤖 Transcribing chunk {i + 1}/{len(chunks)} "
          f"(offset: {chunk_offset_seconds:.1f}s → {chunk_offset_seconds + chunk_duration:.1f}s)")

    buffer = io.BytesIO()
    chunk.export(buffer, format="mp3")
    buffer.seek(0)
    buffer.name = f"chunk_{i + 1}.mp3"

    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=buffer,
        language="en",
        response_format="verbose_json",
        timestamp_granularities=["segment"]
    )

    print(f"📦 Found {len(transcript.segments)} segments")

    for segment in transcript.segments:
        adjusted = {
            "start": segment.start + chunk_offset_seconds,
            "end": segment.end + chunk_offset_seconds,
            "text": segment.text.strip()
        }

        all_segments.append(adjusted)

        print(f"   🧩 [{adjusted['start']:.2f} - {adjusted['end']:.2f}] {adjusted['text']}")

# Print segments (final pass)
print("\n🧾 All segments:")
print("-" * 40)
for seg in all_segments:
    print(f"[{seg['start']:.2f} - {seg['end']:.2f}] {seg['text']}")

# Combine full text
full_text = " ".join(seg["text"] for seg in all_segments)

print("\n📝 Complete Transcription:")
print("-" * 40)
print(full_text)

# %% [markdown]
# ## Step 8: Exporting with Timestamps

# %%
output_dir = Path("outputs") / audio_name
output_dir.mkdir(parents=True, exist_ok=True)

# %%
json_path = output_dir / "transcription_with_timestamps.json"
# Export JSON
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(all_segments, f, indent=2, ensure_ascii=False)


print(f"✅ Exported files to: {output_dir}")
print(f"- {json_path}")

# %%
txt_path = output_dir / "transcription_with_timestamps.txt"

# Export plain text with timestamps
with open(txt_path, "w", encoding="utf-8") as f:
    for seg in all_segments:
        f.write(f"[{seg['start']:.2f} - {seg['end']:.2f}] {seg['text']}\n")
print(f"- {txt_path}")

# %%

srt_path = output_dir / "transcription.srt"

def format_srt_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

# Export SRT
with open(srt_path, "w", encoding="utf-8") as f:
    for i, seg in enumerate(all_segments, start=1):
        start_time = format_srt_time(seg["start"])
        end_time = format_srt_time(seg["end"])
        text = seg["text"]

        f.write(f"{i}\n")
        f.write(f"{start_time} --> {end_time}\n")
        f.write(f"{text}\n\n")
        
print(f"- {srt_path}")




