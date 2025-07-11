import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Document API
export const documentAPI = {
  // Get all documents
  getDocuments: () => api.get('/documents/'),
  
  // Get single document
  getDocument: (id: number) => api.get(`/documents/${id}`),
  
  // Create new document
  createDocument: (data: { title: string; type: string; content?: any }) => 
    api.post('/documents/', data),
  
  // Update document
  updateDocument: (id: number, data: Partial<any>) => 
    api.put(`/documents/${id}`, data),
  
  // Delete document
  deleteDocument: (id: number) => api.delete(`/documents/${id}`),
  
  // Export document
  exportDocument: (id: number, format: 'pdf' | 'docx' | 'pptx', options?: any) => 
    api.post(`/documents/${id}/export`, { format, ...options }, { responseType: 'blob' }),
  
  // Get document versions
  getDocumentVersions: (id: number) => api.get(`/documents/${id}/versions`),
  
  // Restore document version
  restoreVersion: (id: number, versionId: number) => 
    api.post(`/documents/${id}/versions/${versionId}/restore`),
};

// AI API
export const aiAPI = {
  // Get available providers
  getProviders: () => api.get('/ai/providers'),
  
  // Chat with AI
  chat: (data: {
    message: string;
    document_id?: number;
    conversation_id?: number;
    provider?: string;
    model?: string;
  }) => api.post('/ai/chat/', data),
  
  // Stream chat
  streamChat: (data: {
    message: string;
    document_id?: number;
    conversation_id?: number;
    provider?: string;
    model?: string;
  }) => {
    // Use agent streaming endpoint for proper agent process tracking
    const endpoint = data.document_id ? '/ai/agents/chat/stream' : '/ai/chat/stream';
    return fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  },
  
  // Analyze intent
  analyzeIntent: (user_input: string, document_id?: number) => 
    api.post('/ai/analyze-intent', { user_input, document_id }),
  
  // Generate document structure
  generateDocument: (data: {
    prompt: string;
    document_type: string;
    provider?: string;
    model?: string;
  }) => api.post('/ai/generate-document', data),
  
  // Expand content
  expandContent: (data: {
    section_title: string;
    current_content: string;
    user_request: string;
    provider?: string;
    model?: string;
  }) => api.post('/ai/expand-content', data),
  
  // Adjust style
  adjustStyle: (data: {
    document_content: any;
    style_request: string;
    provider?: string;
    model?: string;
  }) => api.post('/ai/adjust-style', data),
  
  // Get conversation context
  getConversationContext: (conversation_id: number) => 
    api.get(`/ai/conversation/${conversation_id}/context`),
  
  // Create conversation
  createConversation: (document_id: number, initial_message: string) => 
    api.post(`/ai/conversation/${document_id}/create`, { initial_message }),
};

