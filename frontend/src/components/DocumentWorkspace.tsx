import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { ChatInterface } from './chat/ChatInterface';
import { DocumentPreview } from './DocumentPreview';
import { DocumentEditor } from './DocumentEditor';
import { useDocumentStore } from '../store/useDocumentStore';
import { documentAPI, wsService } from '../services/api';
import { Eye, Edit, Download, Settings, GripVertical, Calendar, User, FileText, Clock, Save } from 'lucide-react';
import { ProviderSelector } from './chat/ProviderSelector';

export const DocumentWorkspace: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { 
    currentDocument, 
    setCurrentDocument, 
    currentConversation, 
    setCurrentConversation,
    isLoading,
    setLoading,
    setError 
  } = useDocumentStore();
  
  const [previewMode, setPreviewMode] = useState<'preview' | 'edit'>('preview');
  const [isExporting, setIsExporting] = useState(false);
  const [leftPanelWidth, setLeftPanelWidth] = useState(40); // percentage
  const [isResizing, setIsResizing] = useState(false);
  
  useEffect(() => {
    console.log('🎬 DocumentWorkspace useEffect triggered with id:', id);
    if (id) {
      console.log('📄 Loading document:', parseInt(id));
      loadDocument(parseInt(id));
      
      // Setup WebSocket connection with delay to prevent rapid connect/disconnect
      console.log('📡 Setting up WebSocket connection for document:', id);
      console.log('🔌 Calling wsService.connect() for document:', parseInt(id));
      
      const documentId = parseInt(id);
      
      // Add a slight delay to prevent rapid connect/disconnect cycles
      const connectionTimer = setTimeout(() => {
        wsService.connect(documentId, handleWebSocketMessage);
      }, 500);
      
      // Add a backup connection attempt after a longer delay
      const backupConnectionTimer = setTimeout(() => {
        if (!wsService.isConnected()) {
          console.log('🔄 Backup WebSocket connection attempt for document:', documentId);
          wsService.connect(documentId, handleWebSocketMessage);
        }
      }, 3000);
      
      return () => {
        console.log('🧹 DocumentWorkspace cleanup - clearing timers');
        clearTimeout(connectionTimer);
        clearTimeout(backupConnectionTimer);
        // Don't disconnect immediately to prevent rapid disconnect/reconnect
        // wsService.disconnect();
      };
    } else {
      console.log('⚠️ No document id provided to DocumentWorkspace');
    }
  }, [id]);
  
  const loadDocument = async (docId: number) => {
    try {
      setLoading(true);
      const response = await documentAPI.getDocument(docId);
      setCurrentDocument(response.data);
    } catch (error) {
      setError('Failed to load document');
      console.error('Error loading document:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const handleWebSocketMessage = (data: any) => {
    console.log('🔄 Processing WebSocket message:', data);
    switch (data.type) {
      case 'document_streaming_start':
        console.log('📝 Document streaming started');
        useDocumentStore.getState().startStreaming(data.data.user_request);
        break;
        
      case 'document_content_streaming':
        console.log('📝 Streaming content chunk:', data.data.chunk);
        useDocumentStore.getState().updateStreamingContent(
          data.data.chunk,
          data.data.section_name,
          data.data.full_content
        );
        break;
        
      case 'document_content_complete':
        console.log('✅ Document streaming completed');
        useDocumentStore.getState().completeStreaming(data.data.final_content);
        break;
        
      case 'document_updated':
        // Backend sends document in data.data.document format
        const document = data.data?.document || data.document;
        if (document) {
          console.log('📄 Updating document in preview:', document);
          setCurrentDocument(document);
          // Reset streaming state when document is finalized
          useDocumentStore.getState().resetStreaming();
        } else {
          console.warn('⚠️ Document update message missing document data:', data);
        }
        break;
        
      case 'chat_message':
        // Handle real-time chat messages
        if (currentConversation) {
          setCurrentConversation({
            ...currentConversation,
            messages: [...currentConversation.messages, data.message]
          });
        }
        break;
        
      default:
        console.log('Unknown WebSocket message type:', data.type);
    }
  };
  
  const handleExport = async (format: 'pdf' | 'docx' | 'pptx') => {
    if (!currentDocument) return;
    
    try {
      setIsExporting(true);
      const response = await documentAPI.exportDocument(currentDocument.id, format);
      
      // Download the file
      const url = window.URL.createObjectURL(response.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${currentDocument.title}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      setError('Failed to export document');
      console.error('Error exporting document:', error);
    } finally {
      setIsExporting(false);
    }
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
  };

  const handleMouseMove = (e: MouseEvent) => {
    if (!isResizing) return;
    
    const containerWidth = window.innerWidth;
    const newLeftWidth = (e.clientX / containerWidth) * 100;
    
    // Constrain between 25% and 65%
    const constrainedWidth = Math.min(Math.max(newLeftWidth, 25), 65);
    setLeftPanelWidth(constrainedWidth);
  };

  const handleMouseUp = () => {
    setIsResizing(false);
  };

  useEffect(() => {
    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isResizing]);

  // Helper functions for enhanced top bar
  const getWordCount = () => {
    if (!currentDocument?.content?.sections) return 0;
    return currentDocument.content.sections.reduce((acc: number, section: any) => 
      acc + (section.content?.split(' ').length || 0), 0
    );
  };

  const getCharacterCount = () => {
    if (!currentDocument?.content?.sections) return 0;
    return currentDocument.content.sections.reduce((acc: number, section: any) => 
      acc + (section.content?.length || 0), 0
    );
  };

  const getReadingTime = () => {
    const words = getWordCount();
    const averageWordsPerMinute = 200;
    const minutes = Math.ceil(words / averageWordsPerMinute);
    return minutes;
  };

  
  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-gray-500">Loading document...</div>
      </div>
    );
  }
  
  if (!currentDocument) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-gray-500">Document not found</div>
      </div>
    );
  }
  
  return (
    <div className="h-full flex flex-col">
      {/* Enhanced Workspace Header */}
      <div className="bg-white border-b border-gray-200 flex-shrink-0" style={{ position: 'sticky', top: 0, zIndex: 10 }}>
        {/* Main Header Row */}
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Left Section - Document Title and Status */}
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-3">
                <FileText className="w-6 h-6 text-blue-600" />
                <div>
                  <h1 className="text-xl font-semibold text-gray-900">
                    {currentDocument.title}
                  </h1>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-sm text-gray-500">{currentDocument.type}</span>
                    <span className="text-gray-300">•</span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      currentDocument.status === 'published' ? 'bg-green-100 text-green-800' :
                      currentDocument.status === 'draft' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {currentDocument.status}
                    </span>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Right Section - Actions */}
            <div className="flex items-center gap-2">
              <div className="flex bg-gray-100 rounded-lg p-1">
                <button
                  onClick={() => setPreviewMode('preview')}
                  className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    previewMode === 'preview' 
                      ? 'bg-white text-blue-600 shadow-sm' 
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <Eye size={16} />
                  Preview
                </button>
                <button
                  onClick={() => setPreviewMode('edit')}
                  className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    previewMode === 'edit' 
                      ? 'bg-white text-blue-600 shadow-sm' 
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <Edit size={16} />
                  Edit
                </button>
              </div>
              
              <div className="relative group">
                <button
                  disabled={isExporting}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <Download size={16} />
                  {isExporting ? 'Exporting...' : 'Export'}
                </button>
                
                <div className="absolute right-0 top-full mt-1 w-40 bg-white rounded-lg shadow-lg border border-gray-200 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
                  <button
                    onClick={() => handleExport('pdf')}
                    className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-t-lg text-left"
                  >
                    Export as PDF
                  </button>
                  <button
                    onClick={() => handleExport('docx')}
                    className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 text-left"
                  >
                    Export as Word
                  </button>
                  <button
                    onClick={() => handleExport('pptx')}
                    className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-b-lg text-left"
                  >
                    Export as PowerPoint
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Document Info and Agent Status Row */}
        <div className="px-6 py-3 bg-gray-50 border-t border-gray-100">
          <div className="flex items-center justify-between">
            {/* Left Section - Document Stats */}
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <FileText size={14} />
                <span>{getWordCount()} words</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <span>{getCharacterCount()} characters</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Clock size={14} />
                <span>{getReadingTime()} min read</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Calendar size={14} />
                <span>Created {new Date(currentDocument.created_at).toLocaleDateString()}</span>
              </div>
            </div>

            {/* Right Section - Model Picker and Save Info */}
            <div className="flex items-center gap-6">
              {/* Model Picker */}
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">Model:</span>
                <ProviderSelector />
              </div>

              {/* Save Status */}
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Save size={14} />
                <span>Saved {new Date(currentDocument.updated_at).toLocaleTimeString()}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Two-Panel Layout */}
      <div className="flex-1 flex min-h-0">
        {/* Left Panel - Conversation */}
        <div 
          className="bg-white border-r border-gray-200 flex flex-col"
          style={{ width: `${leftPanelWidth}%` }}
        >
          <div className="flex-1 min-h-0">
            <ChatInterface />
          </div>
        </div>
        
        {/* Resize Handle */}
        <div 
          className={`w-1 bg-gray-200 hover:bg-gray-300 cursor-col-resize flex items-center justify-center transition-colors ${
            isResizing ? 'bg-blue-500' : ''
          }`}
          onMouseDown={handleMouseDown}
        >
          <GripVertical size={16} className="text-gray-400" />
        </div>
        
        {/* Right Panel - Document Preview */}
        <div 
          className="bg-white flex flex-col"
          style={{ width: `${100 - leftPanelWidth}%` }}
        >
          <div className="flex-1 min-h-0">
            {previewMode === 'preview' ? (
              <DocumentPreview document={currentDocument} />
            ) : (
              <DocumentEditor document={currentDocument} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
};