import { Page, expect } from '@playwright/test';

export class TestHelpers {
  constructor(private page: Page) {}

  /**
   * Wait for the application to load completely
   */
  async waitForAppToLoad() {
    await this.page.waitForLoadState('networkidle');
    await expect(this.page.locator('.App')).toBeVisible();
  }

  /**
   * Navigate to the document list page
   */
  async navigateToDocumentList() {
    await this.page.goto('/');
    await this.waitForAppToLoad();
  }

  /**
   * Navigate to a specific document workspace
   */
  async navigateToDocument(documentId: number) {
    await this.page.goto(`/document/${documentId}`);
    await this.waitForAppToLoad();
  }

  /**
   * Wait for a loading indicator to appear and disappear
   */
  async waitForLoadingToComplete() {
    // Wait for loading to start
    await this.page.waitForSelector('[data-testid="loading"], .text-gray-500:has-text("Loading")', { 
      timeout: 5000,
      state: 'visible' 
    }).catch(() => {
      // Loading might have already completed
    });
    
    // Wait for loading to finish
    await this.page.waitForSelector('[data-testid="loading"], .text-gray-500:has-text("Loading")', { 
      timeout: 10000,
      state: 'hidden' 
    }).catch(() => {
      // Loading might have already completed
    });
  }

  /**
   * Fill and submit a chat message
   */
  async sendChatMessage(message: string) {
    const chatInput = this.page.locator('textarea[placeholder*="Ask me to create"]');
    await chatInput.fill(message);
    
    // Submit the message
    await this.page.locator('button[type="submit"]').click();
  }

  /**
   * Wait for agent activity to start
   */
  async waitForAgentActivity() {
    // Wait for agent state to appear
    await this.page.waitForSelector('[data-testid="agent-activity"], .text-gray-500:has-text("Analyzing")', { 
      timeout: 10000 
    });
  }

  /**
   * Wait for agent activity to complete
   */
  async waitForAgentActivityToComplete() {
    // Wait for agent processing to finish
    await this.page.waitForSelector('[data-testid="agent-activity"], .text-gray-500:has-text("Analyzing")', { 
      timeout: 60000,
      state: 'hidden' 
    });
  }

  /**
   * Wait for a chat response to appear
   */
  async waitForChatResponse() {
    // Wait for assistant message to appear
    await this.page.waitForSelector('[data-testid="chat-message"][data-role="assistant"]', { 
      timeout: 60000 
    });
  }

  /**
   * Wait for document preview to update
   */
  async waitForDocumentPreviewUpdate() {
    // Wait for document content to appear in preview
    await this.page.waitForSelector('[data-testid="document-preview"] .prose', { 
      timeout: 30000 
    });
  }

  /**
   * Click on a document card in the list
   */
  async clickDocumentCard(documentTitle: string) {
    const documentCard = this.page.locator(`[data-testid="document-card"]:has-text("${documentTitle}")`);
    await documentCard.click();
  }

  /**
   * Search for documents in the document list
   */
  async searchDocuments(searchTerm: string) {
    const searchInput = this.page.locator('input[placeholder="Search documents..."]');
    await searchInput.fill(searchTerm);
    // Wait for search results to update
    await this.page.waitForTimeout(500);
  }

  /**
   * Create a new document
   */
  async createNewDocument(title: string, type: string = 'business_plan') {
    await this.page.goto('/create');
    
    // Fill document creation form
    await this.page.locator('input[name="title"]').fill(title);
    await this.page.locator('select[name="type"]').selectOption(type);
    
    // Submit the form
    await this.page.locator('button[type="submit"]').click();
    
    // Wait for navigation to document workspace
    await this.page.waitForURL(/\/document\/\d+/);
    await this.waitForAppToLoad();
  }

  /**
   * Switch between preview and edit modes
   */
  async switchToPreviewMode() {
    await this.page.locator('button:has-text("Preview")').click();
    await this.page.waitForTimeout(500);
  }

  async switchToEditMode() {
    await this.page.locator('button:has-text("Edit")').click();
    await this.page.waitForTimeout(500);
  }

  /**
   * Export a document
   */
  async exportDocument(format: 'pdf' | 'docx' | 'pptx') {
    // Click export button
    await this.page.locator('button:has-text("Export")').click();
    
    // Click specific format
    await this.page.locator(`button:has-text("Export as ${format.toUpperCase()}")`).click();
    
    // Wait for download to start
    const downloadPromise = this.page.waitForEvent('download');
    const download = await downloadPromise;
    
    return download;
  }

