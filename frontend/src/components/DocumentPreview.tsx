import React from 'react';
import { Document, useDocumentStore } from '../store/useDocumentStore';
import { FileText, Eye, Edit } from 'lucide-react';

interface DocumentPreviewProps {
  document: Document | null;
}

export const DocumentPreview: React.FC<DocumentPreviewProps> = ({ document }) => {
  const { streaming } = useDocumentStore();
  
  if (!document) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <FileText className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No document selected</h3>
          <p className="text-gray-500">Select a document to preview</p>
        </div>
      </div>
    );
  }
  
  const renderSection = (section: any, index: number) => {
    return (
      <div key={index} className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">
          {section.title}
        </h2>
        <div className="prose prose-lg max-w-none">
          {section.content ? (
            <div dangerouslySetInnerHTML={{ __html: section.content }} />
          ) : (
            <p className="text-gray-500 italic">No content available</p>
          )}
        </div>
      </div>
    );
  };
  
  const renderDocumentContent = () => {
    // Show streaming content if streaming is active
    if (streaming.isStreaming && streaming.streamingContent) {
      return (
        <div>
          <div className="flex items-center gap-2 mb-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
            <Edit className="w-4 h-4 text-blue-600 animate-pulse" />
            <span className="text-sm font-medium text-blue-900">Writing: {streaming.currentSection}</span>
            <span className="text-sm text-blue-700">({streaming.wordCount} words)</span>
          </div>
          <div className="prose prose-lg max-w-none">
            <div className="whitespace-pre-wrap">
              {streaming.streamingContent}
              <span className="inline-block w-2 h-5 bg-blue-500 animate-pulse ml-1"></span>
            </div>
          </div>
        </div>
      );
    }
    
    if (!document.content) {
      return (
        <div className="text-center py-12">
          <Eye className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Document is empty</h3>
          <p className="text-gray-500">Start chatting with the AI to generate content</p>
        </div>
      );
    }
    
    // Handle different document content structures
    if (document.content.sections && Array.isArray(document.content.sections)) {
      return (
        <div>
          {document.content.title && (
            <h1 className="text-3xl font-bold text-gray-900 mb-8 pb-4 border-b-2 border-gray-200">
              {document.content.title}
            </h1>
          )}
          
          {document.content.sections.map((section: any, index: number) => 
            renderSection(section, index)
          )}
        </div>
      );
    }
    
    // Handle plain text or HTML content
    if (typeof document.content === 'string') {
      return (
        <div className="prose prose-lg max-w-none">
          <div dangerouslySetInnerHTML={{ __html: document.content }} />
        </div>
      );
    }
    
    // Handle other content structures
    return (
      <div className="prose prose-lg max-w-none">
        <pre className="whitespace-pre-wrap text-gray-700">
          {JSON.stringify(document.content, null, 2)}
        </pre>
      </div>
    );
  };
  
  return (
    <div className="flex-1 bg-gray-50 p-8 overflow-y-auto" style={{ maxHeight: '100%' }}>
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 document-preview" style={{ maxHeight: 'calc(100vh - 250px)', overflowY: 'auto' }}>
          {renderDocumentContent()}
        </div>
      </div>
    </div>
  );
};