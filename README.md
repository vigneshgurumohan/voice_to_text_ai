# 🎤 Voice-to-Text AI Application

A comprehensive AI-powered audio transcription and analysis platform that converts speech to text, identifies speakers, and generates intelligent summaries using advanced machine learning models.

## 🌟 Unique Selling Points (USP)

### 🚀 **Advanced AI-Powered Transcription**
- **OpenAI Whisper Integration** - State-of-the-art speech recognition with 99%+ accuracy
- **Multi-language Support** - Transcribes audio in 100+ languages automatically
- **Noise Reduction** - Advanced audio preprocessing for crystal-clear transcription
- **Speed Adjustment** - Process audio at different speeds without quality loss

### 👥 **Intelligent Speaker Diarization**
- **HuggingFace pyannote** - Advanced speaker identification and separation
- **AssemblyAI Integration** - Enterprise-grade speaker diarization (optional)
- **Multi-speaker Detection** - Automatically identifies and labels different speakers
- **Conversation Flow** - Maintains speaker context throughout the conversation

### 📊 **Smart Document Generation**
- **LLM-Powered Summaries** - GPT-based intelligent summarization
- **Multiple Summary Types**:
  - **General Summary** - Key points and action items
  - **Functional Specification Document (FSD)** - Technical requirements extraction
  - **Custom Prompts** - User-defined summary formats
- **Export Options** - TXT and Word document formats
- **Editable Content** - Modify transcripts and summaries through the interface

### 🎯 **Enterprise-Grade Features**
- **Background Processing** - Celery-based asynchronous task handling
- **Real-time Progress Tracking** - Live updates on processing status
- **RESTful API** - Complete API documentation with Swagger UI
- **Scalable Architecture** - Microservices design for easy scaling
- **Error Handling** - Comprehensive error management and recovery

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Celery        │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   Worker        │
│   Port: 3000    │    │   Port: 8000    │    │   (Background)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Audio Files   │    │   Transcripts   │    │   Documents     │
│   (WAV, MP3,    │    │   (CSV Format)  │    │   (TXT, DOCX)   │
│    M4A, etc.)   │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🛠️ Technology Stack

### **Frontend**
- **React 18** - Modern UI framework
- **React Router** - Client-side routing
- **Tailwind CSS** - Utility-first styling
- **Axios** - HTTP client for API communication
- **React Dropzone** - Drag-and-drop file uploads
- **React Hot Toast** - User notifications
- **Lucide React** - Beautiful icons

### **Backend**
- **FastAPI** - High-performance Python web framework
- **Uvicorn** - ASGI server for FastAPI
- **Celery** - Distributed task queue
- **Redis** - Message broker for Celery (optional)
- **Python 3.9+** - Core programming language

### **AI/ML Components**
- **OpenAI Whisper** - Speech-to-text transcription
- **HuggingFace pyannote** - Speaker diarization
- **AssemblyAI** - Alternative speaker diarization
- **GPT Models** - Intelligent summarization
- **FFmpeg** - Audio processing and manipulation

### **Data Processing**
- **Pandas** - Data manipulation and CSV handling
- **NumPy** - Numerical computing
- **Librosa** - Audio analysis
- **python-docx** - Word document generation

## 📋 Features & Functionality

### 🎵 **Audio Processing Pipeline**

1. **File Upload**
   - Drag-and-drop interface
   - Support for WAV, MP3, M4A, FLAC, AAC
   - Automatic file validation
   - Progress tracking

2. **Audio Preprocessing**
   - Noise reduction and enhancement
   - Speed adjustment (0.5x to 2.0x)
   - Automatic audio optimization
   - Chunk processing for large files

3. **Transcription**
   - OpenAI Whisper integration
   - Multi-language detection
   - High-accuracy speech recognition
   - Timestamp preservation

4. **Speaker Diarization**
   - Automatic speaker identification
   - Speaker labeling (Speaker 1, Speaker 2, etc.)
   - Conversation flow mapping
   - Multiple diarization engines

5. **Transcript Alignment**
   - Speaker-transcript synchronization
   - Timestamp alignment
   - CSV export with speaker labels
   - Editable transcript format

### 📄 **Document Generation**

1. **Intelligent Summarization**
   - GPT-powered content analysis
   - Key points extraction
   - Action item identification
   - Context-aware summarization

2. **Summary Types**
   - **General Summary**: Meeting highlights and key decisions
   - **FSD Summary**: Technical requirements and specifications
   - **Custom Summary**: User-defined prompts and formats

3. **Export Options**
   - Plain text (.txt) format
   - Microsoft Word (.docx) format
   - Structured document layout
   - Professional formatting

### 🔧 **Advanced Features**

1. **Real-time Processing**
   - Live progress updates
   - Status monitoring
   - Error handling and recovery
   - Background task management

2. **API Integration**
   - RESTful API endpoints
   - Swagger documentation
   - JSON response format
   - HTTP status codes

3. **User Interface**
   - Responsive design
   - Modern UI/UX
   - Dark/light theme support
   - Mobile-friendly interface

## 🚀 Quick Start Guide

### **Prerequisites**

- **Python 3.9+** installed on your system
- **Node.js 16+** and npm installed
- **FFmpeg** installed for audio processing
- **Git** for cloning the repository

