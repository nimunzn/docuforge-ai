import { test, expect } from '@playwright/test';
import { TestHelpers } from './utils/test-helpers';

test.describe('Chat Interactions and Document Generation', () => {
  let helpers: TestHelpers;

  test.beforeEach(async ({ page }) => {
    helpers = new TestHelpers(page);
  });

  test('should display chat interface correctly', async ({ page }) => {
    await helpers.navigateToDocument(1);
    
    // Check chat interface elements
    await expect(page.locator('[data-testid="chat-interface"]')).toBeVisible();
    await expect(page.locator('textarea[placeholder*="Ask me to create"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
    
    // Check initial welcome message
    await expect(page.locator('.text-center:has-text("Welcome to DocuForge AI")')).toBeVisible();
    await expect(page.locator('p:has-text("Start by asking me to create a document")')).toBeVisible();
  });

  test('should display suggestion buttons', async ({ page }) => {
    await helpers.navigateToDocument(1);
    
    // Check suggestion buttons are present
    const suggestions = [
      'Create a business proposal for a new product',
      'Write a technical report on AI implementation',
      'Generate a presentation about market trends',
      'Draft a memo about company policies',
      'Create a resume template',
      'Write a whitepaper on blockchain technology'
    ];
    
    for (const suggestion of suggestions) {
      await expect(page.locator(`button:has-text("${suggestion}")`)).toBeVisible();
    }
  });

  test('should handle suggestion clicks', async ({ page }) => {
    await helpers.navigateToDocument(1);
    
    // Click on a suggestion
    const suggestion = 'Create a business proposal for a new product';
    await page.locator(`button:has-text("${suggestion}")`).click();
    
    // Verify suggestion text appears in input
    const chatInput = page.locator('textarea[placeholder*="Ask me to create"]');
    await expect(chatInput).toHaveValue(suggestion);
    
    // Verify input is focused
    await expect(chatInput).toBeFocused();
  });

  test('should send and receive chat messages', async ({ page }) => {
    await helpers.navigateToDocument(1);
    
    // Send a simple message
    const message = 'Hello, how are you?';
    await helpers.sendChatMessage(message);
    
    // Verify user message appears
    await helpers.verifyChatMessage(message, 'user');
    
    // Wait for assistant response
    await helpers.waitForChatResponse();
    
    // Verify assistant message appears
    const assistantMessage = page.locator('[data-testid="chat-message"][data-role="assistant"]').last();
    await expect(assistantMessage).toBeVisible();
    await expect(assistantMessage).toContainText(/hello|hi|how/i);
  });

  test('should create business plan template', async ({ page }) => {
    await helpers.navigateToDocument(1);
    
    // Send business plan request
    const message = 'create a business plan template';
    await helpers.sendChatMessage(message);
    
    // Verify user message appears
    await helpers.verifyChatMessage(message, 'user');
    
    // Wait for agent activity to start
    await helpers.waitForAgentActivity();
    
    // Verify agent activity indicators
    await expect(page.locator('[data-testid="agent-activity"]')).toBeVisible();
    await expect(page.locator('.text-gray-500:has-text("Analyzing")')).toBeVisible();
    
    // Wait for processing to complete
    await helpers.waitForAgentActivityToComplete();
    
    // Wait for assistant response
    await helpers.waitForChatResponse();
    
    // Verify response mentions document creation
    const assistantMessage = page.locator('[data-testid="chat-message"][data-role="assistant"]').last();
    await expect(assistantMessage).toContainText(/created|business plan|template/i);
    
    // Wait for document preview to update
    await helpers.waitForDocumentPreviewUpdate();
    
    // Verify document content was created
    await helpers.verifyDocumentContent('business plan');
  });

  test('should handle document generation with agent process tracking', async ({ page }) => {
    await helpers.navigateToDocument(1);
    
    // Send document generation request
    const message = 'write a minimal proposal to help me get ideas';
    await helpers.sendChatMessage(message);
    
    // Verify user message appears
    await helpers.verifyChatMessage(message, 'user');
    
    // Wait for agent activity
    await helpers.waitForAgentActivity();
    
    // Check agent process indicators
    await expect(page.locator('[data-testid="agent-process"]')).toBeVisible();
    
    // Wait for orchestrator to start
    await helpers.waitForAgentToBeActive('orchestrator');
    
    // Wait for planner (if used)
    try {
      await helpers.waitForAgentToBeActive('planner');
    } catch {
      // Planner might be skipped for simple requests
    }
    
    // Wait for writer
    await helpers.waitForAgentToBeActive('writer');
    
    // Wait for process completion
    await helpers.verifyAgentProcessCompleted();
    
    // Verify document was generated
    await helpers.waitForDocumentPreviewUpdate();
    await helpers.verifyDocumentContent('proposal');
  });

  test('should display streaming responses', async ({ page }) => {
    await helpers.navigateToDocument(1);
    
    // Send a message that will generate a streaming response
    const message = 'explain artificial intelligence in simple terms';
    await helpers.sendChatMessage(message);
    
    // Wait for streaming to start
    await page.waitForSelector('[data-testid="streaming-message"]', { timeout: 10000 });
    
    // Verify streaming indicator
    await expect(page.locator('[data-testid="streaming-indicator"]')).toBeVisible();
    
    // Wait for streaming to complete
    await helpers.waitForChatResponse();
    
    // Verify complete response
    const assistantMessage = page.locator('[data-testid="chat-message"][data-role="assistant"]').last();
    await expect(assistantMessage).toContainText(/artificial intelligence|AI/i);
  });

  test('should handle chat input keyboard shortcuts', async ({ page }) => {
    await helpers.navigateToDocument(1);
    
    const chatInput = page.locator('textarea[placeholder*="Ask me to create"]');
    
    // Test Enter key submission
    await chatInput.fill('Test message');
    await chatInput.press('Enter');
    
    // Verify message was sent
    await helpers.verifyChatMessage('Test message', 'user');
    
    // Test Shift+Enter for new line
    await chatInput.fill('Line 1');
    await chatInput.press('Shift+Enter');
    await chatInput.type('Line 2');
    
    const inputValue = await chatInput.inputValue();
    expect(inputValue).toBe('Line 1\nLine 2');
  });

  test('should disable input during processing', async ({ page }) => {
    await helpers.navigateToDocument(1);
    
    // Send a message
    await helpers.sendChatMessage('create a document');
    
    // Verify input is disabled during processing
    const chatInput = page.locator('textarea[placeholder*="Ask me to create"]');
    const submitButton = page.locator('button[type="submit"]');
    
    await expect(chatInput).toBeDisabled();
    await expect(submitButton).toBeDisabled();
    
    // Wait for processing to complete
    await helpers.waitForChatResponse();
    
    // Verify input is re-enabled
    await expect(chatInput).toBeEnabled();
    await expect(submitButton).toBeEnabled();
  });

  test('should handle connection errors gracefully', async ({ page }) => {
    await helpers.navigateToDocument(1);
    
    // Mock network failure
    await page.route('**/ai/agents/chat/stream', route => {
      route.abort('failed');
    });
    
    // Try to send a message
    await helpers.sendChatMessage('test message');
    
    // Verify error message appears
    await helpers.verifyErrorMessage('Connection failed');
  });

  test('should handle backend errors gracefully', async ({ page }) => {
    await helpers.navigateToDocument(1);
    
    // Mock backend error
    await page.route('**/ai/agents/chat/stream', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal server error' })
      });
    });
    
    // Try to send a message
    await helpers.sendChatMessage('test message');
    
    // Verify error message appears
    await helpers.verifyErrorMessage('Failed to send message');
  });

  test('should display agent activity with timing information', async ({ page }) => {
    await helpers.navigateToDocument(1);
    
    // Send a document generation request
    await helpers.sendChatMessage('create a simple business plan');
    
    // Wait for agent activity
    await helpers.waitForAgentActivity();
    
    // Check agent process dropdown
    const processDropdown = page.locator('[data-testid="agent-process-dropdown"]');
    await expect(processDropdown).toBeVisible();
    
    // Verify timing information
    await expect(page.locator('[data-testid="process-start-time"]')).toBeVisible();
    
    // Wait for completion
    await helpers.verifyAgentProcessCompleted();
    
    // Verify completion timing
    await expect(page.locator('[data-testid="process-end-time"]')).toBeVisible();
    await expect(page.locator('[data-testid="process-duration"]')).toBeVisible();
  });

  test('should handle different document types', async ({ page }) => {
    await helpers.navigateToDocument(1);
    
    const documentTypes = [
      { message: 'create a technical report', expectedContent: 'technical|report' },
      { message: 'write a business memo', expectedContent: 'memo|business' },
      { message: 'generate a presentation outline', expectedContent: 'presentation|outline' },
      { message: 'draft a project proposal', expectedContent: 'proposal|project' }
    ];
    
    for (const { message, expectedContent } of documentTypes) {
      // Send message
      await helpers.sendChatMessage(message);
      
      // Wait for response
      await helpers.waitForChatResponse();
      
      // Verify document content
      await helpers.waitForDocumentPreviewUpdate();
      
      const documentPreview = page.locator('[data-testid="document-preview"]');
      await expect(documentPreview).toContainText(new RegExp(expectedContent, 'i'));
      
      // Wait before next test
      await page.waitForTimeout(1000);
    }
  });

  test('should update document word count after generation', async ({ page }) => {
    await helpers.navigateToDocument(1);
    
    // Get initial word count
    const initialWordCount = await helpers.getDocumentWordCount();
    
    // Send document generation request
    await helpers.sendChatMessage('create a comprehensive business plan');
    
    // Wait for document generation
    await helpers.waitForChatResponse();
    await helpers.waitForDocumentPreviewUpdate();
    
    // Get updated word count
    const updatedWordCount = await helpers.getDocumentWordCount();
    
    // Verify word count increased
    expect(updatedWordCount).toBeGreaterThan(initialWordCount);
  });

  test('should handle chat history correctly', async ({ page }) => {
    await helpers.navigateToDocument(1);
    
    // Send multiple messages
    const messages = [
      'Hello, how are you?',
      'Create a business plan',
      'Add more details to the plan'
    ];
    
    for (const message of messages) {
      await helpers.sendChatMessage(message);
      await helpers.waitForChatResponse();
      await page.waitForTimeout(500);
    }
    
    // Verify all messages are visible in chat history
    for (const message of messages) {
      await helpers.verifyChatMessage(message, 'user');
    }
    
    // Verify assistant responses
    const assistantMessages = page.locator('[data-testid="chat-message"][data-role="assistant"]');
    const count = await assistantMessages.count();
    expect(count).toBe(messages.length);
  });

  test('should scroll to bottom on new messages', async ({ page }) => {
    await helpers.navigateToDocument(1);
    
    // Send multiple messages to create scroll
    for (let i = 0; i < 10; i++) {
      await helpers.sendChatMessage(`Message ${i + 1}`);
      await helpers.waitForChatResponse();
    }
    
    // Verify chat is scrolled to bottom
    const chatMessages = page.locator('[data-testid="chat-messages"]');
    const scrollTop = await chatMessages.evaluate(el => el.scrollTop);
    const scrollHeight = await chatMessages.evaluate(el => el.scrollHeight);
    const clientHeight = await chatMessages.evaluate(el => el.clientHeight);
    
    expect(scrollTop).toBeGreaterThan(scrollHeight - clientHeight - 50); // Allow some tolerance
  });

  test('should handle long messages correctly', async ({ page }) => {
    await helpers.navigateToDocument(1);
    
    // Send a very long message
    const longMessage = 'This is a very long message that should be handled correctly by the chat interface. '.repeat(50);
    await helpers.sendChatMessage(longMessage);
    
    // Verify message is displayed correctly
    await helpers.verifyChatMessage(longMessage, 'user');
    
    // Verify it doesn't break the layout
    const chatInterface = page.locator('[data-testid="chat-interface"]');
    await expect(chatInterface).toBeVisible();
  });
});