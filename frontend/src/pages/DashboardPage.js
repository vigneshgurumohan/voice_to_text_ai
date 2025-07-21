import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  BarChart3, FileAudio, Clock, CheckCircle, AlertCircle, 
  FileText, Trash2, RefreshCw, X
} from 'lucide-react';
import toast from 'react-hot-toast';
import axios from 'axios';

const DashboardPage = () => {
  const navigate = useNavigate();
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [processingTimes, setProcessingTimes] = useState({});
  const [timeEstimates, setTimeEstimates] = useState({});

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    try {
      const response = await axios.get('/dashboard');
      setDashboard(response.data);
      
      // Load time estimates for processing tasks
      const estimates = {};
      for (const audio of response.data.audios || []) {
        if (audio.status === 'processing') {
          try {
            const estimate = await getTimeEstimate(audio);
            estimates[audio.audio_id] = estimate;
          } catch (error) {
            console.error(`Error getting estimate for ${audio.audio_id}:`, error);
          }
        }
      }
      setTimeEstimates(estimates);
    } catch (error) {
      console.error('Error fetching dashboard:', error);
      toast.error('Failed to fetch dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchDashboard();
    setRefreshing(false);
    toast.success('Dashboard refreshed');
  };

  const handleDelete = async (audioId) => {
    if (!window.confirm('Are you sure you want to delete this audio file and all its associated data?')) {
      return;
    }

    try {
      await axios.delete(`/audio/${audioId}`);
      toast.success('Audio deleted successfully');
      fetchDashboard();
    } catch (error) {
      console.error('Error deleting audio:', error);
      toast.error('Failed to delete audio');
    }
  };

  const handleCancelTask = async (audioId) => {
    if (!window.confirm('Are you sure you want to cancel this task? This action cannot be undone.')) {
      return;
    }

    try {
      await axios.post(`/cancel-task/${audioId}`);
      toast.success('Task cancelled successfully');
      fetchDashboard();
    } catch (error) {
      console.error('Error cancelling task:', error);
      toast.error('Failed to cancel task');
    }
  };

  // Get time estimates from self-learning model
  const getTimeEstimate = async (audio) => {
    if (!audio || !audio.configs) return null;
    
    const { diarizer, speedup, chunk_mode, chunk_duration } = audio.configs;
    const filename = audio.filename || '';
    
    // Use actual audio duration if available, otherwise estimate from filename
    let estimatedDuration = 10; // default 10 minutes
    if (audio.actual_audio_duration_minutes) {
      estimatedDuration = audio.actual_audio_duration_minutes;
    } else if (filename.includes('min') || filename.includes('minute')) {
      const match = filename.match(/(\d+)\s*min/);
      if (match) estimatedDuration = parseInt(match[1]);
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
      return Math.round(totalEstimatedSeconds);
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
      return `${minutes}m ${remainingSeconds}s`;
    } else {
      return `${remainingSeconds}s`;
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'processing':
        return <Clock className="w-4 h-4 text-yellow-500" />;
      case 'transcribed':
        return <CheckCircle className="w-4 h-4 text-blue-500" />;
      case 'summary_generated':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Clock className="w-4 h-4 text-gray-400" />;
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

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Audio Processing Dashboard</h1>
            <p className="text-gray-600">Monitor and manage all your audio transcription projects</p>
          </div>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {refreshing ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Refreshing...
              </>
            ) : (
              <>
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh
              </>
            )}
          </button>
        </div>
      </div>

      {/* Metrics */}
      {dashboard?.metrics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <FileAudio className="w-8 h-8 text-blue-600 mr-3" />
              <div>
                <p className="text-sm font-medium text-gray-600">Total Audios</p>
                <p className="text-2xl font-bold text-gray-900">{dashboard.metrics.total}</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <Clock className="w-8 h-8 text-yellow-600 mr-3" />
              <div>
                <p className="text-sm font-medium text-gray-600">Processing</p>
                <p className="text-2xl font-bold text-gray-900">{dashboard.metrics.processing}</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <FileText className="w-8 h-8 text-blue-600 mr-3" />
              <div>
                <p className="text-sm font-medium text-gray-600">Transcribed</p>
                <p className="text-2xl font-bold text-gray-900">{dashboard.metrics.summarised}</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <CheckCircle className="w-8 h-8 text-green-600 mr-3" />
              <div>
                <p className="text-sm font-medium text-gray-600">Summarized</p>
                <p className="text-2xl font-bold text-gray-900">{dashboard.metrics.completed}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Audio Files List */}
      <div className="bg-white rounded-lg shadow-md">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Audio Files</h2>
          <p className="text-sm text-gray-600 mt-1">
            {dashboard?.audios?.length || 0} files processed
          </p>
        </div>

        {!dashboard?.audios?.length ? (
          <div className="p-12 text-center">
            <FileAudio className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No audio files yet</h3>
            <p className="text-gray-600 mb-4">Upload your first audio file to get started</p>
            <button
              onClick={() => navigate('/')}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              Upload Audio
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    File
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Configuration
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {dashboard.audios.map((audio) => (
                  <tr key={audio.audio_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {audio.filename}
                        </div>
                        <div className="text-sm text-blue-600 font-mono">
                          #{audio.audio_id}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        {getStatusIcon(audio.status)}
                        <span className={`ml-2 px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(audio.status)}`}>
                          {audio.status.replace('_', ' ').toUpperCase()}
                        </span>
                      </div>
                      {audio.status === 'processing' && (
                        <div className="mt-1 text-xs text-gray-500">
                          Est: ~{timeEstimates[audio.audio_id] ? formatTimeRemaining(timeEstimates[audio.audio_id]) : 'Calculating...'}
                        </div>
                      )}
                      {audio.status === 'summary_regenerating' && (
                        <div className="mt-1 text-xs text-gray-500">
                          Est: ~moments
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {audio.configs && (
                        <div>
                          <div>Speedup: {audio.configs.speedup}x</div>
                          <div>Diarizer: {audio.configs.diarizer}</div>
                          {audio.configs.chunk_mode && (
                            <div>Chunk: {audio.configs.chunk_duration}min</div>
                          )}
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex space-x-2">
                        <button
                          onClick={() => navigate(`/status/${audio.audio_id}`)}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          Status
                        </button>
                        {audio.status === 'processing' && (
                          <button
                            onClick={() => handleCancelTask(audio.audio_id)}
                            className="text-red-600 hover:text-red-900"
                            title="Cancel Transcription"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        )}
                        {(audio.status === 'transcribed' || audio.status === 'summary_regenerating') && (
                          <button
                            onClick={() => navigate(`/transcript/${audio.audio_id}`)}
                            className="text-green-600 hover:text-green-900"
                          >
                            Transcript
                          </button>
                        )}
                        {audio.status === 'summary_generated' && (
                          <>
                            <button
                              onClick={() => navigate(`/transcript/${audio.audio_id}`)}
                              className="text-green-600 hover:text-green-900"
                            >
                              Transcript
                            </button>
                            <button
                              onClick={() => navigate(`/document/${audio.audio_id}`)}
                              className="text-purple-600 hover:text-purple-900"
                            >
                              Document
                            </button>
                          </>
                        )}
                        <button
                          onClick={() => handleDelete(audio.audio_id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default DashboardPage; 