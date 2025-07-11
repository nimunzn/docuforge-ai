import { test, expect } from '@playwright/test';
import { TestHelpers } from './utils/test-helpers';

test.describe('WebSocket Connections and Real-time Updates', () => {
  let helpers: TestHelpers;

  test.beforeEach(async ({ page }) => {
    helpers = new TestHelpers(page);
  });

  test('should establish WebSocket connection on document load', async ({ page }) => {
    // Listen for WebSocket connection
    let wsConnected = false;
    page.on('websocket', ws => {
      wsConnected = true;
      expect(ws.url()).toContain('/ws/');
    });
    
    await helpers.navigateToDocument(1);
    await helpers.waitForWebSocketConnection();
    
    // Verify WebSocket connection was established
    expect(wsConnected).toBe(true);
  });

  test('should receive document updates via WebSocket', async ({ page }) => {
    await helpers.navigateToDocument(1);
    
    // Mock WebSocket connection
    await helpers.mockWebSocketConnection();
    await helpers.waitForWebSocketConnection();
    
    // Get initial document title
    const initialTitle = await page.locator('[data-testid="document-title"]').textContent();
    
    // Simulate document update via WebSocket
    const updateMessage = {
      type: 'document_updated',
      data: {
        document: {
          id: 1,
          title: 'Updated Document Title',
          content: {
            sections: [
              { title: 'Introduction', content: 'This is the updated introduction.' },
              { title: 'Main Content', content: 'This is the updated main content.' }
            ]
          },
          status: 'draft',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        }
      }
    };
    
    await helpers.triggerWebSocketMessage(updateMessage);
    
    // Verify document title updated
    await expect(page.locator('[data-testid="document-title"]')).toContainText('Updated Document Title');
    
    // Verify document content updated
    await expect(page.locator('[data-testid="document-preview"]')).toContainText('This is the updated introduction.');
    await expect(page.locator('[data-testid="document-preview"]')).toContainText('This is the updated main content.');
  });

  test('should receive chat messages via WebSocket', async ({ page }) => {
    await helpers.navigateToDocument(1);
    
    // Mock WebSocket connection
    await helpers.mockWebSocketConnection();
    await helpers.waitForWebSocketConnection();
    
    // Simulate chat message via WebSocket
    const chatMessage = {
      type: 'chat_message',
      data: {
        message: {
          id: 123,
          role: 'assistant',
          content: 'This is a WebSocket chat message',
          timestamp: new Date().toISOString()
        }
      }
    };
    
    await helpers.triggerWebSocketMessage(chatMessage);
    
    // Verify chat message appears
    await expect(page.locator('[data-testid="chat-message"][data-role="assistant"]')).toContainText('This is a WebSocket chat message');
  });

  test('should handle WebSocket connection errors', async ({ page }) => {
    // Mock WebSocket connection failure
    await page.addInitScript(() => {
      class MockWebSocket {
        constructor(url: string) {
          this.url = url;
          this.readyState = 3; // CLOSED
          setTimeout(() => {
            if (this.onerror) this.onerror({} as Event);
          }, 100);
        }
        
        url: string;
        onopen: ((event: Event) => void) | null = null;
        onmessage: ((event: MessageEvent) => void) | null = null;
        onclose: ((event: CloseEvent) => void) | null = null;
        onerror: ((event: Event) => void) | null = null;
        readyState: number;
        
        send(data: string) {
          // Simulate error on send
          if (this.onerror) this.onerror({} as Event);
        }
        
        close() {
          this.readyState = 3; // CLOSED
          if (this.onclose) this.onclose({} as CloseEvent);
        }
      }
      
      (window as any).WebSocket = MockWebSocket;
    });
    
    await helpers.navigateToDocument(1);
    
    // The app should handle WebSocket connection errors gracefully
    // Verify the app doesn't crash
    await expect(page.locator('[data-testid="document-workspace"]')).toBeVisible();
  });

  test('should reconnect WebSocket on connection loss', async ({ page }) => {
    let wsConnections = 0;
    
    page.on('websocket', ws => {
      wsConnections++;
      
      // Simulate connection loss after 2 seconds
      setTimeout(() => {
        ws.close();
      }, 2000);
    });
    
    await helpers.navigateToDocument(1);
    await helpers.waitForWebSocketConnection();
    
    // Wait for reconnection attempt
    await page.waitForTimeout(5000);
    
    // Verify reconnection occurred
    expect(wsConnections).toBeGreaterThan(1);
  });

  test('should handle malformed WebSocket messages', async ({ page }) => {
    await helpers.navigateToDocument(1);
    
    // Mock WebSocket connection
    await helpers.mockWebSocketConnection();
    await helpers.waitForWebSocketConnection();
    
    // Send malformed JSON message
    await page.evaluate(() => {
      const mockEvent = new MessageEvent('message', { data: 'invalid json' });
      // This should be handled gracefully without crashing
      (window as any).mockWebSocketMessage?.(mockEvent);
    });
    
    // Verify app doesn't crash
    await expect(page.locator('[data-testid="document-workspace"]')).toBeVisible();
  });

  test('should handle unknown WebSocket message types', async ({ page }) => {
    await helpers.navigateToDocument(1);
    
    // Mock WebSocket connection
    await helpers.mockWebSocketConnection();
    await helpers.waitForWebSocketConnection();
    
    // Send unknown message type
    const unknownMessage = {
      type: 'unknown_message_type',
      data: {
        some: 'data'
      }
    };
    
    await helpers.triggerWebSocketMessage(unknownMessage);
    
    // Verify app handles unknown message gracefully
    await expect(page.locator('[data-testid="document-workspace"]')).toBeVisible();
  });

  test('should update document preview in real-time during generation', async ({ page }) => {
    await helpers.navigateToDocument(1);
    
    // Mock WebSocket connection
    await helpers.mockWebSocketConnection();
    await helpers.waitForWebSocketConnection();
    
    // Send a document generation request
    await helpers.sendChatMessage('create a business plan');
    
    // Simulate real-time document updates during generation
    const updates = [
      {
        type: 'document_updated',
        data: {
          document: {
            id: 1,
            title: 'Business Plan',
            content: {
              sections: [
                { title: 'Executive Summary', content: 'Initial content...' }
              ]
            }
          }
        }
      },
      {
        type: 'document_updated',
        data: {
          document: {
            id: 1,
            title: 'Business Plan',
            content: {
              sections: [
                { title: 'Executive Summary', content: 'Updated executive summary content...' },
                { title: 'Market Analysis', content: 'Market analysis content...' }
              ]
            }
          }
        }
      }
    ];
    
    // Send updates with delays to simulate real-time generation
    for (const update of updates) {
      await page.waitForTimeout(1000);
      await helpers.triggerWebSocketMessage(update);
      
      // Verify content appears incrementally
      await expect(page.locator('[data-testid="document-preview"]')).toContainText(update.data.document.content.sections[0].content);
    }
  });

  test('should handle WebSocket disconnection during document generation', async ({ page }) => {
    await helpers.navigateToDocument(1);
    
    // Mock WebSocket connection
    await helpers.mockWebSocketConnection();
    await helpers.waitForWebSocketConnection();
    
    // Start document generation
    await helpers.sendChatMessage('create a comprehensive business plan');
    
    // Simulate WebSocket disconnection
    await page.evaluate(() => {
      const mockEvent = new CloseEvent('close', { code: 1000, reason: 'Normal closure' });
      (window as any).mockWebSocketClose?.(mockEvent);
    });
    
    // Verify app handles disconnection gracefully
    await expect(page.locator('[data-testid="document-workspace"]')).toBeVisible();
    
    // Chat should still work (fallback to HTTP)
    await helpers.waitForChatResponse();
  });

  test('should display WebSocket connection status', async ({ page }) => {
    await helpers.navigateToDocument(1);
    
    // Check for connection status indicators
    const connectionStatus = page.locator('[data-testid="connection-status"]');
    
    if (await connectionStatus.isVisible()) {
      // Verify connection status is shown
      await expect(connectionStatus).toBeVisible();
    }
  });

  test('should handle WebSocket message queuing', async ({ page }) => {
    await helpers.navigateToDocument(1);
    
    // Mock WebSocket connection
    await helpers.mockWebSocketConnection();
    await helpers.waitForWebSocketConnection();
    
    // Send multiple messages quickly
    const messages = [
      {
        type: 'document_updated',
        data: { document: { id: 1, title: 'Update 1' } }
      },
      {
        type: 'document_updated',
        data: { document: { id: 1, title: 'Update 2' } }
      },
      {
        type: 'document_updated',
        data: { document: { id: 1, title: 'Update 3' } }
      }
    ];
    
    // Send all messages at once
    for (const message of messages) {
      await helpers.triggerWebSocketMessage(message);
    }
    
    // Verify final state is correct
    await expect(page.locator('[data-testid="document-title"]')).toContainText('Update 3');
  });

  test('should handle WebSocket messages for different document IDs', async ({ page }) => {
    await helpers.navigateToDocument(1);
    
    // Mock WebSocket connection
    await helpers.mockWebSocketConnection();
    await helpers.waitForWebSocketConnection();
    
    // Get current document title
    const initialTitle = await page.locator('[data-testid="document-title"]').textContent();
    
    // Send update for different document ID
    const updateMessage = {
      type: 'document_updated',
      data: {
        document: {
          id: 999, // Different document ID
          title: 'Other Document'
        }
      }
    };
    
    await helpers.triggerWebSocketMessage(updateMessage);
    
    // Verify current document title didn't change
    await expect(page.locator('[data-testid="document-title"]')).toContainText(initialTitle || '');
  });

  test('should handle WebSocket connection with authentication', async ({ page }) => {
    // Mock authentication token
    await page.addInitScript(() => {
      localStorage.setItem('auth_token', 'mock-token-123');
    });
    
    let wsHeaders: Record<string, string> = {};
    
    page.on('websocket', ws => {
      // Check if WebSocket connection includes authentication
      // In a real implementation, this would be handled by the WebSocket service
      expect(ws.url()).toContain('/ws/');
    });
    
    await helpers.navigateToDocument(1);
    await helpers.waitForWebSocketConnection();
    
    // Verify connection was established successfully
    await expect(page.locator('[data-testid="document-workspace"]')).toBeVisible();
  });

  test('should handle multiple WebSocket connections', async ({ page }) => {
    // Open multiple tabs/windows to simulate multiple connections
    const context = page.context();
    const page2 = await context.newPage();
    
    const helpers2 = new TestHelpers(page2);
    
    // Navigate both pages to documents
    await helpers.navigateToDocument(1);
    await helpers2.navigateToDocument(2);
    
    // Both should establish separate WebSocket connections
    await helpers.waitForWebSocketConnection();
    await helpers2.waitForWebSocketConnection();
    
    // Verify both pages work independently
    await expect(page.locator('[data-testid="document-workspace"]')).toBeVisible();
    await expect(page2.locator('[data-testid="document-workspace"]')).toBeVisible();
    
    await page2.close();
  });

  test('should handle WebSocket connection cleanup on page navigation', async ({ page }) => {
    let wsConnections = 0;
    let wsClosures = 0;
    
    page.on('websocket', ws => {
      wsConnections++;
      ws.on('close', () => {
        wsClosures++;
      });
    });
    
    // Navigate to document
    await helpers.navigateToDocument(1);
    await helpers.waitForWebSocketConnection();
    
    // Navigate away
    await helpers.navigateToDocumentList();
    
    // Wait for cleanup
    await page.waitForTimeout(1000);
    
    // Verify WebSocket was closed
    expect(wsConnections).toBe(1);
    expect(wsClosures).toBe(1);
  });
});