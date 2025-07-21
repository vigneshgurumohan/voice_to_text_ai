import argparse
import os
import tempfile
import json
from datetime import datetime
from config import OPENAI_API_KEY, HUGGINGFACE_TOKEN
from config import ASSEMBLYAI_API_KEY

from audio_processor import (
    preprocess_audio, get_audio_duration, calculate_optimal_speedup, 
    chunk_audio_file, cleanup_chunks
)
from transcriber import WhisperTranscriber
from diarizer import SpeakerDiarizer
from aligner import TranscriptAligner

def find_input_audio(audio_id):
    input_dir = os.path.join("data", audio_id, "input_audio")
    if not os.path.exists(input_dir):
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
    audio_files = [f for f in files if f.lower().endswith((".wav", ".mp3", ".m4a", ".flac", ".aac"))]
    if not audio_files:
        raise FileNotFoundError(f"No audio file found in {input_dir}")
    if len(audio_files) > 1:
        raise RuntimeError(f"Multiple audio files found in {input_dir}. Please keep only one.")
    return os.path.join(input_dir, audio_files[0])

def get_processed_dir(audio_id):
    processed_dir = os.path.join("data", audio_id, "processed_audio")
    if not os.path.exists(processed_dir):
        os.makedirs(processed_dir)
    return processed_dir

def get_transcript_path(audio_id, base):
    transcript_dir = os.path.join("data", audio_id, "transcript")
    if not os.path.exists(transcript_dir):
        os.makedirs(transcript_dir)
    return os.path.join(transcript_dir, f"{base}.csv")

def get_summary_path(audio_id, base):
    document_dir = os.path.join("data", audio_id, "document")
    if not os.path.exists(document_dir):
        os.makedirs(document_dir)
    return os.path.join(document_dir, f"{base}_summary.txt")

def get_metadata_path(audio_id, base):
    metadata_dir = os.path.join("data", audio_id, "metadata")
    if not os.path.exists(metadata_dir):
        os.makedirs(metadata_dir)
    return os.path.join(metadata_dir, f"{base}.json")

def update_metadata(metadata_path, data):
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def prompt_for_large_file_option():
    """Prompt user to choose how to handle large audio file."""
    print("\n" + "="*50)
    print("AUDIO FILE TOO LARGE FOR WHISPER API (25MB limit)")
    print("="*50)
    print("Choose an option:")
    print("1. Auto-adjust speedup (recommended)")
    print("   - Automatically calculates optimal speedup to get under 25MB")
    print("   - Maintains single file processing")
    print("   - Faster processing, lower cost")
    print()
    print("2. Chunk processing")
    print("   - Splits file into smaller chunks (10 minutes each)")
    print("   - Processes each chunk separately")
    print("   - Better for very long meetings")
    print("   - Higher accuracy, but more complex")
    print()
    
    while True:
        choice = input("Enter your choice (1 or 2): ").strip()
        if choice == "1":
            return "auto-adjust"
        elif choice == "2":
            return "chunk"
        else:
            print("Invalid choice. Please enter 1 or 2.")

