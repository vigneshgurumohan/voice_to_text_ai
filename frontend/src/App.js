import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import UploadPage from './pages/UploadPage';
import StatusPage from './pages/StatusPage';
import TranscriptPage from './pages/TranscriptPage';
import DocumentPage from './pages/DocumentPage';
import DashboardPage from './pages/DashboardPage';
import Navbar from './components/Navbar';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<UploadPage />} />
            <Route path="/status/:audioId" element={<StatusPage />} />
            <Route path="/transcript/:audioId" element={<TranscriptPage />} />
            <Route path="/document/:audioId" element={<DocumentPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
          </Routes>
        </main>
        <Toaster position="top-right" />
      </div>
    </Router>
  );
}

export default App; 