import { test, expect } from '@playwright/test';
import { TestHelpers } from './utils/test-helpers';

test.describe('Sample E2E Test - Complete Document Generation Workflow', () => {
  let helpers: TestHelpers;

  test.beforeEach(async ({ page }) => {
    helpers = new TestHelpers(page);
  });

  test('should complete full document generation workflow like a real user', async ({ page }) => {
    // Step 1: Navigate to document list
    await helpers.navigateToDocumentList();
    
    // Step 2: Wait for page to load
    await helpers.waitForLoadingToComplete();
    
    // Step 3: Navigate to a document (or create one if needed)
    try {
      // Try to navigate to document 1
      await helpers.navigateToDocument(1);
    } catch {
      // If document doesn't exist, this test will adapt
      console.log('Document 1 not found, test will adapt to available documents');
    }
    
    // Step 4: Wait for document workspace to load
    await helpers.waitForAppToLoad();
    
    // Step 5: Verify the workspace is displayed correctly
    await expect(page.locator('[data-testid="document-workspace"]')).toBeVisible();
    await expect(page.locator('[data-testid="chat-interface"]')).toBeVisible();
    await expect(page.locator('[data-testid="document-preview"]')).toBeVisible();
    
    // Step 6: Send a document generation request (the main user story)
    const userMessage = 'create a business plan template';
    await helpers.sendChatMessage(userMessage);
    
    // Step 7: Verify user message appears in chat
    await helpers.verifyChatMessage(userMessage, 'user');
    
    // Step 8: Wait for AI processing to start
    await helpers.waitForAgentActivity();
    
    // Step 9: Verify agent activity is visible to user
    await expect(page.locator('[data-testid="agent-activity"], .text-gray-500:has-text("Analyzing")')).toBeVisible();
    
    // Step 10: Wait for processing to complete (with extended timeout for real generation)
    await helpers.waitForChatResponse();
    
    // Step 11: Verify assistant response
    const assistantMessage = page.locator('[data-testid="chat-message"][data-role="assistant"]').last();
    await expect(assistantMessage).toBeVisible();
    
    // Step 12: Verify document preview was updated
    await helpers.waitForDocumentPreviewUpdate();
    
    // Step 13: Verify document contains business plan content
    await helpers.verifyDocumentContent('business plan');
    
    // Step 14: Verify document statistics updated
    const wordCount = await helpers.getDocumentWordCount();
    expect(wordCount).toBeGreaterThan(0);
    
    // Step 15: Test export functionality
    await helpers.switchToPreviewMode();
    
    // Step 16: Verify export options are available
    await expect(page.locator('button:has-text("Export")')).toBeVisible();
    
    // Step 17: Test mode switching
    await helpers.switchToEditMode();
    await expect(page.locator('button:has-text("Edit")')).toHaveClass(/bg-white text-blue-600/);
    
    await helpers.switchToPreviewMode();
    await expect(page.locator('button:has-text("Preview")')).toHaveClass(/bg-white text-blue-600/);
    
    // Step 18: Test additional interaction
    await helpers.sendChatMessage('add more details to the executive summary');
    await helpers.waitForChatResponse();
    
    // Step 19: Verify system handled follow-up request
    await expect(page.locator('[data-testid="chat-message"][data-role="assistant"]').last()).toBeVisible();
    
    console.log('✅ Complete document generation workflow test passed!');
  });

  test('should handle the specific user issue - business plan template generation', async ({ page }) => {
    // This test specifically addresses the user's reported issue:
    // "I sent 'create a business plan template' and I got nothing in the document preview"
    
    await helpers.navigateToDocument(1);
    await helpers.waitForAppToLoad();
    
    // Send the exact message that was causing issues
    await helpers.sendChatMessage('create a business plan template');
    
    // Verify user message appears
    await helpers.verifyChatMessage('create a business plan template', 'user');
    
    // Wait for agent processing
    await helpers.waitForAgentActivity();
    
    // Verify agent process is visible to user
    await expect(page.locator('[data-testid="agent-activity"], .text-gray-500:has-text("Analyzing")')).toBeVisible();
    
    // Wait for processing to complete
    await helpers.waitForChatResponse();
    
    // Verify assistant response
    const assistantMessage = page.locator('[data-testid="chat-message"][data-role="assistant"]').last();
    await expect(assistantMessage).toBeVisible();
    await expect(assistantMessage).toContainText(/created|business plan|template/i);
    
    // The critical test: verify document preview shows content
    await helpers.waitForDocumentPreviewUpdate();
    
    // Verify document preview has content (this was failing before)
    const documentPreview = page.locator('[data-testid="document-preview"]');
    await expect(documentPreview).toBeVisible();
    await expect(documentPreview).not.toBeEmpty();
    
    // Verify business plan structure
    await helpers.verifyDocumentContent('Executive Summary');
    await helpers.verifyDocumentContent('Business Plan');
    
    // Verify word count increased
    const wordCount = await helpers.getDocumentWordCount();
    expect(wordCount).toBeGreaterThan(100); // Should have substantial content
    
    console.log('✅ Business plan template generation issue resolved!');
  });
});