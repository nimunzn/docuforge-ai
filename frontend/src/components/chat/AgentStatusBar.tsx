import React from 'react';
import { Brain, Clock, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

export interface AgentStatus {
  state: 'idle' | 'analyzing' | 'planning' | 'writing' | 'reviewing' | 'updating';
  message?: string;
  progress?: {
    current: number;
    total: number;
    description?: string;
  };
}

interface AgentStatusBarProps {
  status: AgentStatus;
  documentStats?: {
    wordCount: number;
    lastSaved: string;
  };
}

export const AgentStatusBar: React.FC<AgentStatusBarProps> = ({ 
  status, 
  documentStats 
}) => {
  const getStatusIcon = () => {
    switch (status.state) {
      case 'idle':
        return <CheckCircle className="w-4 h-4" />;
      case 'analyzing':
        return <Brain className="w-4 h-4 animate-pulse" />;
      case 'planning':
        return <Clock className="w-4 h-4 animate-pulse" />;
      case 'writing':
        return <Loader2 className="w-4 h-4 animate-spin" />;
      case 'reviewing':
        return <AlertCircle className="w-4 h-4 animate-pulse" />;
      case 'updating':
        return <Loader2 className="w-4 h-4 animate-spin" />;
      default:
        return <CheckCircle className="w-4 h-4" />;
    }
  };

  const getStatusMessage = () => {
    if (status.message) {
      return status.message;
    }
    
    switch (status.state) {
      case 'idle':
        return 'Ready to help';
      case 'analyzing':
        return 'Analyzing your request...';
      case 'planning':
        return 'Creating document plan...';
      case 'writing':
        return 'Writing content...';
      case 'reviewing':
        return 'Reviewing and improving...';
      case 'updating':
        return 'Updating preview...';
      default:
        return 'Ready to help';
    }
  };

  return (
    <div className="bg-gray-50 border-b border-gray-200 px-4 py-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {/* Agent Status */}
          <div className={`agent-status ${status.state}`}>
            {getStatusIcon()}
            <span>{getStatusMessage()}</span>
          </div>

          {/* Progress Bar */}
          {status.progress && (
            <div className="flex items-center gap-2">
              <div className="w-20 bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${(status.progress.current / status.progress.total) * 100}%` }}
                />
              </div>
              <span className="text-xs text-gray-600">
                {status.progress.current}/{status.progress.total}
              </span>
              {status.progress.description && (
                <span className="text-xs text-gray-500">
                  {status.progress.description}
                </span>
              )}
            </div>
          )}
        </div>

        {/* Document Stats */}
        {documentStats && (
          <div className="flex items-center gap-4 text-xs text-gray-500">
            <span>
              {documentStats.wordCount} words
            </span>
            <span>
              Saved {documentStats.lastSaved}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};