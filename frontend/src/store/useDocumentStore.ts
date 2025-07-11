import { create } from 'zustand';
import { documentAPI } from '../services/api';

export interface Document {
  id: number;
  title: string;
  content: any;
  type: string;
  status: 'draft' | 'published' | 'archived';
  created_at: string;
  updated_at: string;
  conversations?: Conversation[];
}

export interface Conversation {
  id: number;
  document_id: number;
  messages: Message[];
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface AIProvider {
  name: string;
  models: string[];
  available: boolean;
}

interface StreamingState {
  isStreaming: boolean;
  streamingContent: string;
  currentSection: string;
  wordCount: number;
  startTime: string | null;
}

interface DocumentState {
  documents: Document[];
  currentDocument: Document | null;
  currentConversation: Conversation | null;
  providers: Record<string, AIProvider>;
  currentProvider: string;
  currentModel: string;
  isLoading: boolean;
  error: string | null;
  streaming: StreamingState;
  
  // Actions
  setDocuments: (documents: Document[]) => void;
  setCurrentDocument: (document: Document | null) => void;
  setCurrentConversation: (conversation: Conversation | null) => void;
  setProviders: (providers: Record<string, AIProvider>) => void;
  setCurrentProvider: (provider: string) => void;
  setCurrentModel: (model: string) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  
  // Document actions
  createDocument: (title: string, type: string) => Promise<void>;
  updateDocument: (id: number, updates: Partial<Document>) => void;
  deleteDocument: (id: number) => void;
  
  // Conversation actions
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void;
  clearConversation: () => void;
  
  // Streaming actions
  startStreaming: (userRequest: string) => void;
  updateStreamingContent: (chunk: string, sectionName: string, fullContent: string) => void;
  completeStreaming: (finalContent: string) => void;
  resetStreaming: () => void;
}

export const useDocumentStore = create<DocumentState>((set, get) => ({
  documents: [],
  currentDocument: null,
  currentConversation: null,
  providers: {},
  currentProvider: 'openai',
  currentModel: 'gpt-4',
  isLoading: false,
  error: null,
  streaming: {
    isStreaming: false,
    streamingContent: '',
    currentSection: '',
    wordCount: 0,
    startTime: null
  },
  
  setDocuments: (documents) => set({ documents }),
  setCurrentDocument: (document) => set({ currentDocument: document }),
  setCurrentConversation: (conversation) => set({ currentConversation: conversation }),
  setProviders: (providers) => set({ providers }),
  setCurrentProvider: (provider) => set({ currentProvider: provider }),
  setCurrentModel: (model) => set({ currentModel: model }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
  
  createDocument: async (title, type) => {
    try {
      set({ isLoading: true });
      
      // Create document through API
      const response = await documentAPI.createDocument({ 
        title, 
        type,
        content: {
          sections: []
        }
      });
      
      const newDocument = response.data;
      
      set(state => ({
        documents: [...state.documents, newDocument],
        currentDocument: newDocument,
        isLoading: false
      }));
      
      // The navigation will be handled by the component that calls createDocument
    } catch (error) {
      set({ 
        error: 'Failed to create document',
        isLoading: false 
      });
      console.error('Error creating document:', error);
    }
  },
  
  updateDocument: (id, updates) => {
    set(state => ({
      documents: state.documents.map(doc => 
        doc.id === id 
          ? { ...doc, ...updates, updated_at: new Date().toISOString() }
          : doc
      ),
      currentDocument: state.currentDocument?.id === id 
        ? { ...state.currentDocument, ...updates, updated_at: new Date().toISOString() }
        : state.currentDocument
    }));
  },
  
  deleteDocument: (id) => {
    set(state => ({
      documents: state.documents.filter(doc => doc.id !== id),
      currentDocument: state.currentDocument?.id === id ? null : state.currentDocument
    }));
  },
  
  addMessage: (message) => {
    const newMessage: Message = {
      ...message,
      id: Date.now(),
      timestamp: new Date().toISOString()
    };
    
    set(state => ({
      currentConversation: state.currentConversation 
        ? {
            ...state.currentConversation,
            messages: [...state.currentConversation.messages, newMessage]
          }
        : {
            id: Date.now(),
            document_id: state.currentDocument?.id || 0,
            messages: [newMessage],
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
          }
    }));
  },
  
  clearConversation: () => set({ currentConversation: null }),
  
  // Streaming actions
  startStreaming: (userRequest: string) => set(state => ({
    streaming: {
      isStreaming: true,
      streamingContent: '',
      currentSection: 'Document',
      wordCount: 0,
      startTime: new Date().toISOString()
    }
  })),
  
  updateStreamingContent: (chunk: string, sectionName: string, fullContent: string) => set(state => ({
    streaming: {
      ...state.streaming,
      streamingContent: fullContent,
      currentSection: sectionName,
      wordCount: fullContent.split(' ').length
    }
  })),
  
  completeStreaming: (finalContent: string) => set(state => ({
    streaming: {
      ...state.streaming,
      isStreaming: false,
      streamingContent: finalContent
    }
  })),
  
  resetStreaming: () => set(state => ({
    streaming: {
      isStreaming: false,
      streamingContent: '',
      currentSection: '',
      wordCount: 0,
      startTime: null
    }
  }))
}));