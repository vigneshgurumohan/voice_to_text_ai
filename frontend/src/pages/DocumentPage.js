import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'react-hot-toast';
import ReactMarkdown from 'react-markdown';

import { 
  ArrowLeft, 
  RefreshCw, 
  Download, 
  Settings, 
  BarChart3, 
  Edit3, 
  Share2, 
  Printer,
  ChevronDown,
  ChevronRight,
  ChevronLeft,
  Play,
  Pause,
  Check,
  X,
  Plus,
  Search,
  Star,
  Clock,
  FileText,
  Users,
  Zap,
  RotateCcw,
  Edit
} from 'lucide-react';
import './DocumentPage.css';

// Constants
const SUMMARY_TYPE_KEY = 'default_summary_type';
const FALLBACK_PROMPT_TEMPLATES = {
  'general': 'You are an expert business analyst.\n\nExtract key business requirements from this meeting transcript between vendor and client.\n\nFormat:\n1. Executive Summary (2-3 sentences)\n2. Key Decisions\n3. Action Items (with assignees)\n4. Technical Requirements\n5. Next Steps\n6. Open Issues\n\nKeep it professional and actionable.',
  'fsd': 'You are an expert FSD writer.\n\nCreate a Functional Specification Document from this meeting transcript.\n\nFormat:\n1. Executive Summary\n2. Functional Requirements\n3. User Stories\n4. System Features\n5. Data Requirements\n6. Technical Specs\n7. Constraints\n\nFocus on development-ready requirements.',
  'technical': 'You are an expert technical architect.\n\nExtract technical requirements and architecture decisions from this meeting transcript.\n\nFormat:\n1. Technical Overview\n2. Requirements\n3. Architecture Decisions\n4. Implementation Details\n5. Constraints\n6. Deployment\n7. Risks\n\nProvide specific technical specifications.',
  'action_items': 'You are an expert project manager.\n\nExtract all action items and tasks from this meeting transcript.\n\nFormat:\n1. High Priority (This Week)\n2. Medium Priority (Next 2 Weeks)\n3. Low Priority (Future)\n4. Follow-ups\n5. Blocking Issues\n6. Resources Needed\n\nInclude: Task, Assignee, Deadline, Dependencies, Notes.',
  'meeting_minutes': 'You are an expert meeting facilitator.\n\nCreate formal meeting minutes from this transcript.\n\nFormat:\nMEETING MINUTES\n\nMeeting Info: Date, Time, Location, Attendees\nAgenda: [extract from discussion]\nDiscussion Points: [key topics with decisions]\nDecisions Made: [list all decisions]\nAction Items: [task - assignee - due date]\nNext Steps: [immediate actions]\nNext Meeting: [if mentioned]\n\nKeep it professional and organized.',
  'project_plan': 'You are an expert project manager.\n\nCreate a project plan from this meeting transcript.\n\nFormat:\nPROJECT PLAN\n\n1. Overview: Name, Objectives, Scope, Success Criteria\n2. Timeline: Start/End, Key Milestones\n3. Team: Members, Roles, Responsibilities\n4. Deliverables: [item - description - due date]\n5. Resources: Human, Technical, Budget\n6. Risks: High/Medium with mitigation\n7. Communication: Stakeholders, Reporting, Escalation\n8. Quality: Standards, Testing, Review Process\n\nMake it actionable and realistic.'
};

// Utility functions
const setDefaultSummaryType = (type) => localStorage.setItem(SUMMARY_TYPE_KEY, type);
const getDefaultSummaryType = () => localStorage.getItem(SUMMARY_TYPE_KEY) || 'general';
const getCustomPrompts = () => {
  try {
    return JSON.parse(localStorage.getItem('customPrompts') || '[]');
  } catch {
    return [];
  }
};
const saveCustomPrompts = (prompts) => localStorage.setItem('customPrompts', JSON.stringify(prompts));
const saveLastUsedPrompt = (name) => localStorage.setItem('lastUsedPrompt', name);
const getLastUsedPrompt = () => localStorage.getItem('lastUsedPrompt');

