import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { FileText, Plus, Settings, Archive, Search, ChevronLeft, ChevronRight, Bell, User } from 'lucide-react';
import { useDocumentStore } from '../../store/useDocumentStore';

interface SidebarProps {
  isCollapsed: boolean;
  onToggle: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isCollapsed, onToggle }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { documents, createDocument, currentDocument } = useDocumentStore();
  
  const handleCreateDocument = async () => {
    const title = `New Document ${documents.length + 1}`;
    await createDocument(title, 'document');
    // Navigate to the newly created document
    // Get the current document from store after createDocument completes
    const { currentDocument: newDocument } = useDocumentStore.getState();
    if (newDocument) {
      navigate(`/document/${newDocument.id}`);
    }
  };
  
  const menuItems = [
    { icon: FileText, label: 'Documents', path: '/' },
    { icon: Archive, label: 'Archived', path: '/archived' },
    { icon: Settings, label: 'Settings', path: '/settings' },
  ];
  
  return (
    <div className={`${isCollapsed ? 'w-16' : 'w-64'} bg-white border-r border-gray-200 flex flex-col transition-all duration-300`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200 flex items-center justify-between">
        {!isCollapsed && (
          <h1 className="text-xl font-bold text-gray-800">DocuForge AI</h1>
        )}
        <button
          onClick={onToggle}
          className="p-1 hover:bg-gray-100 rounded-lg transition-colors"
          title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {isCollapsed ? (
            <ChevronRight size={20} className="text-gray-600" />
          ) : (
            <ChevronLeft size={20} className="text-gray-600" />
          )}
        </button>
      </div>
      
      {/* Create Document Button */}
      <div className="p-4">
        <button
          onClick={handleCreateDocument}
          className={`w-full flex items-center ${isCollapsed ? 'justify-center' : 'justify-center gap-2'} bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors`}
          title={isCollapsed ? 'New Document' : ''}
        >
          <Plus size={20} />
          {!isCollapsed && 'New Document'}
        </button>
      </div>
      
      {/* Navigation */}
      <nav className="flex-1 px-4">
        <ul className="space-y-2">
          {menuItems.map(({ icon: Icon, label, path }) => (
            <li key={path}>
              <Link
                to={path}
                className={`flex items-center ${isCollapsed ? 'justify-center' : 'gap-3'} px-3 py-2 rounded-lg transition-colors ${
                  location.pathname === path
                    ? 'bg-blue-50 text-blue-600'
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
                title={isCollapsed ? label : ''}
              >
                <Icon size={20} />
                {!isCollapsed && label}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
      
      {/* Recent Documents */}
      {!isCollapsed && (
        <div className="p-4 border-t border-gray-200">
          <h3 className="text-sm font-medium text-gray-500 mb-3">Recent Documents</h3>
          <div className="space-y-2">
            {documents.slice(0, 5).map((doc) => (
              <Link
                key={doc.id}
                to={`/document/${doc.id}`}
                className="block p-2 text-sm text-gray-600 hover:bg-gray-50 rounded-lg truncate"
              >
                <div className="font-medium">{doc.title}</div>
                <div className="text-xs text-gray-400">
                  {new Date(doc.updated_at).toLocaleDateString()}
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
      
      {/* Collapsed Recent Documents - Show only document icons */}
      {isCollapsed && documents.length > 0 && (
        <div className="p-4 border-t border-gray-200">
          <div className="space-y-2 flex flex-col items-center">
            {documents.slice(0, 5).map((doc) => (
              <Link
                key={doc.id}
                to={`/document/${doc.id}`}
                className="p-2 text-gray-600 hover:bg-gray-50 rounded-lg"
                title={doc.title}
              >
                <FileText size={20} />
              </Link>
            ))}
          </div>
        </div>
      )}
      
      {/* User Profile and Notifications */}
      <div className="p-4 border-t border-gray-200">
        <div className={`flex ${isCollapsed ? 'flex-col space-y-2' : 'items-center justify-between'}`}>
          {!isCollapsed && (
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                <User size={16} className="text-white" />
              </div>
              <div className="flex-1">
                <div className="text-sm font-medium text-gray-900">User</div>
                <div className="text-xs text-gray-500">user@example.com</div>
              </div>
            </div>
          )}
          
          <div className={`flex ${isCollapsed ? 'flex-col space-y-2' : 'items-center gap-2'}`}>
            <button 
              className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
              title="Notifications"
            >
              <Bell size={20} />
            </button>
            
            {isCollapsed && (
              <button 
                className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
                title="Profile"
              >
                <User size={20} />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};