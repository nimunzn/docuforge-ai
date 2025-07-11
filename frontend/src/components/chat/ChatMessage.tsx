import React from 'react';
import { Bot, User, Copy, Check, Brain, Clock, Loader2, AlertCircle } from 'lucide-react';
import { Message } from '../../store/useDocumentStore';
import { AgentProcessDropdown, AgentProcessData } from './AgentProcessDropdown';

interface ChatMessageProps {
  message: Message;
  isStreaming?: boolean;
  agentState?: 'analyzing' | 'planning' | 'writing' | 'reviewing' | 'updating' | null;
  agentMessage?: string;
  agentProcessData?: AgentProcessData;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message, isStreaming = false, agentState, agentMessage, agentProcessData }) => {
  const [copied, setCopied] = React.useState(false);
  
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy message:', error);
    }
  };
  
  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';
  
  const getAgentStateIcon = () => {
    switch (agentState) {
      case 'analyzing':
        return <Brain className="w-4 h-4 text-blue-500 animate-pulse" />;
      case 'planning':
        return <Clock className="w-4 h-4 text-yellow-500 animate-pulse" />;
      case 'writing':
        return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />;
      case 'reviewing':
        return <AlertCircle className="w-4 h-4 text-orange-500 animate-pulse" />;
      case 'updating':
        return <Loader2 className="w-4 h-4 text-purple-500 animate-spin" />;
      default:
        return <Loader2 className="w-4 h-4 text-gray-500 animate-spin" />;
    }
  };
  
  const getAgentStateMessage = () => {
    if (agentMessage) return agentMessage;
    
    switch (agentState) {
      case 'analyzing':
        return 'Analyzing your request...';
      case 'planning':
        return 'Creating document plan...';
      case 'writing':
        return 'Writing response...';
      case 'reviewing':
        return 'Reviewing and improving...';
      case 'updating':
        return 'Updating preview...';
      default:
        return 'Thinking...';
    }
  };
  
  return (
    <div className={`flex gap-4 ${isUser ? 'justify-end' : 'justify-start'} chat-message`}>
      {!isUser && (
        <div className="flex-shrink-0">
          <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
            <Bot className="w-4 h-4 text-blue-600" />
          </div>
        </div>
      )}
      
      <div className={`max-w-2xl ${isUser ? 'order-1' : 'order-2'}`}>
        {/* Show agent process dropdown for assistant messages with process data */}
        {isAssistant && agentProcessData && (
          <AgentProcessDropdown 
            processData={agentProcessData} 
            isActive={!message.content && !!agentState}
          />
        )}
        
        <div className={`p-4 rounded-lg ${
          isUser 
            ? 'bg-blue-600 text-white' 
            : 'bg-gray-100 text-gray-900'
        }`}>
          {/* Show agent state when in processing mode (only if no process data available) */}
          {isAssistant && agentState && !message.content && !agentProcessData && (
            <div className="flex items-center gap-3">
              {getAgentStateIcon()}
              <span className="text-gray-600 italic">{getAgentStateMessage()}</span>
            </div>
          )}
          
          {/* Show message content */}
          {message.content && (
            <div className="prose prose-sm max-w-none">
              {message.content.split('\n').map((line, index) => (
                <div key={index} className={index > 0 ? 'mt-2' : ''}>
                  {line || '\u00A0'}
                </div>
              ))}
            </div>
          )}
          
          {/* Show streaming indicator for actual content */}
          {isStreaming && message.content && (
            <div className="mt-2 flex items-center gap-1">
              <div className="w-1 h-1 bg-gray-400 rounded-full animate-bounce" />
              <div className="w-1 h-1 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
              <div className="w-1 h-1 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
            </div>
          )}
        </div>
        
        <div className={`flex items-center gap-2 mt-2 text-xs text-gray-500 ${
          isUser ? 'justify-end' : 'justify-start'
        }`}>
          <span>
            {new Date(message.timestamp).toLocaleTimeString([], { 
              hour: '2-digit', 
              minute: '2-digit' 
            })}
          </span>
          
          {isAssistant && !isStreaming && (
            <button
              onClick={handleCopy}
              className="flex items-center gap-1 hover:text-gray-700 transition-colors"
            >
              {copied ? (
                <>
                  <Check className="w-3 h-3" />
                  <span>Copied</span>
                </>
              ) : (
                <>
                  <Copy className="w-3 h-3" />
                  <span>Copy</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>
      
      {isUser && (
        <div className="flex-shrink-0 order-2">
          <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
            <User className="w-4 h-4 text-white" />
          </div>
        </div>
      )}
    </div>
  );
};