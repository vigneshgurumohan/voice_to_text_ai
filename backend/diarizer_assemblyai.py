import os
import time
import requests
from typing import List, Dict, Any, Tuple
import subprocess

class AssemblyAIDiarizer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {"authorization": self.api_key}
        self.upload_url = "https://api.assemblyai.com/v2/upload"
        self.transcript_url = "https://api.assemblyai.com/v2/transcript"
        self.poll_url = "https://api.assemblyai.com/v2/transcript/{}"

    def _ensure_standard_mp3(self, audio_path: str) -> str:
        # Output path for re-encoded file
        if audio_path.endswith('_pcm.mp3'):
            return audio_path
        out_path = os.path.splitext(audio_path)[0] + '_pcm.mp3'
        if not os.path.exists(out_path):
            print(f"Re-encoding {audio_path} to standard MP3 for AssemblyAI...")
            subprocess.run([
                'ffmpeg', '-y', '-i', audio_path,
                '-ar', '16000', '-ac', '1', '-codec:a', 'libmp3lame', out_path
            ], check=True)
        return out_path

    def _upload_audio(self, audio_path: str) -> str:
        print(f"Uploading audio to AssemblyAI: {audio_path}")
        with open(audio_path, "rb") as f:
            response = requests.post(self.upload_url, headers=self.headers, files={"file": f})
        response.raise_for_status()
        audio_url = response.json()["upload_url"]
        print(f"Audio uploaded. URL: {audio_url}")
        return audio_url

    def _request_transcription(self, audio_url: str) -> str:
        json = {
            "audio_url": audio_url,
            "speaker_labels": True
        }
        response = requests.post(self.transcript_url, json=json, headers=self.headers)
        response.raise_for_status()
        transcript_id = response.json()["id"]
        print(f"Transcription requested. ID: {transcript_id}")
        return transcript_id

    def _poll_transcription(self, transcript_id: str) -> Dict[str, Any]:
        print("Polling for transcription result...")
        while True:
            response = requests.get(self.poll_url.format(transcript_id), headers=self.headers)
            response.raise_for_status()
            data = response.json()
            status = data["status"]
            if status == "completed":
                print("Transcription completed.")
                return data
            elif status == "failed" or status == "error":
                print("Transcription failed or errored.")
                print("AssemblyAI error details:", data)
                raise RuntimeError(f"AssemblyAI transcription failed: {data}")
            else:
                print(f"Status: {status}. Waiting 5 seconds...")
                time.sleep(5)

    def diarize_audio(self, audio_path: str) -> List[Dict[str, Any]]:
        audio_path = self._ensure_standard_mp3(audio_path)
        audio_url = self._upload_audio(audio_path)
        transcript_id = self._request_transcription(audio_url)
        data = self._poll_transcription(transcript_id)
        segments = []
        utterances = data.get("utterances", [])
        for utt in utterances:
            segments.append({
                "start": utt["start"] / 1000.0,  # ms to seconds
                "end": utt["end"] / 1000.0,
                "speaker": utt["speaker"]
            })
        print(f"Diarization completed. Found {len(segments)} speaker segments.")
        return segments

    def diarize_chunks(self, chunk_paths: List[str], chunk_duration_minutes: int = 10) -> List[Dict[str, Any]]:
        all_segments = []
        chunk_offset = 0  # Time offset for each chunk
        for i, chunk_path in enumerate(chunk_paths):
            print(f"Diarizing chunk {i+1}/{len(chunk_paths)}: {chunk_path}")
            chunk_segments = self.diarize_audio(chunk_path)
            # Adjust timestamps for this chunk
            for segment in chunk_segments:
                segment['start'] += chunk_offset
                segment['end'] += chunk_offset
            all_segments.extend(chunk_segments)
            chunk_offset += chunk_duration_minutes * 60  # Convert minutes to seconds
        print(f"Batch diarization completed. Total speaker segments: {len(all_segments)}")
        return all_segments

    def transcribe_and_diarize_chunks(self, chunk_paths: List[str], chunk_duration_minutes: int = 10) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Transcribe and diarize multiple chunks using AssemblyAI.
        Returns (transcript_segments, speaker_segments) with adjusted timestamps.
        """
        all_transcript_segments = []
        all_speaker_segments = []
        chunk_offset = 0  # Time offset for each chunk
        
        for i, chunk_path in enumerate(chunk_paths):
            print(f"Processing chunk {i+1}/{len(chunk_paths)} with AssemblyAI: {chunk_path}")
            chunk_transcript, chunk_speaker = self.diarize_and_transcribe_audio(chunk_path)
            
            # Adjust timestamps for this chunk
            for segment in chunk_transcript:
                segment['start'] += chunk_offset
                segment['end'] += chunk_offset
            for segment in chunk_speaker:
                segment['start'] += chunk_offset
                segment['end'] += chunk_offset
            
            all_transcript_segments.extend(chunk_transcript)
            all_speaker_segments.extend(chunk_speaker)
            chunk_offset += chunk_duration_minutes * 60  # Convert minutes to seconds
        
        print(f"Batch transcription and diarization completed. Total transcript segments: {len(all_transcript_segments)}, speaker segments: {len(all_speaker_segments)}")
        return all_transcript_segments, all_speaker_segments

    def diarize_and_transcribe_audio(self, audio_path: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Returns (transcript_segments, speaker_segments) from AssemblyAI API.
        transcript_segments: list of dicts with 'start', 'end', 'text'
        speaker_segments: list of dicts with 'start', 'end', 'speaker'
        """
        audio_path = self._ensure_standard_mp3(audio_path)
        audio_url = self._upload_audio(audio_path)
        transcript_id = self._request_transcription(audio_url)
        data = self._poll_transcription(transcript_id)
        # Transcript segments (utterances)
        transcript_segments = []
        speaker_segments = []
        utterances = data.get("utterances", [])
        for utt in utterances:
            transcript_segments.append({
                "start": utt["start"] / 1000.0,
                "end": utt["end"] / 1000.0,
                "text": utt["text"].strip()
            })
            speaker_segments.append({
                "start": utt["start"] / 1000.0,
                "end": utt["end"] / 1000.0,
                "speaker": utt["speaker"]
            })
        print(f"AssemblyAI: Found {len(transcript_segments)} transcript segments and {len(speaker_segments)} speaker segments.")
        return transcript_segments, speaker_segments 