def main():
    parser = argparse.ArgumentParser(description="Transcribe and diarize a meeting audio file.")
    parser.add_argument("audio_id", type=str, help="Audio ID (subfolder in ../data/)")
    parser.add_argument("--speedup", type=float, default=1.0, help="Speed up audio by this factor (e.g., 1.2)")
    parser.add_argument("--auto-adjust", action="store_true", 
                       help="Automatically adjust speedup to get under 25MB limit")
    parser.add_argument("--chunk", action="store_true", 
                       help="Split large files into chunks and process separately")
    parser.add_argument("--chunk-duration", type=int, default=10, 
                       help="Duration of each chunk in minutes (default: 10)")
    parser.add_argument("--diarizer", type=str, choices=["huggingface", "assemblyai"], default="huggingface", help="Choose diarization backend")
    parser.add_argument("--assemblyai-key", type=str, default=None, help="AssemblyAI API key (if using AssemblyAI)")
    args = parser.parse_args()

    audio_id = args.audio_id
    audio_path = find_input_audio(audio_id)
    base = os.path.splitext(os.path.basename(audio_path))[0]
    speedup = args.speedup
    auto_adjust = args.auto_adjust
    chunk_mode = args.chunk
    chunk_duration = args.chunk_duration
    processed_dir = get_processed_dir(audio_id)
    transcript_path = get_transcript_path(audio_id, base)
    summary_path = get_summary_path(audio_id, base)
    metadata_path = get_metadata_path(audio_id, base)

    # Validate inputs
    if not os.path.exists(audio_path):
        print(f"Error: Audio file not found: {audio_path}")
        return
    if not OPENAI_API_KEY or OPENAI_API_KEY == "your-openai-api-key-here":
        print("Error: Please set your OpenAI API key in config.py")
        return
    if not HUGGINGFACE_TOKEN or HUGGINGFACE_TOKEN == "your-huggingface-token-here":
        print("Error: Please set your Hugging Face token in config.py")
        return

    print(f"=== Meeting Audio Processing ===")
    print(f"Audio ID: {audio_id}")
    print(f"Input file: {audio_path}")
    print(f"Transcript CSV: {transcript_path}")
    print(f"Summary TXT: {summary_path}")
    print(f"Processed audio directory: {processed_dir}")
    print(f"Audio duration: {get_audio_duration(audio_path):.1f} seconds")

    if auto_adjust and chunk_mode:
        print("Error: Cannot use both --auto-adjust and --chunk options together")
        return
    if auto_adjust:
        print("Mode: Auto-adjust speedup")
        speedup = calculate_optimal_speedup(audio_path)
    elif chunk_mode:
        print(f"Mode: Chunk processing ({chunk_duration}min chunks)")
    else:
        print(f"Mode: Manual speedup ({speedup}x)")
    print()

    diarizer = None
    if args.diarizer == "huggingface":
        diarizer = SpeakerDiarizer(HUGGINGFACE_TOKEN)
    elif args.diarizer == "assemblyai":
        try:
            from diarizer_assemblyai import AssemblyAIDiarizer
        except ImportError:
            print("Error: diarizer_assemblyai.py not found. Please add AssemblyAI diarizer implementation.")
            return
        if not args.assemblyai_key:
            if not ASSEMBLYAI_API_KEY:
                print("Error: AssemblyAI API key not found in config.py or --assemblyai-key.")
                return
            args.assemblyai_key = ASSEMBLYAI_API_KEY
        diarizer = AssemblyAIDiarizer(args.assemblyai_key)
    else:
        print(f"Error: Unknown diarizer backend: {args.diarizer}")
        return

    try:
        # Build initial metadata
        metadata = {
            "filename": os.path.basename(audio_path),
            "configs": {
                "speedup": speedup,
                "auto_adjust": auto_adjust,
                "chunk_mode": chunk_mode,
                "chunk_duration": chunk_duration,
                "diarizer": args.diarizer,
                "assemblyai_key_used": bool(args.assemblyai_key) if args.diarizer == "assemblyai" else False
            },
            "audio_path": os.path.relpath(audio_path),
            "transcript_path": os.path.relpath(transcript_path),
            "summary_path": os.path.relpath(summary_path),
            "status": "processing"
        }
        update_metadata(metadata_path, metadata)

        if chunk_mode:
            print("=== Chunk Processing Mode ===")
            chunk_paths = chunk_audio_file(audio_path, chunk_duration, processed_dir, speedup)
            if args.diarizer == "assemblyai":
                transcript_segments = []
                speaker_segments = []
                for i, chunk_path in enumerate(chunk_paths):
                    print(f"AssemblyAI: Processing chunk {i+1}/{len(chunk_paths)}: {chunk_path}")
                    t_segments, s_segments = diarizer.diarize_and_transcribe_audio(chunk_path)
                    offset = i * chunk_duration * 60
                    for t in t_segments:
                        t['start'] += offset
                        t['end'] += offset
                    for s in s_segments:
                        s['start'] += offset
                        s['end'] += offset
                    transcript_segments.extend(t_segments)
                    speaker_segments.extend(s_segments)
            else:
                transcriber = WhisperTranscriber(OPENAI_API_KEY)
                transcript_segments = transcriber.transcribe_chunks(chunk_paths, chunk_duration)
                speaker_segments = diarizer.diarize_chunks(chunk_paths, chunk_duration)
            aligner = TranscriptAligner()
            conversation = aligner.align_transcript_with_speakers(transcript_segments, speaker_segments)
            aligner.save_to_csv(conversation, transcript_path)
            metadata["status"] = "transcribed"
            update_metadata(metadata_path, metadata)
            try:
                import subprocess
                result = subprocess.run([
                    'python', 'summarize_csv.py', transcript_path, '--output', summary_path
                ], capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"\n=== Summary Complete ===")
                    print(f"Summary written to: {summary_path}")
                    metadata["status"] = "summary_generated"
                    update_metadata(metadata_path, metadata)
                else:
                    print(f"[ERROR] Failed to summarize CSV.\n{result.stderr}")
            except Exception as e:
                print(f"[ERROR] Exception during summarization: {e}")
        else:
            print("=== Standard Processing Mode ===")
            processed_audio_path = preprocess_audio(audio_path, speedup, processed_dir)
            if not auto_adjust and not chunk_mode:
                processed_file_size_mb = os.path.getsize(processed_audio_path) / (1024 * 1024)
                if processed_file_size_mb > 24:
                    print(f"\nProcessed file size: {processed_file_size_mb:.1f}MB (Whisper API limit: 25MB)")
                    print("Switching to chunk processing mode...")
                    chunk_paths = chunk_audio_file(audio_path, chunk_duration, processed_dir, speedup)
                    transcriber = WhisperTranscriber(OPENAI_API_KEY)
                    transcript_segments = transcriber.transcribe_chunks(chunk_paths, chunk_duration)
                    speaker_segments = diarizer.diarize_chunks(chunk_paths, chunk_duration)
                    aligner = TranscriptAligner()
                    conversation = aligner.align_transcript_with_speakers(transcript_segments, speaker_segments)
                    aligner.save_to_csv(conversation, transcript_path)
                    metadata["status"] = "transcribed"
                    update_metadata(metadata_path, metadata)
                    print(f"\n=== Processing Complete ===")
                    print(f"Results saved to: {transcript_path}")
                    return
            if args.diarizer == "assemblyai":
                transcript_segments, speaker_segments = diarizer.diarize_and_transcribe_audio(processed_audio_path)
            else:
                transcriber = WhisperTranscriber(OPENAI_API_KEY)
                transcript_segments = transcriber.transcribe_audio(processed_audio_path)
                speaker_segments = diarizer.diarize_audio(processed_audio_path)
            aligner = TranscriptAligner()
            conversation = aligner.align_transcript_with_speakers(transcript_segments, speaker_segments)
            aligner.save_to_csv(conversation, transcript_path)
            metadata["status"] = "transcribed"
            update_metadata(metadata_path, metadata)
            try:
                import subprocess
                result = subprocess.run([
                    'python', 'summarize_csv.py', transcript_path, '--output', summary_path
                ], capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"\n=== Summary Complete ===")
                    print(f"Summary written to: {summary_path}")
                    metadata["status"] = "summary_generated"
                    update_metadata(metadata_path, metadata)
                else:
                    print(f"[ERROR] Failed to summarize CSV.\n{result.stderr}")
            except Exception as e:
                print(f"[ERROR] Exception during summarization: {e}")
        print(f"\n=== Processing Complete ===")
        print(f"Results saved to: {transcript_path}")
    except Exception as e:
        print(f"Error during processing: {str(e)}")
        return

if __name__ == "__main__":
    main() 