import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { Upload, FileAudio, Settings, Play } from 'lucide-react';
import toast from 'react-hot-toast';
import axios from 'axios';

const UploadPage = () => {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [configs, setConfigs] = useState({
    speedup: 1.0,
    auto_adjust: false,
    chunk: false,
    chunk_duration: 10,
    diarizer: 'huggingface'
  });
  const [isUploading, setIsUploading] = useState(false);

  const onDrop = (acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'audio/*': ['.wav', '.mp3', '.m4a', '.flac', '.aac']
    },
    multiple: false
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      toast.error('Please select an audio file');
      return;
    }

    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('speedup', configs.speedup);
    formData.append('auto_adjust', configs.auto_adjust);
    formData.append('chunk', configs.chunk);
    formData.append('chunk_duration', configs.chunk_duration);
    formData.append('diarizer', configs.diarizer);

    try {
      const response = await axios.post('/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      toast.success('Audio uploaded successfully! Processing started.');
      navigate(`/status/${response.data.audio_id}`);
    } catch (error) {
      console.error('Upload error:', error);
      toast.error(error.response?.data?.detail || 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Audio Transcription & Analysis
        </h1>
        <p className="text-lg text-gray-600">
          Upload your audio file and get AI-powered transcription with speaker diarization
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-8">
        {/* File Upload Section */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center mb-4">
            <FileAudio className="w-6 h-6 text-blue-600 mr-2" />
            <h2 className="text-xl font-semibold">Upload Audio File</h2>
          </div>

          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
              isDragActive
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-300 hover:border-gray-400'
            }`}
          >
            <input {...getInputProps()} />
            <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            {file ? (
              <div>
                <p className="text-green-600 font-medium">{file.name}</p>
                <p className="text-sm text-gray-500">
                  {(file.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            ) : (
              <div>
                <p className="text-lg font-medium text-gray-700">
                  {isDragActive ? 'Drop the file here' : 'Drag & drop audio file here'}
                </p>
                <p className="text-sm text-gray-500 mt-2">
                  or click to select file
                </p>
                <p className="text-xs text-gray-400 mt-2">
                  Supports: WAV, MP3, M4A, FLAC, AAC
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Configuration Section */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center mb-4">
            <Settings className="w-6 h-6 text-green-600 mr-2" />
            <h2 className="text-xl font-semibold">Processing Options</h2>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Speedup Factor
              </label>
              <input
                type="number"
                step="0.1"
                min="0.5"
                max="3.0"
                value={configs.speedup}
                onChange={(e) => setConfigs({...configs, speedup: parseFloat(e.target.value)})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={configs.auto_adjust}
              />
              <p className="text-xs text-gray-500 mt-1">
                Speed up audio to reduce processing time (1.0 = normal speed)
              </p>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="auto_adjust"
                checked={configs.auto_adjust}
                onChange={(e) => setConfigs({...configs, auto_adjust: e.target.checked})}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="auto_adjust" className="ml-2 text-sm text-gray-700">
                Auto-adjust speedup to fit API limits
              </label>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="chunk"
                checked={configs.chunk}
                onChange={(e) => setConfigs({...configs, chunk: e.target.checked})}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="chunk" className="ml-2 text-sm text-gray-700">
                Process in chunks (for large files)
              </label>
            </div>

            {configs.chunk && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Chunk Duration (minutes)
                </label>
                <input
                  type="number"
                  min="1"
                  max="30"
                  value={configs.chunk_duration}
                  onChange={(e) => setConfigs({...configs, chunk_duration: parseInt(e.target.value)})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Speaker Diarization
              </label>
              <select
                value={configs.diarizer}
                onChange={(e) => setConfigs({...configs, diarizer: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="huggingface">Hugging Face (Free)</option>
                <option value="assemblyai">AssemblyAI (Paid)</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={!file || isUploading}
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center"
            >
              {isUploading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Uploading...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 mr-2" />
                  Start Processing
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default UploadPage; 