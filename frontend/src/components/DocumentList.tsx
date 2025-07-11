import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { FileText, Download, Trash2, Edit3, Eye, Calendar, Search } from 'lucide-react';
import { useDocumentStore } from '../store/useDocumentStore';
import { documentAPI } from '../services/api';

export const DocumentList: React.FC = () => {
  const { documents, setDocuments, deleteDocument, isLoading, setLoading, setError } = useDocumentStore();
  const [selectedDocuments, setSelectedDocuments] = useState<number[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  
  useEffect(() => {
    loadDocuments();
  }, []);
  
  const loadDocuments = async () => {
    try {
      setLoading(true);
      const response = await documentAPI.getDocuments();
      setDocuments(response.data);
    } catch (error) {
      setError('Failed to load documents');
      console.error('Error loading documents:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const handleDeleteDocument = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this document?')) {
      try {
        await documentAPI.deleteDocument(id);
        deleteDocument(id);
      } catch (error) {
        setError('Failed to delete document');
        console.error('Error deleting document:', error);
      }
    }
  };
  
  const handleExportDocument = async (id: number, format: 'pdf' | 'docx' | 'pptx') => {
    try {
      const response = await documentAPI.exportDocument(id, format);
      const url = window.URL.createObjectURL(response.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = `document.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      setError('Failed to export document');
      console.error('Error exporting document:', error);
    }
  };
  
  const toggleDocumentSelection = (id: number) => {
    setSelectedDocuments(prev => 
      prev.includes(id) 
        ? prev.filter(docId => docId !== id)
        : [...prev, id]
    );
  };
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'published':
        return 'bg-green-100 text-green-800';
      case 'draft':
        return 'bg-yellow-100 text-yellow-800';
      case 'archived':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // Filter documents based on search term
  const filteredDocuments = documents.filter(doc => 
    doc.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    doc.type.toLowerCase().includes(searchTerm.toLowerCase())
  );
  
  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-gray-500">Loading documents...</div>
      </div>
    );
  }
  
  if (documents.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <FileText className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No documents yet</h3>
          <p className="text-gray-500 mb-4">Create your first document to get started</p>
          <Link
            to="/create"
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <FileText className="mr-2 h-4 w-4" />
            Create Document
          </Link>
        </div>
      </div>
    );
  }
  
  return (
    <div className="flex-1 p-6">
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Documents</h2>
            <p className="text-gray-600">Manage your AI-generated documents</p>
          </div>
          
          {/* Search Bar */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="Search documents..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 w-64 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>
      </div>
      
      {/* Actions Bar */}
      {selectedDocuments.length > 0 && (
        <div className="mb-4 p-4 bg-blue-50 rounded-lg">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-blue-900">
              {selectedDocuments.length} document(s) selected
            </span>
            <div className="flex gap-2">
              <button className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700">
                Export Selected
              </button>
              <button className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700">
                Delete Selected
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Documents Grid */}
      {filteredDocuments.length === 0 && searchTerm ? (
        <div className="flex-1 flex items-center justify-center py-12">
          <div className="text-center">
            <Search className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No documents found</h3>
            <p className="text-gray-500">Try adjusting your search term or browse all documents</p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredDocuments.map((document) => (
            <div
              key={document.id}
              className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow"
            >
            <div className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={selectedDocuments.includes(document.id)}
                    onChange={() => toggleDocumentSelection(document.id)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <FileText className="h-8 w-8 text-blue-600" />
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(document.status)}`}>
                  {document.status}
                </span>
              </div>
              
              <h3 className="text-lg font-semibold text-gray-900 mb-2">{document.title}</h3>
              <p className="text-gray-600 text-sm mb-4">{document.type}</p>
              
              <div className="flex items-center gap-2 text-xs text-gray-500 mb-4">
                <Calendar size={14} />
                <span>Updated {new Date(document.updated_at).toLocaleDateString()}</span>
              </div>
              
              <div className="flex items-center gap-2">
                <Link
                  to={`/document/${document.id}`}
                  className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  <Edit3 size={16} />
                  Edit
                </Link>
                
                <div className="relative group">
                  <button className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100">
                    <Download size={16} />
                  </button>
                  <div className="absolute right-0 top-full mt-1 w-32 bg-white rounded-lg shadow-lg border border-gray-200 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
                    <button
                      onClick={() => handleExportDocument(document.id, 'pdf')}
                      className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-t-lg"
                    >
                      Export PDF
                    </button>
                    <button
                      onClick={() => handleExportDocument(document.id, 'docx')}
                      className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                    >
                      Export Word
                    </button>
                    <button
                      onClick={() => handleExportDocument(document.id, 'pptx')}
                      className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-b-lg"
                    >
                      Export PPT
                    </button>
                  </div>
                </div>
                
                <button
                  onClick={() => handleDeleteDocument(document.id)}
                  className="p-2 text-gray-400 hover:text-red-600 rounded-lg hover:bg-gray-100"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          </div>
        ))}
        </div>
      )}
    </div>
  );
};