// Simple header consistent with other pages
const HeaderBar = ({ title, status, audioId, onBack, onAnalytics, onRegenerate, onEdit, onExport, regenerating, document, onViewTranscript }) => (
  <div className="bg-white rounded-lg shadow-md p-6 mb-6">
    <div className="flex items-center justify-between">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          {title || 'Document'}
        </h1>
        <p className="text-gray-600">Audio ID: {audioId}</p>
      </div>
      <div className="flex items-center space-x-3">
        <button
          onClick={onRegenerate}
          disabled={regenerating}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          <RotateCcw className={`w-4 h-4 mr-2 ${regenerating ? 'animate-spin' : ''}`} />
          Regenerate
        </button>
        
        <button
          onClick={onEdit}
          disabled={!document}
          className="flex items-center px-4 py-2 bg-white text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
        >
          <Edit className="w-4 h-4 mr-2" />
          Edit
        </button>
        
        <button
          onClick={onViewTranscript}
          className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
        >
          <FileText className="w-4 h-4 mr-2" />
          View Transcript
        </button>
        
        <button
          onClick={onExport}
          disabled={!document}
          className="flex items-center px-4 py-2 bg-white text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
        >
          <Download className="w-4 h-4 mr-2" />
          Export
        </button>
      </div>
    </div>
  </div>
);

const StatusBadge = ({ status, className = "" }) => {
  const getStatusConfig = (status) => {
    switch (status) {
      case 'summary_generated':
        return { color: 'bg-green-50 text-green-700 border-green-200', icon: Check };
      case 'summary_regenerating':
        return { color: 'bg-blue-50 text-blue-700 border-blue-200', icon: RefreshCw };
      case 'transcribed':
        return { color: 'bg-yellow-50 text-yellow-700 border-yellow-200', icon: FileText };
      case 'processing':
        return { color: 'bg-purple-50 text-purple-700 border-purple-200', icon: Zap };
      default:
        return { color: 'bg-gray-50 text-gray-700 border-gray-200', icon: Clock };
    }
  };

  const config = getStatusConfig(status);
  const Icon = config.icon;

  return (
    <div className={`inline-flex items-center space-x-2 px-3 py-1.5 rounded-full border text-sm font-medium ${config.color} ${className}`}>
      <Icon className="w-4 h-4" />
      <span className="capitalize">{status?.replace('_', ' ')}</span>
    </div>
  );
};

const PromptCard = ({ prompt, isSelected, onClick, onEdit, onDelete, onFavorite }) => (
  <div 
    className={`p-4 rounded-xl border-2 cursor-pointer transition-all duration-200 hover:shadow-md ${
      isSelected 
        ? 'border-blue-500 bg-blue-50' 
        : 'border-gray-200 bg-white hover:border-gray-300'
    }`}
    onClick={onClick}
  >
    <div className="flex items-start justify-between mb-2">
      <h3 className="font-semibold text-gray-900 truncate">{prompt.name}</h3>
      <div className="flex items-center space-x-1">
        {prompt.isFavorite && (
          <Star className="w-4 h-4 text-yellow-500 fill-current" />
        )}
        <button
          onClick={(e) => {
            e.stopPropagation();
            onEdit(prompt);
          }}
          className="p-1 rounded hover:bg-gray-100 transition-colors"
        >
          <Edit3 className="w-4 h-4 text-gray-500" />
        </button>
      </div>
    </div>
    <p className="text-sm text-gray-600 line-clamp-2">{prompt.description}</p>
    <div className="flex items-center justify-between mt-3">
      <span className="text-xs text-gray-500">{prompt.type}</span>
      <div className="flex items-center space-x-1">
        {prompt.isCustom && (
          <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded-full">Custom</span>
        )}
      </div>
    </div>
  </div>
);

const SidePanel = ({ isOpen, onToggle, children }) => (
  <>
    <div className={`w-80 bg-white border-r border-gray-200 transition-all duration-300 ease-in-out ${
      isOpen ? 'block' : 'hidden'
    }`}>
      <div className="h-full overflow-y-auto">
        {children}
      </div>
    </div>
    
    {/* Toggle button */}
    <button
      onClick={onToggle}
      className="w-8 h-8 bg-white border border-gray-200 rounded-full flex items-center justify-center shadow-lg hover:shadow-xl transition-all duration-200 hover:bg-gray-50"
    >
      {isOpen ? <ChevronLeft className="w-4 h-4 text-gray-600" /> : <ChevronRight className="w-4 h-4 text-gray-600" />}
    </button>
  </>
);

