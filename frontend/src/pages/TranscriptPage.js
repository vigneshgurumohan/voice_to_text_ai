import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Download, FileText, Clock, Edit3, Save, X, Users, MessageSquare, Timer } from 'lucide-react';
import toast from 'react-hot-toast';
import axios from 'axios';
import Papa from 'papaparse';

const TranscriptPage = () => {
  const { audioId } = useParams();
  const navigate = useNavigate();
  const [transcript, setTranscript] = useState([]);
  const [editedTranscript, setEditedTranscript] = useState([]);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [savingTranscript, setSavingTranscript] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch status first to get filename
        const statusResponse = await axios.get(`/status/${audioId}`);
        setStatus(statusResponse.data);

        // Fetch transcript
        const transcriptResponse = await axios.get(`/transcript/${audioId}`);
        const csvText = transcriptResponse.data;
        // Parse CSV using PapaParse for robust handling of commas and quotes
        const parsed = Papa.parse(csvText, { header: true, skipEmptyLines: true });
        setTranscript(parsed.data);
        setEditedTranscript(parsed.data);
      } catch (error) {
        console.error('Error fetching transcript:', error);
        toast.error('Failed to fetch transcript');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [audioId]);

  const handleEdit = (index, newText) => {
    const updated = [...editedTranscript];
    updated[index] = { ...updated[index], text: newText };
    setEditedTranscript(updated);
  };

  const handleSave = async () => {
    try {
      setSavingTranscript(true);
      await axios.post(`/transcript/${audioId}/edit`, { transcript: editedTranscript });
      toast.success('Transcript saved!');
      setTranscript(editedTranscript);
      setIsEditing(false);
    } catch (error) {
      toast.error('Failed to save transcript');
    } finally {
      setSavingTranscript(false);
    }
  };

  const handleCancelEdit = () => {
    setEditedTranscript(transcript);
    setIsEditing(false);
  };

  const downloadTranscript = () => {
    const csvContent = [
      'timestamp_start,timestamp_end,speaker,text',
      ...editedTranscript.map(row =>
        `"${row.timestamp_start}","${row.timestamp_end}","${row.speaker}","${row.text}"`
      )
    ].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${status?.filename || 'transcript'}.csv`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  const getSpeakerColor = (speaker) => {
    const colors = [
      'bg-blue-100 text-blue-800 border-blue-200',
      'bg-green-100 text-green-800 border-green-200',
      'bg-purple-100 text-purple-800 border-purple-200',
      'bg-orange-100 text-orange-800 border-orange-200',
      'bg-pink-100 text-pink-800 border-pink-200',
      'bg-indigo-100 text-indigo-800 border-indigo-200'
    ];
    const speakerIndex = parseInt(speaker.replace(/\D/g, '')) || 0;
    return colors[speakerIndex % colors.length];
  };

  const formatTimestamp = (timestamp) => {
    // Convert seconds to MM:SS format
    const seconds = parseFloat(timestamp);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const getTotalDuration = () => {
    if (editedTranscript.length === 0) return '00:00';
    const lastSegment = editedTranscript[editedTranscript.length - 1];
    return formatTimestamp(lastSegment.timestamp_end);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!transcript.length) {
    return (
      <div className="text-center py-12">
        <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-gray-900 mb-2">No Transcript Found</h2>
        <p className="text-gray-600">The transcript for this audio file is not available.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Header */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div>
                <button
                  onClick={() => navigate(`/status/${audioId}`)}
                  className="text-2xl font-bold text-gray-900 hover:text-blue-600 transition-colors mb-1 block"
                >
                  {status?.filename || 'Transcript'}
                </button>
                <p className="text-gray-600">Audio ID: {audioId}</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              {!isEditing && (
                <button
                  onClick={() => setIsEditing(true)}
                  className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  <Edit3 className="w-4 h-4 mr-2" />
                  Edit
                </button>
              )}
              
              <button
                onClick={() => navigate(`/document/${audioId}`)}
                className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              >
                <FileText className="w-4 h-4 mr-2" />
                View Document
              </button>
              
              <button
                onClick={downloadTranscript}
                className="flex items-center px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
              >
                <Download className="w-4 h-4 mr-2" />
                Export
              </button>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
            <div className="flex items-center">
              <MessageSquare className="w-8 h-8 text-blue-600 mr-3" />
              <div>
                <p className="text-sm font-medium text-gray-600">Total Segments</p>
                <p className="text-2xl font-bold text-gray-900">{editedTranscript.length}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
            <div className="flex items-center">
              <Users className="w-8 h-8 text-green-600 mr-3" />
              <div>
                <p className="text-sm font-medium text-gray-600">Speakers</p>
                <p className="text-2xl font-bold text-gray-900">
                  {new Set(editedTranscript.map(s => s.speaker)).size}
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
            <div className="flex items-center">
              <FileText className="w-8 h-8 text-purple-600 mr-3" />
              <div>
                <p className="text-sm font-medium text-gray-600">Characters</p>
                <p className="text-2xl font-bold text-gray-900">
                  {editedTranscript.reduce((acc, segment) => acc + segment.text.length, 0).toLocaleString()}
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
            <div className="flex items-center">
              <Timer className="w-8 h-8 text-orange-600 mr-3" />
              <div>
                <p className="text-sm font-medium text-gray-600">Duration</p>
                <p className="text-2xl font-bold text-gray-900">{getTotalDuration()}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
          
          {/* Edit Controls */}
          {isEditing && (
            <div className="bg-blue-50 border-b border-blue-200 px-6 py-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-blue-900">Editing Transcript</h3>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={handleCancelEdit}
                    disabled={savingTranscript}
                    className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSave}
                    disabled={savingTranscript}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 transition-colors flex items-center space-x-2"
                  >
                    {savingTranscript ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                        <span>Saving...</span>
                      </>
                    ) : (
                      <>
                        <Save className="w-4 h-4" />
                        <span>Save Changes</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Transcript Content */}
          <div className="p-6">
            <div className="space-y-6">
              {editedTranscript.map((segment, index) => (
                <div key={index} className="group">
                  <div className="flex items-start space-x-4">
                    
                    {/* Speaker & Time Info */}
                    <div className="flex-shrink-0 w-24">
                      <div className={`inline-flex items-center justify-center w-10 h-10 rounded-full text-sm font-bold border-2 ${getSpeakerColor(segment.speaker)}`}>
                        {segment.speaker}
                      </div>
                      <div className="text-xs text-gray-500 mt-1 text-center">
                        {formatTimestamp(segment.timestamp_start)}
                      </div>
                    </div>
                    
                    {/* Text Content */}
                    <div className="flex-1 min-w-0">
                      {isEditing ? (
                        <textarea
                          value={segment.text}
                          onChange={(e) => handleEdit(index, e.target.value)}
                          className="w-full p-3 border border-gray-300 rounded-lg bg-white text-gray-900 leading-relaxed resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                          rows={Math.max(2, Math.ceil(segment.text.length / 80))}
                          style={{ fontFamily: 'system-ui, -apple-system, sans-serif' }}
                        />
                      ) : (
                        <div className="p-3 bg-gray-50 rounded-lg text-gray-900 leading-relaxed">
                          {segment.text}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TranscriptPage; 