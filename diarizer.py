import os
import tempfile
from pyannote.audio import Pipeline
from pyannote.audio.pipelines.utils.hook import ProgressHook
import torch
from typing import List, Dict, Any


class SpeakerDiarizer:
    def __init__(self, hf_token: str):
        """
        Initialize speaker diarizer with Hugging Face token.
        
        Args:
            hf_token (str): Hugging Face API token
        """
        self.hf_token = hf_token
        self.pipeline = None
        
    def load_pipeline(self):
        """Load the pyannote speaker diarization pipeline."""
        try:
            print("Loading speaker diarization pipeline...")
            self.pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=self.hf_token
            )
            
            # Use GPU if available, otherwise CPU
            if torch.cuda.is_available():
                self.pipeline = self.pipeline.to(torch.device("cuda"))
                print("Using GPU for diarization")
            else:
                print("Using CPU for diarization")
                
        except Exception as e:
            print(f"Error loading diarization pipeline: {str(e)}")
            raise
    
    def diarize_audio(self, audio_path: str) -> List[Dict[str, Any]]:
        """
        Perform speaker diarization on audio file.
        
        Args:
            audio_path (str): Path to audio file
            
        Returns:
            List[Dict]: List of speaker segments with timestamps
        """
        if self.pipeline is None:
            self.load_pipeline()
        
        print(f"Performing speaker diarization: {audio_path}")
        
        try:
            # Run diarization
            with ProgressHook() as hook:
                diarization = self.pipeline(audio_path, hook=hook)
            
            # Extract speaker segments
            segments = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                segments.append({
                    'start': turn.start,
                    'end': turn.end,
                    'speaker': speaker
                })
            
            print(f"Diarization completed. Found {len(segments)} speaker segments.")
            return segments
            
        except Exception as e:
            print(f"Error during diarization: {str(e)}")
            raise
    
    def diarize_chunks(self, chunk_paths: List[str], chunk_duration_minutes: int = 10) -> List[Dict[str, Any]]:
        """
        Perform speaker diarization on multiple audio chunks and merge results.
        
        Args:
            chunk_paths (List[str]): List of paths to audio chunks
            chunk_duration_minutes (int): Duration of each chunk in minutes
            
        Returns:
            List[Dict]: Merged speaker segments with adjusted timestamps
        """
        if self.pipeline is None:
            self.load_pipeline()
        
        print(f"Performing speaker diarization on {len(chunk_paths)} chunks...")
        
        all_segments = []
        chunk_offset = 0  # Time offset for each chunk
        
        for i, chunk_path in enumerate(chunk_paths):
            print(f"Diarizing chunk {i+1}/{len(chunk_paths)}: {chunk_path}")
            
            try:
                # Diarize this chunk
                chunk_segments = self.diarize_audio(chunk_path)
                
                # Adjust timestamps for this chunk
                for segment in chunk_segments:
                    segment['start'] += chunk_offset
                    segment['end'] += chunk_offset
                
                all_segments.extend(chunk_segments)
                
                # Update offset for next chunk
                chunk_offset += chunk_duration_minutes * 60  # Convert minutes to seconds
                
            except Exception as e:
                print(f"Error diarizing chunk {i+1}: {str(e)}")
                raise
        
        print(f"Batch diarization completed. Total speaker segments: {len(all_segments)}")
        return all_segments
    
    def save_diarization(self, segments: List[Dict], output_path: str):
        """
        Save diarization segments to JSON file.
        
        Args:
            segments (List[Dict]): Diarization segments
            output_path (str): Output file path
        """
        import json
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(segments, f, indent=2, ensure_ascii=False)
        print(f"Diarization results saved to: {output_path}") 