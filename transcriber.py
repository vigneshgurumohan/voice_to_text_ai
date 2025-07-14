import os
import openai
from openai import OpenAI
import json
import re
from typing import List, Dict, Any


class WhisperTranscriber:
    def __init__(self, api_key: str):
        """
        Initialize Whisper transcriber with OpenAI API key.
        
        Args:
            api_key (str): OpenAI API key
        """
        self.client = OpenAI(api_key=api_key)
        self.max_file_size = 25 * 1024 * 1024  # 25MB limit for Whisper API
    
    def clean_text(self, text: str) -> str:
        """
        Clean and format transcription text.
        
        Args:
            text (str): Raw transcription text
            
        Returns:
            str: Cleaned and formatted text
        """
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Add basic sentence breaks for better readability
        # Add period if sentence doesn't end with punctuation
        if text and not text[-1] in '.!?':
            text += '.'
        
        # Capitalize first letter
        if text:
            text = text[0].upper() + text[1:]
        
        return text
    
    def transcribe_audio(self, audio_path: str) -> List[Dict[str, Any]]:
        """
        Transcribe audio file using OpenAI Whisper API with verbose JSON response.
        
        Args:
            audio_path (str): Path to audio file
            
        Returns:
            List[Dict]: List of transcription segments with timestamps
        """
        print(f"Transcribing audio: {audio_path}")
        
        # Check file size
        file_size = os.path.getsize(audio_path)
        file_size_mb = file_size / (1024 * 1024)
        print(f"Audio file size: {file_size_mb:.1f}MB")
        
        if file_size > self.max_file_size:
            raise ValueError(f"Audio file too large ({file_size_mb:.1f}MB). "
                           f"Whisper API limit is 25MB. Consider using speedup option.")
        
        try:
            print("Opening audio file for API call...")
            with open(audio_path, "rb") as audio_file:
                print("Making Whisper API call with verbose JSON...")
                # Use Whisper API with verbose JSON response for detailed segments
                response = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json"
                )
            
            print(f"API response received. Response type: {type(response)}")
            
            # Check if response is None
            if response is None:
                raise ValueError("Whisper API returned None response")
            
            # Check if response has segments attribute
            if not hasattr(response, 'segments'):
                print(f"Response attributes: {dir(response)}")
                print(f"Response content: {response}")
                raise ValueError("Whisper API response does not have segments attribute")
            
            # Check if segments is None or empty
            if response.segments is None:
                print("Response.segments is None")
                print(f"Response text: {getattr(response, 'text', 'No text attribute')}")
                print(f"Response duration: {getattr(response, 'duration', 'No duration attribute')}")
                print(f"Response language: {getattr(response, 'language', 'No language attribute')}")
                
                # Create fallback segment from text if available
                if hasattr(response, 'text') and response.text.strip():
                    fallback_duration = getattr(response, 'duration', file_size_mb * 0.6)
                    segments = [{
                        'start': 0.0,
                        'end': fallback_duration,
                        'text': self.clean_text(response.text),
                        'words': [],
                        'confidence': 0.5  # Low confidence for fallback
                    }]
                    print(f"Created fallback segment with duration: {fallback_duration:.1f}s")
                    return segments
                else:
                    print("No transcription text received")
                    return []
            
            print(f"Number of segments in response: {len(response.segments)}")
            print(f"Segments type: {type(response.segments)}")
            
            # If no segments, check if there's text and create a fallback segment
            if len(response.segments) == 0:
                print(f"Response text: {getattr(response, 'text', 'No text attribute')}")
                print(f"Response duration: {getattr(response, 'duration', 'No duration attribute')}")
                print(f"Response language: {getattr(response, 'language', 'No language attribute')}")
                
                # Create fallback segment from text if available
                if hasattr(response, 'text') and response.text.strip():
                    fallback_duration = getattr(response, 'duration', file_size_mb * 0.6)
                    segments = [{
                        'start': 0.0,
                        'end': fallback_duration,
                        'text': self.clean_text(response.text),
                        'words': [],
                        'confidence': 0.5  # Low confidence for fallback
                    }]
                    print(f"Created fallback segment with duration: {fallback_duration:.1f}s")
                    return segments
                else:
                    print("No transcription text received")
                    return []
            
            # Extract segments with timestamps and word-level details
            segments = []
            for i, segment in enumerate(response.segments):
                try:
                    print(f"Processing segment {i+1}: start={segment.start:.2f}s, end={segment.end:.2f}s")
                    
                    # Clean the text
                    cleaned_text = self.clean_text(segment.text)
                    
                    # Extract word-level timestamps if available
                    words = []
                    if hasattr(segment, 'words') and segment.words:
                        for word in segment.words:
                            words.append({
                                'word': word.word,
                                'start': word.start,
                                'end': word.end
                            })
                    
                    segment_data = {
                        'start': segment.start,
                        'end': segment.end,
                        'text': cleaned_text,
                        'words': words,
                        'confidence': getattr(segment, 'confidence', 0.8)  # Default confidence
                    }
                    
                    # Only add segments with actual text
                    if cleaned_text.strip():
                        segments.append(segment_data)
                        print(f"  Text: '{cleaned_text[:50]}{'...' if len(cleaned_text) > 50 else ''}'")
                        print(f"  Words: {len(words)}")
                    else:
                        print(f"  Skipping empty segment")
                        
                except Exception as e:
                    print(f"Error processing segment {i}: {str(e)}")
                    print(f"Segment data: {segment}")
                    raise
            
            print(f"Transcription completed. Found {len(segments)} valid segments.")
            return segments
            
        except Exception as e:
            print(f"Error during transcription: {str(e)}")
            print(f"Error type: {type(e)}")
            # Print more details about the error
            if hasattr(e, 'response'):
                print(f"API Response: {e.response}")
            raise
    
    def transcribe_chunks(self, chunk_paths: List[str], chunk_duration_minutes: int = 10) -> List[Dict[str, Any]]:
        """
        Transcribe multiple audio chunks and merge results with proper timestamp adjustment.
        
        Args:
            chunk_paths (List[str]): List of paths to audio chunks
            chunk_duration_minutes (int): Duration of each chunk in minutes
            
        Returns:
            List[Dict]: Merged transcription segments with adjusted timestamps
        """
        print(f"Transcribing {len(chunk_paths)} audio chunks...")
        
        all_segments = []
        chunk_offset = 0  # Time offset for each chunk
        
        for i, chunk_path in enumerate(chunk_paths):
            print(f"Processing chunk {i+1}/{len(chunk_paths)}: {chunk_path}")
            
            try:
                # Transcribe this chunk
                chunk_segments = self.transcribe_audio(chunk_path)
                
                # Check if chunk_segments is None or empty
                if chunk_segments is None:
                    print(f"Warning: Chunk {i+1} returned None segments, skipping...")
                    continue
                
                if len(chunk_segments) == 0:
                    print(f"Warning: Chunk {i+1} returned empty segments, skipping...")
                    continue
                
                # Adjust timestamps for this chunk
                for segment in chunk_segments:
                    segment['start'] += chunk_offset
                    segment['end'] += chunk_offset
                    
                    # Adjust word timestamps too
                    for word in segment.get('words', []):
                        word['start'] += chunk_offset
                        word['end'] += chunk_offset
                
                all_segments.extend(chunk_segments)
                
                # Update offset for next chunk
                chunk_offset += chunk_duration_minutes * 60  # Convert minutes to seconds
                
            except Exception as e:
                print(f"Error transcribing chunk {i+1}: {str(e)}")
                print(f"Chunk path: {chunk_path}")
                print(f"Chunk exists: {os.path.exists(chunk_path)}")
                if os.path.exists(chunk_path):
                    chunk_size = os.path.getsize(chunk_path) / (1024 * 1024)
                    print(f"Chunk size: {chunk_size:.1f}MB")
                raise
        
        print(f"Batch transcription completed. Total segments: {len(all_segments)}")
        return all_segments
    
    def save_transcript(self, segments: List[Dict], output_path: str):
        """
        Save transcription segments to JSON file.
        
        Args:
            segments (List[Dict]): Transcription segments
            output_path (str): Output file path
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(segments, f, indent=2, ensure_ascii=False)
        print(f"Transcript saved to: {output_path}") 