const DocumentPreview = ({ content, isRegenerating, regenerationProgress, isEditing, editText, onEditText, onSave, onCancel, savingSummary }) => (
  <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
    <div className="p-6">
      {isEditing ? (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">Editing Summary</h3>
            <div className="flex items-center space-x-2">
              <button
                onClick={onCancel}
                disabled={savingSummary}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={onSave}
                disabled={savingSummary}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 transition-colors flex items-center space-x-2"
              >
                {savingSummary ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>Saving...</span>
                  </>
                ) : (
                  <span>Save Changes</span>
                )}
              </button>
            </div>
          </div>
          <textarea
            value={editText}
            onChange={(e) => onEditText(e.target.value)}
            className="w-full p-4 border border-gray-300 rounded-xl bg-white text-sm min-h-[600px] focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all resize-none"
            placeholder="Edit your summary as plain text. When you save, proper formatting will be applied automatically..."
            style={{ fontFamily: 'system-ui, -apple-system, sans-serif', lineHeight: '1.6' }}
          />
        </div>
      ) : (
        <div className="prose prose-lg max-w-none">
          <ReactMarkdown 
            components={{
              h1: ({children}) => <h1 className="text-2xl font-bold text-gray-900 mt-6 mb-4 first:mt-0">{children}</h1>,
              h2: ({children}) => <h2 className="text-xl font-semibold text-gray-800 mt-5 mb-3">{children}</h2>,
              h3: ({children}) => <h3 className="text-lg font-medium text-gray-700 mt-4 mb-2">{children}</h3>,
              h4: ({children}) => <h4 className="text-base font-medium text-gray-700 mt-3 mb-2">{children}</h4>,
              p: ({children}) => <p className="text-gray-800 mb-3 leading-relaxed">{children}</p>,
              ul: ({children}) => <ul className="ml-6 mb-3 list-disc">{children}</ul>,
              ol: ({children}) => <ol className="ml-6 mb-3 list-decimal">{children}</ol>,
              li: ({children}) => <li className="text-gray-700 mb-1">{children}</li>,
              strong: ({children}) => <strong className="font-semibold">{children}</strong>,
              em: ({children}) => <em className="italic">{children}</em>,
              table: ({children}) => <table className="min-w-full border-collapse border border-gray-300 my-4">{children}</table>,
              thead: ({children}) => <thead className="bg-gray-50">{children}</thead>,
              tbody: ({children}) => <tbody>{children}</tbody>,
              tr: ({children}) => <tr className="border-b border-gray-200">{children}</tr>,
              th: ({children}) => <th className="border border-gray-300 px-3 py-2 text-left font-medium text-gray-700">{children}</th>,
              td: ({children}) => <td className="border border-gray-300 px-3 py-2 text-sm text-gray-700">{children}</td>,
            }}
          >
            {content}
          </ReactMarkdown>
        </div>
              )}
      </div>
    </div>
  );



const AnalyticsCard = ({ title, value, icon: Icon, trend, color = "blue" }) => (
  <div className="bg-white rounded-xl p-6 border border-gray-200 hover:shadow-md transition-shadow card-hover">
    <div className="flex items-center justify-between mb-4">
      <div className={`p-2 rounded-lg bg-${color}-100`}>
        <Icon className={`w-5 h-5 text-${color}-600`} />
      </div>
      {trend && (
        <span className={`text-sm font-medium text-${trend > 0 ? 'green' : 'red'}-600`}>
          {trend > 0 ? '+' : ''}{trend}%
        </span>
      )}
    </div>
    <h3 className="text-2xl font-bold text-gray-900 mb-1">{value}</h3>
    <p className="text-sm text-gray-600">{title}</p>
  </div>
);







