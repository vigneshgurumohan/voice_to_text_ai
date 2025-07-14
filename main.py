import argparse
import os
import tempfile
from config import OPENAI_API_KEY, HUGGINGFACE_TOKEN

from audio_processor import (
    preprocess_audio, get_audio_duration, calculate_optimal_speedup, 
    chunk_audio_file, cleanup_chunks
)
from transcriber import WhisperTranscriber
from diarizer import SpeakerDiarizer
from aligner import TranscriptAligner

def get_default_output_name(audio_path):
    base = os.path.splitext(os.path.basename(audio_path))[0]
    candidate = f"{base}.csv"
    if not os.path.exists(candidate):
        return candidate
    version = 1
    while True:
        candidate = f"{base}_v{version}.csv"
        if not os.path.exists(candidate):
            return candidate
        version += 1

def get_processed_dir(audio_path):
    base = os.path.splitext(os.path.basename(audio_path))[0]
    processed_dir = os.path.join("processed_audio", base)
    if not os.path.exists(processed_dir):
        os.makedirs(processed_dir)
    return processed_dir

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
    parser.add_argument("audio_file", type=str, help="Path to the input audio file")
    parser.add_argument("--speedup", type=float, default=1.0, help="Speed up audio by this factor (e.g., 1.2)")
    parser.add_argument("--output", type=str, default=None, help="Output CSV file path")
    parser.add_argument("--auto-adjust", action="store_true", 
                       help="Automatically adjust speedup to get under 25MB limit")
    parser.add_argument("--chunk", action="store_true", 
                       help="Split large files into chunks and process separately")
    parser.add_argument("--chunk-duration", type=int, default=10, 
                       help="Duration of each chunk in minutes (default: 10)")
    args = parser.parse_args()

    audio_path = args.audio_file
    speedup = args.speedup
    output_path = args.output
    auto_adjust = args.auto_adjust
    chunk_mode = args.chunk
    chunk_duration = args.chunk_duration

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

    # Determine output file name
    if output_path is None:
        output_path = get_default_output_name(audio_path)

    # Determine processed audio directory
    processed_dir = get_processed_dir(audio_path)

    print(f"=== Meeting Audio Processing ===")
    print(f"Input file: {audio_path}")
    print(f"Output file: {output_path}")
    print(f"Processed audio directory: {processed_dir}")
    print(f"Audio duration: {get_audio_duration(audio_path):.1f} seconds")
    
    # Check if user specified options
    if auto_adjust and chunk_mode:
        print("Error: Cannot use both --auto-adjust and --chunk options together")
        return
    
    # Handle large file options
    if auto_adjust:
        print("Mode: Auto-adjust speedup")
        speedup = calculate_optimal_speedup(audio_path)
    elif chunk_mode:
        print(f"Mode: Chunk processing ({chunk_duration}min chunks)")
    else:
        print(f"Mode: Manual speedup ({speedup}x)")
    
    print()

    try:
        if chunk_mode:
            # Chunk processing mode
            print("=== Chunk Processing Mode ===")
            # Step 1: Split audio into chunks (reuse if present)
            chunk_paths = chunk_audio_file(audio_path, chunk_duration, processed_dir, speedup)
            # Step 2: Transcribe all chunks
            transcriber = WhisperTranscriber(OPENAI_API_KEY)
            transcript_segments = transcriber.transcribe_chunks(chunk_paths, chunk_duration)
            # Step 3: Diarize all chunks
            diarizer = SpeakerDiarizer(HUGGINGFACE_TOKEN)
            speaker_segments = diarizer.diarize_chunks(chunk_paths, chunk_duration)
            # Step 4: Align transcript with speakers
            aligner = TranscriptAligner()
            conversation = aligner.align_transcript_with_speakers(transcript_segments, speaker_segments)
            # Step 5: Save to CSV
            aligner.save_to_csv(conversation, output_path)
            # Clean up chunks (optional, comment out if you want to keep them)
            # cleanup_chunks(chunk_paths)
        else:
            # Standard processing mode (with optional auto-adjust)
            print("=== Standard Processing Mode ===")
            # Step 1: Preprocess audio (reuse if present)
            processed_audio_path = preprocess_audio(audio_path, speedup, processed_dir)
            
            # Check if processed file is too large and prompt if needed
            if not auto_adjust and not chunk_mode:
                processed_file_size_mb = os.path.getsize(processed_audio_path) / (1024 * 1024)
                if processed_file_size_mb > 24:  # Conservative limit
                    print(f"\nProcessed file size: {processed_file_size_mb:.1f}MB (Whisper API limit: 25MB)")
                    choice = prompt_for_large_file_option()
                    if choice == "auto-adjust":
                        # Recalculate optimal speedup and reprocess
                        print("Recalculating optimal speedup for processed file...")
                        optimal_speedup = calculate_optimal_speedup(processed_audio_path)
                        print(f"Optimal speedup for processed file: {optimal_speedup:.2f}x")
                        # Reprocess with new speedup
                        processed_audio_path = preprocess_audio(audio_path, optimal_speedup, processed_dir)
                    elif choice == "chunk":
                        # Switch to chunk mode
                        print("Switching to chunk processing mode...")
                        chunk_paths = chunk_audio_file(audio_path, chunk_duration, processed_dir, speedup)
                        transcriber = WhisperTranscriber(OPENAI_API_KEY)
                        transcript_segments = transcriber.transcribe_chunks(chunk_paths, chunk_duration)
                        diarizer = SpeakerDiarizer(HUGGINGFACE_TOKEN)
                        speaker_segments = diarizer.diarize_chunks(chunk_paths, chunk_duration)
                        aligner = TranscriptAligner()
                        conversation = aligner.align_transcript_with_speakers(transcript_segments, speaker_segments)
                        aligner.save_to_csv(conversation, output_path)
                        print(f"\n=== Processing Complete ===")
                        print(f"Results saved to: {output_path}")
                        return
            
            # Step 2: Transcribe with Whisper
            transcriber = WhisperTranscriber(OPENAI_API_KEY)
            transcript_segments = transcriber.transcribe_audio(processed_audio_path)
            # Step 3: Perform speaker diarization
            diarizer = SpeakerDiarizer(HUGGINGFACE_TOKEN)
            speaker_segments = diarizer.diarize_audio(processed_audio_path)
            # Step 4: Align transcript with speakers
            aligner = TranscriptAligner()
            conversation = aligner.align_transcript_with_speakers(transcript_segments, speaker_segments)
            # Step 5: Save to CSV
            aligner.save_to_csv(conversation, output_path)
            # Clean up processed audio (optional, comment out if you want to keep it)
            # if os.path.exists(processed_audio_path):
            #     os.remove(processed_audio_path)
            #     print("Cleaned up temporary files")
        print(f"\n=== Processing Complete ===")
        print(f"Results saved to: {output_path}")
    except Exception as e:
        print(f"Error during processing: {str(e)}")
        return

if __name__ == "__main__":
    main() 