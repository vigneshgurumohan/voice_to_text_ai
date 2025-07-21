from celery import Celery
import os
import sys
import subprocess
import json
from datetime import datetime

# Add the current directory to Python path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import (
    find_input_audio, get_processed_dir, get_transcript_path, 
    get_summary_path, get_metadata_path, update_metadata
)
from audio_processor import preprocess_audio, chunk_audio_file
from transcriber import WhisperTranscriber
from diarizer import SpeakerDiarizer
from aligner import TranscriptAligner
from config import OPENAI_API_KEY, HUGGINGFACE_TOKEN, REDIS_URL
from prompt_manager import format_prompt
from timing_model import timing_model

# Celery configuration
celery_app = Celery(
    'audio_processor',
    broker=REDIS_URL,
    backend=None  # Explicitly disable result backend
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    # Note: Using thread pool - task termination not supported, but revocation works
)

# Debug: Print pool configuration
print(f"[DEBUG] Celery worker pool configured as: {celery_app.conf.get('worker_pool', 'default')} (thread pool - revocation only, no termination)")

@celery_app.task(bind=True)
def process_audio_task(self, audio_id: str, filename: str, speedup: float = 1.0, 
                      auto_adjust: bool = False, chunk: bool = False, 
                      chunk_duration: int = 10, diarizer: str = "huggingface",
                      actual_duration_minutes: float = None):
    """Background task to process audio file"""
    
    print(f"[DEBUG] Starting audio processing task {self.request.id} for audio {audio_id}")
    print(f"[DEBUG] Task can be revoked: {hasattr(self.request, 'revoked')}")
    print(f"[DEBUG] Actual duration passed to task: {actual_duration_minutes} minutes")
    
    start_time = datetime.now()
    
    try:
        # Update task status
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Starting audio processing...'}
        )
        
        # Find input audio file
        audio_path = find_input_audio(audio_id)
        base = os.path.splitext(os.path.basename(audio_path))[0]
        
        # Get paths
        processed_dir = get_processed_dir(audio_id)
        transcript_path = get_transcript_path(audio_id, base)
        summary_path = get_summary_path(audio_id, base)
        metadata_path = get_metadata_path(audio_id, base)
        
        # Initialize metadata
        processing_start_time = datetime.now().isoformat()
        
        metadata = {
            "filename": filename,
            "configs": {
                "speedup": speedup,
                "auto_adjust": auto_adjust,
                "chunk_mode": chunk,
                "chunk_duration": chunk_duration,
                "diarizer": diarizer,
                "assemblyai_key_used": False
            },
            "audio_path": os.path.relpath(audio_path),
            "transcript_path": os.path.relpath(transcript_path),
            "summary_path": os.path.relpath(summary_path),
            "status": "processing",
            "task_id": self.request.id,
            "processing_started_at": processing_start_time
        }
        
        # Add actual duration to metadata if available
        if actual_duration_minutes is not None:
            metadata["actual_audio_duration_minutes"] = actual_duration_minutes
            print(f"[DEBUG] Set actual duration in initial metadata: {actual_duration_minutes} minutes")
        
        update_metadata(metadata_path, metadata)
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'current': 10, 'total': 100, 'status': 'Preprocessing audio...'}
        )
        
        # Check if task was revoked (thread pool limitation: task continues but won't be picked up again)
        if getattr(self.request, 'revoked', False):
            print(f"[DEBUG] Task {self.request.id} was revoked during preprocessing")
            # Update metadata to cancelled status
            metadata["status"] = "cancelled"
            metadata["cancelled_at"] = datetime.now().isoformat()
            update_metadata(metadata_path, metadata)
            return {'status': 'cancelled', 'message': 'Task was cancelled'}
        
        # Preprocess audio
        if chunk:
            chunk_paths = chunk_audio_file(audio_path, chunk_duration, processed_dir, speedup)
            processed_audio_path = chunk_paths[0] if chunk_paths else None
        else:
            processed_audio_path = preprocess_audio(audio_path, speedup, processed_dir)
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'current': 30, 'total': 100, 'status': 'Transcribing audio...'}
        )
        
        # Debug: Log diarizer selection
        print(f"[DEBUG] Celery task received diarizer parameter: {diarizer}")
        
        # Initialize diarizer
        if diarizer == "huggingface":
            print(f"[DEBUG] Initializing HuggingFace diarizer")
            diarizer_instance = SpeakerDiarizer(HUGGINGFACE_TOKEN)
            metadata["configs"]["diarizer_used"] = "huggingface"
        else:
            print(f"[DEBUG] Initializing AssemblyAI diarizer")
            from diarizer_assemblyai import AssemblyAIDiarizer
            from config import ASSEMBLYAI_API_KEY
            diarizer_instance = AssemblyAIDiarizer(ASSEMBLYAI_API_KEY)
            metadata["configs"]["assemblyai_key_used"] = True
            metadata["configs"]["diarizer_used"] = "assemblyai"
        
        # Transcribe and diarize
        if chunk:
            if diarizer == "assemblyai":
                # Use AssemblyAI for both transcription and diarization of chunks
                print(f"[DEBUG] Using AssemblyAI for chunked transcription and diarization")
                transcript_segments, speaker_segments = diarizer_instance.transcribe_and_diarize_chunks(chunk_paths, chunk_duration)
                metadata["configs"]["transcription_method"] = "assemblyai_chunks"
            else:
                # Use Whisper for transcription and HuggingFace for diarization
                print(f"[DEBUG] Using Whisper + HuggingFace for chunked processing")
                transcriber = WhisperTranscriber(OPENAI_API_KEY)
                transcript_segments = transcriber.transcribe_chunks(chunk_paths, chunk_duration)
                speaker_segments = diarizer_instance.diarize_chunks(chunk_paths, chunk_duration)
                metadata["configs"]["transcription_method"] = "whisper_chunks"
        else:
            if diarizer == "assemblyai":
                print(f"[DEBUG] Using AssemblyAI for single file transcription and diarization")
                transcript_segments, speaker_segments = diarizer_instance.diarize_and_transcribe_audio(processed_audio_path)
                metadata["configs"]["transcription_method"] = "assemblyai_single"
            else:
                print(f"[DEBUG] Using Whisper + HuggingFace for single file processing")
                transcriber = WhisperTranscriber(OPENAI_API_KEY)
                transcript_segments = transcriber.transcribe_audio(processed_audio_path)
                speaker_segments = diarizer_instance.diarize_audio(processed_audio_path)
                metadata["configs"]["transcription_method"] = "whisper_single"
        
        # Check for revocation after transcription (thread pool limitation)
        if getattr(self.request, 'revoked', False):
            print(f"[DEBUG] Task {self.request.id} was revoked after transcription")
            metadata["status"] = "cancelled"
            metadata["cancelled_at"] = datetime.now().isoformat()
            update_metadata(metadata_path, metadata)
            return {'status': 'cancelled', 'message': 'Task was cancelled'}
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'current': 70, 'total': 100, 'status': 'Aligning transcript with speakers...'}
        )
        
        # Check if task was revoked (thread pool limitation: task continues but won't be picked up again)
        if getattr(self.request, 'revoked', False):
            print(f"[DEBUG] Task {self.request.id} was revoked during alignment")
            # Update metadata to cancelled status
            metadata["status"] = "cancelled"
            metadata["cancelled_at"] = datetime.now().isoformat()
            update_metadata(metadata_path, metadata)
            return {'status': 'cancelled', 'message': 'Task was cancelled'}
        
        # Align transcript with speakers
        aligner = TranscriptAligner()
        conversation = aligner.align_transcript_with_speakers(transcript_segments, speaker_segments)
        
        # Save transcript
        aligner.save_to_csv(conversation, transcript_path)
        
        # Calculate actual processing time
        end_time = datetime.now()
        actual_processing_time = (end_time - start_time).total_seconds()
        
        # Get actual audio duration from the file (not filename estimation)
        if actual_duration_minutes is not None:
            # Use the duration we already determined at upload
            print(f"[DEBUG] Using pre-calculated audio duration: {actual_duration_minutes:.2f} minutes")
        else:
            # Fallback: determine duration from file
            try:
                from audio_processor import get_audio_duration
                actual_duration_seconds = get_audio_duration(audio_path)
                actual_duration_minutes = actual_duration_seconds / 60.0
                print(f"[DEBUG] Calculated audio duration from file: {actual_duration_minutes:.2f} minutes ({actual_duration_seconds:.1f} seconds)")
            except Exception as e:
                print(f"[WARNING] Could not determine actual audio duration: {e}")
                # Fallback to filename-based estimation
                actual_duration_minutes = 10  # Default estimate
                if filename and ('min' in filename.lower() or 'minute' in filename.lower()):
                    import re
                    match = re.search(r'(\d+)\s*min', filename.lower())
                    if match:
                        actual_duration_minutes = float(match.group(1))
                print(f"[DEBUG] Using fallback duration estimate: {actual_duration_minutes} minutes")
        
        # Record timing data for learning
        print(f"[DEBUG] About to record timing data: {actual_processing_time}s for {actual_duration_minutes}min audio")
        try:
            timing_model.add_audio_processing_record(
                audio_duration_minutes=actual_duration_minutes,
                diarizer=diarizer,
                speedup=speedup,
                chunk_mode=chunk,
                chunk_duration=chunk_duration,
                actual_time_seconds=actual_processing_time,
                configs=metadata.get("configs", {})
            )
            print(f"[DEBUG] Successfully recorded timing data")
        except Exception as e:
            print(f"[ERROR] Failed to record timing data: {e}")
            import traceback
            traceback.print_exc()
        
        # Update metadata with actual duration
        metadata["status"] = "transcribed"
        metadata["actual_processing_time_seconds"] = actual_processing_time
        metadata["actual_audio_duration_minutes"] = actual_duration_minutes
        update_metadata(metadata_path, metadata)
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'current': 90, 'total': 100, 'status': 'Processing complete!'}
        )
        
        return {
            'current': 100,
            'total': 100,
            'status': 'Audio processing completed successfully',
            'audio_id': audio_id,
            'transcript_path': transcript_path
        }
        
    except Exception as e:
        # Update metadata with error status
        try:
            metadata["status"] = "error"
            metadata["error"] = str(e)
            update_metadata(metadata_path, metadata)
        except:
            pass
        
        raise e

