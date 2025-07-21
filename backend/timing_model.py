import json
import os
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import statistics

class TimingModel:
    def __init__(self, data_file: str = "timing_data.json"):
        # Use absolute path to ensure file is saved in the backend directory
        if not os.path.isabs(data_file):
            self.data_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), data_file)
        else:
            self.data_file = data_file
        self.timing_data = self._load_timing_data()
    
    def _load_timing_data(self) -> Dict:
        """Load timing data from file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[WARNING] Could not load timing data: {e}")
        return {
            "audio_processing": [],
            "summary_generation": []
        }
    
    def _save_timing_data(self):
        """Save timing data to file"""
        try:
            print(f"[TIMING] Saving timing data to: {self.data_file}")
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.timing_data, f, indent=2, ensure_ascii=False)
            print(f"[TIMING] Successfully saved timing data with {len(self.timing_data['audio_processing'])} audio records and {len(self.timing_data['summary_generation'])} summary records")
        except Exception as e:
            print(f"[WARNING] Could not save timing data: {e}")
            print(f"[WARNING] File path: {self.data_file}")
            print(f"[WARNING] Current working directory: {os.getcwd()}")
    
    def add_audio_processing_record(self, 
                                  audio_duration_minutes: float,
                                  diarizer: str,
                                  speedup: float,
                                  chunk_mode: bool,
                                  chunk_duration: int,
                                  actual_time_seconds: float,
                                  configs: Dict = None):
        """Add a record of audio processing time"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "audio_duration_minutes": audio_duration_minutes,
            "diarizer": diarizer,
            "speedup": speedup,
            "chunk_mode": chunk_mode,
            "chunk_duration": chunk_duration,
            "actual_time_seconds": actual_time_seconds,
            "configs": configs or {}
        }
        
        print(f"[TIMING] Adding audio processing record: {audio_duration_minutes}min audio, {actual_time_seconds}s processing time")
        print(f"[TIMING] Record details: diarizer={diarizer}, speedup={speedup}, chunk_mode={chunk_mode}")
        self.timing_data["audio_processing"].append(record)
        self._save_timing_data()
        print(f"[TIMING] Added audio processing record: {audio_duration_minutes}min audio, {actual_time_seconds}s processing time")
    
    def add_summary_generation_record(self,
                                    transcript_length_chars: int,
                                    summary_type: str,
                                    actual_time_seconds: float,
                                    configs: Dict = None):
        """Add a record of summary generation time"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "transcript_length_chars": transcript_length_chars,
            "summary_type": summary_type,
            "actual_time_seconds": actual_time_seconds,
            "configs": configs or {}
        }
        
        self.timing_data["summary_generation"].append(record)
        self._save_timing_data()
        print(f"[TIMING] Added summary generation record: {transcript_length_chars} chars, {actual_time_seconds}s processing time")
    
    def estimate_audio_processing_time(self,
                                     audio_duration_minutes: float,
                                     diarizer: str,
                                     speedup: float,
                                     chunk_mode: bool,
                                     chunk_duration: int) -> Tuple[float, float]:
        """
        Estimate audio processing time based on historical data
        Returns: (estimated_seconds, confidence_score)
        """
        if not self.timing_data["audio_processing"]:
            # No historical data, use fallback estimates
            return self._fallback_audio_estimate(audio_duration_minutes, diarizer, speedup, chunk_mode, chunk_duration)
        
        # Filter relevant historical data
        print(f"[TIMING] Filtering for: diarizer={diarizer}, chunk_mode={chunk_mode}, speedup={speedup}")
        print(f"[TIMING] Total records available: {len(self.timing_data['audio_processing'])}")
        
        relevant_records = []
        for record in self.timing_data["audio_processing"]:
            if (record["diarizer"] == diarizer and 
                record["chunk_mode"] == chunk_mode and
                abs(record["speedup"] - speedup) < 0.1):  # Similar speedup
                relevant_records.append(record)
        
        print(f"[TIMING] Found {len(relevant_records)} exact matches")
        
        if not relevant_records:
            # No exact matches, use broader filtering
            relevant_records = [r for r in self.timing_data["audio_processing"] if r["diarizer"] == diarizer]
            print(f"[TIMING] Found {len(relevant_records)} records with matching diarizer only")
        
        if not relevant_records:
            # Still no matches, use all data
            relevant_records = self.timing_data["audio_processing"]
            print(f"[TIMING] No diarizer matches found, using all {len(relevant_records)} records")
        
        # Calculate time per minute for each record
        times_per_minute = []
        for record in relevant_records:
            if record["audio_duration_minutes"] > 0:
                time_per_minute = record["actual_time_seconds"] / record["audio_duration_minutes"]
                times_per_minute.append(time_per_minute)
                print(f"[TIMING] Using record: {record['audio_duration_minutes']}min -> {record['actual_time_seconds']}s ({time_per_minute:.1f}s/min) [diarizer={record['diarizer']}]")
        
        if not times_per_minute:
            return self._fallback_audio_estimate(audio_duration_minutes, diarizer, speedup, chunk_mode, chunk_duration)
        
        # Calculate estimate using median (more robust than mean)
        median_time_per_minute = statistics.median(times_per_minute)
        estimated_seconds = median_time_per_minute * audio_duration_minutes
        
        # Calculate confidence based on data consistency
        if len(times_per_minute) >= 3:
            std_dev = statistics.stdev(times_per_minute)
            mean_time = statistics.mean(times_per_minute)
            coefficient_of_variation = std_dev / mean_time if mean_time > 0 else 1.0
            confidence = max(0.1, min(1.0, 1.0 - coefficient_of_variation))
        else:
            confidence = 0.5  # Lower confidence with fewer samples
        
        print(f"[TIMING] Audio estimate: {estimated_seconds:.1f}s for {audio_duration_minutes}min audio (confidence: {confidence:.2f})")
        return estimated_seconds, confidence
    
    def estimate_summary_generation_time(self,
                                       transcript_length_chars: int,
                                       summary_type: str) -> Tuple[float, float]:
        """
        Estimate summary generation time based on historical data
        Returns: (estimated_seconds, confidence_score)
        """
        if not self.timing_data["summary_generation"]:
            # No historical data, use fallback estimate
            return self._fallback_summary_estimate(transcript_length_chars, summary_type)
        
        # Filter relevant historical data
        relevant_records = [r for r in self.timing_data["summary_generation"] if r["summary_type"] == summary_type]
        
        if not relevant_records:
            # No exact match, use all data
            relevant_records = self.timing_data["summary_generation"]
        
        # Calculate time per character for each record
        times_per_char = []
        for record in relevant_records:
            if record["transcript_length_chars"] > 0:
                time_per_char = record["actual_time_seconds"] / record["transcript_length_chars"]
                times_per_char.append(time_per_char)
        
        if not times_per_char:
            return self._fallback_summary_estimate(transcript_length_chars, summary_type)
        
        # Calculate estimate using median
        median_time_per_char = statistics.median(times_per_char)
        estimated_seconds = median_time_per_char * transcript_length_chars
        
        # Calculate confidence
        if len(times_per_char) >= 3:
            std_dev = statistics.stdev(times_per_char)
            mean_time = statistics.mean(times_per_char)
            coefficient_of_variation = std_dev / mean_time if mean_time > 0 else 1.0
            confidence = max(0.1, min(1.0, 1.0 - coefficient_of_variation))
        else:
            confidence = 0.5
        
        print(f"[TIMING] Summary estimate: {estimated_seconds:.1f}s for {transcript_length_chars} chars (confidence: {confidence:.2f})")
        return estimated_seconds, confidence
    
    def _fallback_audio_estimate(self,
                                audio_duration_minutes: float,
                                diarizer: str,
                                speedup: float,
                                chunk_mode: bool,
                                chunk_duration: int) -> Tuple[float, float]:
        """Fallback estimate when no historical data is available"""
        # Base processing time per minute (in seconds)
        base_time_per_minute = 30 if diarizer == "assemblyai" else 60
        
        # Apply speedup factor
        adjusted_time_per_minute = base_time_per_minute / speedup
        
        # Calculate total estimated time
        total_seconds = audio_duration_minutes * adjusted_time_per_minute
        
        # Add overhead for chunking
        if chunk_mode:
            num_chunks = max(1, int(audio_duration_minutes / chunk_duration))
            total_seconds += num_chunks * 30
        
        # Add fixed overhead
        total_seconds += 60
        
        return total_seconds, 0.3  # Low confidence for fallback estimates
    
    def _fallback_summary_estimate(self,
                                  transcript_length_chars: int,
                                  summary_type: str) -> Tuple[float, float]:
        """Fallback estimate for summary generation"""
        # Rough estimate: 0.001 seconds per character
        estimated_seconds = transcript_length_chars * 0.001 + 10  # Base 10 seconds
        return estimated_seconds, 0.3
    
    def get_timing_stats(self) -> Dict:
        """Get statistics about the timing model"""
        stats = {
            "total_audio_records": len(self.timing_data["audio_processing"]),
            "total_summary_records": len(self.timing_data["summary_generation"]),
            "last_updated": datetime.now().isoformat()
        }
        
        if self.timing_data["audio_processing"]:
            audio_times = [r["actual_time_seconds"] for r in self.timing_data["audio_processing"]]
            stats["audio_stats"] = {
                "avg_time": statistics.mean(audio_times),
                "median_time": statistics.median(audio_times),
                "min_time": min(audio_times),
                "max_time": max(audio_times)
            }
        
        if self.timing_data["summary_generation"]:
            summary_times = [r["actual_time_seconds"] for r in self.timing_data["summary_generation"]]
            stats["summary_stats"] = {
                "avg_time": statistics.mean(summary_times),
                "median_time": statistics.median(summary_times),
                "min_time": min(summary_times),
                "max_time": max(summary_times)
            }
        
        return stats

# Global instance
timing_model = TimingModel() 