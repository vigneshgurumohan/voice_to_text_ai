import os
import json
from datetime import datetime

def find_input_audio(audio_id: str) -> str:
    """Find the input audio file for a given audio ID"""
    # Update path to look in parent directory for data
    input_dir = os.path.join("..", "data", audio_id, "input_audio")
    if not os.path.exists(input_dir):
        raise FileNotFoundError(f"Input directory not found for audio ID: {audio_id}")
    
    audio_files = [f for f in os.listdir(input_dir) if f.lower().endswith(('.wav', '.mp3', '.m4a', '.flac', '.aac'))]
    if not audio_files:
        raise FileNotFoundError(f"No audio files found in {input_dir}")
    
    return os.path.join(input_dir, audio_files[0])

def get_processed_dir(audio_id: str) -> str:
    """Get the processed audio directory for a given audio ID"""
    # Update path to look in parent directory for data
    processed_dir = os.path.join("..", "data", audio_id, "processed_audio")
    os.makedirs(processed_dir, exist_ok=True)
    return processed_dir

def get_transcript_path(audio_id: str, base_name: str) -> str:
    """Get the transcript file path for a given audio ID"""
    # Update path to look in parent directory for data
    transcript_dir = os.path.join("..", "data", audio_id, "transcript")
    os.makedirs(transcript_dir, exist_ok=True)
    return os.path.join(transcript_dir, f"{base_name}.csv")

def get_summary_path(audio_id: str, base_name: str) -> str:
    """Get the summary file path for a given audio ID"""
    # Update path to look in parent directory for data
    document_dir = os.path.join("..", "data", audio_id, "document")
    os.makedirs(document_dir, exist_ok=True)
    return os.path.join(document_dir, f"{base_name}.txt")

def get_metadata_path(audio_id: str, base_name: str) -> str:
    """Get the metadata file path for a given audio ID"""
    # Update path to look in parent directory for data
    metadata_dir = os.path.join("..", "data", audio_id, "metadata")
    os.makedirs(metadata_dir, exist_ok=True)
    return os.path.join(metadata_dir, f"{base_name}.json")

def update_metadata(metadata_path: str, metadata: dict):
    """Update metadata file with new information"""
    metadata['last_updated'] = datetime.now().isoformat()
    print(f"[DEBUG] update_metadata: Writing to {metadata_path}")
    print(f"[DEBUG] update_metadata: Status = {metadata.get('status')}")
    print(f"[DEBUG] update_metadata: Summary updated at = {metadata.get('summary_updated_at')}")
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"[DEBUG] update_metadata: File written successfully")