@celery_app.task(bind=True)
def generate_summary_task(self, audio_id: str, prompt: str = None, instructions: str = None):
    """Background task to generate summary from transcript"""
    
    start_time = datetime.now()
    
    try:
        # Update task status
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Starting summary generation...'}
        )
        
        # Get metadata
        metadata_dir = os.path.join("..", "data", audio_id, "metadata")
        metadata_files = [f for f in os.listdir(metadata_dir) if f.endswith('.json')]
        if not metadata_files:
            raise Exception("Metadata not found")
        
        metadata_path = os.path.join(metadata_dir, metadata_files[0])
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # Store task ID for cancellation
        summary_start_time = datetime.now().isoformat()
        
        metadata["task_id"] = self.request.id
        metadata["summary_started_at"] = summary_start_time
        update_metadata(metadata_path, metadata)
        
        transcript_path = metadata.get("transcript_path")
        summary_path = metadata.get("summary_path")
        
        # Fix path resolution for Celery worker
        if transcript_path and not os.path.isabs(transcript_path):
            if transcript_path.startswith('data/'):
                transcript_path = os.path.join("..", transcript_path)
            elif not transcript_path.startswith('..'):
                transcript_path = os.path.join("..", transcript_path)
        
        if summary_path and not os.path.isabs(summary_path):
            if summary_path.startswith('data/'):
                summary_path = os.path.join("..", summary_path)
            elif not summary_path.startswith('..'):
                summary_path = os.path.join("..", summary_path)
        
        if not transcript_path or not os.path.exists(transcript_path):
            raise Exception(f"Transcript not found at: {transcript_path}")
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'current': 30, 'total': 100, 'status': 'Generating summary with LLM...'}
        )
        
        # Create a temporary prompt file to avoid command line argument issues with multi-line prompts
        import tempfile
        
        # Build command for summarize_csv.py - update path to current directory
        cmd = [
            'python', 'summarize_csv.py', transcript_path, '--output', summary_path
        ]
        
        # Use environment variables to pass prompt and instructions
        env = os.environ.copy()
        if prompt:
            env['CUSTOM_PROMPT'] = prompt
            cmd += ['--prompt', 'ENV_VAR']
        if instructions:
            env['CUSTOM_INSTRUCTIONS'] = instructions
            cmd += ['--instructions', 'ENV_VAR']
        
        # Debug: Print the command being executed
        print(f"[DEBUG] Executing command: {' '.join(cmd)}")
        print(f"[DEBUG] Prompt length: {len(prompt) if prompt else 0}")
        print(f"[DEBUG] Prompt preview: {prompt[:200] if prompt else 'None'}...")
        
        # Generate summary using summarize_csv.py - run from backend directory
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd(), env=env)
        
        if result.returncode != 0:
            raise Exception(f"Summary generation failed: {result.stderr}")
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'current': 90, 'total': 100, 'status': 'Summary generated successfully!'}
        )
        
        # Calculate actual processing time
        end_time = datetime.now()
        actual_processing_time = (end_time - start_time).total_seconds()
        
        # Get transcript length for timing model
        transcript_length_chars = 0
        if os.path.exists(transcript_path):
            with open(transcript_path, 'r', encoding='utf-8') as f:
                transcript_length_chars = len(f.read())
        
        # Get summary type from metadata
        summary_type = "general"
        if metadata.get("summary_config"):
            summary_type = metadata["summary_config"].get("summary_type", "general")
        
        # Record timing data for learning
        timing_model.add_summary_generation_record(
            transcript_length_chars=transcript_length_chars,
            summary_type=summary_type,
            actual_time_seconds=actual_processing_time,
            configs=metadata.get("configs", {})
        )
        
        # Update metadata with timestamp
        metadata["status"] = "summary_generated"
        metadata["summary_updated_at"] = datetime.now().isoformat()
        metadata["actual_summary_time_seconds"] = actual_processing_time
        print(f"[DEBUG] Updating metadata: status={metadata['status']}, timestamp={metadata['summary_updated_at']}")
        update_metadata(metadata_path, metadata)
        print(f"[DEBUG] Metadata updated successfully to: {metadata_path}")
        
        return {
            'current': 100,
            'total': 100,
            'status': 'Summary generated successfully',
            'audio_id': audio_id,
            'summary_path': summary_path
        }
        
    except Exception as e:
        # Update metadata with error status
        try:
            metadata["status"] = "summary_error"
            metadata["error"] = str(e)
            update_metadata(metadata_path, metadata)
        except:
            pass
        
        raise e

if __name__ == '__main__':
    celery_app.worker_main(['worker', '--loglevel=info']) #, '--pool=threads'
