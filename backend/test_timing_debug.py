#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from timing_model import timing_model

def test_timing_model():
    print("=== TIMING MODEL DEBUG TEST ===")
    
    # Test AssemblyAI filtering
    print("\n1. Testing AssemblyAI estimation:")
    estimated_time, confidence = timing_model.estimate_audio_processing_time(
        audio_duration_minutes=10.0,
        diarizer="assemblyai",
        speedup=1.0,
        chunk_mode=False,
        chunk_duration=10
    )
    print(f"AssemblyAI Estimate: {estimated_time:.1f}s (confidence: {confidence:.2f})")
    
    # Test HuggingFace filtering
    print("\n2. Testing HuggingFace estimation:")
    estimated_time, confidence = timing_model.estimate_audio_processing_time(
        audio_duration_minutes=10.0,
        diarizer="huggingface",
        speedup=1.0,
        chunk_mode=False,
        chunk_duration=10
    )
    print(f"HuggingFace Estimate: {estimated_time:.1f}s (confidence: {confidence:.2f})")
    
    # Show data statistics
    print("\n3. Data statistics:")
    stats = timing_model.get_timing_stats()
    print(f"Total audio records: {stats['total_audio_records']}")
    
    # Count by diarizer
    assemblyai_count = 0
    huggingface_count = 0
    for record in timing_model.timing_data["audio_processing"]:
        if record["diarizer"] == "assemblyai":
            assemblyai_count += 1
        elif record["diarizer"] == "huggingface":
            huggingface_count += 1
    
    print(f"AssemblyAI records: {assemblyai_count}")
    print(f"HuggingFace records: {huggingface_count}")
    
    # Show some sample records
    print("\n4. Sample AssemblyAI records:")
    ai_records = [r for r in timing_model.timing_data["audio_processing"] if r["diarizer"] == "assemblyai"]
    for i, record in enumerate(ai_records[:3]):
        duration = record["audio_duration_minutes"]
        time_taken = record["actual_time_seconds"]
        rate = time_taken / duration if duration > 0 else 0
        print(f"  Record {i+1}: {duration}min -> {time_taken:.1f}s ({rate:.1f}s/min)")
    
    print("\n5. Sample HuggingFace records:")
    hf_records = [r for r in timing_model.timing_data["audio_processing"] if r["diarizer"] == "huggingface"]
    for i, record in enumerate(hf_records[:3]):
        duration = record["audio_duration_minutes"]
        time_taken = record["actual_time_seconds"]
        rate = time_taken / duration if duration > 0 else 0
        print(f"  Record {i+1}: {duration}min -> {time_taken:.1f}s ({rate:.1f}s/min)")

if __name__ == "__main__":
    test_timing_model() 