// Main component
const DocumentPage = () => {
  const { audioId } = useParams();
  const navigate = useNavigate();
  const [document, setDocument] = useState('');
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [summaryType, setSummaryType] = useState('general');
  const [prompt, setPrompt] = useState(FALLBACK_PROMPT_TEMPLATES['general']);
  const [editingPrompt, setEditingPrompt] = useState(false);
  const [customPrompt, setCustomPrompt] = useState('');
  const [instructions, setInstructions] = useState('');
  const [regenerating, setRegenerating] = useState(false);
  const [regenerationProgress, setRegenerationProgress] = useState('');
  const [pollInterval, setPollInterval] = useState(null);
  const [customPrompts, setCustomPrompts] = useState(getCustomPrompts());
  const [serverPrompts, setServerPrompts] = useState({});
  const [selectedPromptName, setSelectedPromptName] = useState(getLastUsedPrompt() || 'general');
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [newPromptName, setNewPromptName] = useState('');
  const [renamePromptId, setRenamePromptId] = useState(null);
  const [renamePromptName, setRenamePromptName] = useState('');
  const [showPromptModal, setShowPromptModal] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editSummaryText, setEditSummaryText] = useState('');
  const [savingSummary, setSavingSummary] = useState(false);
  const [loadingPrompts, setLoadingPrompts] = useState(true);
  const [showAnalytics, setShowAnalytics] = useState(false);

  const summaryRef = useRef(null);

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

  // Fetch initial data
  useEffect(() => {
    const fetchData = async () => {
      try {
        const statusResponse = await axios.get(`/status/${audioId}`);
        setStatus(statusResponse.data);

        const documentResponse = await axios.get(`/document/${audioId}`);
        setDocument(documentResponse.data);
      } catch (error) {
        console.error('Error fetching document:', error);
        toast.error('Failed to fetch document');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    fetchServerPrompts();
    
    const lastUsed = getLastUsedPrompt() || 'general';
    setSelectedPromptName(lastUsed);
  }, [audioId, document]);

  // Set prompt when server prompts are loaded
  useEffect(() => {
    if (!loadingPrompts && status) {
      // Check if there's a summary configuration from the status page
      const summaryConfig = status.summary_config;
      
      if (summaryConfig && summaryConfig.summary_type) {
        // Use the prompt that was used to generate this summary
        const promptType = summaryConfig.summary_type;
        setSelectedPromptName(promptType);
        
        if (promptType === 'general' || promptType === 'fsd' || promptType === 'technical' || 
            promptType === 'action_items' || promptType === 'meeting_minutes' || promptType === 'project_plan') {
          setSummaryType(promptType);
          const promptContent = serverPrompts[promptType] || FALLBACK_PROMPT_TEMPLATES[promptType];
          setPrompt(promptContent);
          setCustomPrompt('');
        } else if (serverPrompts[promptType]) {
          // Custom template from server
          setPrompt(serverPrompts[promptType]);
          setSummaryType('custom');
          setCustomPrompt('');
        } else {
          // Fallback to last used prompt
          const lastUsed = getLastUsedPrompt() || 'general';
          setSelectedPromptName(lastUsed);
          if (lastUsed === 'general' || lastUsed === 'fsd') {
            setSummaryType(lastUsed);
            const promptContent = serverPrompts[lastUsed] || FALLBACK_PROMPT_TEMPLATES[lastUsed];
            setPrompt(promptContent);
            setCustomPrompt('');
          } else if (serverPrompts[lastUsed]) {
            setPrompt(serverPrompts[lastUsed]);
            setSummaryType('custom');
            setCustomPrompt('');
          } else {
            const found = getCustomPrompts().find(p => p.name === lastUsed);
            if (found) {
              setPrompt(found.content);
              setSummaryType('custom');
              setCustomPrompt('');
            }
          }
        }
      } else {
        // No summary config, use last used prompt
    const lastUsed = getLastUsedPrompt() || 'general';
    setSelectedPromptName(lastUsed);
    if (lastUsed === 'general' || lastUsed === 'fsd') {
      setSummaryType(lastUsed);
          const promptContent = serverPrompts[lastUsed] || FALLBACK_PROMPT_TEMPLATES[lastUsed];
          setPrompt(promptContent);
          setCustomPrompt('');
        } else if (serverPrompts[lastUsed]) {
          setPrompt(serverPrompts[lastUsed]);
          setSummaryType('custom');
      setCustomPrompt('');
    } else {
      const found = getCustomPrompts().find(p => p.name === lastUsed);
      if (found) {
        setPrompt(found.content);
        setSummaryType('custom');
        setCustomPrompt('');
      }
    }
      }
    }
  }, [loadingPrompts, serverPrompts, status]);

  // Set edit text when document changes
  useEffect(() => {
    if (document && !isEditing) {
    setEditSummaryText(document);
    }
  }, [document, isEditing]);

  // Cleanup polling interval
  useEffect(() => {
    return () => {
      if (pollInterval) {
        clearInterval(pollInterval);
        setPollInterval(null);
      }
    };
  }, [pollInterval]);

  useEffect(() => {
    if (!regenerating && pollInterval) {
      clearInterval(pollInterval);
      setPollInterval(null);
      setRegenerationProgress('');
    }
  }, [regenerating, pollInterval]);



  // Handlers
  const handleRegenerate = async () => {
    setRegenerating(true);
    try {
      await axios.post(`/generate-summary/${audioId}`, {
        summary_type: summaryType,
        prompt: editingPrompt ? customPrompt : prompt,
        instructions,
      });
      toast.success('Summary regeneration started!');
      
      const regenerationStartTime = new Date().toISOString();
      let pollCount = 0;
      
      const interval = setInterval(async () => {
        pollCount++;
        console.log(`[DEBUG] Poll attempt #${pollCount}`);
        try {
          const statusResponse = await axios.get(`/status/${audioId}`);
          const status = statusResponse.data.status;
          const summaryUpdatedAt = statusResponse.data.summary_updated_at;
          
          console.log('[DEBUG] Polling status:', { 
            status, 
            summaryUpdatedAt, 
            regenerationStartTime,
            hasSummaryUpdatedAt: !!summaryUpdatedAt,
            isRegenerating: status === 'summary_regenerating',
            isGenerated: status === 'summary_generated'
          });
          
          if (status === 'summary_regenerating') {
            setRegenerationProgress('Generating new summary...');
            if (pollCount > 20) {
              console.log('[DEBUG] Fallback: Been polling too long, assuming regeneration is complete');
              clearInterval(interval);
              setPollInterval(null);
              setRegenerationProgress('Summary completed!');
              setRegenerating(false);
              toast.success('Summary regenerated successfully!');
              window.location.reload();
            }
          } else if (status === 'summary_generated' && summaryUpdatedAt) {
            const updatedTime = new Date(summaryUpdatedAt);
            const startTime = new Date(regenerationStartTime);
            
            console.log('[DEBUG] Time comparison:', { 
              updatedTime: updatedTime.toISOString(), 
              startTime: startTime.toISOString(), 
              isNewer: updatedTime > startTime,
              timeDiff: updatedTime.getTime() - startTime.getTime()
            });
            
            if (updatedTime > startTime) {
              console.log('[DEBUG] Regeneration complete, clearing interval');
              clearInterval(interval);
              setPollInterval(null);
              setRegenerationProgress('Summary completed!');
              setRegenerating(false);
              toast.success('Summary regenerated successfully!');
              window.location.reload();
            } else {
              console.log('[DEBUG] Summary exists but not newer than start time');
            }
          } else if (status === 'summary_generated' && !summaryUpdatedAt) {
            console.log('[DEBUG] Summary generated but no timestamp - this might be an old summary');
            console.log('[DEBUG] Using fallback logic - assuming regeneration is complete');
            clearInterval(interval);
            setPollInterval(null);
            setRegenerationProgress('Summary completed!');
            setRegenerating(false);
            toast.success('Summary regenerated successfully!');
            window.location.reload();
          }
        } catch (error) {
          console.error('Error polling status:', error);
        }
      }, 3000);
      
      setPollInterval(interval);
      
      setTimeout(() => {
        if (interval) {
          clearInterval(interval);
          setPollInterval(null);
        }
        setRegenerating(false);
        setRegenerationProgress('');
        toast.error('Regeneration timed out. Please check status page.');
      }, 300000);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to regenerate summary');
      setRegenerating(false);
    }
  };

  const handleDownloadWord = () => {
    try {
      console.log('[DEBUG] Starting Word export for audioId:', audioId);
      toast.loading('Generating Word document...');
      
      // Direct navigation approach - most reliable for file downloads
      const downloadUrl = `http://localhost:8000/export-document/${audioId}`;
      console.log('[DEBUG] Download URL:', downloadUrl);
      
      // Direct navigation to download URL
      window.location.href = downloadUrl;
      
      // Show success message after a brief delay
      setTimeout(() => {
        toast.dismiss();
        toast.success('Word document exported successfully!');
        console.log('[DEBUG] Export completed');
      }, 2000);
      
    } catch (error) {
      console.error('[ERROR] Export failed:', error);
      toast.dismiss();
      toast.error('Failed to export Word document');
    }
  };

  const handlePromptDropdownChange = (e) => {
    const value = e.target.value;
    setSelectedPromptName(value);
    saveLastUsedPrompt(value);
    setEditingPrompt(false);
    
    if (serverPrompts[value]) {
      setPrompt(serverPrompts[value]);
      setSummaryType('custom');
      setCustomPrompt('');
    } else if (value === 'general' || value === 'fsd') {
      setSummaryType(value);
      const promptContent = serverPrompts[value] || FALLBACK_PROMPT_TEMPLATES[value];
      setPrompt(promptContent);
      setCustomPrompt('');
    } else {
      const found = customPrompts.find(p => p.name === value);
      if (found) {
        setPrompt(found.content);
        setSummaryType('custom');
        setCustomPrompt('');
      }
    }
  };

  const handleSaveAsCustomPrompt = () => {
    setShowSaveDialog(true);
    setNewPromptName('');
  };

  const handleConfirmSavePrompt = async () => {
    if (!newPromptName.trim()) {
      toast.error('Prompt name cannot be empty');
      return;
    }
    
    try {
      await axios.post('/prompts', {
        prompt_name: `custom_templates.${newPromptName.trim()}`,
        content: editingPrompt ? customPrompt : prompt
      });
      
      await fetchServerPrompts();
      
    setShowSaveDialog(false);
      setSelectedPromptName(`custom_templates.${newPromptName.trim()}`);
      saveLastUsedPrompt(`custom_templates.${newPromptName.trim()}`);
    setPrompt(editingPrompt ? customPrompt : prompt);
    setEditingPrompt(false);
      toast.success('Custom prompt saved to server!');
    } catch (error) {
      console.error('Error saving custom prompt:', error);
      toast.error('Failed to save custom prompt to server');
    }
  };

  const handleDeletePrompt = async (name) => {
    try {
      await axios.delete(`/prompts/${name}`);
      await fetchServerPrompts();
      
    if (selectedPromptName === name) {
      setSelectedPromptName('general');
      saveLastUsedPrompt('general');
        setPrompt(FALLBACK_PROMPT_TEMPLATES['general']);
      setSummaryType('general');
      }
      toast.success('Custom prompt deleted from server');
    } catch (error) {
      console.error('Error deleting custom prompt:', error);
      toast.error('Failed to delete custom prompt from server');
    }
  };

  const handleStartRenamePrompt = (name) => {
    setRenamePromptId(name);
    setRenamePromptName(name);
  };

  const handleConfirmRenamePrompt = async () => {
    if (!renamePromptName.trim()) {
      toast.error('Prompt name cannot be empty');
      return;
    }
    
    try {
      const currentPrompt = serverPrompts[renamePromptId];
      if (!currentPrompt) {
        toast.error('Prompt not found');
      return;
    }
      
      await axios.delete(`/prompts/${renamePromptId}`);
      await axios.post('/prompts', {
        prompt_name: `custom_templates.${renamePromptName.trim()}`,
        content: currentPrompt
      });
      
      await fetchServerPrompts();
      
    setRenamePromptId(null);
    setRenamePromptName('');
    if (selectedPromptName === renamePromptId) {
        const newName = `custom_templates.${renamePromptName.trim()}`;
        setSelectedPromptName(newName);
        saveLastUsedPrompt(newName);
      }
      toast.success('Custom prompt renamed on server');
    } catch (error) {
      console.error('Error renaming custom prompt:', error);
      toast.error('Failed to rename custom prompt on server');
    }
  };

  const handleOpenEditSummary = () => {
    // Convert markdown to plain text for editing
    const plainText = document
      .replace(/^#{1,6}\s+/gm, '') // Remove header markers
      .replace(/\*\*(.*?)\*\*/g, '$1') // Remove bold markers
      .replace(/\*(.*?)\*/g, '$1') // Remove italic markers
      .replace(/^[-*]\s+/gm, '• ') // Convert list markers to simple bullets
      .replace(/^\d+\.\s+/gm, '') // Remove numbered list markers
      .trim();
    
    setEditSummaryText(plainText);
    setIsEditing(true);
  };

  const handleSaveEditSummary = async () => {
    setSavingSummary(true);
    try {
      // Send the plain text to backend for formatting
      const response = await axios.post(`/summary/${audioId}/edit`, { 
        summary: editSummaryText,
        apply_formatting: true  // Tell backend to apply formatting
      });
      
      // Use the formatted content from backend if available
      const formattedContent = response.data.formatted_content || editSummaryText;
      setDocument(formattedContent);
      setIsEditing(false);
      toast.success('Summary updated!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update summary');
    } finally {
      setSavingSummary(false);
    }
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditSummaryText(document);
  };

  const isPromptEdited = (() => {
    if (editingPrompt) {
      const current = customPrompt.trim();
      const fallbackPrompt = FALLBACK_PROMPT_TEMPLATES[summaryType]?.trim();
      if (current === fallbackPrompt) return false;
      const serverPrompt = serverPrompts[selectedPromptName]?.trim();
      if (current === serverPrompt) return false;
      if (customPrompts.some(p => p.content.trim() === current)) return false;
      return true;
    } else {
    const current = prompt.trim();
      const fallbackPrompt = FALLBACK_PROMPT_TEMPLATES[summaryType]?.trim();
      if (current === fallbackPrompt) return false;
      const serverPrompt = serverPrompts[selectedPromptName]?.trim();
      if (current === serverPrompt) return false;
    if (customPrompts.some(p => p.content.trim() === current)) return false;
    return true;
    }
  })();

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-200 border-t-blue-500 rounded-full animate-spin mx-auto mb-4"></div>
          <h2 className="text-xl font-semibold text-gray-900">Loading Document</h2>
          <p className="text-gray-600 mt-2">Please wait while we fetch your document...</p>
      </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <HeaderBar
        title={status?.filename || 'Document'}
        status={status}
        audioId={audioId}
        onBack={() => navigate(`/status/${audioId}`)}
        onViewTranscript={() => navigate(`/transcript/${audioId}`)}
        onAnalytics={() => setShowAnalytics(!showAnalytics)}
        onRegenerate={handleRegenerate}
        onEdit={handleOpenEditSummary}
        onExport={handleDownloadWord}
        regenerating={regenerating}
        document={document}
      />

      {/* Main Content */}
      <div className="flex">
        {/* Side Panel */}
        <SidePanel isOpen={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)}>
          <div className="p-6 space-y-6">
            {/* Prompt Section */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Prompt Settings</h3>
              
              {/* Prompt Type Selector */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">Summary Type</label>
                <select
                  value={selectedPromptName}
                  onChange={handlePromptDropdownChange}
                  className="w-full p-3 border border-gray-300 rounded-xl bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
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

              {/* Prompt Preview */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">Current Prompt</label>
                <div 
                  className="p-3 bg-gray-50 rounded-xl border border-gray-200 text-sm text-gray-700 max-h-32 overflow-y-auto cursor-pointer hover:bg-gray-100 transition-colors"
                  onClick={() => setShowPromptModal(true)}
                >
                  {prompt}
                </div>
              </div>

              {/* Instructions */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">Additional Instructions</label>
                <textarea
                  value={instructions}
                  onChange={(e) => setInstructions(e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-xl bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all resize-none"
                  rows={3}
                  placeholder="E.g., Focus on technical requirements, split into 3 sections..."
                />
              </div>

              {/* Action Buttons */}
              <div className="space-y-2">
                <button
                  onClick={handleRegenerate}
                  disabled={regenerating}
                  className="w-full px-4 py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center space-x-2"
                >
                  {regenerating ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      <span>Regenerating...</span>
                    </>
                  ) : (
                    <>
                      <RefreshCw className="w-4 h-4" />
                      <span>Regenerate Summary</span>
                    </>
                  )}
                </button>

                {isPromptEdited && (
                  <button
                    onClick={handleSaveAsCustomPrompt}
                    className="w-full px-4 py-2 bg-purple-600 text-white rounded-xl font-medium hover:bg-purple-700 transition-all duration-200"
                  >
                    Save as Custom Prompt
                  </button>
                )}
              </div>
            </div>

            {/* Analytics Section */}
            {showAnalytics && (
            <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Document Analytics</h3>
                <div className="grid grid-cols-2 gap-3">
                  <AnalyticsCard
                    title="Words"
                    value={document.split(' ').length.toLocaleString()}
                    icon={FileText}
                    color="blue"
                  />
                  <AnalyticsCard
                    title="Characters"
                    value={document.length.toLocaleString()}
                    icon={FileText}
                    color="green"
                  />
                  <AnalyticsCard
                    title="Lines"
                    value={document.split('\n').filter(line => line.trim()).length}
                    icon={FileText}
                    color="purple"
                  />
                  <AnalyticsCard
                    title="Reading Time"
                    value={`${Math.ceil(document.split(' ').length / 200)}m`}
                    icon={Clock}
                    color="orange"
                  />
                </div>
              </div>
            )}
            </div>
        </SidePanel>

        {/* Main Content Area */}
        <div className="flex-1">
          <div className="px-4">
            {/* Loading Message */}
            {regenerating && (
              <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-xl">
                <div className="flex items-center space-x-3">
                  <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
            <div>
                    <h3 className="text-lg font-semibold text-blue-900">Regenerating Summary</h3>
                    <p className="text-blue-700">{regenerationProgress || 'Please wait...'}</p>
                  </div>
                </div>
              </div>
            )}
            
            {/* Document Preview */}
            <div className="relative">
              <DocumentPreview
                content={document}
                isRegenerating={regenerating}
                regenerationProgress={regenerationProgress}
                isEditing={isEditing}
                editText={editSummaryText}
                onEditText={(text) => setEditSummaryText(text)}
                onSave={handleSaveEditSummary}
                onCancel={handleCancelEdit}
                savingSummary={savingSummary}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Modals */}
      {showPromptModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-xl font-semibold text-gray-900">Edit Prompt</h3>
              <p className="text-gray-600 mt-1">Customize the prompt for your summary generation</p>
              </div>
            <div className="p-6">
              <textarea
                value={customPrompt || prompt}
                onChange={(e) => setCustomPrompt(e.target.value)}
                className="w-full p-4 border border-gray-300 rounded-xl bg-gray-50 text-sm min-h-[300px] focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all resize-none"
                placeholder="Enter your custom prompt..."
              />
            </div>
            <div className="p-6 border-t border-gray-200 flex items-center justify-end space-x-3">
              <button
                onClick={() => {
                  setShowPromptModal(false);
                  setCustomPrompt('');
                }}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  setPrompt(customPrompt);
                  setShowPromptModal(false);
                  setEditingPrompt(false);
                }}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}



      {showSaveDialog && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-xl font-semibold text-gray-900">Save Custom Prompt</h3>
              <p className="text-gray-600 mt-1">Give your custom prompt a name</p>
            </div>
            <div className="p-6">
            <input
              type="text"
              value={newPromptName}
                onChange={(e) => setNewPromptName(e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-xl bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                placeholder="Enter prompt name..."
                autoFocus
              />
            </div>
            <div className="p-6 border-t border-gray-200 flex items-center justify-end space-x-3">
              <button
                onClick={() => setShowSaveDialog(false)}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmSavePrompt}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Save Prompt
              </button>
            </div>
          </div>
        </div>
      )}


    </div>
  );
};

export default DocumentPage; 