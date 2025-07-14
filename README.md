# Meeting Audio Transcription & Speaker Diarization Agent

## Overview
This project is a production-grade Python agent that extracts structured conversations from meeting audio files. It combines high-quality transcription (using OpenAI Whisper API) with speaker diarization (using pyannote.audio) to generate a CSV file containing timestamps, speaker labels, and transcribed text. The solution is designed for scalability, reliability, and ease of deployment.

---

## Table of Contents
- [Features](#features)
- [Architecture](#architecture)
- [Setup & Installation](#setup--installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Output Format](#output-format)
- [Advanced Options](#advanced-options)
- [Troubleshooting](#troubleshooting)
- [Extending the Solution](#extending-the-solution)
- [Cost & Performance](#cost--performance)
- [FAQ](#faq)
- [License](#license)

---

## Features
- **Automatic Transcription**: Converts meeting audio to text using OpenAI Whisper API.
- **Speaker Diarization**: Identifies "who spoke when" using pyannote.audio.
- **Smart Audio Preprocessing**: Converts audio to mono, 16kHz WAV, and can speed up audio to reduce API costs.
- **Chunked Processing**: Splits large files into manageable chunks for API compatibility.
- **File Caching**: Reuses processed audio/chunks to avoid redundant computation.
- **Interactive CLI**: Prompts for user choices when large files are detected.
- **Structured Output**: Generates a CSV file with timestamps, speaker labels, and cleaned text.
- **Robust Error Handling**: Handles API errors, file issues, and diarization/model access problems gracefully.
- **Extensible**: Modular codebase for easy extension and integration.

---

## Architecture

### Directory Structure
```
├── config.py              # API keys (OpenAI + Hugging Face)
├── main.py                # Main orchestration script
├── audio_processor.py     # Audio preprocessing & chunking
├── transcriber.py         # OpenAI Whisper API integration
├── diarizer.py            # Speaker diarization (pyannote.audio)
├── aligner.py             # Transcript-speaker alignment
├── requirements.txt       # Dependencies
├── README.md              # Documentation
└── input_audio/           # Place your audio files here
```

### Processing Pipeline
1. **Audio Preprocessing**: Converts input audio to mono, 16kHz WAV, applies speedup if needed, and saves in `processed_audio/`.
2. **Transcription**: Sends audio (or chunks) to OpenAI Whisper API, receives detailed segments with timestamps.
3. **Speaker Diarization**: Runs pyannote.audio to label each segment with a speaker.
4. **Alignment**: Matches transcript segments to speaker labels using timestamps.
5. **Output**: Writes a CSV file with `timestamp_start`, `timestamp_end`, `speaker`, and `text` columns.

---

## Setup & Installation

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd <repo-directory>
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Install FFmpeg
- **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html), extract, and add `bin/` to your PATH.
- **Linux/macOS**: `sudo apt install ffmpeg` or `brew install ffmpeg`

### 4. Configure API Keys
- Edit `config.py`:
  ```python
  OPENAI_API_KEY = "sk-..."  # Your OpenAI API key
  HUGGINGFACE_TOKEN = "hf_..."  # Your Hugging Face token
  ```
- **Get your OpenAI key**: https://platform.openai.com/api-keys
- **Get your Hugging Face token**: https://huggingface.co/settings/tokens

### 5. Accept Model Terms on Hugging Face
- Visit [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1) and [pyannote/segmentation-3.0](https://huggingface.co/pyannote/segmentation-3.0)
- Click “Access repository” or “Agree and access repository” for both

---

## Configuration

- **config.py**: Store your API keys here.
- **requirements.txt**: All dependencies are listed here.
- **input_audio/**: Place your meeting audio files here (any format supported by ffmpeg/pydub).

---

## Usage

### Basic Command
```bash
python main.py input_audio/your_meeting.m4a
```

### If File is Too Large
- The script will prompt:
  - **Option 1**: Auto-adjust speedup (recommended)
  - **Option 2**: Chunk processing (splits into 10-min chunks)

### With Manual Speedup
```bash
python main.py input_audio/your_meeting.m4a --speedup 1.2
```

### Force Chunk Processing
```bash
python main.py input_audio/your_meeting.m4a --chunk
```

### Custom Output File
```bash
python main.py input_audio/your_meeting.m4a --output my_transcript.csv
```

### All Options
```bash
python main.py input_audio/your_meeting.m4a --speedup 1.2 --output my_transcript.csv --chunk --chunk-duration 5
```

---

## Output Format

The output is a CSV file with the following columns:
- `timestamp_start`: Start time (MM:SS)
- `timestamp_end`: End time (MM:SS)
- `speaker`: Speaker label (e.g., SPEAKER_00)
- `text`: Cleaned, readable transcript

**Example:**
```csv
timestamp_start,timestamp_end,speaker,text
00:00,00:05,SPEAKER_00,"Hello everyone, welcome to the meeting."
00:05,00:12,SPEAKER_01,"Thank you for having us today."
```

---

## Advanced Options

- **Auto Speedup**: Automatically increases audio speed to fit under Whisper API’s 25MB limit.
- **Chunk Processing**: Splits audio into N-minute chunks for large files.
- **File Caching**: Reuses processed audio/chunks if already present.
- **Interactive Prompts**: Guides user through options for large files.
- **Custom Output**: Specify output CSV name; default is based on input file name.

---

## Troubleshooting

### Common Issues & Fixes

#### 1. **FFmpeg Not Found**
- **Error**: `Couldn't find ffmpeg or avconv...`
- **Fix**: Install FFmpeg and add to your PATH.

#### 2. **Audio File Too Large**
- **Error**: `Audio file too large (XX.XMB). Whisper API limit is 25MB.`
- **Fix**: Use auto-adjust speedup or chunk processing.

#### 3. **Hugging Face Model Access**
- **Error**: `Could not download 'pyannote/segmentation-3.0' model...`
- **Fix**: Accept user conditions for all required models on Hugging Face.

#### 4. **API Key Issues**
- **Error**: `Invalid API key` or authentication errors
- **Fix**: Double-check your API keys in `config.py`.

#### 5. **No Segments in Transcription**
- **Error**: `Whisper API response segments is None`
- **Fix**: The script will fallback to a single segment using the text field.

#### 6. **Symlink Warning on Windows**
- **Warning**: `huggingface_hub cache-system uses symlinks by default...`
- **Fix**: Enable Developer Mode on Windows or ignore the warning.

---

## Extending the Solution

- **Add More Output Formats**: Extend `aligner.py` to support JSON, SRT, or plain text.
- **Integrate Summarization**: Add a post-processing step using GPT or similar models.
- **Web/API Interface**: Wrap `main.py` in a FastAPI or Flask app for web-based uploads.
- **Speaker Name Mapping**: Allow mapping of speaker labels to real names.
- **Batch Processing**: Add a loop in `main.py` to process all files in `input_audio/`.

---

## Cost & Performance

- **Whisper API**: ~$0.006 per minute of audio
- **pyannote.audio**: Free (runs locally, but requires model download)
- **Speedup Option**: 1.2x speedup reduces cost by ~17%
- **Chunking**: Allows processing of arbitrarily large files

---

## FAQ

**Q: What audio formats are supported?**
A: Any format supported by ffmpeg/pydub (WAV, MP3, M4A, etc.)

**Q: How many speakers can it detect?**
A: pyannote.audio can detect multiple speakers, but accuracy depends on audio quality and model.

**Q: Can I use this for languages other than English?**
A: Yes, Whisper supports many languages, but diarization is best for clear, multi-speaker English audio.

**Q: Is my data secure?**
A: Audio is sent to OpenAI for transcription. Diarization is local. No data is stored beyond your machine unless you choose to upload it elsewhere.

---

## License
This project is open source. Please ensure you comply with the licenses of:
- OpenAI Whisper API
- pyannote.audio
- All other dependencies

---

## Acknowledgements
- [OpenAI Whisper](https://platform.openai.com/docs/guides/speech-to-text)
- [pyannote.audio](https://github.com/pyannote/pyannote-audio)
- [Hugging Face](https://huggingface.co/)
- [pydub](https://github.com/jiaaro/pydub)
- [pandas](https://pandas.pydata.org/) 