// WebSocket connection for real-time updates
export class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectDelay = 2000;
  private currentDocumentId: number | null = null;
  private currentOnMessage: ((data: any) => void) | null = null;
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private isConnecting = false;
  private isConnectedFlag = false;
  private connectionAttempts = 0;
  
  connect(documentId: number, onMessage: (data: any) => void) {
    this.connectionAttempts++;
    console.log(`🎯 WebSocket connect() called for document ${documentId} (attempt #${this.connectionAttempts})`);
    console.log(`🔍 Current state: isConnecting=${this.isConnecting}, currentDocumentId=${this.currentDocumentId}, ws=${this.ws?.readyState}`);
    
    // If already connected to the same document, just update the message handler
    if (this.isConnected() && this.currentDocumentId === documentId) {
      console.log('✅ Already connected to document', documentId, 'updating message handler');
      this.currentOnMessage = onMessage;
      return;
    }
    
    // Prevent multiple connection attempts
    if (this.isConnecting && this.currentDocumentId === documentId) {
      console.log('🔄 Connection already in progress for document', documentId);
      return;
    }
    
    // Disconnect existing connection if different document
    if (this.ws && this.currentDocumentId !== documentId) {
      console.log('🔄 Switching documents, closing existing connection');
      this.disconnect();
    }
    
    this.currentDocumentId = documentId;
    this.currentOnMessage = onMessage;
    this.isConnecting = true;
    
    const wsUrl = `ws://localhost:8000/ws/${documentId}`;
    
    console.log(`🔌 Attempting to connect to WebSocket: ${wsUrl} (attempt ${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`);
    console.log(`📍 Browser location: ${window.location.href}`);
    this.ws = new WebSocket(wsUrl);
    
    this.ws.onopen = () => {
      console.log('✅ WebSocket connected successfully for document', documentId);
      console.log(`🔗 WebSocket readyState: ${this.ws?.readyState}`);
      this.reconnectAttempts = 0;
      this.isConnecting = false;
      this.isConnectedFlag = true;
      this.startHeartbeat();
    };
    
    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('📨 WebSocket message received:', data);
        
        // Handle heartbeat messages
        if (data.type === 'heartbeat') {
          this.send({ type: 'heartbeat_response' });
          return;
        }
        
        onMessage(data);
      } catch (error) {
        console.error('❌ Error parsing WebSocket message:', error);
      }
    };
    
    this.ws.onclose = (event) => {
      console.log(`❌ WebSocket disconnected: code=${event.code}, reason=${event.reason}`);
      console.log(`🔗 Document ${documentId} WebSocket closed`);
      this.isConnecting = false;
      this.isConnectedFlag = false;
      this.stopHeartbeat();
      
      // Only reconnect if it wasn't a clean disconnect
      if (event.code !== 1000 && event.code !== 1001) {
        this.reconnect(documentId, onMessage);
      }
    };
    
    this.ws.onerror = (error) => {
      console.error('❌ WebSocket error for document', documentId, ':', error);
      console.error('🚫 WebSocket connection failed');
      this.isConnecting = false;
      this.isConnectedFlag = false;
    };
  }
  
  private reconnect(documentId: number, onMessage: (data: any) => void) {
    if (this.reconnectAttempts < this.maxReconnectAttempts && !this.isConnecting) {
      this.reconnectAttempts++;
      const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), 30000); // Exponential backoff, max 30s
      
      console.log(`🔄 Reconnecting in ${delay}ms... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      
      setTimeout(() => {
        if (this.currentDocumentId === documentId && !this.isConnecting) {
          this.connect(documentId, onMessage);
        }
      }, delay);
    } else {
      console.error('❌ Max reconnection attempts reached or already connecting');
    }
  }
  
  private startHeartbeat() {
    this.stopHeartbeat();
    this.heartbeatInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        console.log('💓 Sending WebSocket heartbeat');
        this.send({ type: 'ping' });
      } else {
        console.log('💔 WebSocket not open, stopping heartbeat');
        this.stopHeartbeat();
      }
    }, 30000); // Send ping every 30 seconds
  }
  
  private stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }
  
  disconnect() {
    console.log('🔌 Disconnecting WebSocket');
    this.stopHeartbeat();
    this.isConnecting = false;
    this.isConnectedFlag = false;
    this.reconnectAttempts = 0;
    this.currentDocumentId = null;
    this.currentOnMessage = null;
    
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
  }
  
  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.warn('⚠️ Cannot send message: WebSocket not connected');
    }
  }
  
  isConnected(): boolean {
    const connected = this.ws !== null && this.ws.readyState === WebSocket.OPEN && this.isConnectedFlag;
    console.log(`🔍 isConnected() check: ws=${this.ws?.readyState}, flag=${this.isConnectedFlag}, result=${connected}`);
    return connected;
  }
  
  waitForConnection(timeout: number = 5000): Promise<boolean> {
    console.log('⏳ Waiting for WebSocket connection...');
    return new Promise((resolve) => {
      if (this.isConnected()) {
        console.log('✅ WebSocket already connected');
        resolve(true);
        return;
      }
      
      let attempts = 0;
      const maxAttempts = timeout / 100;
      
      const checkConnection = () => {
        attempts++;
        console.log(`🔍 WebSocket connection check ${attempts}/${maxAttempts}`);
        
        if (this.isConnected()) {
          console.log('✅ WebSocket connection established');
          resolve(true);
        } else if (attempts >= maxAttempts) {
          console.log('❌ WebSocket connection timeout');
          resolve(false);
        } else {
          setTimeout(checkConnection, 100);
        }
      };
      
      checkConnection();
    });
  }
}

export const wsService = new WebSocketService();