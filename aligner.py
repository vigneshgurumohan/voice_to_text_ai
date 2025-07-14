from typing import List, Dict, Any
import pandas as pd


class TranscriptAligner:
    def __init__(self):
        """Initialize the transcript aligner."""
        pass
    
    def align_transcript_with_speakers(self, 
                                     transcript_segments: List[Dict], 
                                     speaker_segments: List[Dict]) -> List[Dict]:
        """
        Align transcription segments with speaker diarization results.
        
        Args:
            transcript_segments (List[Dict]): Transcription segments with timestamps
            speaker_segments (List[Dict]): Speaker segments with timestamps
            
        Returns:
            List[Dict]: Aligned conversation with speaker labels
        """
        print("Aligning transcript with speaker diarization...")
        
        aligned_conversation = []
        
        for trans_segment in transcript_segments:
            trans_start = trans_segment['start']
            trans_end = trans_segment['end']
            trans_text = trans_segment['text']
            
            # Find the speaker who spoke during this time segment
            speaker = self._find_speaker_for_time(trans_start, trans_end, speaker_segments)
            
            aligned_conversation.append({
                'timestamp_start': trans_start,
                'timestamp_end': trans_end,
                'speaker': speaker,
                'text': trans_text
            })
        
        print(f"Alignment completed. Processed {len(aligned_conversation)} segments.")
        return aligned_conversation
    
    def _find_speaker_for_time(self, start_time: float, end_time: float, 
                              speaker_segments: List[Dict]) -> str:
        """
        Find which speaker was active during a given time period.
        
        Args:
            start_time (float): Start time of transcript segment
            end_time (float): End time of transcript segment
            speaker_segments (List[Dict]): Speaker segments
            
        Returns:
            str: Speaker label
        """
        # Find speaker segments that overlap with the transcript segment
        overlapping_speakers = []
        
        for speaker_seg in speaker_segments:
            speaker_start = speaker_seg['start']
            speaker_end = speaker_seg['end']
            
            # Check for overlap
            if (speaker_start < end_time and speaker_end > start_time):
                overlap_start = max(start_time, speaker_start)
                overlap_end = min(end_time, speaker_end)
                overlap_duration = overlap_end - overlap_start
                
                overlapping_speakers.append({
                    'speaker': speaker_seg['speaker'],
                    'overlap_duration': overlap_duration
                })
        
        if not overlapping_speakers:
            return "Unknown"
        
        # Return the speaker with the longest overlap
        best_speaker = max(overlapping_speakers, key=lambda x: x['overlap_duration'])
        return best_speaker['speaker']
    
    def save_to_csv(self, conversation: List[Dict], output_path: str):
        """
        Save aligned conversation to CSV file.
        
        Args:
            conversation (List[Dict]): Aligned conversation
            output_path (str): Output CSV file path
        """
        # Convert to DataFrame
        df = pd.DataFrame(conversation)
        
        # Format timestamps for better readability
        df['timestamp_start'] = df['timestamp_start'].apply(self._format_timestamp)
        df['timestamp_end'] = df['timestamp_end'].apply(self._format_timestamp)
        
        # Save to CSV
        df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"Conversation saved to CSV: {output_path}")
        
        # Print summary
        print(f"\nConversation Summary:")
        print(f"Total segments: {len(conversation)}")
        print(f"Speakers identified: {df['speaker'].nunique()}")
        print(f"Speakers: {', '.join(df['speaker'].unique())}")
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds to MM:SS format."""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}" 