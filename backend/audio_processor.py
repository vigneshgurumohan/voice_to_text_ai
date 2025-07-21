import os
import tempfile
from pydub import AudioSegment
import soundfile as sf
import numpy as np
import math

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def preprocess_audio(audio_path, speedup=1.0, processed_dir=None):
    """
    Preprocess audio file: convert to WAV format and optionally speed up.
    Save in processed_dir if provided, else temp.
    Reuse if already present.
    """
    print(f"Preprocessing audio: {audio_path}")
    base = os.path.splitext(os.path.basename(audio_path))[0]
    if processed_dir is None:
        raise ValueError("processed_dir must be provided and point to processed_audio/<audio_id>/")
    ensure_dir(processed_dir)
    processed_path = os.path.join(processed_dir, f"{base}_speed{speedup:.2f}.wav")
    
    # Check if processed file already exists
    print(f"Checking for existing processed file: {processed_path}")
    if os.path.exists(processed_path):
        file_size_mb = os.path.getsize(processed_path) / (1024 * 1024)
        print(f"✓ Found existing processed file ({file_size_mb:.1f}MB) - REUSING")
        return processed_path
    else:
        print("✗ No existing processed file found - PROCESSING FRESH")
    
    # Load audio file
    print("Loading original audio file...")
    audio = AudioSegment.from_file(audio_path)
    
    # Convert to mono if stereo
    if audio.channels > 1:
        audio = audio.set_channels(1)
        print("✓ Converted stereo to mono")
    else:
        print("✓ Audio is already mono")
    
    # Set sample rate to 16kHz (Whisper requirement)
    if audio.frame_rate != 16000:
        audio = audio.set_frame_rate(16000)
        print(f"✓ Converted sample rate to 16kHz (was {audio.frame_rate}Hz)")
    else:
        print("✓ Sample rate is already 16kHz")
    
    # Speed up audio if requested
    if speedup != 1.0:
        new_frame_rate = int(audio.frame_rate * speedup)
        audio = audio._spawn(audio.raw_data, overrides={'frame_rate': new_frame_rate})
        audio = audio.set_frame_rate(16000)
        print(f"✓ Sped up audio by {speedup}x")
    else:
        print("✓ No speedup applied (1.0x)")
    
    # Export as WAV
    print("Exporting processed audio...")
    audio.export(processed_path, format="wav")
    
    # Verify the file was created
    if os.path.exists(processed_path):
        file_size_mb = os.path.getsize(processed_path) / (1024 * 1024)
        print(f"✓ Processed audio saved: {processed_path} ({file_size_mb:.1f}MB)")
    else:
        print("✗ Error: Failed to save processed audio file")
    
    return processed_path


def get_audio_duration(audio_path):
    audio = AudioSegment.from_file(audio_path)
    return len(audio) / 1000.0  # Convert ms to seconds


def calculate_optimal_speedup(audio_path, target_size_mb=24):
    print(f"Calculating optimal speedup for {audio_path}")
    original_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
    print(f"Original file size: {original_size_mb:.1f}MB")
    if original_size_mb <= target_size_mb:
        print("File is already under size limit, no speedup needed")
        return 1.0
    required_speedup = original_size_mb / target_size_mb
    optimal_speedup = min(max(required_speedup, 1.0), 3.0)
    print(f"Optimal speedup calculated: {optimal_speedup:.2f}x")
    print(f"Estimated final size: {original_size_mb / optimal_speedup:.1f}MB")
    return optimal_speedup


def chunk_audio_file(audio_path, chunk_duration_minutes=10, processed_dir=None, speedup=1.0):
    """
    Split audio file into chunks for batch processing.
    Save in processed_dir if provided, reuse if already present.
    """
    print(f"Chunking audio file: {audio_path}")
    base = os.path.splitext(os.path.basename(audio_path))[0]
    if processed_dir is None:
        raise ValueError("processed_dir must be provided and point to processed_audio/<audio_id>/")
    ensure_dir(processed_dir)
    
    # Check for existing chunks first
    existing_chunks = []
    missing_chunks = []
    chunk_count = 0
    
    # Estimate number of chunks based on audio duration
    audio_duration = get_audio_duration(audio_path)
    estimated_chunks = int(audio_duration / (chunk_duration_minutes * 60)) + 1
    
    print(f"Checking for existing chunks (estimated {estimated_chunks} chunks)...")
    
    for i in range(estimated_chunks):
        chunk_path = os.path.join(processed_dir, f"chunk_{i:03d}_speed{speedup:.2f}.wav")
        if os.path.exists(chunk_path):
            chunk_size_mb = os.path.getsize(chunk_path) / (1024 * 1024)
            existing_chunks.append(chunk_path)
            print(f"✓ Found existing chunk {i+1}: {chunk_path} ({chunk_size_mb:.1f}MB)")
        else:
            missing_chunks.append(i)
            print(f"✗ Missing chunk {i+1}: {chunk_path}")
    
    if len(missing_chunks) == 0:
        print(f"✓ All {len(existing_chunks)} chunks found - REUSING")
        return existing_chunks
    
    print(f"✗ {len(missing_chunks)} chunks missing - PROCESSING FRESH")
    
    # Load audio
    print("Loading original audio file for chunking...")
    audio = AudioSegment.from_file(audio_path)
    
    # Convert to mono and 16kHz if needed
    if audio.channels > 1:
        audio = audio.set_channels(1)
        print("✓ Converted stereo to mono")
    else:
        print("✓ Audio is already mono")
        
    if audio.frame_rate != 16000:
        audio = audio.set_frame_rate(16000)
        print(f"✓ Converted sample rate to 16kHz")
    else:
        print("✓ Sample rate is already 16kHz")
    
    # Speed up if needed
    if speedup != 1.0:
        new_frame_rate = int(audio.frame_rate * speedup)
        audio = audio._spawn(audio.raw_data, overrides={'frame_rate': new_frame_rate})
        audio = audio.set_frame_rate(16000)
        print(f"✓ Applied {speedup}x speedup")
    else:
        print("✓ No speedup applied")
    
    chunk_duration_ms = chunk_duration_minutes * 60 * 1000
    chunks = []
    
    print(f"Creating chunks ({chunk_duration_minutes} minutes each)...")
    for i, start_ms in enumerate(range(0, len(audio), chunk_duration_ms)):
        end_ms = min(start_ms + chunk_duration_ms, len(audio))
        chunk = audio[start_ms:end_ms]
        chunk_path = os.path.join(processed_dir, f"chunk_{i:03d}_speed{speedup:.2f}.wav")
        
        # Check if this chunk already exists
        if os.path.exists(chunk_path):
            print(f"✓ Chunk {i+1} already exists: {chunk_path}")
            chunks.append(chunk_path)
            continue
            
        # Create new chunk
        chunk.export(chunk_path, format="wav")
        chunk_size_mb = os.path.getsize(chunk_path) / (1024 * 1024)
        chunks.append(chunk_path)
        print(f"✓ Created chunk {i+1}: {chunk_path} ({len(chunk)/1000:.1f}s, {chunk_size_mb:.1f}MB)")
    
    print(f"✓ Audio split into {len(chunks)} chunks")
    return chunks


def cleanup_chunks(chunk_paths):
    for chunk_path in chunk_paths:
        if os.path.exists(chunk_path):
            os.remove(chunk_path)
    print("Cleaned up temporary chunk files") 