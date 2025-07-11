import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2, Sparkles } from 'lucide-react';
import { useDocumentStore } from '../../store/useDocumentStore';
import { aiAPI, wsService } from '../../services/api';
import { ChatMessage } from './ChatMessage';
import { AgentProcessData, AgentActivity } from './AgentProcessDropdown';

export const ChatInterface: React.FC = () => {
  const {
    currentDocument,
    currentConversation,
    setCurrentConversation,
    addMessage,
    currentProvider,
    currentModel,
    providers,
    setError
  } = useDocumentStore();
  
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState('');
  const [agentState, setAgentState] = useState<'analyzing' | 'planning' | 'writing' | 'reviewing' | 'updating' | null>(null);
  const [agentMessage, setAgentMessage] = useState<string>('');
  const [currentProcessData, setCurrentProcessData] = useState<AgentProcessData | null>(null);
  const [lastProcessData, setLastProcessData] = useState<AgentProcessData | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  
  useEffect(() => {
    scrollToBottom();
  }, [currentConversation?.messages, streamingMessage]);
  
  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const initializeProcessTracking = () => {
    const startTime = new Date().toISOString();
    setCurrentProcessData({
      activities: [],
      startTime,
    });
  };

  const updateAgentActivity = (
    agent: string, 
    action: string, 
    status: 'pending' | 'in_progress' | 'completed' | 'error',
    input?: string,
    output?: string,
    error?: string,
    metadata?: Record<string, any>
  ) => {
    setCurrentProcessData(prev => {
      if (!prev) return null;
      
      const activities = [...prev.activities];
      const existingIndex = activities.findIndex(a => a.agent === agent && a.action === action);
      
      if (existingIndex >= 0) {
        // Update existing activity
        activities[existingIndex] = {
          ...activities[existingIndex],
          status,
          endTime: status === 'completed' || status === 'error' ? new Date().toISOString() : undefined,
          output: output || activities[existingIndex].output,
          error: error || activities[existingIndex].error,
          metadata: metadata || activities[existingIndex].metadata
        };
      } else {
        // Add new activity
        activities.push({
          agent,
          action,
          status,
          startTime: new Date().toISOString(),
          endTime: status === 'completed' || status === 'error' ? new Date().toISOString() : undefined,
          input,
          output,
          error,
          metadata
        });
      }
      
      return {
        ...prev,
        activities,
        currentStep: activities.filter(a => a.status === 'completed').length,
        totalSteps: activities.length
      };
    });
  };

  const finalizeProcessTracking = () => {
    setCurrentProcessData(prev => {
      if (!prev) return null;
      
      const endTime = new Date().toISOString();
      const startTime = new Date(prev.startTime);
      const processingTime = (new Date(endTime).getTime() - startTime.getTime()) / 1000;
      
      const finalData = {
        ...prev,
        endTime,
        processingTime
      };
      
      setLastProcessData(finalData);
      return null;
    });
  };
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;
    
    const userMessage = input.trim();
    setInput('');
    
    // Add user message
    addMessage({ role: 'user', content: userMessage });
    
    try {
      setIsStreaming(true);
      setStreamingMessage('');
      setAgentState('analyzing');
      setAgentMessage('Analyzing your request...');
      setLastProcessData(null);
      
      // Initialize process tracking
      initializeProcessTracking();
      
      // Ensure WebSocket connection before sending message (for document streaming)
      if (currentDocument?.id) {
        console.log('🔍 Ensuring WebSocket connection before sending message...');
        console.log('📊 Current document ID:', currentDocument.id);
        console.log('🔗 WebSocket connected:', wsService.isConnected());
        
        // Force reconnect if not connected
        if (!wsService.isConnected()) {
          console.log('🔄 WebSocket not connected, forcing reconnection...');
          wsService.connect(currentDocument.id, (data: any) => {
            console.log('📨 WebSocket message in chat:', data);
            // Handle WebSocket messages in chat context if needed
          });
        }
        
        const wsConnected = await wsService.waitForConnection(5000);
        if (!wsConnected) {
          console.warn('⚠️ WebSocket connection not established after 5s, proceeding anyway');
          console.warn('🔴 This may cause streaming issues');
        } else {
          console.log('✅ WebSocket connection confirmed, proceeding with message');
        }
      }
      
      // Only send conversation_id if it's a valid backend ID (not a timestamp)
      const conversationId = currentConversation?.id && currentConversation.id < 1000000000000 
        ? currentConversation.id 
        : undefined;
      
      const response = await aiAPI.streamChat({
        message: userMessage,
        document_id: currentDocument?.id,
        conversation_id: conversationId,
        provider: currentProvider,
        model: currentModel
      });
      
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let fullResponse = '';
      
      // Update agent status to writing when response starts
      setAgentState('writing');
      setAgentMessage('Writing response...');
      
      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                
                // Handle agent process updates
                if (data.agent_activity) {
                  const activity = data.agent_activity;
                  updateAgentActivity(
                    activity.agent,
                    activity.action,
                    activity.status,
                    activity.input,
                    activity.output,
                    activity.error,
                    activity.metadata
                  );
                  
                  // Update current agent state for simple display fallback
                  if (activity.status === 'in_progress') {
                    setAgentState(activity.agent === 'planner' ? 'planning' : 
                                 activity.agent === 'writer' ? 'writing' :
                                 activity.agent === 'reviewer' ? 'reviewing' : 'analyzing');
                    setAgentMessage(activity.action);
                  } else if (activity.status === 'error') {
                    setError(`Agent error: ${activity.error}`);
                    setAgentState(null);
                    setAgentMessage('');
                  }
                }
                
                // Handle error messages
                if (data.error) {
                  setError(`Processing error: ${data.error}`);
                  setAgentState(null);
                  setAgentMessage('');
                  finalizeProcessTracking();
                  return;
                }
                
                // Handle content chunks
                if (data.chunk) {
                  fullResponse += data.chunk;
                  setStreamingMessage(fullResponse);
                  // Clear agent state when actual content starts streaming
                  if (agentState) {
                    setAgentState(null);
                    setAgentMessage('');
                  }
                } else if (data.done) {
                  // Stream complete
                  finalizeProcessTracking();
                  addMessage({ role: 'assistant', content: fullResponse });
                  setStreamingMessage('');
                  setAgentState(null);
                  setAgentMessage('');
                  break;
                }
              } catch (e) {
                // Ignore JSON parse errors
              }
            }
          }
        }
      }
    } catch (error) {
      console.error('Error in streaming request:', error);
      
      if (error instanceof TypeError && error.message.includes('fetch')) {
        setError('Connection failed. Please check if the backend server is running.');
      } else if (error instanceof Error) {
        setError(`Failed to send message: ${error.message}`);
      } else {
        setError('Failed to send message. Please try again.');
      }
      
      setAgentState(null);
      setAgentMessage('');
      setCurrentProcessData(null);
      finalizeProcessTracking();
    } finally {
      setIsStreaming(false);
    }
  };
  
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };
  
  const suggestions = [
    'Create a business proposal for a new product',
    'Write a technical report on AI implementation',
    'Generate a presentation about market trends',
    'Draft a memo about company policies',
    'Create a resume template',
    'Write a whitepaper on blockchain technology'
  ];
  
  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion);
    inputRef.current?.focus();
  };
  
  return (
    <div className="chat-interface h-full flex flex-col">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 chat-messages">
        {!currentConversation?.messages.length && !streamingMessage && (
          <div className="text-center py-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full mb-4">
              <Sparkles className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Welcome to DocuForge AI
            </h3>
            <p className="text-gray-600 mb-6">
              Start by asking me to create a document or help you with content
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl mx-auto">
              {suggestions.map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="p-3 text-left bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <div className="text-sm font-medium text-gray-900">{suggestion}</div>
                </button>
              ))}
            </div>
          </div>
        )}
        
        {currentConversation?.messages.map((message, index) => (
          <ChatMessage 
            key={index} 
            message={message} 
            agentProcessData={message.role === 'assistant' && index === currentConversation.messages.length - 1 ? lastProcessData : undefined}
          />
        ))}
        
        {/* Show agent state placeholder when processing */}
        {agentState && !streamingMessage && (
          <ChatMessage
            message={{
              id: 0,
              role: 'assistant',
              content: '',
              timestamp: new Date().toISOString()
            }}
            agentState={agentState}
            agentMessage={agentMessage}
            agentProcessData={currentProcessData}
          />
        )}
        
        {streamingMessage && (
          <ChatMessage
            message={{
              id: 0,
              role: 'assistant',
              content: streamingMessage,
              timestamp: new Date().toISOString()
            }}
            isStreaming={true}
            agentProcessData={currentProcessData}
          />
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      {/* Input Area */}
      <div className="bg-white border-t border-gray-200 p-4 chat-input flex-shrink-0">
        <form onSubmit={handleSubmit} className="flex items-end gap-3">
          <div className="flex-1">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me to create a document, modify content, or help with writing..."
              className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none text-sm"
              rows={2}
              disabled={isStreaming}
            />
          </div>
          
          <button
            type="submit"
            disabled={!input.trim() || isStreaming}
            className="flex items-center justify-center w-10 h-10 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isStreaming ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </form>
        
        <div className="mt-2 text-xs text-gray-500">
          Press Enter to send, Shift+Enter for new line
        </div>
      </div>
    </div>
  );
};