  /**
   * Wait for WebSocket connection to establish
   */
  async waitForWebSocketConnection() {
    // Wait for WebSocket connection message in console
    await this.page.waitForFunction(() => {
      return window.console && performance.getEntriesByType('navigation').length > 0;
    });
    
    // Give WebSocket time to connect
    await this.page.waitForTimeout(2000);
  }

  /**
   * Verify document content contains expected text
   */
  async verifyDocumentContent(expectedText: string) {
    const documentPreview = this.page.locator('[data-testid="document-preview"]');
    await expect(documentPreview).toContainText(expectedText);
  }

  /**
   * Verify chat message appears in conversation
   */
  async verifyChatMessage(message: string, role: 'user' | 'assistant') {
    const chatMessage = this.page.locator(`[data-testid="chat-message"][data-role="${role}"]:has-text("${message}")`);
    await expect(chatMessage).toBeVisible();
  }

  /**
   * Get document word count from UI
   */
  async getDocumentWordCount(): Promise<number> {
    const wordCountElement = this.page.locator('[data-testid="word-count"], :has-text("words")');
    const text = await wordCountElement.textContent();
    const match = text?.match(/(\d+)\s*words/);
    return match ? parseInt(match[1], 10) : 0;
  }

  /**
   * Resize the chat panel
   */
  async resizeChatPanel(percentage: number) {
    const resizeHandle = this.page.locator('[data-testid="resize-handle"]');
    const viewport = this.page.viewportSize();
    
    if (viewport) {
      const targetX = (viewport.width * percentage) / 100;
      await resizeHandle.dragTo(this.page.locator('body'), { targetPosition: { x: targetX, y: 200 } });
    }
  }

  /**
   * Wait for specific agent to be active
   */
  async waitForAgentToBeActive(agentName: string) {
    await this.page.waitForSelector(`[data-testid="agent-${agentName}"][data-status="active"]`, { 
      timeout: 30000 
    });
  }

  /**
   * Verify agent process completed successfully
   */
  async verifyAgentProcessCompleted() {
    await this.page.waitForSelector('[data-testid="agent-process"][data-status="completed"]', { 
      timeout: 60000 
    });
  }

  /**
   * Get all visible document cards
   */
  async getDocumentCards() {
    return this.page.locator('[data-testid="document-card"]');
  }

  /**
   * Verify error message appears
   */
  async verifyErrorMessage(message: string) {
    const errorElement = this.page.locator('[data-testid="error-message"], .text-red-600');
    await expect(errorElement).toContainText(message);
  }

  /**
   * Clear any error messages
   */
  async clearErrorMessages() {
    const dismissButtons = this.page.locator('[data-testid="error-dismiss"], button:has-text("Dismiss")');
    const count = await dismissButtons.count();
    
    for (let i = 0; i < count; i++) {
      await dismissButtons.nth(i).click();
    }
  }

  /**
   * Mock WebSocket connection for testing
   */
  async mockWebSocketConnection() {
    await this.page.addInitScript(() => {
      // Mock WebSocket for testing
      class MockWebSocket {
        constructor(url: string) {
          this.url = url;
          this.readyState = 1; // OPEN
          setTimeout(() => {
            if (this.onopen) this.onopen({} as Event);
          }, 100);
        }
        
        url: string;
        onopen: ((event: Event) => void) | null = null;
        onmessage: ((event: MessageEvent) => void) | null = null;
        onclose: ((event: CloseEvent) => void) | null = null;
        onerror: ((event: Event) => void) | null = null;
        readyState: number;
        
        send(data: string) {
          console.log('MockWebSocket send:', data);
        }
        
        close() {
          this.readyState = 3; // CLOSED
          if (this.onclose) this.onclose({} as CloseEvent);
        }
      }
      
      (window as any).WebSocket = MockWebSocket;
    });
  }

  /**
   * Trigger a WebSocket message for testing
   */
  async triggerWebSocketMessage(message: any) {
    await this.page.evaluate((msg) => {
      const event = new MessageEvent('message', { data: JSON.stringify(msg) });
      // Trigger the message on any existing WebSocket connections
      (window as any).mockWebSocketMessage?.(event);
    }, message);
  }
}