### **Installation**

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd voice-to-text-ai
   ```

2. **Install Python Dependencies**
```bash
cd backend
pip install -r requirements.txt
   ```

3. **Install Node.js Dependencies**
   ```bash
   cd frontend
   npm install
   ```

4. **Environment Setup**
   - Create `.env` file in backend directory
   - Add your API keys:
     ```
     OPENAI_API_KEY=your_openai_key_here
     HUGGINGFACE_TOKEN=your_huggingface_token_here
     ASSEMBLYAI_API_KEY=your_assemblyai_key_here
     ```

### **Starting the Application**

#### **Option 1: Single Command (Recommended)**
```powershell
# Windows PowerShell
.\start_app.ps1
```

This will:
- ✅ Start Backend (FastAPI) on port 8000
- ✅ Start Frontend (React) on port 3000
- ✅ Start Celery Worker for background tasks
- ✅ Open separate terminal windows for each service
- ✅ Show real-time logs in individual terminals

#### **Option 2: Manual Startup**
```bash
# Terminal 1: Backend
cd backend
python -m uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm start

# Terminal 3: Celery Worker
cd backend
python celery_worker.py
```

### **Accessing the Application**

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Alternative API Docs**: http://localhost:8000/redoc

## 📖 Usage Guide

### **1. Upload Audio File**

1. Navigate to the **Upload** page
2. Drag and drop your audio file or click to browse
3. Configure processing options:
   - **Speed**: Adjust playback speed (0.5x - 2.0x)
   - **Auto-adjust**: Automatic audio optimization
   - **Chunk Mode**: Process large files in chunks
   - **Diarizer**: Choose speaker identification engine
4. Click **Upload & Process**

### **2. Monitor Processing**

1. Go to the **Status** page to track progress
2. View real-time updates:
   - Audio preprocessing
   - Transcription progress
   - Speaker diarization
   - Summary generation
3. Check individual terminal windows for detailed logs

### **3. View Results**

1. **Transcript Page**: View and edit the transcribed text
   - Speaker-labeled conversation
   - Timestamp information
   - CSV export option
   - Edit functionality

2. **Document Page**: Access generated summaries
   - Multiple summary types
   - Download options (TXT/DOCX)
   - Edit and regenerate summaries

### **4. Export and Share**

1. **Download Transcript**: CSV format with speaker labels
2. **Download Summary**: TXT or Word document format
3. **Share Results**: Copy links or export files

## 🔧 Configuration Options

### **Audio Processing Settings**

```python
# Speed adjustment (0.5x to 2.0x)
speedup: float = 1.0

# Automatic audio optimization
auto_adjust: bool = False

# Chunk processing for large files
chunk_mode: bool = False
chunk_duration: int = 10  # seconds

# Speaker diarization engine
diarizer: str = "huggingface"  # or "assemblyai"
```

### **Summary Generation Options**

```python
# Summary types
summary_type: str = "general"  # "general", "fsd", "custom"

# Custom prompts
prompt: str = "Your custom prompt here"
instructions: str = "Additional instructions"
```

## 🛠️ API Endpoints

### **Core Endpoints**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/upload` | Upload and process audio file |
| `GET` | `/status/{audio_id}` | Get processing status |
| `GET` | `/transcript/{audio_id}` | Download transcript |
| `GET` | `/document/{audio_id}` | Download summary document |
| `POST` | `/generate-summary/{audio_id}` | Generate custom summary |
| `GET` | `/dashboard` | Get all audio files overview |

### **Example API Usage**

```bash
# Upload audio file
curl -X POST "http://localhost:8000/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@audio.mp3" \
  -F "speedup=1.0" \
  -F "diarizer=huggingface"

# Check status
curl "http://localhost:8000/status/abc12345"

# Download transcript
curl "http://localhost:8000/transcript/abc12345" -o transcript.csv

# Generate summary
curl -X POST "http://localhost:8000/generate-summary/abc12345" \
  -H "Content-Type: application/json" \
  -d '{"summary_type": "general"}'
```

## 🐛 Troubleshooting

### **Common Issues**

1. **Port Already in Use**
   ```bash
   # Check what's using the port
   netstat -ano | findstr :8000
   netstat -ano | findstr :3000
   
   # Kill the process
   taskkill /PID <process_id> /F
   ```

2. **Python Dependencies Missing**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Node.js Dependencies Missing**
   ```bash
   cd frontend
   npm install
   ```

4. **FFmpeg Not Found**
   - Download FFmpeg from https://ffmpeg.org/
   - Add to system PATH
   - Restart terminal

5. **API Keys Missing**
   - Check `.env` file in backend directory
   - Ensure all required API keys are set
   - Restart the application

### **Log Files**

- **Backend Logs**: Check the Backend terminal window
- **Frontend Logs**: Check the Frontend terminal window
- **Celery Logs**: Check the Celery terminal window

## 🔒 Security Considerations

- **API Key Management**: Store API keys in environment variables
- **File Upload Validation**: Validate file types and sizes
- **Error Handling**: Don't expose sensitive information in errors
- **Rate Limiting**: Implement rate limiting for API endpoints
- **CORS Configuration**: Configure CORS for production deployment

## 🚀 Deployment

### **Development**
- Use the provided `start_app.ps1` script
- Individual terminal windows for debugging
- Hot reload enabled for development

### **Production**
- Use Docker containers for consistency
- Set up reverse proxy (nginx)
- Configure SSL certificates
- Use production-grade database
- Implement proper logging and monitoring

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the API documentation

---

**Built with ❤️ using cutting-edge AI technology**
