import React from 'react';
import { Search, Bell, User } from 'lucide-react';
import { useDocumentStore } from '../../store/useDocumentStore';

export const Header: React.FC = () => {
  const { currentDocument } = useDocumentStore();
  
  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4 flex-shrink-0">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="Search documents..."
              className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          
          {currentDocument && (
            <div className="flex items-center gap-2">
              <span className="text-gray-400">|</span>
              <span className="font-medium text-gray-800">{currentDocument.title}</span>
              <span className={`px-2 py-1 rounded-full text-xs ${
                currentDocument.status === 'published' ? 'bg-green-100 text-green-800' :
                currentDocument.status === 'draft' ? 'bg-yellow-100 text-yellow-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {currentDocument.status}
              </span>
            </div>
          )}
        </div>
        
        <div className="flex items-center gap-4">
          <button className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100">
            <Bell size={20} />
          </button>
          <button className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100">
            <User size={20} />
          </button>
        </div>
      </div>
    </header>
  );
};