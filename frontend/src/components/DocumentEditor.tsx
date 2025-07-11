import React, { useState, useEffect } from 'react';
import { Document, useDocumentStore } from '../store/useDocumentStore';
import { documentAPI } from '../services/api';
import { Save, Plus, Trash2, Edit3, Type, AlignLeft } from 'lucide-react';

interface DocumentEditorProps {
  document: Document | null;
}

export const DocumentEditor: React.FC<DocumentEditorProps> = ({ document }) => {
  const { updateDocument, setError } = useDocumentStore();
  const [editingDocument, setEditingDocument] = useState<Document | null>(null);
  const [hasChanges, setHasChanges] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  
  useEffect(() => {
    if (document) {
      setEditingDocument(JSON.parse(JSON.stringify(document)));
      setHasChanges(false);
    }
  }, [document]);
  
  const handleTitleChange = (newTitle: string) => {
    if (editingDocument) {
      setEditingDocument({
        ...editingDocument,
        title: newTitle
      });
      setHasChanges(true);
    }
  };
  
  const handleContentChange = (newContent: any) => {
    if (editingDocument) {
      setEditingDocument({
        ...editingDocument,
        content: newContent
      });
      setHasChanges(true);
    }
  };
  
  const handleSectionChange = (index: number, field: string, value: string) => {
    if (editingDocument && editingDocument.content?.sections) {
      const newSections = [...editingDocument.content.sections];
      newSections[index] = {
        ...newSections[index],
        [field]: value
      };
      
      handleContentChange({
        ...editingDocument.content,
        sections: newSections
      });
    }
  };
  
  const addSection = () => {
    if (editingDocument) {
      const newSection = {
        title: 'New Section',
        content: ''
      };
      
      const sections = editingDocument.content?.sections || [];
      handleContentChange({
        ...editingDocument.content,
        sections: [...sections, newSection]
      });
    }
  };
  
  const removeSection = (index: number) => {
    if (editingDocument && editingDocument.content?.sections) {
      const newSections = editingDocument.content.sections.filter((_: any, i: number) => i !== index);
      handleContentChange({
        ...editingDocument.content,
        sections: newSections
      });
    }
  };
  
  const handleSave = async () => {
    if (!editingDocument || !hasChanges) return;
    
    try {
      setIsSaving(true);
      await documentAPI.updateDocument(editingDocument.id, {
        title: editingDocument.title,
        content: editingDocument.content
      });
      
      updateDocument(editingDocument.id, {
        title: editingDocument.title,
        content: editingDocument.content
      });
      
      setHasChanges(false);
    } catch (error) {
      setError('Failed to save document');
      console.error('Error saving document:', error);
    } finally {
      setIsSaving(false);
    }
  };
  
  const handleStatusChange = (newStatus: 'draft' | 'published' | 'archived') => {
    if (editingDocument) {
      setEditingDocument({
        ...editingDocument,
        status: newStatus
      });
      setHasChanges(true);
    }
  };
  
  if (!editingDocument) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <Edit3 className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No document selected</h3>
          <p className="text-gray-500">Select a document to edit</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="flex-1 flex flex-col">
      {/* Editor Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Type className="w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={editingDocument.title}
                onChange={(e) => handleTitleChange(e.target.value)}
                className="text-xl font-semibold text-gray-900 bg-transparent border-none focus:outline-none focus:ring-0 p-0"
                placeholder="Document title"
              />
            </div>
            
            <select
              value={editingDocument.status}
              onChange={(e) => handleStatusChange(e.target.value as any)}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="draft">Draft</option>
              <option value="published">Published</option>
              <option value="archived">Archived</option>
            </select>
          </div>
          
          <div className="flex items-center gap-2">
            {hasChanges && (
              <span className="text-sm text-yellow-600">Unsaved changes</span>
            )}
            
            <button
              onClick={handleSave}
              disabled={!hasChanges || isSaving}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Save className="w-4 h-4" />
              {isSaving ? 'Saving...' : 'Save'}
            </button>
          </div>
        </div>
      </div>
      
      {/* Editor Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Document Title in Content */}
          {editingDocument.content?.title && (
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">
                Document Title
              </label>
              <input
                type="text"
                value={editingDocument.content.title}
                onChange={(e) => handleContentChange({
                  ...editingDocument.content,
                  title: e.target.value
                })}
                className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter document title"
              />
            </div>
          )}
          
          {/* Sections */}
          {editingDocument.content?.sections && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">Sections</h3>
                <button
                  onClick={addSection}
                  className="flex items-center gap-2 px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                >
                  <Plus className="w-4 h-4" />
                  Add Section
                </button>
              </div>
              
              {editingDocument.content.sections.map((section: any, index: number) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4 space-y-4">
                  <div className="flex items-center justify-between">
                    <input
                      type="text"
                      value={section.title || ''}
                      onChange={(e) => handleSectionChange(index, 'title', e.target.value)}
                      className="flex-1 text-lg font-medium text-gray-900 bg-transparent border-none focus:outline-none focus:ring-0 p-0"
                      placeholder="Section title"
                    />
                    
                    <button
                      onClick={() => removeSection(index)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                  
                  <div className="space-y-2">
                    <label className="block text-sm font-medium text-gray-700">
                      Content
                    </label>
                    <textarea
                      value={section.content || ''}
                      onChange={(e) => handleSectionChange(index, 'content', e.target.value)}
                      rows={8}
                      className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                      placeholder="Enter section content..."
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
          
          {/* Raw Content Editor (fallback) */}
          {!editingDocument.content?.sections && (
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">
                Raw Content
              </label>
              <textarea
                value={typeof editingDocument.content === 'string' 
                  ? editingDocument.content 
                  : JSON.stringify(editingDocument.content, null, 2)}
                onChange={(e) => {
                  try {
                    const parsedContent = JSON.parse(e.target.value);
                    handleContentChange(parsedContent);
                  } catch {
                    handleContentChange(e.target.value);
                  }
                }}
                rows={20}
                className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                placeholder="Enter content..."
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};