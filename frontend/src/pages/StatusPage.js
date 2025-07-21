import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Clock, CheckCircle, AlertCircle, FileText, Download, X } from 'lucide-react';
import toast from 'react-hot-toast';
import axios from 'axios';

const SUMMARY_TYPE_KEY = 'defaultSummaryType';
const getDefaultSummaryType = () => localStorage.getItem(SUMMARY_TYPE_KEY) || 'general';
const setDefaultSummaryType = (type) => localStorage.setItem(SUMMARY_TYPE_KEY, type);

// Fallback prompt templates
const FALLBACK_PROMPT_TEMPLATES = {
  'general': 'You are an expert meeting summarizer. Create a comprehensive summary of this meeting transcript, highlighting key points, decisions, and action items.',
  'fsd': 'You are an expert technical writer. Extract functional requirements and technical specifications from this meeting transcript to create a Functional Specification Document (FSD).',
  'technical': 'You are a technical analyst. Create a detailed technical summary of this meeting, focusing on technical discussions, requirements, and implementation details.',
  'action_items': 'You are an expert project manager. Extract all action items and tasks from this meeting transcript. Format: 1. High Priority (This Week) 2. Medium Priority (Next 2 Weeks) 3. Low Priority (Future) 4. Follow-ups 5. Blocking Issues 6. Resources Needed. For each item include: Task, Assignee, Deadline, Dependencies, Notes.',
  'meeting_minutes': 'You are a professional meeting minutes writer. Create formal meeting minutes from this transcript, including: Meeting Info (Date, Time, Location), Attendees, Agenda, Discussion Points, Decisions Made, Action Items, Next Meeting.',
  'project_plan': 'You are a project management expert. Create a project plan from this meeting transcript, including: Project Overview, Objectives, Timeline, Milestones, Resources, Risk Assessment, Success Criteria.'
};

const StatusPage = () => {
  const { audioId } = useParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [summaryType, setSummaryType] = useState(getDefaultSummaryType());
  const [serverPrompts, setServerPrompts] = useState({});
  const [loadingPrompts, setLoadingPrompts] = useState(true);
  const [timeEstimate, setTimeEstimate] = useState(null);
  const [startTime, setStartTime] = useState(null);
  const [loadingMessage, setLoadingMessage] = useState('');

  // Fetch server prompts
  const fetchServerPrompts = async () => {
    try {
      setLoadingPrompts(true);
      const response = await axios.get('/prompts');
      const prompts = response.data.prompts || [];
      
      const promptContents = {};
      for (const promptName of prompts) {
        try {
          const contentResponse = await axios.get(`/prompts/${promptName}`);
          promptContents[promptName] = contentResponse.data.content;
        } catch (error) {
          console.warn(`Failed to fetch content for prompt ${promptName}:`, error);
        }
      }
      
      setServerPrompts(promptContents);
    } catch (error) {
      console.error('Error fetching server prompts:', error);
      toast.error('Failed to load server prompts, using fallback templates');
    } finally {
      setLoadingPrompts(false);
    }
  };

  // Get time estimates from self-learning model
  const getTimeEstimate = async (status) => {
    if (!status || !status.configs) {
      return null;
    }
    
    const { diarizer, speedup, chunk_mode, chunk_duration } = status.configs;
    
    // Use actual audio duration if available in metadata, otherwise estimate from filename
    let estimatedDuration = 10; // default 10 minutes
    
    if (status.actual_audio_duration_minutes) {
      // Use actual duration from backend processing
      estimatedDuration = status.actual_audio_duration_minutes;
      console.log(`[DEBUG] Using actual audio duration: ${estimatedDuration} minutes`);
    } else {
      // Fallback to filename estimation
      const filename = status.filename || '';
      if (filename.includes('min') || filename.includes('minute')) {
        const match = filename.match(/(\d+)\s*min/);
        if (match) estimatedDuration = parseInt(match[1]);
      }
      console.log(`[DEBUG] Using estimated duration from filename: ${estimatedDuration} minutes`);
    }
    
    try {
      const response = await axios.get('/timing-estimate', {
        params: {
          audio_duration_minutes: estimatedDuration,
          diarizer: diarizer,
          speedup: speedup,
          chunk_mode: chunk_mode,
          chunk_duration: chunk_duration
        }
      });
      
      console.log(`[DEBUG] Time estimate for ${estimatedDuration}min audio: ${response.data.audio_processing.estimated_seconds}s`);
      return response.data.audio_processing.estimated_seconds;
    } catch (error) {
      console.error('Error getting timing estimate:', error);
      // Fallback to simple calculation
      const baseTimePerMinute = diarizer === 'assemblyai' ? 30 : 60;
      const adjustedTimePerMinute = baseTimePerMinute / speedup;
      let totalEstimatedSeconds = estimatedDuration * adjustedTimePerMinute;
      
      if (chunk_mode) {
        const numChunks = Math.ceil(estimatedDuration / chunk_duration);
        totalEstimatedSeconds += numChunks * 30;
      }
      
      totalEstimatedSeconds += 60;
      console.log(`[DEBUG] Using fallback time estimate: ${Math.round(totalEstimatedSeconds)}s`);
      return Math.round(totalEstimatedSeconds);
    }
  };

  // Calculate time remaining
  const calculateTimeRemaining = () => {
    if (!startTime || !timeEstimate) return null;
    
    const elapsed = Math.floor((Date.now() - startTime) / 1000);
    const remaining = timeEstimate - elapsed;
    
    // Add some debugging
    if (process.env.NODE_ENV === 'development') {
      console.log(`[DEBUG] Time calculation: elapsed=${elapsed}s, estimate=${timeEstimate}s, remaining=${remaining}s`);
    }
    
    // If remaining time goes negative by more than 30 seconds, something is wrong with our estimate
    if (remaining < -30) {
      console.log('[DEBUG] Time estimate appears to be incorrect (gone negative), hiding progress');
      return null;
    }
    
    // Round to nearest whole second for cleaner display
    return remaining > 0 ? Math.round(remaining) : 0;
  };

  // Get start time from status for persistent progress
  const getStartTimeFromStatus = (status) => {
    if (status.status === 'processing' && status.processing_started_at) {
      return new Date(status.processing_started_at).getTime();
    } else if (status.status === 'summary_regenerating' && status.summary_started_at) {
      return new Date(status.summary_started_at).getTime();
    }
    return null;
  };

  useEffect(() => {
    let retryCount = 0;
    let isMounted = true;
    let pollInterval = null;
    
    const fetchStatus = async () => {
      try {
        const response = await axios.get(`/status/${audioId}`);
        const newStatus = response.data;
        
        if (!isMounted) return;
        
        setStatus(newStatus);
        setLoading(false);
        setLoadingMessage('');
        
        // Start polling once we have successful initial load
        if (!pollInterval) {
          pollInterval = setInterval(() => {
            if (isMounted) {
              fetchStatus();
            }
          }, 5000);
        }
        
        // Set start time and estimate from backend metadata
        const startTimeFromBackend = getStartTimeFromStatus(newStatus);
        
        if (startTimeFromBackend && !startTime) {
          setStartTime(startTimeFromBackend);
          getTimeEstimate(newStatus).then(estimate => {
            setTimeEstimate(estimate);
          });
        }
        
        // Recalculate time estimate if we got actual duration and status is still processing
        if (newStatus.actual_audio_duration_minutes && 
            newStatus.status === 'processing' && 
            startTime && 
            (!timeEstimate || newStatus.actual_audio_duration_minutes !== status?.actual_audio_duration_minutes)) {
          console.log('[DEBUG] Recalculating time estimate with actual audio duration');
          getTimeEstimate(newStatus).then(estimate => {
            setTimeEstimate(estimate);
          });
        }
        
        // Clear estimates when processing completes
        if (['transcribed', 'summary_generated', 'error', 'cancelled'].includes(newStatus.status)) {
          setStartTime(null);
          setTimeEstimate(null);
        }
      } catch (error) {
        console.error('Error fetching status:', error);
        
        if (!isMounted) return;
        
        // Handle 404 errors with retries (race condition after upload)
        if (error.response?.status === 404 && retryCount < 5) {
          retryCount++;
          console.log(`[DEBUG] Status not found, retrying... (attempt ${retryCount}/5)`);
          setLoadingMessage(`Setting up your audio processing... (attempt ${retryCount}/5)`);
          
          setTimeout(() => {
            if (isMounted) {
              fetchStatus();
            }
          }, 2000);
          return;
        }
        
        // After retries exhausted or other errors
        setLoading(false);
        toast.error('Failed to fetch status');
      }
    };

    fetchStatus();
    fetchServerPrompts();

    return () => {
      isMounted = false;
      if (pollInterval) {
        clearInterval(pollInterval);
      }
    };
  }, [audioId, startTime]);

  const getStatusIcon = (status) => {
    switch (status) {
      case 'processing':
        return <Clock className="w-6 h-6 text-yellow-500" />;
      case 'summary_regenerating':
        return <Clock className="w-6 h-6 text-yellow-500" />;
      case 'transcribed':
        return <CheckCircle className="w-6 h-6 text-green-500" />;
      case 'summary_generated':
        return <CheckCircle className="w-6 h-6 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-6 h-6 text-red-500" />;
      default:
        return <Clock className="w-6 h-6 text-gray-400" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'processing':
      case 'summary_regenerating':
        return 'bg-yellow-100 text-yellow-800';
      case 'transcribed':
        return 'bg-blue-100 text-blue-800';
      case 'summary_generated':
        return 'bg-green-100 text-green-800';
      case 'cancelled':
        return 'bg-gray-100 text-gray-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusMessage = (status) => {
    switch (status) {
      case 'processing':
        return 'Audio is being processed...';
      case 'summary_regenerating':
        return 'Summary is being regenerated...';
      case 'transcribed':
        return 'Transcription completed!';
      case 'summary_generated':
        return 'Summary generated successfully!';
      case 'cancelled':
        return 'Task was cancelled';
      case 'error':
        return 'An error occurred during processing';
      default:
        return 'Unknown status';
    }
  };

  const handleGenerateSummary = async () => {
    try {
      await axios.post(`/generate-summary/${audioId}`, {
        summary_type: summaryType || getDefaultSummaryType() || 'general',
        prompt: '',
        instructions: ''
      });
      toast.success('Summary generation started!');
      // Don't reload - let the polling update the status naturally
      // The status will change to 'summary_regenerating' and the UI will update automatically
    } catch (error) {
      console.error('Error generating summary:', error);
      toast.error(error.response?.data?.detail || 'Failed to generate summary');
    }
  };

  const handleCancelTask = async () => {
    try {
      await axios.post(`/cancel-task/${audioId}`);
      toast.success('Task cancelled successfully!');
      setTimeout(() => {
        window.location.reload();
      }, 1000);
    } catch (error) {
      console.error('Error cancelling task:', error);
      toast.error(error.response?.data?.detail || 'Failed to cancel task');
    }
  };

  const handleDownloadAudio = () => {
    try {
      console.log('[DEBUG] Starting audio download for audioId:', audioId);
      toast.loading('Downloading audio file...');
      
      // Simple approach: direct navigation to download URL
      const downloadUrl = `http://localhost:8000/download-audio/${audioId}`;
      console.log('[DEBUG] Download URL:', downloadUrl);
      
      // Direct navigation to download URL
      window.location.href = downloadUrl;
      
      // Show success message after a brief delay
      setTimeout(() => {
        toast.dismiss();
        toast.success('Audio file download started!');
        console.log('[DEBUG] Audio download completed');
      }, 1000);
      
    } catch (error) {
      console.error('[ERROR] Audio download failed:', error);
      toast.dismiss();
      toast.error('Failed to download audio file');
    }
  };

  // Format time remaining
  const formatTimeRemaining = (seconds) => {
    if (!seconds || seconds <= 0) return 'Almost done...';
    
    // Round to nearest whole second
    const roundedSeconds = Math.round(seconds);
    const minutes = Math.floor(roundedSeconds / 60);
    const remainingSeconds = roundedSeconds % 60;
    
    if (minutes > 0) {
      return `${minutes}m ${remainingSeconds}s remaining`;
    } else {
      return `${remainingSeconds}s remaining`;
    }
  };

  // Time remaining component
  const TimeRemaining = () => {
    const [currentTime, setCurrentTime] = useState(Date.now());
    
    useEffect(() => {
      if (startTime && timeEstimate) {
        const interval = setInterval(() => setCurrentTime(Date.now()), 1000);
        return () => clearInterval(interval);
      }
    }, [startTime, timeEstimate]);
    
    const remaining = calculateTimeRemaining();
    
    if (!remaining || !startTime || !timeEstimate) {
      return null;
    }
    
    const progress = Math.max(0, Math.min(100, ((timeEstimate - remaining) / timeEstimate) * 100));
    
    return (
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-blue-800">Processing Progress</span>
          <span className="text-sm text-blue-600">{formatTimeRemaining(remaining)}</span>
        </div>
        <div className="w-full bg-blue-200 rounded-full h-2">
          <div 
            className="bg-blue-600 h-2 rounded-full transition-all duration-1000" 
            style={{ width: `${progress}%` }}
          ></div>
        </div>
        <div className="text-xs text-blue-600 mt-1">
          {Math.round(progress)}% complete
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-4"></div>
        {loadingMessage ? (
          <div className="text-center">
            <p className="text-gray-600 mb-2">{loadingMessage}</p>
            <p className="text-sm text-gray-500">Please wait a moment...</p>
          </div>
        ) : (
          <p className="text-gray-600">Loading status...</p>
        )}
      </div>
    );
  }

  if (!status) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Audio Not Found</h2>
        <p className="text-gray-600 mb-4">The audio file you're looking for doesn't exist or failed to process.</p>
        <button
          onClick={() => navigate('/')}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          Upload New Audio
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow-md p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              {status.filename}
            </h1>
            <p className="text-gray-600">Audio ID: {audioId}</p>
          </div>
          <div className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(status.status)}`}>
            {status.status.replace('_', ' ').toUpperCase()}
          </div>
        </div>

        {/* Status Display */}
        <div className="flex items-center mb-6">
          {getStatusIcon(status.status)}
          <div className="ml-3">
            <p className="text-lg font-medium text-gray-900">
              {getStatusMessage(status.status)}
            </p>
            <p className="text-sm text-gray-500">
              Current status: {status.status}
            </p>
          </div>
        </div>

        {/* Time Remaining Progress - Only for audio transcription */}
        {status.status === 'processing' && (
          <>
            <TimeRemaining />
            {/* Fallback progress indicator if no timing data */}
            {(!startTime || !timeEstimate) && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-yellow-800">Audio Processing in Progress</span>
                  <span className="text-sm text-yellow-600">Calculating time...</span>
                </div>
                <div className="w-full bg-yellow-200 rounded-full h-2">
                  <div className="bg-yellow-600 h-2 rounded-full animate-pulse"></div>
                </div>
                <div className="text-xs text-yellow-600 mt-1">
                  Processing started at: {status.processing_started_at || 'Unknown'}
                </div>
              </div>
            )}
          </>
        )}

        {/* Summary Regeneration Progress */}
        {status.status === 'summary_regenerating' && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-yellow-800">Summary Generation in Progress</span>
              <span className="text-sm text-yellow-600">This will take a few moments</span>
            </div>
            <div className="w-full bg-yellow-200 rounded-full h-2">
              <div className="bg-yellow-600 h-2 rounded-full animate-pulse"></div>
            </div>
            <div className="text-xs text-yellow-600 mt-1">
              Using AI to generate your document...
            </div>
          </div>
        )}



        {/* Configuration Details */}
        {status.configs && (
          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Processing Configuration</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
              <div>
                <span className="font-medium">Speedup:</span> {status.configs.speedup}x
              </div>
              <div>
                <span className="font-medium">Auto-adjust:</span> {status.configs.auto_adjust ? 'Yes' : 'No'}
              </div>
              <div>
                <span className="font-medium">Chunk mode:</span> {status.configs.chunk_mode ? 'Yes' : 'No'}
              </div>
              {status.configs.chunk_mode && (
                <div>
                  <span className="font-medium">Chunk duration:</span> {status.configs.chunk_duration} min
                </div>
              )}
              <div>
                <span className="font-medium">Diarizer:</span> {status.configs.diarizer}
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex flex-wrap gap-4 items-center">

          {/* Download Audio Button - Available for all statuses except error/cancelled */}
          {!['error', 'cancelled'].includes(status.status) && (
            <button
              onClick={handleDownloadAudio}
              className="flex items-center px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors"
            >
              <Download className="w-4 h-4 mr-2" />
              Download Audio
            </button>
          )}

          {/* Cancel Task Button - Show only for audio transcription */}
          {status.status === 'processing' && (
            <button
              onClick={handleCancelTask}
              className="flex items-center px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
            >
              <X className="w-4 h-4 mr-2" />
              Cancel Transcription
            </button>
          )}

          {status.status === 'transcribed' && (
            <>
              <button
                onClick={() => navigate(`/transcript/${audioId}`)}
                className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                <FileText className="w-4 h-4 mr-2" />
                View Transcript
              </button>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleGenerateSummary}
                  className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
                >
                  <FileText className="w-4 h-4 mr-2" />
                  Generate AI Document
                </button>
                <select
                  value={summaryType}
                  onChange={e => setSummaryType(e.target.value)}
                  className="ml-2 p-2 border rounded"
                  title="Select summary type"
                >
                  <option value="general">General Summary</option>
                  <option value="fsd">Functional Specification</option>
                  <option value="technical">Technical Summary</option>
                  <option value="action_items">Action Items</option>
                  <option value="meeting_minutes">Meeting Minutes</option>
                  <option value="project_plan">Project Plan</option>
                  {Object.keys(serverPrompts).filter(name => name.startsWith('custom_templates.')).map(name => (
                    <option key={name} value={name}>
                      {name.replace('custom_templates.', '').replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </option>
                  ))}
                </select>
              </div>
            </>
          )}

          {status.status === 'summary_regenerating' && (
            <button
              onClick={() => navigate(`/transcript/${audioId}`)}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              <FileText className="w-4 h-4 mr-2" />
              View Transcript
            </button>
          )}

          {status.status === 'summary_generated' && (
            <>
              <button
                onClick={() => navigate(`/transcript/${audioId}`)}
                className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                <FileText className="w-4 h-4 mr-2" />
                View Transcript
              </button>
              <button
                onClick={() => navigate(`/document/${audioId}`)}
                className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
              >
                <FileText className="w-4 h-4 mr-2" />
                View AI Document
              </button>
            </>
          )}

          {status.status === 'cancelled' && (
            <div className="w-full bg-gray-50 border border-gray-200 rounded-md p-4">
              <p className="text-gray-800 mb-3">
                <strong>Task Cancelled:</strong> The processing was cancelled by the user.
              </p>
              <button
                onClick={() => navigate(`/`)}
                className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                <FileText className="w-4 h-4 mr-2" />
                Upload New Audio
              </button>
            </div>
          )}

          {status.status === 'error' && (
            <div className="w-full bg-red-50 border border-red-200 rounded-md p-4">
              <p className="text-red-800">
                <strong>Error:</strong> {status.error || 'An unknown error occurred'}
              </p>
            </div>
          )}
        </div>

        {/* Progress Steps */}
        <div className="mt-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Processing Steps</h3>
          <div className="space-y-3">
            <div className="flex items-center">
              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${
                ['processing', 'transcribed', 'summary_generated'].includes(status.status)
                  ? 'bg-green-500 text-white'
                  : 'bg-gray-300 text-gray-600'
              }`}>
                ✓
              </div>
              <span className="ml-3 text-gray-700">Audio uploaded</span>
            </div>
            <div className="flex items-center">
              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${
                ['transcribed', 'summary_generated'].includes(status.status)
                  ? 'bg-green-500 text-white'
                  : status.status === 'processing'
                  ? 'bg-yellow-500 text-white'
                  : 'bg-gray-300 text-gray-600'
              }`}>
                {status.status === 'processing' ? '⟳' : '✓'}
              </div>
              <span className="ml-3 text-gray-700">Transcription & diarization</span>
            </div>
            <div className="flex items-center">
              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${
                status.status === 'summary_generated'
                  ? 'bg-green-500 text-white'
                  : status.status === 'summary_regenerating'
                  ? 'bg-yellow-500 text-white'
                  : 'bg-gray-300 text-gray-600'
              }`}>
                {status.status === 'summary_regenerating' ? '⟳' : '✓'}
              </div>
              <span className="ml-3 text-gray-700">Summary generation</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StatusPage; 